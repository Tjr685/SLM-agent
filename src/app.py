"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from http import HTTPStatus
import json
import logging
import asyncio
from datetime import datetime

from aiohttp import web
from botbuilder.core import TurnContext, MessageFactory
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes

from bot import bot_app
from webhook_handler import JiraWebhookHandler
from teams_notifier import initialize_teams_notifier, send_teams_notification
from customer_actions import CustomerActionsHandler


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize webhook handler
webhook_handler = JiraWebhookHandler()

# Initialize Teams notifier
teams_notifier = initialize_teams_notifier(bot_app.adapter)

# Initialize customer actions handler
customer_actions_handler = CustomerActionsHandler()

def extract_action_from_ticket(ticket_data):
    """
    Extract the action type and details from JIRA ticket data
    Returns: (action_type, action_details)
    """
    try:
        if not ticket_data or not ticket_data.get('issue'):
            return None, {}
        
        issue = ticket_data['issue']
        fields = issue.get('fields', {})
        
        # Extract summary and description
        summary = fields.get('summary', '').lower()
        description = fields.get('description', '')
        
        # Parse description if it exists
        description_text = ""
        if description:
            if isinstance(description, dict):
                # Handle ADF (Atlassian Document Format) content
                content = description.get('content', [])
                for item in content:
                    if item.get('type') == 'paragraph':
                        for text_item in item.get('content', []):
                            if text_item.get('type') == 'text':
                                description_text += text_item.get('text', '') + " "
            else:
                description_text = str(description)
        
        description_text = description_text.lower()
        full_text = f"{summary} {description_text}"
        
        print(f"🔍 Analyzing ticket text: {full_text}")
        
        # Determine action type based on keywords
        action_details = {"customer_id": "CUST001"}  # Default customer ID
        
        if any(keyword in full_text for keyword in ["extend trial", "trial extension", "extend the trial"]):
            return "extend_trial", action_details
        elif any(keyword in full_text for keyword in ["upgrade", "enterprise", "upgrade subscription"]):
            return "upgrade_subscription", action_details
        elif any(keyword in full_text for keyword in ["enable feature", "enable beta", "activate feature"]):
            # Try to extract feature name
            feature = None
            for allowed_feature in customer_actions_handler.allowed_features:
                if allowed_feature.lower() in full_text:
                    feature = allowed_feature
                    break
            if feature:
                action_details["feature"] = feature
                return "enable_feature", action_details
        elif any(keyword in full_text for keyword in ["approve signup", "activate account", "signup approval"]):
            return "approve_signup", action_details
        elif any(keyword in full_text for keyword in ["extend subscription", "subscription extension"]):
            return "extend_subscription", action_details
        
        # Default fallback
        print(f"⚠️ Could not determine action type from ticket text")
        return None, {}
        
    except Exception as e:
        print(f"❌ Error extracting action from ticket: {e}")
        return None, {}

async def execute_customer_action_and_notify(ticket_key, ticket_data):
    """
    Execute customer action based on ticket content and send result to Teams
    """
    try:
        # Extract action type from ticket
        action_type, action_details = extract_action_from_ticket(ticket_data)
        
        if not action_type:
            # Send generic approval message
            notification = f"""🎉 **JIRA TICKET APPROVED**
            
✅ Ticket {ticket_key} has been approved!
⚠️ Could not determine specific action to execute.
👥 Please check ticket details manually.

This notification was triggered by JIRA approval."""
            await send_teams_notification(notification, ticket_key)
            return
        
        print(f"🚀 Executing action: {action_type} with details: {action_details}")
        
        # Execute the customer action
        result = await customer_actions_handler.execute_customer_action(
            action_type, 
            action_details.get("customer_id", "CUST001"), 
            **action_details
        )
        
        print(f"📋 Action result: {result}")
        
        # Format result for Teams notification
        if result.get("status") == "success":
            notification = f"""✅ **ACTION COMPLETED SUCCESSFULLY**
            
🎉 Ticket {ticket_key} has been approved and processed!
🔧 Action: {action_type.replace('_', ' ').title()}
✅ Result: {result.get("message", "Action completed successfully")}

The requested customer action has been executed."""
        else:
            notification = f"""⚠️ **ACTION COMPLETED WITH ISSUES**
            
✅ Ticket {ticket_key} was approved but action execution had issues.
🔧 Action: {action_type.replace('_', ' ').title()}
❌ Error: {result.get("message", "Unknown error occurred")}

Please review the action manually."""
        
        # Send notification to Teams
        await send_teams_notification(notification, ticket_key)
        
        print(f"📨 Sent action result notification for ticket {ticket_key}")
        
    except Exception as e:
        print(f"❌ Error executing customer action for ticket {ticket_key}: {e}")
        
        # Send error notification
        error_notification = f"""❌ **ACTION EXECUTION ERROR**
        
✅ Ticket {ticket_key} was approved but action execution failed.
🔧 Error: {str(e)}

Please review and execute the action manually."""
        
        await send_teams_notification(error_notification, ticket_key)

