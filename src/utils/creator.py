import asyncio, os, argparse
from teams.ai.planners import AssistantsPlanner
from openai.types.beta import AssistantCreateParams
from openai.types.beta.function_tool_param import FunctionToolParam
from openai.types.shared_params import FunctionDefinition

from dotenv import load_dotenv

load_dotenv(f'{os.getcwd()}/env/.env.local.user', override=True)

def load_keys_from_args():
    parser = argparse.ArgumentParser(description='Load keys from command input parameters.')
    parser.add_argument('--api-key', type=str, required=True, help='Azure OpenAI API key for authentication')
    args = parser.parse_args()
    return args

async def main():
    args = load_keys_from_args()

    # Debug: Print environment variables
    print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    print(f"Model: {os.getenv('AZURE_OPENAI_MODEL_DEPLOYMENT_NAME')}")
    print(f"API Key (first 10 chars): {args.api_key[:10]}...")

    options = AssistantCreateParams(
        name="MontyCloud Customer Support Bot",
        instructions="\n".join([
            "You are a comprehensive customer support bot for MontyCloud. You automate critical customer support workflows for the Customer Success team.",
            "",
            "CORE FUNCTIONS:",
            "1. approve_signup - Approve and activate new customer signups",
            "2. extend_trial - Extend trial duration for customers", 
            "3. enable_beta_features - Enable specific MSP features for customers",
            "4. upgrade_subscription - Convert subscription from standard to enterprise",
            "5. update_jira - Log all actions for audit and traceability",
            "",
            "WORKFLOW REQUIREMENTS:",
            "• Always validate customer email format and subscription status",
            "• Ask clarifying questions when request details are ambiguous, by natural language should be able to identify the date in any format given",
            "• Confirm high-impact actions before execution",
            "• Do not proceed with creation of Jira ticket until the customer confirms the data, ask a yes or no",
            "• Each main function (approve_signup, extend_trial, enable_beta_features, upgrade_subscription) automatically creates its own JIRA ticket - DO NOT call update_jira separately",
            "• Provide clear status updates with ticket references",
            "",
            "VALIDATION RULES:",
            "• Email must contain @ symbol and valid domain",
            "• Plan types: trial, standard, enterprise", 
            "• Upgrade paths: trial→(standard|enterprise), standard→enterprise",
            "• Dates support NATURAL LANGUAGE: Accept '20th June 2025', 'June 20, 2025', 'next month', 'in 30 days', etc. - NEVER ask for YYYY-MM-DD format",
            "",
            "INTERACTION STYLE:",
            "• Be professional and helpful",
            "• Use emojis for visual clarity (📧 for email, 🎫 for tickets, ✅ for success)",
            "• Always provide next steps and expected timeline",
            "• Handle natural language queries intelligently",
            "• When users provide dates like '20th June 2025' or 'next month', accept them directly - DO NOT ask for YYYY-MM-DD format"
        ]),
        tools=[
            {
                "type": "code_interpreter",
            },
            FunctionToolParam(
                type="function",
                function=FunctionDefinition(
                    name="approve_signup",
                    description="Approve and activate new customer signup",
                    parameters={
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Customer email address",
                            },
                            "company_name": {
                                "type": "string", 
                                "description": "Company name for the new customer",
                            },
                            "plan_type": {
                                "type": "string",
                                "description": "Initial plan type (trial, standard, enterprise)",
                                "enum": ["trial", "standard", "enterprise"]
                            },
                        },
                        "required": ["email", "company_name"],
                    }
                )
            ),
            FunctionToolParam(
                type="function",
                function=FunctionDefinition(
                    name="extend_trial",
                    description="Extend trial period for a customer",
                    parameters={
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Customer email address",
                            },
                            "end_date": {
                                "type": "string",
                                "description": "New trial end date. Accepts natural language like '20th June 2025', 'June 20, 2025', 'next month', 'in 30 days'. Do NOT require YYYY-MM-DD format.",
                            },
                        },
                        "required": ["email", "end_date"],
                    }
                )
            ),
            FunctionToolParam(
                type="function",
                function=FunctionDefinition(
                    name="enable_beta_features",
                    description="Enable beta features for a customer",
                    parameters={
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Customer email address",
                            },
                            "features": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of beta features to enable",
                            },
                        },
                        "required": ["email", "features"],
                    }
                )
            ),
            FunctionToolParam(
                type="function",
                function=FunctionDefinition(
                    name="upgrade_subscription",
                    description="Upgrade customer subscription from current plan to target plan",
                    parameters={
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Customer email address",
                            },
                            "current_plan": {
                                "type": "string",
                                "description": "Current subscription plan",
                                "enum": ["trial", "standard", "enterprise"]
                            },
                            "target_plan": {
                                "type": "string", 
                                "description": "Target subscription plan",
                                "enum": ["standard", "enterprise"]
                            },
                            "effective_date": {
                                "type": "string",
                                "description": "Effective date for upgrade. Accepts natural language like '20th June 2025', 'June 20, 2025', 'next month', 'in 30 days'. Do NOT require YYYY-MM-DD format.",
                            },
                        },
                        "required": ["email", "current_plan", "target_plan", "effective_date"],
                    }
                )
            ),
            FunctionToolParam(
                type="function",
                function=FunctionDefinition(
                    name="update_jira",
                    description="Create or update JIRA ticket for tracking",
                    parameters={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "Action being performed (approve_signup, extend_trial, enable_beta_features, upgrade_subscription)",
                            },
                            "email": {
                                "type": "string",
                                "description": "Customer email address",
                            },
                            "status": {
                                "type": "string",
                                "description": "Current status (pending, in-progress, complete, error)",
                            },
                            "details": {
                                "type": "string",
                                "description": "Additional details about the action",
                            },
                        },
                        "required": ["action", "email", "status"],
                    }
                )
            )           
        ],
        model=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME"),
    )

    print("Creating assistant...")
    try:
        assistant = await AssistantsPlanner.create_assistant(
            api_key=args.api_key,
            azure_ad_token_provider=None,
            api_version="2024-02-15-preview", 
            organization="", 
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"), 
            request=options
        )
        
        print(f"Assistant creation result type: {type(assistant)}")
        print(f"Assistant creation result: {assistant}")
        
        # Check if assistant is properly created
        if assistant and hasattr(assistant, 'id'):
            print(f"Created a new assistant with an ID of: {assistant.id}")
            if hasattr(assistant, 'tools'):
                print(f"Assistant tools: {assistant.tools}")
        elif assistant:
            print(f"Assistant created but unexpected format: {assistant}")
        else:
            print("Assistant creation returned None or empty result")
            
    except Exception as e:
        print(f"Error creating assistant: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())