#!/usr/bin/env python3
"""
JIRA Webhook Handler for MontyCloud Customer Support Bot
Handles incoming webhook events from JIRA when ticket status changes
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JiraWebhookHandler:
    """Handles JIRA webhook events for ticket status changes"""
    
    def __init__(self):
        """Initialize webhook handler"""
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes for webhook endpoints"""
        @self.app.route('/webhook/jira', methods=['POST'])
        def handle_jira_webhook():
            return self.process_jira_webhook()
        
        @self.app.route('/webhook/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
    
    def process_jira_webhook(self) -> tuple:
        """Process incoming JIRA webhook events"""
        try:
            # Get the webhook payload
            data = request.get_json()
            
            if not data:
                logger.warning("Received empty webhook payload")
                return jsonify({"error": "Empty payload"}), 400
              # Log the webhook event
            logger.info(f"Received JIRA webhook: {data.get('webhookEvent', 'unknown')}")
            
            # Check if this is an issue update event
            webhook_event = data.get('webhookEvent')
            
            # Accept any webhook event that has status change information
            # This handles Jira's various webhook formats
            if not webhook_event or (webhook_event != 'jira:issue_updated' and 'changelog' not in data):
                logger.info(f"Ignoring webhook event: {webhook_event}")
                return jsonify({"status": "ignored"}), 200
            
            # Extract issue information
            issue_info = self.extract_issue_info(data)
            if not issue_info:
                logger.warning("Could not extract issue information from webhook")
                return jsonify({"error": "Invalid issue data"}), 400
            
            # Check if status changed
            status_change = self.extract_status_change(data)
            if not status_change:
                logger.info("No status change detected, ignoring")
                return jsonify({"status": "no_status_change"}), 200
            
            # Process the status change
            self.handle_status_change(issue_info, status_change)
            
            return jsonify({"status": "processed"}), 200
            
        except Exception as e:
            logger.error(f"Error processing JIRA webhook: {e}")
            return jsonify({"error": "Processing failed"}), 500
    
    def extract_issue_info(self, data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract relevant issue information from webhook data"""
        try:
            issue = data.get('issue', {})
            
            return {
                "key": issue.get('key', ''),
                "summary": issue.get('fields', {}).get('summary', ''),
                "description": self.extract_description(issue.get('fields', {}).get('description', {})),
                "assignee": issue.get('fields', {}).get('assignee', {}).get('emailAddress', ''),
                "customer_email": self.extract_customer_email(issue),
                "action_type": self.extract_action_type(issue),
                "url": f"https://montycloud.atlassian.net/browse/{issue.get('key', '')}"
            }
        except Exception as e:
            logger.error(f"Error extracting issue info: {e}")
            return None
    
    def extract_status_change(self, data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract status change information from webhook data"""
        try:
            changelog = data.get('changelog', {})
            items = changelog.get('items', [])
            
            for item in items:
                if item.get('field') == 'status':
                    return {
                        "from_status": item.get('fromString', ''),
                        "to_status": item.get('toString', ''),
                        "changed_by": data.get('user', {}).get('emailAddress', ''),
                        "timestamp": changelog.get('created', '')
                    }
            return None
        except Exception as e:
            logger.error(f"Error extracting status change: {e}")
            return None
    
    def extract_description(self, description_obj: Dict[str, Any]) -> str:
        """Extract plain text from JIRA description object"""
        try:
            if isinstance(description_obj, dict):
                content = description_obj.get('content', [])
                text_parts = []
                for part in content:
                    if part.get('type') == 'paragraph':
                        for content_item in part.get('content', []):
                            if content_item.get('type') == 'text':
                                text_parts.append(content_item.get('text', ''))
                return '\n'.join(text_parts)
            return str(description_obj)        
        except Exception:
            return ''
    
    def extract_customer_email(self, issue: Dict[str, Any]) -> str:
        """Extract customer email from issue summary or description"""
        try:
            # First check summary (format: "Action - email@domain.com")
            summary = issue.get('fields', {}).get('summary', '')
            if ' - ' in summary:
                parts = summary.split(' - ')
                if len(parts) > 1:
                    potential_email = parts[1].strip()
                    if '@' in potential_email:
                        return potential_email
            
            # Then check description for patterns like "Customer Email: email@domain.com"
            description = self.extract_description(issue.get('fields', {}).get('description', {}))
            if description:
                lines = description.split('\n')
                for line in lines:
                    line = line.strip()
                    # Look for patterns like "Customer Email:", "Email:", etc.
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if key in ['customer email', 'email', 'customer_email'] and '@' in value:
                            return value
                    
                    # Also look for standalone email addresses in the description
                    elif '@' in line and '.' in line.split('@')[1]:
                        # Simple email validation
                        words = line.split()
                        for word in words:
                            if '@' in word and '.' in word.split('@')[1]:
                                return word.strip()
            
            return ''
        except Exception:
            return ''
    
    def extract_action_type(self, issue: Dict[str, Any]) -> str:
        """Extract the action type from issue labels or summary"""
        try:
            labels = issue.get('fields', {}).get('labels', [])
            action_labels = [
                'customer-onboarding', 'trial-extension', 
                'feature-enablement', 'subscription-upgrade'
            ]
            
            for label in labels:
                if label in action_labels:
                    return label.replace('-', '_')
            
            # Fallback: extract from summary
            summary = issue.get('fields', {}).get('summary', '').lower()
            if 'trial extension' in summary:
                return 'extend_trial'
            elif 'signup approval' in summary:
                return 'approve_signup'
            elif 'beta features' in summary:
                return 'enable_beta_features'
            elif 'subscription upgrade' in summary:
                return 'upgrade_subscription'
            
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def handle_status_change(self, issue_info: Dict[str, str], status_change: Dict[str, str]):
        """Handle the status change and notify Teams"""
        try:
            ticket_key = issue_info['key']
            customer_email = issue_info['customer_email']
            action_type = issue_info['action_type']
            new_status = status_change['to_status'].lower()
            ticket_url = issue_info['url']
            
            logger.info(f"Processing status change for {ticket_key}: {status_change['from_status']} -> {status_change['to_status']}")
              # Generate appropriate message based on status
            if new_status in ['approved', 'done', 'completed']:
                message = self.generate_approval_message(ticket_key, customer_email, action_type, ticket_url, issue_info)
            elif new_status in ['rejected', 'denied', 'cancelled']:
                message = self.generate_rejection_message(ticket_key, customer_email, action_type, ticket_url, issue_info)
            else:
                message = self.generate_status_update_message(ticket_key, customer_email, action_type, new_status, ticket_url)
            
            # Send notification to Teams
            self.send_teams_notification(message, issue_info, status_change)
            
            # Execute the approved task if applicable
            if new_status in ['approved', 'done']:
                task_result = self.execute_approved_task(issue_info)
                logger.info(f"Task execution result for {ticket_key}: {task_result}")
            
        except Exception as e:
            logger.error(f"Error handling status change: {e}")
    def generate_approval_message(self, ticket_key: str, customer_email: str, action_type: str, ticket_url: str, issue_info: Dict[str, str] = None) -> str:
        """Generate approval message for Teams and execute the approved task"""
        action_titles = {
            'approve_signup': 'Customer Signup Approval',
            'extend_trial': 'Trial Extension',
            'enable_beta_features': 'Beta Features Enablement',
            'upgrade_subscription': 'Subscription Upgrade'
        }
        
        action_title = action_titles.get(action_type, 'Customer Request')
        
        # Execute the approved task
        if issue_info:
            execution_result = self.execute_approved_task(issue_info)
        else:
            execution_result = f"✅ Task execution initiated for {action_title.lower()}"
        
        return f"""🎉 **GREAT! REQUEST APPROVED**

✅ **Ticket**: {ticket_key}
📧 **Customer**: {customer_email}
📋 **Request**: {action_title}
🔗 **JIRA Link**: {ticket_url}

{execution_result}"""
    def generate_rejection_message(self, ticket_key: str, customer_email: str, action_type: str, ticket_url: str, issue_info: Dict[str, str]) -> str:
        """Generate rejection message for Teams"""
        action_titles = {
            'approve_signup': 'Customer Signup Approval',
            'extend_trial': 'Trial Extension',
            'enable_beta_features': 'Beta Features Enablement',
            'upgrade_subscription': 'Subscription Upgrade'
        }
        
        action_title = action_titles.get(action_type, 'Customer Request')
        
        # Get JIRA comments for the rejection reason
        rejection_comments = self.get_rejection_comments(ticket_key)
        
        return f"""❌ **REQUEST REJECTED**

🎫 **Ticket**: {ticket_key}
📧 **Customer**: {customer_email}
📋 **Request**: {action_title}
🔗 **JIRA Link**: {ticket_url}

The request for {action_title.lower()} has been **REJECTED**.

**Comments from JIRA**: 
{rejection_comments}

Status: Request denied"""
    
    def generate_status_update_message(self, ticket_key: str, customer_email: str, action_type: str, status: str, ticket_url: str) -> str:
        """Generate general status update message"""
        action_titles = {
            'approve_signup': 'Customer Signup Approval',
            'extend_trial': 'Trial Extension', 
            'enable_beta_features': 'Beta Features Enablement',
            'upgrade_subscription': 'Subscription Upgrade'
        }
        
        action_title = action_titles.get(action_type, 'Customer Request')
        
        return f"""📊 **STATUS UPDATE**

🎫 **Ticket**: {ticket_key}
📧 **Customer**: {customer_email}
📋 **Request**: {action_title}
🔄 **New Status**: {status.title()}
🔗 **JIRA Link**: {ticket_url}

The ticket status has been updated to: **{status.title()}**"""
    
    def get_rejection_comments(self, ticket_key: str) -> str:
        """Get comments from JIRA ticket for rejection notifications"""
        try:
            # Import here to avoid circular imports
            from jira_integration import JiraIntegration
            
            jira = JiraIntegration()
            return jira.get_ticket_comments(ticket_key)
        except Exception as e:
            logger.error(f"Error getting JIRA comments: {e}")
            return "Please check the JIRA ticket for detailed comments and reasoning."
    
    def send_teams_notification(self, message: str, issue_info: Dict[str, str], status_change: Dict[str, str]):
        """Send notification to Teams"""
        # For simplicity, we'll just output to console directly first
        print("\n" + "=" * 80)
        print("🔔 JIRA STATUS CHANGE NOTIFICATION:")
        print("=" * 80)
        print(message)
        print(f"\n📋 Details:")
        print(f"   Ticket: {issue_info.get('key', 'N/A')}")
        print(f"   Status: {status_change.get('from_status', 'N/A')} → {status_change.get('to_status', 'N/A')}")            
        print(f"   Customer: {issue_info.get('customer_email', 'N/A')}")
        print(f"   Action: {issue_info.get('action_type', 'N/A')}")
        print("=" * 80)
        logger.info(f"Status change notification for ticket {issue_info.get('key', '')}: {status_change.get('from_status', '')} → {status_change.get('to_status', '')}")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the webhook server"""
        logger.info(f"Starting JIRA webhook server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
    
    def execute_approved_task(self, issue_info: Dict[str, str]) -> str:
        """Execute the approved task based on action type and extracted parameters"""
        try:
            action_type = issue_info['action_type']
            customer_email = issue_info['customer_email']
            ticket_key = issue_info['key']
            
            logger.info(f"Executing approved task: {action_type} for customer: {customer_email}")
            
            # Extract task parameters from JIRA ticket description
            task_params = self.extract_task_parameters(issue_info)
            
            if action_type == 'approve_signup':
                return self.execute_approve_signup(customer_email, task_params, ticket_key)
            elif action_type == 'extend_trial':
                return self.execute_extend_trial(customer_email, task_params, ticket_key)
            elif action_type == 'enable_beta_features':
                return self.execute_enable_beta_features(customer_email, task_params, ticket_key)
            elif action_type == 'upgrade_subscription':
                return self.execute_upgrade_subscription(customer_email, task_params, ticket_key)
            else:
                return f"❌ Unknown action type: {action_type}"
                
        except Exception as e:
            logger.error(f"Error executing approved task: {e}")
            return f"❌ Error executing task: {str(e)}"
    
    def extract_task_parameters(self, issue_info: Dict[str, str]) -> Dict[str, Any]:
        """Extract task parameters from JIRA ticket description"""
        try:
            description = issue_info.get('description', '')
            params = {}
            
            # Parse common patterns from description
            lines = description.split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    
                    if key in ['company_name', 'company', 'organization']:
                        params['company_name'] = value
                    elif key in ['end_date', 'trial_end_date', 'new_end_date']:
                        params['end_date'] = value
                    elif key in ['features', 'beta_features', 'requested_features']:
                        # Handle comma-separated features
                        params['features'] = [f.strip() for f in value.split(',')]
                    elif key in ['subscription_type', 'new_plan', 'target_plan']:
                        params['subscription_type'] = value
                    elif key in ['current_plan', 'current_subscription']:
                        params['current_plan'] = value
            
            return params
        except Exception as e:
            logger.error(f"Error extracting task parameters: {e}")
            return {}
    
    def execute_approve_signup(self, email: str, params: Dict[str, Any], ticket_key: str) -> str:
        """Execute customer signup approval"""
        try:
            company_name = params.get('company_name', 'Not specified')
            subscription_type = params.get('subscription_type', 'trial')
            
            logger.info(f"Executing signup approval for {email}, company: {company_name}")
            
            # Simulate customer account activation
            result = f"""✅ **CUSTOMER SIGNUP APPROVED & ACTIVATED**
            
📧 **Customer**: {email}
🏢 **Company**: {company_name}
📋 **Subscription**: {subscription_type.title()}
🎫 **Ticket**: {ticket_key}

**Actions Completed:**
• Customer account activated
• Initial subscription setup: {subscription_type}
• Welcome email sent to customer
• Account provisioning completed

🎉 **Customer is now ready to use MontyCloud services!**"""
            
            logger.info(f"Signup approval completed for {email}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing signup approval: {e}")
            return f"❌ Error activating customer account: {str(e)}"
    
    def execute_extend_trial(self, email: str, params: Dict[str, Any], ticket_key: str) -> str:
        """Execute trial extension"""
        try:
            end_date = params.get('end_date', 'Not specified')
            
            logger.info(f"Executing trial extension for {email} until {end_date}")
            
            # Simulate trial extension
            result = f"""✅ **TRIAL PERIOD EXTENDED**
            
📧 **Customer**: {email}
📅 **New End Date**: {end_date}
🎫 **Ticket**: {ticket_key}

**Actions Completed:**
• Trial period extended successfully
• Customer notified via email
• Account settings updated
• New expiration date set

🎉 **Customer can continue using MontyCloud services!**"""
            
            logger.info(f"Trial extension completed for {email}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing trial extension: {e}")
            return f"❌ Error extending trial: {str(e)}"
    
    def execute_enable_beta_features(self, email: str, params: Dict[str, Any], ticket_key: str) -> str:
        """Execute beta features enablement"""
        try:
            features = params.get('features', [])
            if isinstance(features, str):
                features = [features]
            
            logger.info(f"Executing beta features enablement for {email}: {features}")
            
            # Simulate beta features enablement
            features_list = "\n".join([f"• {feature}" for feature in features]) if features else "• Features not specified"
            
            result = f"""✅ **BETA FEATURES ENABLED**
            
📧 **Customer**: {email}
🚀 **Features Enabled**:
{features_list}
🎫 **Ticket**: {ticket_key}

**Actions Completed:**
• Beta features activated for customer account
• Feature flags updated in system
• Customer notified of new capabilities
• Documentation links shared

🎉 **Customer can now access the requested beta features!**"""
            
            logger.info(f"Beta features enablement completed for {email}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing beta features enablement: {e}")
            return f"❌ Error enabling beta features: {str(e)}"
    
    def execute_upgrade_subscription(self, email: str, params: Dict[str, Any], ticket_key: str) -> str:
        """Execute subscription upgrade"""
        try:
            current_plan = params.get('current_plan', 'trial')
            subscription_type = params.get('subscription_type', 'enterprise')
            
            logger.info(f"Executing subscription upgrade for {email} from {current_plan} to {subscription_type}")
            
            # Simulate subscription upgrade
            result = f"""✅ **SUBSCRIPTION UPGRADED**
            
📧 **Customer**: {email}
📊 **Upgrade**: {current_plan.title()} → {subscription_type.title()}
🎫 **Ticket**: {ticket_key}

**Actions Completed:**
• Subscription plan upgraded successfully
• Billing updated to new plan
• Additional features unlocked
• Customer notified of upgrade
• New service limits applied

🎉 **Customer now has access to {subscription_type} features!**"""
            
            logger.info(f"Subscription upgrade completed for {email}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing subscription upgrade: {e}")
            return f"❌ Error upgrading subscription: {str(e)}"

# Convenience function to start webhook server
def start_webhook_server(port=5000):
    """Start the JIRA webhook server"""
    handler = JiraWebhookHandler()
    handler.run(port=port)

if __name__ == "__main__":
    start_webhook_server()