routes = web.RouteTableDef()

@routes.post("/api/messages")
async def on_messages(req: web.Request) -> web.Response:
    # Process normally through the bot
    res = await bot_app.process(req)

    if res is not None:
        return res

    return web.Response(status=HTTPStatus.OK)

@routes.post("/webhook/jira")
async def jira_webhook(req: web.Request) -> web.Response:
    """Handle JIRA webhook events"""
    try:
        # Get the webhook payload
        data = await req.json()
        
        if not data:
            logger.warning("Received empty webhook payload")
            return web.json_response({"error": "Empty payload"}, status=400)
        
        # Extract ticket key if available
        ticket_key = None
        if data.get('issue') and data['issue'].get('key'):
            ticket_key = data['issue']['key']
        
        # Log the webhook event
        webhook_event = data.get('webhookEvent', 'unknown')
        logger.info(f"Received JIRA webhook: {webhook_event} for ticket {ticket_key}")
        print(f"DEBUG: Received JIRA webhook for ticket {ticket_key}")
        
        # Save webhook data to file for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"webhook_data_{ticket_key}_{timestamp}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"📁 Webhook data saved to: {filename}")
        except Exception as save_error:
            print(f"❌ Failed to save webhook data: {save_error}")
        
        # Print the full webhook data
        print("="*80)
        print("FULL WEBHOOK DATA:")
        print(json.dumps(data, indent=2, default=str))
        print("="*80)
        
        # Extract and print customfield_10094 information
        print("\n" + "="*50)
        print("CUSTOMFIELD_10094 ANALYSIS:")
        print("="*50)
        
        if data.get('issue') and data['issue'].get('fields'):
            customfield_10094 = data['issue']['fields'].get('customfield_10094')
            
            if customfield_10094:
                print(f"✅ customfield_10094 EXISTS:")
                print(f"📋 Type: {type(customfield_10094)}")
                print(f"📄 Content:")
                print(json.dumps(customfield_10094, indent=2, default=str))
                
                # If it's a list, analyze each item
                if isinstance(customfield_10094, list):
                    print(f"\n📊 List contains {len(customfield_10094)} items:")
                    for i, item in enumerate(customfield_10094):
                        print(f"\n  Item {i+1}:")
                        if isinstance(item, dict):
                            for key, value in item.items():
                                print(f"    {key}: {value}")
                        else:
                            print(f"    {item}")
                
                # Check for approval-related fields
                if isinstance(customfield_10094, list) and len(customfield_10094) > 0:
                    approval_item = customfield_10094[0]
                    if isinstance(approval_item, dict):
                        final_decision = approval_item.get('finalDecision')
                        approval_name = approval_item.get('name')
                        approvers = approval_item.get('approvers', [])
                        
                        print(f"\n🔍 APPROVAL DETAILS:")
                        print(f"   Name: {approval_name}")
                        print(f"   Final Decision: {final_decision}")
                        print(f"   Number of Approvers: {len(approvers)}")
                        
                        if approvers:
                            for j, approver in enumerate(approvers):
                                if isinstance(approver, dict):
                                    approver_decision = approver.get('approverDecision')
                                    approver_info = approver.get('approver', {})
                                    approver_name = approver_info.get('displayName', 'Unknown')
                                    print(f"   Approver {j+1}: {approver_name} - Decision: {approver_decision}")
            else:
                print("❌ customfield_10094 is NULL or does not exist")
        else:
            print("❌ No issue.fields found in webhook data")
        
        print("="*50 + "\n")
        
        # Extract status change if available
        # status_change = None
        # if data.get('changelog'):
        #     print("getting changelog items")
        #     for item in data['changelog']['items']:
        #         print("item is ", item)
        #         if item.get('field') == 'status':
        #             status_change = {
        #                 'from': item.get('fromString'),
        #                 'to': item.get('toString')
        #             }
        
        # Also check approval status from customfield_10094
        approval_status_change = None
        if data.get('issue') and data['issue'].get('fields'):
            customfield_10094 = data['issue']['fields'].get('customfield_10094')
            if customfield_10094 and isinstance(customfield_10094, list) and len(customfield_10094) > 0:
                approval_item = customfield_10094[0]
                if isinstance(approval_item, dict):
                    final_decision = approval_item.get('finalDecision')
                    if final_decision == 'approved':
                        approval_status_change = {
                            'from': 'Pending Approval',
                            'to': 'Approved'
                        }
                        print(f"🎯 APPROVAL DETECTED from customfield_10094: {approval_status_change}")
        
        print(f"DEBUG: Status change detected: {approval_status_change}")
        print(f"DEBUG: Approval status change detected: {approval_status_change}")
        
        # Check for approval either from status change or approval field
        should_notify = False
        notification_reason = ""
        
        if approval_status_change and approval_status_change['to'] == 'Approved':
            should_notify = True
            notification_reason = "Status changed to Approved"
        elif approval_status_change:
            should_notify = True
            notification_reason = "Approval workflow completed"
        
        if should_notify:
            # First, execute the customer action based on ticket content
            await execute_customer_action_and_notify(ticket_key, data)
            
            # Then send the generic approval notification
            notification = f"""🎉 **JIRA TICKET UPDATE: APPROVED**

            ✅ Ticket {ticket_key} has been APPROVED!
            🚀 The requested action is now being processed.
            ⏱️ You will receive updates as the action completes.

            📋 Reason: {notification_reason}
            This notification was triggered by a status change in JIRA."""
            
            # Send proactive notification to Teams
            await send_teams_notification(notification, ticket_key)
            
            # Log the notification
            print(f"📨 Sent JIRA approval notification for ticket {ticket_key} - Reason: {notification_reason}")
            logger.info(f"Sent proactive notification for ticket {ticket_key} - {notification_reason}")
        else:
            print(f"ℹ️  No approval notification sent for ticket {ticket_key}")
        
        return web.json_response({"status": "processed"}, status=200)
        
    except Exception as e:
        logger.error(f"Error processing JIRA webhook: {e}")
        print(f"ERROR processing webhook: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({"error": "Processing failed"}, status=500)

@routes.get("/webhook/health")
async def webhook_health(req: web.Request) -> web.Response:
    """Health check for webhook"""
    return web.json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})

