import os
import sys
import traceback
import json
import logging
from typing import Any, Dict, Optional
from dataclasses import asdict

from botbuilder.core import MemoryStorage, TurnContext
from teams import Application, ApplicationOptions, TeamsAdapter
from teams.ai import AIOptions
from teams.ai.planners import AssistantsPlanner, OpenAIAssistantsOptions, AzureOpenAIAssistantsOptions
from teams.state import TurnState
from teams.feedback_loop_data import FeedbackLoopData

from config import Config
from jira_integration import JiraIntegration, create_support_ticket, update_support_ticket
from utils.date_parser import parse_natural_date, validate_future_date
# from teams_notifier import initialize_teams_notifier  # Commented out to fix circular import
from slm_api import SLMAPIClient

# Setup logging
logger = logging.getLogger(__name__)

# Enhanced validation and confirmation functions
def validate_email_format(email: str) -> tuple[bool, str]:
    """Enhanced email validation"""
    if not email:
        return False, "Email is required"
    
    if "@" not in email:
        return False, "Invalid email format - missing @ symbol"
    
    if "." not in email.split("@")[1]:
        return False, "Invalid email format - invalid domain"
    
    if len(email.split("@")) != 2:
        return False, "Invalid email format - multiple @ symbols"
    
    return True, "Valid email format"

def validate_and_parse_date(date_input: str, field_name: str = "date", require_future: bool = True) -> tuple[bool, str, str]:
    """
    Enhanced date validation with natural language support
    
    Args:
        date_input: Natural language date string
        field_name: Name of the field for error messages
        require_future: Whether to require future dates
        
    Returns:
        Tuple of (is_valid: bool, parsed_date: str, message: str)
    """
    if not date_input:
        return False, "", f"{field_name} is required"
    
    # Parse natural language date
    success, parsed_date, error = parse_natural_date(date_input)
    
    if not success:
        return False, date_input, f"Invalid {field_name}: {error}"
    
    # Validate future date if required
    if require_future:
        is_future, future_message = validate_future_date(parsed_date, allow_past=False)
        if not is_future:
            return False, parsed_date, f"Invalid {field_name}: {future_message}"
    
    return True, parsed_date, f"Valid {field_name} format"

def get_mock_customer_info(email: str) -> dict:
    """Mock customer database lookup"""
    # Simulate customer database with sample data
    mock_customers = {
        "john.doe@acmecorp.com": {
            "company": "ACME Corporation",
            "current_plan": "trial",
            "trial_end": "2024-12-31",
            "status": "active"
        },
        "sarah.smith@techstartup.io": {
            "company": "Tech Startup Inc",
            "current_plan": "standard", 
            "trial_end": None,
            "status": "active"
        }
    }
    
    return mock_customers.get(email, {
        "company": "Unknown",
        "current_plan": "unknown",
        "trial_end": None,
        "status": "not_found"
    })

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
        return "❌ Error: Trial end date is required. You can use formats like '2025-06-20', '20th June 2025', 'June 20, 2025', 'next month', etc."
    
    # Enhanced email validation
    is_valid_email, email_message = validate_email_format(email)
    if not is_valid_email:
        return f"❌ Error: {email_message}"
    
    # Enhanced date validation with natural language support
    is_valid_date, parsed_date, date_message = validate_and_parse_date(end_date, "trial end date", require_future=True)
    if not is_valid_date:
        return f"❌ Error: {date_message}\n\n💡 Supported formats: '2025-06-20', '20th June 2025', 'June 20, 2025', 'next month', 'in 30 days', etc."
    
    # Use the parsed date for processing
    formatted_date = parsed_date
    
    # Step 1: Validate customer using SLM APIs and get confirmation
    action_details = {
        "end_date": formatted_date,
        "original_input": end_date
    }
    
    is_valid, validation_message = await validate_customer_and_ask_confirmation(
        email, "extend_trial", action_details
    )
    
    if not is_valid:
        return validation_message
    
    # Store the validated details for when user confirms
    state.temp.pending_action = {
        "type": "extend_trial",
        "email": email,
        "end_date": formatted_date,
        "original_input": end_date
    }
    
    return validation_message

