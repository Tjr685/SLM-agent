import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv('env/.env.local.user', override=True)

# Test basic connection
client = AzureOpenAI(
    api_key="1XxKwcyn6ADhAEt9kCp6YPCQPLWt69F55vTYMkmQ08jAtQLhZuVzJQQJ99BFACYeBjFXJ3w3AAAAACOGKSzW",
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

try:
    # Test if we can list assistants
    assistants = client.beta.assistants.list()
    print(f"Connection successful! Found {len(assistants.data)} existing assistants")
    
    # Try creating a simple assistant with debugging
    print("Attempting to create assistant...")
    
    response = client.beta.assistants.create(
        name="Test Assistant",
        instructions="You are a helpful assistant.",
        model=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME"),
        tools=[{"type": "code_interpreter"}]
    )
    
    print(f"Response type: {type(response)}")
    print(f"Response: {response}")
    
    if hasattr(response, 'id'):
        print(f"Created assistant with ID: {response.id}")
    else:
        print("Response doesn't have an 'id' attribute")
        print(f"Response attributes: {dir(response)}")
    
except Exception as e:
    print(f"Error during assistant creation: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()