"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import os

from dotenv import load_dotenv

# Load environment files - check playground first, then local
if os.path.exists("../env/.env.playground.user"):
    load_dotenv("../env/.env.playground.user", override=True)
    print("🔍 Loaded playground environment")
elif os.path.exists("../env/.env.local.user"):
    load_dotenv("../env/.env.local.user", override=True)
    print("🔍 Loaded local environment")
else:
    load_dotenv()
    print("🔍 Loaded default environment")

class Config:
    """Bot Configuration"""

    PORT = 3978
    APP_ID = os.environ.get("BOT_ID", "")
    APP_PASSWORD = os.environ.get("BOT_PASSWORD", "")
    APP_TYPE = os.environ.get("BOT_TYPE", "")
    APP_TENANTID = os.environ.get("BOT_TENANT_ID", "")
    AZURE_OPENAI_API_KEY = os.environ.get("SECRET_AZURE_OPENAI_API_KEY", os.environ.get("AZURE_OPENAI_API_KEY", "")) # Azure OpenAI API key
    AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"] # Azure OpenAI endpoint
    AZURE_OPENAI_MODEL_DEPLOYMENT_NAME = os.environ["AZURE_OPENAI_MODEL_DEPLOYMENT_NAME"] # Azure OpenAI deployment model name
    AZURE_OPENAI_ASSISTANT_ID = os.environ["AZURE_OPENAI_ASSISTANT_ID"] # Azure OpenAI Assistant ID

    def __init__(self):
        # Debug: Print configuration values (masking sensitive data)
        print(f"🔍 Config Debug:")
        print(f"  APP_ID: {self.APP_ID}")
        print(f"  AZURE_OPENAI_ENDPOINT: {self.AZURE_OPENAI_ENDPOINT}")
        print(f"  AZURE_OPENAI_MODEL: {self.AZURE_OPENAI_MODEL_DEPLOYMENT_NAME}")
        print(f"  AZURE_OPENAI_ASSISTANT_ID: {self.AZURE_OPENAI_ASSISTANT_ID}")
        print(f"  API_KEY (first 10 chars): {self.AZURE_OPENAI_API_KEY[:10]}..." if self.AZURE_OPENAI_API_KEY else "  API_KEY: NOT SET")