@bot_app.ai.action("approve_signup")
async def approve_signup(context: TurnContext, state: TurnState):
    """Approve and activate new customer signup"""
    
    # Try multiple ways to get parameters
    email = None
    company_name = None
    plan_type = None
    
    if hasattr(context, 'activity') and hasattr(context.activity, 'value') and context.activity.value:
        email = context.activity.value.get("email")
        company_name = context.activity.value.get("company_name")
        plan_type = context.activity.value.get("plan_type", "standard")
    elif hasattr(context, 'data'):
        email = context.data.get("email")
        company_name = context.data.get("company_name")
        plan_type = context.data.get("plan_type", "standard")
    
    print(f"approve_signup called with email: {email}, company_name: {company_name}, plan_type: {plan_type}")
    
    if not email:
        return "❌ Error: Customer email is required"
    
    if not company_name:
        return "❌ Error: Company name is required"
    
    # Enhanced email validation
    is_valid, validation_message = validate_email_format(email)
    if not is_valid:
        return f"❌ Error: {validation_message}"
    
    # Valid plan types
    valid_plans = ["trial", "standard", "enterprise"]
    if plan_type not in valid_plans:
        return f"❌ Error: Invalid plan type. Must be one of: {', '.join(valid_plans)}"
    
    # Step 1: Validate customer using SLM APIs and get confirmation
    action_details = {
        "company_name": company_name,
        "plan_type": plan_type
    }
    
    is_valid, validation_message = await validate_customer_and_ask_confirmation(
        email, "approve_signup", action_details
    )
    
    if not is_valid:
        return validation_message
    
    # Store the validated details for when user confirms
    state.temp.pending_action = {
        "type": "approve_signup",
        "email": email,
        "company_name": company_name,
        "plan_type": plan_type
    }
    
    return validation_message

@bot_app.ai.action("upgrade_subscription")
async def upgrade_subscription(context: TurnContext, state: TurnState):
    """Upgrade customer subscription from standard or trial to enterprise"""
    
    # Try multiple ways to get parameters
    email = None
    current_plan = None
    target_plan = None
    effective_date = None
    
    if hasattr(context, 'activity') and hasattr(context.activity, 'value') and context.activity.value:
        email = context.activity.value.get("email")
        current_plan = context.activity.value.get("current_plan")
        target_plan = context.activity.value.get("target_plan", "enterprise")
        effective_date = context.activity.value.get("effective_date")
    elif hasattr(context, 'data'):
        email = context.data.get("email")
        current_plan = context.data.get("current_plan")
        target_plan = context.data.get("target_plan", "enterprise")
        effective_date = context.data.get("effective_date")
    
    print(f"upgrade_subscription called with email: {email}, current_plan: {current_plan}, target_plan: {target_plan}, effective_date: {effective_date}")
    
    if not email:
        return "❌ Error: Customer email is required"
    
    if not current_plan:
        return "❌ Error: Current plan type is required"
    
    if not effective_date:
        return "❌ Error: Effective date is required. You can use formats like '2025-06-20', '20th June 2025', 'June 20, 2025', 'next month', etc."
    
    # Enhanced email validation
    is_valid_email, email_message = validate_email_format(email)
    if not is_valid_email:
        return f"❌ Error: {email_message}"
    
    # Enhanced date validation with natural language support
    is_valid_date, parsed_date, date_message = validate_and_parse_date(effective_date, "effective date", require_future=True)
    if not is_valid_date:
        return f"❌ Error: {date_message}\n\n💡 Supported formats: '2025-06-20', '20th June 2025', 'June 20, 2025', 'next month', 'in 30 days', etc."
    
    # Use the parsed date for JIRA ticket
    formatted_date = parsed_date
    
    # Valid plan types
    valid_plans = ["trial", "standard", "enterprise"]
    if current_plan not in valid_plans or target_plan not in valid_plans:
        return f"❌ Error: Invalid plan type. Must be one of: {', '.join(valid_plans)}"
    
    # Upgrade logic validation
    upgrade_paths = {
        "trial": ["standard", "enterprise"],
        "standard": ["enterprise"]
    }
    
    if current_plan not in upgrade_paths or target_plan not in upgrade_paths[current_plan]:
        return f"❌ Error: Cannot upgrade from {current_plan} to {target_plan}. Valid upgrades from {current_plan}: {', '.join(upgrade_paths.get(current_plan, []))}"
    
    # Create JIRA ticket with real integration
    success, ticket_key, ticket_url = create_support_ticket(
        action="upgrade_subscription",
        email=email,
        current_plan=current_plan,
        target_plan=target_plan,
        effective_date=formatted_date,
        requested_by="Customer Success Bot"
    )
    
    if success:
        # Show both original input and parsed date if different
        date_display = f"{formatted_date}"
        if effective_date.lower() != formatted_date:
            date_display = f"{formatted_date} (parsed from '{effective_date}')"
            
        return f"""✅ Subscription Upgrade Request Created
    
📧 Customer: {email}
📊 Upgrade: {current_plan.title()} → {target_plan.title()}
📅 Effective Date: {date_display}
🎫 JIRA Ticket: {ticket_key}
🔗 Ticket URL: {ticket_url}

Status: Pending validation and processing
    
Next: Billing team will review and process the subscription upgrade."""
    else:
        # Show both original input and parsed date if different
        date_display = f"{formatted_date}"
        if effective_date.lower() != formatted_date:
            date_display = f"{formatted_date} (parsed from '{effective_date}')"
            
        return f"""❌ Error: Failed to create JIRA ticket
        
📧 Customer: {email}
📊 Requested Upgrade: {current_plan.title()} → {target_plan.title()}
📅 Effective Date: {date_display}

Please contact Customer Success team manually or try again later."""

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
    
    # Enhanced email validation
    is_valid, validation_message = validate_email_format(email)
    if not is_valid:
        return f"❌ Error: {validation_message}"
    
    # Convert features to list if it's a string
    if isinstance(features, str):
        features = [features]
    
    features_list = ", ".join(features)
    
    # Create JIRA ticket with real integration
    success, ticket_key, ticket_url = create_support_ticket(
        action="enable_beta_features",
        email=email,
        features=features_list,
        feature_count=len(features),
        requested_by="Customer Success Bot"
    )
    
    if success:
        return f"""✅ Beta Features Enablement Request Created
    
📧 Customer: {email}
🚀 Features: {features_list}
🎫 JIRA Ticket: {ticket_key}
🔗 Ticket URL: {ticket_url}

Status: Pending validation and processing
    
Next: Technical team will review and enable the requested features."""
    else:
        return f"""❌ Error: Failed to create JIRA ticket
        
📧 Customer: {email}
🚀 Requested Features: {features_list}

Please contact Customer Success team manually or try again later."""

