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



# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize webhook handler
webhook_handler = JiraWebhookHandler()

# Helper function to send proactive messages to Teams
async def send_teams_notification(message_text):
    """
    Send a proactive message to Teams using the stored conversation references
    """
    from bot import conversation_references
    
    if not conversation_references:
        logger.warning("No conversation references available for proactive messaging")
        print(f"📢 TEAMS MESSAGE (No conversation available): {message_text}")
        return
        
    # Use the first available conversation reference
    conversation_reference = next(iter(conversation_references.values()))
    
    # Create a message activity
    message_activity = MessageFactory.text(message_text)
    
    # Use the bot's adapter to send the proactive message
    try:
        adapter = bot_app.adapter
        
        async def send_proactive(turn_context):
            await turn_context.send_activity(message_activity)
        
        await adapter.continue_conversation(
            conversation_reference,
            send_proactive
        )
        
        logger.info("Proactive Teams message sent successfully")
        print(f"📢 TEAMS MESSAGE SENT: {message_text}")
    except Exception as e:
        logger.error(f"Error sending proactive message: {e}")
        print(f"📢 TEAMS MESSAGE (Error): {message_text}")

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
        
        # Extract status change if available
        status_change = None
        if data.get('changelog') and data['changelog'].get('items'):
            for item in data['changelog']['items']:
                if item.get('field') == 'status':
                    status_change = {
                        'from': item.get('fromString'),
                        'to': item.get('toString')
                    }
        
        # If the status changed to Approved, send proactive notification
        if status_change and status_change['to'] == 'Approved':
            notification = f"""🎉 **JIRA TICKET UPDATE: APPROVED**

✅ Ticket {ticket_key} has been APPROVED!
🚀 The requested action is now being processed.
⏱️ You will receive updates as the action completes.

This notification was triggered by a status change in JIRA."""
            
            # Send proactive notification to Teams
            await send_teams_notification(notification)
            
            # Log the notification
            print(f"Sent JIRA approval notification for ticket {ticket_key}")
            logger.info(f"Sent proactive notification for ticket {ticket_key} status change to Approved")
        
        return web.json_response({"status": "processed"}, status=200)
        
    except Exception as e:
        logger.error(f"Error processing JIRA webhook: {e}")
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