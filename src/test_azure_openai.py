"""
Test Azure OpenAI Assistant connection
"""

import os
from openai import AzureOpenAI
from config import Config

def test_azure_openai_connection():
    """Test if Azure OpenAI connection is working"""
    try:
        config = Config()
        
        print("🔍 Testing Azure OpenAI Connection...")
        print(f"Endpoint: {config.AZURE_OPENAI_ENDPOINT}")
        print(f"Model: {config.AZURE_OPENAI_MODEL_DEPLOYMENT_NAME}")
        print(f"Assistant ID: {config.AZURE_OPENAI_ASSISTANT_ID}")
        
        # Create client
        client = AzureOpenAI(
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version="2024-05-01-preview",
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT
        )
        
        # Test basic connection
        print("Testing basic connection...")
        models = client.models.list()
        print(f"✅ Connection successful! Found {len(models.data)} models")
        
        # Test assistant retrieval
        print("Testing assistant retrieval...")
        assistant = client.beta.assistants.retrieve(config.AZURE_OPENAI_ASSISTANT_ID)
        print(f"✅ Assistant found: {assistant.name}")
        print(f"Model: {assistant.model}")
        print(f"Instructions: {assistant.instructions[:100]}...")
        
        # Test creating a thread and sending a message
        print("Testing thread creation and message...")
        thread = client.beta.threads.create()
        print(f"✅ Thread created: {thread.id}")
        
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Hello, can you help me upgrade a subscription?"
        )
        print(f"✅ Message created: {message.id}")
        
        # Test running the assistant
        print("Testing assistant run...")
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=config.AZURE_OPENAI_ASSISTANT_ID
        )
        print(f"✅ Run created: {run.id}")
        print(f"Status: {run.status}")
        
        print("\n🎉 All tests passed! Azure OpenAI connection is working.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing Azure OpenAI connection:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_azure_openai_connection()