@bot_app.ai.action("update_jira")
async def update_jira(context: TurnContext, state: TurnState):
    """Create or update JIRA ticket for tracking"""
    
    # Try multiple ways to get parameters
    action = None
    email = None
    status = None
    details = None
    ticket_key = None
    
    if hasattr(context, 'activity') and hasattr(context.activity, 'value') and context.activity.value:
        action = context.activity.value.get("action")
        email = context.activity.value.get("email")
        status = context.activity.value.get("status")
        details = context.activity.value.get("details", "")
        ticket_key = context.activity.value.get("ticket_key")
    elif hasattr(context, 'data'):
        action = context.data.get("action")
        email = context.data.get("email")
        status = context.data.get("status")
        details = context.data.get("details", "")
        ticket_key = context.data.get("ticket_key")
    
    print(f"update_jira called with action: {action}, email: {email}, status: {status}, ticket_key: {ticket_key}")
    
    if not action or not email or not status:
        return "❌ Error: Action, email, and status are required for JIRA update"
    
    # If ticket_key is provided, update existing ticket
    if ticket_key:
        success = update_support_ticket(ticket_key, status, details)
        if success:
            return f"""🎫 JIRA Ticket Updated: {ticket_key}
    
📋 Action: {action.replace('_', ' ').title()}
📧 Customer: {email}
📊 Status: {status.title()}
{f'📝 Details: {details}' if details else ''}
    
🔗 Link: https://montycloud.atlassian.net/browse/{ticket_key}
✅ Status successfully updated"""
        else:
            return f"""❌ Error: Failed to update JIRA ticket {ticket_key}
    
📋 Action: {action.replace('_', ' ').title()}
📧 Customer: {email}
📊 Requested Status: {status.title()}

Please update the ticket manually or try again later."""
    
    # If no ticket_key provided, create new ticket
    else:
        success, new_ticket_key, ticket_url = create_support_ticket(
            action=action,
            email=email,
            status=status,
            details=details,
            requested_by="Customer Success Bot - Manual Update"
        )
        
        if success:
            return f"""🎫 New JIRA Ticket Created: {new_ticket_key}
    
📋 Action: {action.replace('_', ' ').title()}
📧 Customer: {email}
📊 Status: {status.title()}
{f'📝 Details: {details}' if details else ''}
    
🔗 Link: {ticket_url}
✅ Ticket successfully created"""
        else:
            return f"""❌ Error: Failed to create JIRA ticket
    
📋 Action: {action.replace('_', ' ').title()}
📧 Customer: {email}
📊 Status: {status.title()}

Please create the ticket manually or try again later."""

