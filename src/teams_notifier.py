"""
Teams proactive messaging module for sending notifications to users.
"""

import os
import logging
from typing import Dict, Optional
from botbuilder.core import BotFrameworkAdapter, TurnContext, MessageFactory
from botbuilder.schema import ConversationReference
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store conversation references by ticket key and user ID
# Format: {ticket_key: ConversationReference}
CONVERSATION_REFERENCES: Dict[str, ConversationReference] = {}
USER_INITIATED_TICKETS: Dict[str, str] = {}  # Maps ticket_key to user_id

class TeamsNotifier:
    """Handles proactive messaging to Teams users"""
    
    def __init__(self, adapter: BotFrameworkAdapter):
        """Initialize with bot adapter"""
        self.adapter = adapter
        
    async def send_notification(self, ticket_key: str, message: str) -> bool:
        """
        Send a notification to the user who initiated a specific ticket
        
        Args:
            ticket_key: The JIRA ticket key (e.g., CST-123)
            message: The message to send
            
        Returns:
            bool: True if message was sent, False otherwise
        """
        try:
            # Try to get the conversation reference for this ticket
            conversation_ref = CONVERSATION_REFERENCES.get(ticket_key)
            
            if not conversation_ref:
                logger.warning(f"No conversation reference found for ticket {ticket_key}")
                return False
            
            # Send the message using the stored conversation reference
            await self.adapter.continue_conversation(
                conversation_ref,
                lambda turn_context: self._send_message(turn_context, message),
                Config.APP_ID
            )
            
            logger.info(f"Proactive notification sent for ticket {ticket_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending proactive notification: {e}")
            return False
    
    async def _send_message(self, turn_context: TurnContext, message: str):
        """Helper to send a message in the continued conversation"""
        await turn_context.send_activity(message)
    
    async def send_to_all_users(self, message: str) -> int:
        """
        Send a notification to all users who have active conversations
        
        Args:
            message: The message to send
            
        Returns:
            int: Number of users notified
        """
        sent_count = 0
        unique_refs = set()
        
        # Deduplicate conversation references by conversation ID
        for ref in CONVERSATION_REFERENCES.values():
            # Create a unique key for this conversation to avoid duplicates
            conv_key = f"{ref.conversation.id}:{ref.conversation.conversation_type}"
            if conv_key not in unique_refs:
                unique_refs.add(conv_key)
                
                try:
                    # Send message to this unique conversation
                    await self.adapter.continue_conversation(
                        ref,
                        lambda turn_context: self._send_message(turn_context, message),
                        Config.APP_ID
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send message to conversation {conv_key}: {e}")
        
        return sent_count

def store_conversation_reference(ticket_key: str, reference: ConversationReference, user_id: str = None):
    """
    Store a conversation reference for future proactive messages
    
    Args:
        ticket_key: The JIRA ticket key (e.g., CST-123)
        reference: The conversation reference object
        user_id: Optional user ID for tracking who initiated the ticket
    """
    CONVERSATION_REFERENCES[ticket_key] = reference
    
    if user_id:
        USER_INITIATED_TICKETS[ticket_key] = user_id
        logger.info(f"Stored conversation reference for ticket {ticket_key} initiated by user {user_id}")
    else:
        logger.info(f"Stored conversation reference for ticket {ticket_key}")

# Global notifier instance (initialized later)
teams_notifier = None

def initialize_teams_notifier(adapter: BotFrameworkAdapter):
    """Initialize the global Teams notifier instance"""
    global teams_notifier
    teams_notifier = TeamsNotifier(adapter)
    return teams_notifier

# async def send_teams_notification(message: str, ticket_key: str = None):
#     """
#     Send a Teams notification that the ticket is approved
    
#     Args:
#         message: The message to send
#         ticket_key: Optional ticket key to target specific user
#     """
#     global teams_notifier
    
#     if not teams_notifier:
#         logger.error("Teams notifier not initialized. Call initialize_teams_notifier first.")
#         return False
    
#     if ticket_key:
#         # Send to specific user who initiated this ticket
#         return await teams_notifier.send_notification(ticket_key, message)
#     else:
#         # Send to all users (broadcast)
#         sent_count = await teams_notifier.send_to_all_users(message)
#         return sent_count > 0


async def send_teams_notification(message_text: str, ticket_key: str = None) -> bool:
    """Send proactive notification to Teams"""
    try:
        # Try different import patterns to find the correct one
        conversation_references = None
        adapter = None
        
        try:
            from bot import conversation_references, adapter
        except ImportError as e1:
            print(f"Import attempt 1 failed: {e1}")
            try:
                import bot
                conversation_references = getattr(bot, 'conversation_references', None)
                adapter = getattr(bot, 'adapter', None)
            except Exception as e2:
                print(f"Import attempt 2 failed: {e2}")
                try:
                    # Try importing the bot instance and get attributes
                    from bot import bot_instance
                    conversation_references = getattr(bot_instance, 'conversation_references', {})
                    adapter = getattr(bot_instance, 'adapter', None)
                except Exception as e3:
                    print(f"Import attempt 3 failed: {e3}")
                    # Last resort - check if there's a global variable
                    try:
                        import sys
                        bot_module = sys.modules.get('bot')
                        if bot_module:
                            conversation_references = getattr(bot_module, 'conversation_references', {})
                            adapter = getattr(bot_module, 'adapter', None)
                    except Exception as e4:
                        print(f"All import attempts failed: {e4}")
        
        if not conversation_references:
            logger.warning("No conversation references available for proactive messaging")
            print(f"📢 TEAMS MESSAGE (No conversation available): {message_text}")
            return False
        
        if not adapter:
            logger.error("Bot adapter not available for proactive messaging")
            print(f"📢 TEAMS MESSAGE (No adapter available): {message_text}")
            return False
        
        # Send to ALL active conversations instead of looking for specific ticket
        success_count = 0
        total_conversations = len(conversation_references)
        
        print(f"🔄 Attempting to send notification to {total_conversations} active conversations...")
        
        for conv_id, conversation_reference in conversation_references.items():
            try:
                message_activity = MessageFactory.text(message_text)
                
                async def send_proactive(turn_context):
                    await turn_context.send_activity(message_activity)
                
                await adapter.continue_conversation(
                    conversation_reference,
                    send_proactive
                )
                
                success_count += 1
                print(f"✅ TEAMS MESSAGE SENT to conversation {conv_id}")
                
            except Exception as conv_error:
                logger.error(f"Error sending to conversation {conv_id}: {conv_error}")
                continue
        
        if success_count > 0:
            logger.info(f"Proactive Teams message sent to {success_count}/{total_conversations} conversations")
            return True
        else:
            logger.warning("Failed to send message to any conversation")
            return False
            
    except Exception as e:
        logger.error(f"Error in send_teams_notification: {e}")
        print(f"📢 TEAMS MESSAGE (Error occurred): {message_text}")
        return False