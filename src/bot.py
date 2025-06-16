import os
import sys
import traceback
import json
from typing import Any, Dict, Optional
from dataclasses import asdict

from botbuilder.core import MemoryStorage, TurnContext
from teams import Application, ApplicationOptions, TeamsAdapter
from teams.ai import AIOptions
from teams.ai.planners import AssistantsPlanner, OpenAIAssistantsOptions, AzureOpenAIAssistantsOptions
from teams.state import TurnState
from teams.feedback_loop_data import FeedbackLoopData

from config import Config

config = Config()

planner = AssistantsPlanner[TurnState](
    AzureOpenAIAssistantsOptions(
        api_key=config.AZURE_OPENAI_API_KEY,
        endpoint=config.AZURE_OPENAI_ENDPOINT,
        default_model=config.AZURE_OPENAI_MODEL_DEPLOYMENT_NAME,
        assistant_id=config.AZURE_OPENAI_ASSISTANT_ID)
)

# Define storage and application
storage = MemoryStorage()
bot_app = Application[TurnState](
    ApplicationOptions(
        bot_app_id=config.APP_ID,
        storage=storage,
        adapter=TeamsAdapter(config),
        ai=AIOptions(planner=planner, enable_feedback_loop=True),
    )
)
    
@bot_app.ai.action("extend_trial")
async def extend_trial(context: TurnContext, state: TurnState):
    """Extend trial period for a customer"""
    
    # Try multiple ways to get parameters
    email = None
    end_date = None
    
    if hasattr(context, 'activity') and hasattr(context.activity, 'value') and context.activity.value:
        email = context.activity.value.get("email")
        end_date = context.activity.value.get("end_date")
    elif hasattr(context, 'data'):
        email = context.data.get("email")
        end_date = context.data.get("end_date")
    
    print(f"extend_trial called with email: {email}, end_date: {end_date}")
    
    if not email:
        return "❌ Error: Customer email is required"
    
    if not end_date:
        return "❌ Error: Trial end date is required (YYYY-MM-DD format)"
    
    # Mock validation - in real implementation, validate against subscription DB
    if "@" not in email:
        return f"❌ Error: Invalid email format: {email}"
    
    # Mock implementation - simulate trial extension
    return f"""✅ Trial Extension Initiated
    
📧 Customer: {email}
📅 New End Date: {end_date}
🎫 JIRA Ticket: JIT-{hash(email+end_date) % 10000}

Status: Pending validation and processing
    
Next: Customer Success team will be notified once extension is complete."""

@bot_app.ai.action("enable_beta_features")
async def enable_beta_features(context: TurnContext, state: TurnState):
    """Enable beta features for a customer"""
    
    # Try multiple ways to get parameters
    email = None
    features = None
    
    if hasattr(context, 'activity') and hasattr(context.activity, 'value') and context.activity.value:
        email = context.activity.value.get("email")
        features = context.activity.value.get("features")
    elif hasattr(context, 'data'):
        email = context.data.get("email")
        features = context.data.get("features")
    
    print(f"enable_beta_features called with email: {email}, features: {features}")
    
    if not email:
        return "❌ Error: Customer email is required"
    
    if not features:
        return "❌ Error: List of beta features is required"
    
    # Mock validation
    if "@" not in email:
        return f"❌ Error: Invalid email format: {email}"
    
    # Convert features to list if it's a string
    if isinstance(features, str):
        features = [features]
    
    features_list = ", ".join(features)
    
    # Mock implementation
    return f"""✅ Beta Features Enablement Initiated
    
📧 Customer: {email}
🚀 Features: {features_list}
🎫 JIRA Ticket: JIT-{hash(email+features_list) % 10000}

Status: Pending validation and processing
    
Next: Features will be enabled after subscription validation."""

@bot_app.ai.action("update_jira")
async def update_jira(context: TurnContext, state: TurnState):
    """Create or update JIRA ticket for tracking"""
    
    # Try multiple ways to get parameters
    action = None
    email = None
    status = None
    details = None
    
    if hasattr(context, 'activity') and hasattr(context.activity, 'value') and context.activity.value:
        action = context.activity.value.get("action")
        email = context.activity.value.get("email")
        status = context.activity.value.get("status")
        details = context.activity.value.get("details", "")
    elif hasattr(context, 'data'):
        action = context.data.get("action")
        email = context.data.get("email")
        status = context.data.get("status")
        details = context.data.get("details", "")
    
    print(f"update_jira called with action: {action}, email: {email}, status: {status}")
    
    if not action or not email or not status:
        return "❌ Error: Action, email, and status are required for JIRA update"
    
    # Mock JIRA ticket creation/update
    ticket_id = f"JIT-{hash(email+action) % 10000}"
    
    return f"""🎫 JIRA Ticket Updated: {ticket_id}
    
Action: {action}
Customer: {email}
Status: {status}
{f'Details: {details}' if details else ''}
    
Timestamp: {context.activity.timestamp if hasattr(context.activity, 'timestamp') else 'Now'}"""

@bot_app.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The agent encountered an error or bug.")

@bot_app.feedback_loop()
async def feedback_loop(_context: TurnContext, _state: TurnState, feedback_loop_data: FeedbackLoopData):
    # Add custom feedback process logic here.
    print(f"Your feedback is:\n{json.dumps(asdict(feedback_loop_data), indent=4)}")