# Enhanced validation and confirmation functions
async def validate_customer_and_ask_confirmation(
    email: str, 
    action_type: str, 
    action_details: Dict[str, Any]
) -> tuple[bool, str]:
    """
    Validate customer using SLM APIs and prepare confirmation message
    Returns: (is_valid: bool, message: str)
    """
    try:
        # Step 1: Validate customer using SLM APIs
        async with SLMAPIClient() as slm_client:
            validation_result = await slm_client.validate_customer(email, action_type)
        
        if not validation_result["valid"]:
            return False, f"""❌ Customer Validation Failed
            
📧 Email: {email}
🚫 Error: {validation_result['error']}
💡 Suggestion: {validation_result['suggestion']}

Please verify the information and try again."""
        
        # Step 2: Show original customer data from database and ask for confirmation
        customer_info = f"""✅ Customer Found in Database
        
� **ORIGINAL CUSTOMER DATA:**
📧 Email: {validation_result['customer_email']}
🏢 Company: {validation_result['customer_name']}
🏗️ Tenant: {validation_result['tenant']}
📦 Current Plan: {validation_result['current_plan']}
📅 Plan End Date: {validation_result['plan_end_date']}
🔧 Current Features: {', '.join(validation_result['features']) if validation_result['features'] else 'None'}

🎯 **YOUR REQUEST:**"""
        
        # Add action-specific details
        if action_type == "extend_trial":
            customer_info += f"\n• Action: Extend Trial Period\n• New End Date: {action_details.get('end_date', 'Not specified')}"
        elif action_type == "upgrade_subscription":
            customer_info += f"\n• Action: Upgrade Subscription Plan\n• From: {validation_result['current_plan']} → {action_details.get('plan', 'Enterprise')}\n• Effective Date: {action_details.get('effective_date', 'Not specified')}"
        elif action_type == "enable_beta_features":
            features = action_details.get('features', [])
            customer_info += f"\n• Action: Enable Beta Features\n• Features to Enable: {', '.join(features) if features else 'Not specified'}"
        elif action_type == "approve_signup":
            customer_info += f"\n• Action: Approve Customer Signup\n• Company: {action_details.get('company_name', 'Not specified')}"
        
        customer_info += f"""

✅ **REQUEST VALIDATION:** Your request is valid and can be processed.

❓ **Can I proceed to create a JIRA ticket for this request?**
- Reply **'yes'** to create JIRA ticket
- Reply **'no'** to cancel"""
        
        return True, customer_info
        
    except Exception as e:
        print(f"Error during customer validation: {e}")
        return False, f"""❌ Validation Error
        
An error occurred while validating customer information: {str(e)}
Please try again or contact support."""

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
    
@bot_app.ai.action("confirm_action")
async def confirm_action(context: TurnContext, state: TurnState):
    """Handle user confirmation for pending actions"""
    
    # Check if there's a pending action
    if not hasattr(state.temp, 'pending_action') or not state.temp.pending_action:
        return "❌ No pending action to confirm. Please start a new request."
    
    # Get the user's response
    user_response = ""
    if hasattr(context, 'activity') and hasattr(context.activity, 'text'):
        user_response = context.activity.text.lower().strip()
    
    # Check for confirmation
    if user_response in ['yes', 'y', 'confirm', 'proceed', 'ok']:
        return await process_confirmed_action(context, state)
    elif user_response in ['no', 'n', 'cancel', 'abort']:
        # Clear the pending action
        state.temp.pending_action = None
        return "❌ Action cancelled. No JIRA ticket was created."
    else:
        return "❓ Please respond with 'yes' to proceed or 'no' to cancel the action."