@routes.get("/test/jira-approval")
async def test_jira_approval(req: web.Request) -> web.Response:
    """Test endpoint to simulate a JIRA ticket approval notification in Teams"""
    ticket_key = req.query.get('ticket', 'CST-123')
    
    try:
        # Create a notification message directly
        notification = f"""🎉 **TEST NOTIFICATION - JIRA TICKET APPROVED!**

✅ **Ticket {ticket_key}** has been approved!
⏱️ **Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a test notification to verify Teams messaging is working."""
        
        # Print to console
        print("\n" + "="*50)
        print("TEST NOTIFICATION (JIRA Approval):")
        print(notification)
        print("="*50 + "\n")
        
        # Send proactive notification to Teams
        await send_teams_notification(notification)
        
        return web.json_response({
            "status": "sent", 
            "message": "Test notification sent to Teams successfully"
        })
            
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return web.json_response({"error": str(e)}, status=500)

@routes.get("/test/send-notification")
async def test_send_notification(req: web.Request) -> web.Response:
    """Test endpoint to send a simple notification"""
    message = req.query.get('message', 'Test notification from JIRA webhook!')
    
    try:
        await send_teams_notification(message)
        return web.json_response({
            "status": "success",
            "message": "Notification sent successfully"
        })
    except Exception as e:
        logger.error(f"Error in test notification: {e}")
        return web.json_response({
            "status": "error", 
            "error": str(e)
        }, status=500)

app = web.Application(middlewares=[aiohttp_error_middleware])
app.add_routes(routes)

from config import Config

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=Config.PORT)