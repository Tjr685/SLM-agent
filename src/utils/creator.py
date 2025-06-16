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
            "You are a customer support bot for MontyCloud and you will mainly interact with Customer Success team.",
            "You are tasked with automating the following actions so that they become self-serviceable:",
            "1. Extend trial for a customer",
            "2. Enable beta features for the customer",
            "",
            "Operating instructions:",
            "1. The customer will be identified by a valid email id.",
            "2. Always validate the input before carrying out actions",
            "3. You have access to the following tools: extend_trial, enable_beta_features and update_jira",
            "4. Update JIRA with the status of the current task, every step of the way - from user request, tool calling, status of the tool action etc",
            "",
            "Workflow:",
            "1. Parse user intent and validate email format",
            "2. Confirm action details with user before proceeding",
            "3. Create JIRA ticket for traceability",
            "4. Execute the requested action",
            "5. Update JIRA with results",
            "6. Provide feedback to user with JIRA ticket reference"
        ]),
        tools=[
            {
                "type": "code_interpreter",
            },
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
                                "description": "New trial end date (YYYY-MM-DD format)",
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
                    name="update_jira",
                    description="Create or update JIRA ticket for tracking",
                    parameters={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "Action being performed (extend_trial, enable_beta_features)",
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