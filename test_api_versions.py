import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv('env/.env.local.user', override=True)

api_versions = [
    "2024-02-15-preview",
    "2024-05-01-preview", 
    "2024-10-01-preview"
]

for version in api_versions:
    print(f"\n=== Testing API Version: {version} ===")
    
    client = AzureOpenAI(
        api_key=os.getenv('SECRET_AZURE_OPENAI_API_KEY'),
        api_version=version,
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    
    try:
        response = client.beta.assistants.create(
            name="Test Assistant",
            instructions="You are a test assistant.",
            model=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME")
        )
        
        if hasattr(response, 'id'):
            print(f"✓ SUCCESS with {version}: {response.id}")
            client.beta.assistants.delete(response.id)
            break
        else:
            print(f"✗ Unexpected response with {version}: {type(response)} - {response}")
            
    except Exception as e:
        print(f"✗ Failed with {version}: {e}")