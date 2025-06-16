import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv('env/.env.local.user', override=True)

print("=== Azure OpenAI Configuration ===")
print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"Model Deployment: {os.getenv('AZURE_OPENAI_MODEL_DEPLOYMENT_NAME')}")
print(f"API Key (first 10 chars): {os.getenv('SECRET_AZURE_OPENAI_API_KEY')[:10]}...")

client = AzureOpenAI(
    api_key=os.getenv('SECRET_AZURE_OPENAI_API_KEY'),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

print("\n=== Testing Connection ===")
try:
    # Test basic connection
    assistants = client.beta.assistants.list()
    print(f"✓ Connection successful! Found {len(assistants.data)} existing assistants")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

print("\n=== Testing Model Deployment ===")
try:
    # Test if model deployment works with a simple chat completion
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME"),
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    print(f"✓ Model deployment works: {response.choices[0].message.content}")
except Exception as e:
    print(f"✗ Model deployment failed: {e}")
    print("This might indicate an issue with your model deployment name or configuration")

print("\n=== Testing Assistant Creation (Simple) ===")
try:
    # Try the simplest possible assistant creation
    response = client.beta.assistants.create(
        name="Simple Test",
        instructions="You are a test assistant.",
        model=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME")
    )
    
    print(f"Response type: {type(response)}")
    if hasattr(response, 'id'):
        print(f"✓ Assistant created successfully: {response.id}")
        # Clean up - delete the test assistant
        client.beta.assistants.delete(response.id)
        print("✓ Test assistant deleted")
    else:
        print(f"✗ Unexpected response: {response}")
        
except Exception as e:
    print(f"✗ Assistant creation failed: {e}")
    import traceback
    traceback.print_exc()