async def process_confirmed_action(context: TurnContext, state: TurnState):
    """Process the confirmed action and create JIRA ticket"""
    
    pending_action = state.temp.pending_action
    action_type = pending_action["type"]
    email = pending_action["email"]
    
    try:
        if action_type == "extend_trial":
            # Create JIRA ticket for trial extension
            success, ticket_key, ticket_url = create_support_ticket(
                action="extend_trial",
                email=email,
                end_date=pending_action["end_date"],
                current_date=pending_action["end_date"],
                requested_by="Customer Success Bot"
            )
            
            if success:
                # Show both original input and parsed date if different
                date_display = pending_action["end_date"]
                if pending_action.get("original_input", "").lower() != pending_action["end_date"]:
                    date_display = f"{pending_action['end_date']} (parsed from '{pending_action['original_input']}')"
                
                result = f"""✅ Trial Extension Request Created
    
📧 Customer: {email}
📅 New End Date: {date_display}
🎫 JIRA Ticket: {ticket_key}
🔗 Ticket URL: {ticket_url}

Status: Pending review and processing
    
Next: SRE team will review and process the extension request."""
            else:
                result = f"""❌ Error: Failed to create JIRA ticket
        
📧 Customer: {email}
📅 Requested End Date: {pending_action['end_date']}

Please contact Customer Success team manually or try again later."""
                
        elif action_type == "approve_signup":
            # Create JIRA ticket for signup approval
            success, ticket_key, ticket_url = create_support_ticket(
                action="approve_signup",
                email=email,
                company_name=pending_action.get("company_name"),
                plan_type=pending_action.get("plan_type"),
                requested_by="Customer Success Bot"
            )
            
            if success:
                result = f"""✅ Signup Approval Request Created
    
📧 Customer: {email}
🏢 Company: {pending_action.get('company_name')}
📋 Plan Type: {pending_action.get('plan_type')}
🎫 JIRA Ticket: {ticket_key}
🔗 Ticket URL: {ticket_url}

Status: Pending validation and activation
    
Next: Customer Success team will review and activate the account."""
            else:
                result = f"""❌ Error: Failed to create JIRA ticket
        
📧 Customer: {email}
🏢 Company: {pending_action.get('company_name')}

Please contact Customer Success team manually or try again later."""
        else:
            result = f"❌ Error: Unknown action type: {action_type}"
        
        # Clear the pending action
        state.temp.pending_action = None
        return result
        
    except Exception as e:
        print(f"Error processing confirmed action: {e}")
        state.temp.pending_action = None
        return f"❌ Error: Failed to process action: {str(e)}"

@bot_app.ai.action("get_customer_info")
async def get_customer_info(context: TurnContext, state: TurnState):
    """Get current subscription and customer information"""
    
    # Try multiple ways to get parameters
    email = None
    
    if hasattr(context, 'activity') and hasattr(context.activity, 'value') and context.activity.value:
        email = context.activity.value.get("email")
    elif hasattr(context, 'data'):
        email = context.data.get("email")
    
    print(f"get_customer_info called with email: {email}")
    
    if not email:
        return "❌ Error: Customer email is required"
    
    # Enhanced email validation
    is_valid_email, email_message = validate_email_format(email)
    if not is_valid_email:
        return f"❌ Error: {email_message}"
    
    try:
        # Query SLM APIs to get customer information
        async with SLMAPIClient() as slm_client:
            subscription = await slm_client.fetch_subscription_plan(email)
            tenant_details = await slm_client.fetch_tenant_details(email)
        
        if not subscription or not tenant_details:
            return f"""❌ Customer Not Found
            
📧 Email: {email}
🚫 Status: Customer not found in system

Please verify the email address is correct."""
        
        # Format customer information
        features_list = tenant_details['features']
        features_display = ', '.join(features_list) if features_list else "None"
        
        # Calculate days until plan expires
        from datetime import datetime
        try:
            end_date = datetime.strptime(subscription['end_date'], '%Y-%m-%d')
            current_date = datetime.now()
            days_remaining = (end_date - current_date).days
            
            if days_remaining > 0:
                expiry_info = f"📅 Plan Expires: {subscription['end_date']} ({days_remaining} days remaining)"
            elif days_remaining == 0:
                expiry_info = f"⚠️ Plan Expires: {subscription['end_date']} (Expires today!)"
            else:
                expiry_info = f"🚨 Plan Expired: {subscription['end_date']} ({abs(days_remaining)} days ago)"
        except:
            expiry_info = f"📅 Plan End Date: {subscription['end_date']}"
        
        return f"""✅ Customer Information Retrieved
        
📧 Email: {email}
🏢 Company: {tenant_details['customer']}
🏗️ Tenant: {tenant_details['tenant']}
📦 Current Plan: {subscription['plan'].title()}
{expiry_info}
🔧 Enabled Features: {features_display}

💡 Available Actions:
- Trial Extension (for trial customers)
- Subscription Upgrade (for trial/standard customers)
- Enable Beta Features (for all customers)"""
        
    except Exception as e:
        logger.error(f"Error retrieving customer info: {e}")
        return f"""❌ Error: Failed to retrieve customer information
        
📧 Email: {email}
🚫 Error: {str(e)}

Please try again or contact support."""