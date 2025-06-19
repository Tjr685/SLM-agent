#!/usr/bin/env python3
"""
Teams Notification Service for JIRA Webhook Integration
Sends proactive messages to Teams when JIRA ticket status changes
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from botbuilder.core import TurnContext, MessageFactory
from botbuilder.core.conversation_state import ConversationState
from botbuilder.core.user_state import UserState
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount
from teams import Application
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamsNotifier:
    """Handles proactive messaging to Teams for JIRA updates"""
    
    def __init__(self, bot_app: Application):
        """Initialize Teams notifier with bot application"""
        self.bot_app = bot_app
        self.config = Config()
    
    async def send_proactive_message(self, message: str, conversation_reference: Dict[str, Any] = None):
        """Send a proactive message to Teams"""
        try:
            if conversation_reference:
                # Send to specific conversation
                await self._send_to_conversation(message, conversation_reference)
            else:
                # Send to default channel or user
                await self._send_to_default_target(message)
                
        except Exception as e:
            logger.error(f"Error sending proactive message: {e}")
    
    async def _send_to_conversation(self, message: str, conversation_reference: Dict[str, Any]):
        """Send message to a specific conversation"""
        try:
            # Create message activity
            message_activity = MessageFactory.text(message)
            
            # Send proactive message
            await self.bot_app.adapter.continue_conversation(
                conversation_reference,
                self._send_message_callback(message_activity)
            )
            
            logger.info(f"Sent proactive message to conversation")
            
        except Exception as e:
            logger.error(f"Error sending to conversation: {e}")
    
    async def _send_to_default_target(self, message: str):
        """Send message to default target (placeholder)"""
        # TODO: Implement default target logic
        # This could be a specific Teams channel or user
        logger.info(f"Proactive message (default target): {message}")
    
    def _send_message_callback(self, message_activity: Activity):
        """Callback function for sending proactive messages"""
        async def callback(turn_context: TurnContext):
            await turn_context.send_activity(message_activity)
        return callback
    
    def format_jira_notification(self, issue_info: Dict[str, str], status_change: Dict[str, str]) -> str:
        """Format JIRA status change into Teams-friendly message"""
        ticket_key = issue_info.get('key', '')
        customer_email = issue_info.get('customer_email', '')
        action_type = issue_info.get('action_type', '')
        new_status = status_change.get('to_status', '').lower()
        ticket_url = issue_info.get('url', '')
        
        if new_status in ['approved', 'done', 'completed']:
            return self._format_approval_message(ticket_key, customer_email, action_type, ticket_url)
        elif new_status in ['rejected', 'denied', 'cancelled']:
            return self._format_rejection_message(ticket_key, customer_email, action_type, ticket_url)
        else:
            return self._format_status_update(ticket_key, customer_email, action_type, new_status, ticket_url)
    
    def _format_approval_message(self, ticket_key: str, customer_email: str, action_type: str, ticket_url: str) -> str:
        """Format approval message"""
        action_titles = {
            'approve_signup': 'activate the customer account',
            'extend_trial': 'extend the trial period',
            'enable_beta_features': 'enable the requested beta features',
            'upgrade_subscription': 'upgrade the subscription'
        }
        
        action_message = action_titles.get(action_type, 'process the request')
        
        return f"""🎉 **GREAT! REQUEST APPROVED**

✅ **Ticket**: {ticket_key}
📧 **Customer**: {customer_email}
🔗 **JIRA Link**: {ticket_url}

This ticket has been **APPROVED**! I will now go ahead and {action_message}."""
    
    def _format_rejection_message(self, ticket_key: str, customer_email: str, action_type: str, ticket_url: str) -> str:
        """Format rejection message"""
        return f"""❌ **REQUEST REJECTED**

🎫 **Ticket**: {ticket_key}
📧 **Customer**: {customer_email}
🔗 **JIRA Link**: {ticket_url}

The request has been **REJECTED**. Please check the JIRA ticket for detailed comments and reasoning."""
    
    def _format_status_update(self, ticket_key: str, customer_email: str, action_type: str, status: str, ticket_url: str) -> str:
        """Format general status update"""
        return f"""📊 **STATUS UPDATE**

🎫 **Ticket**: {ticket_key}
📧 **Customer**: {customer_email}
🔄 **New Status**: {status.title()}
🔗 **JIRA Link**: {ticket_url}"""

# Global notifier instance
_teams_notifier = None

def initialize_teams_notifier(bot_app: Application):
    """Initialize the global Teams notifier"""
    global _teams_notifier
    _teams_notifier = TeamsNotifier(bot_app)
    return _teams_notifier

def get_teams_notifier() -> Optional[TeamsNotifier]:
    """Get the global Teams notifier instance"""
    return _teams_notifier

async def notify_teams_status_change(issue_info: Dict[str, str], status_change: Dict[str, str]):
    """Convenience function to notify Teams of status change"""
    notifier = get_teams_notifier()
    if notifier:
        message = notifier.format_jira_notification(issue_info, status_change)
        await notifier.send_proactive_message(message)
    else:
        logger.warning("Teams notifier not initialized")
