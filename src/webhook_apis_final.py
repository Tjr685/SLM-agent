#!/usr/bin/env python3
"""
JIRA Webhook Registration Script
Creates a webhook in JIRA to monitor CST project for issue updates
"""

import requests
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('../env/.env.local.user')

class JiraWebhookManager:
    """Manages JIRA webhook creation and configuration"""
    
    def __init__(self):
        """Initialize with JIRA configuration"""
        self.jira_url = os.getenv('ATLASSIAN_BASE_URL', 'https://montycloud.atlassian.net')
        self.webhook_endpoint = f"{self.jira_url}/rest/webhooks/1.0/webhook"
        
        # Get credentials from environment - using your variable names
        self.email = os.getenv('ATLASSIAN_EMAIL')
        self.api_token = os.getenv('SECRET_ATLASSIAN_API_TOKEN')
        
        if not self.email or not self.api_token:
            raise ValueError("ATLASSIAN_EMAIL and SECRET_ATLASSIAN_API_TOKEN environment variables must be set")
        
        # Setup authentication
        self.auth = (self.email, self.api_token)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        print(f"🔧 Initialized JIRA Webhook Manager")
        print(f"📧 Email: {self.email}")
        print(f"🌐 JIRA URL: {self.jira_url}")
        print(f"🔑 API Token: {'*' * 20}...{self.api_token[-10:]}")
    
    def create_webhook(self, ngrok_url: str) -> Dict[str, Any]:
        """Create a new JIRA webhook"""
        
        webhook_config = {
            "name": "MontyCloud Customer Support Bot Webhook",
            "description": "Webhook for monitoring CST project ticket status changes and approvals",
            "url": f"{ngrok_url}/webhook/jira",
            "events": [
                "jira:issue_created",
                "jira:issue_updated"
            ],
            "filters": {
                "issue-related-events-section": "Project = CST"
            },
            "excludeBody": False
            # Note: No secret field - removes the secret requirement
        }
        
        print(f"\n📡 Creating webhook with configuration:")
        print(json.dumps(webhook_config, indent=2))
        
        try:
            response = requests.post(
                self.webhook_endpoint,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(webhook_config)
            )
            
            print(f"\n📊 Response Status: {response.status_code}")
            
            if response.status_code == 201:
                webhook_data = response.json()
                print(f"✅ Webhook created successfully!")
                print(f"🆔 Webhook ID: {webhook_data.get('self', '').split('/')[-1]}")
                print(f"🌐 Webhook URL: {webhook_data.get('url')}")
                print(f"📋 Events: {webhook_data.get('events')}")
                print(f"🟢 Enabled: {webhook_data.get('enabled')}")
                print(f"🔐 Is Signed: {webhook_data.get('isSigned', False)}")
                return webhook_data
            else:
                print(f"❌ Failed to create webhook. Status: {response.status_code}")
                print(f"📝 Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating webhook: {e}")
            return None
    
    def list_webhooks(self) -> Optional[list]:
        """List all existing webhooks"""
        try:
            print(f"\n📋 Fetching webhooks from: {self.webhook_endpoint}")
            
            response = requests.get(
                self.webhook_endpoint,
                auth=self.auth,
                headers=self.headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                webhooks = response.json()
                print(f"\n🔍 Found {len(webhooks)} existing webhooks:")
                print("=" * 60)
                
                for i, webhook in enumerate(webhooks, 1):
                    webhook_id = webhook.get('self', '').split('/')[-1]
                    print(f"\n{i}. {webhook.get('name')}")
                    print(f"   🆔 ID: {webhook_id}")
                    print(f"   🌐 URL: {webhook.get('url')}")
                    print(f"   📋 Events: {', '.join(webhook.get('events', []))}")
                    print(f"   🟢 Enabled: {webhook.get('enabled')}")
                    print(f"   🔐 Is Signed: {webhook.get('isSigned', False)}")
                    if webhook.get('filters'):
                        print(f"   🔍 Filters: {webhook.get('filters')}")
                
                return webhooks
            else:
                print(f"❌ Failed to list webhooks. Status: {response.status_code}")
                print(f"📝 Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error listing webhooks: {e}")
            return None
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a specific webhook"""
        try:
            delete_url = f"{self.webhook_endpoint}/{webhook_id}"
            print(f"\n🗑️ Deleting webhook: {delete_url}")
            
            response = requests.delete(
                delete_url,
                auth=self.auth,
                headers=self.headers
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 204:
                print(f"✅ Webhook {webhook_id} deleted successfully!")
                return True
            else:
                print(f"❌ Failed to delete webhook {webhook_id}. Status: {response.status_code}")
                print(f"📝 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting webhook {webhook_id}: {e}")
            return False
    
    def update_webhook(self, webhook_id: str, ngrok_url: str) -> Dict[str, Any]:
        """Update an existing webhook with new ngrok URL"""
        
        webhook_config = {
            "name": "MontyCloud Customer Support Bot Webhook",
            "description": "Webhook for monitoring CST project ticket status changes and approvals",
            "url": f"{ngrok_url}/webhook/jira",
            "events": [
                "jira:issue_created",
                "jira:issue_updated"
            ],
            "filters": {
                "issue-related-events-section": "Project = CST"
            },
            "excludeBody": False
        }
        
        try:
            update_url = f"{self.webhook_endpoint}/{webhook_id}"
            print(f"\n🔄 Updating webhook: {update_url}")
            print(f"📡 New configuration:")
            print(json.dumps(webhook_config, indent=2))
            
            response = requests.put(
                update_url,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(webhook_config)
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                webhook_data = response.json()
                print(f"✅ Webhook {webhook_id} updated successfully!")
                print(f"🌐 New URL: {webhook_data.get('url')}")
                print(f"🟢 Enabled: {webhook_data.get('enabled')}")
                return webhook_data
            else:
                print(f"❌ Failed to update webhook {webhook_id}. Status: {response.status_code}")
                print(f"📝 Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error updating webhook {webhook_id}: {e}")
            return None

def main():
    """Main function to manage JIRA webhooks"""
    
    # Your ngrok URL
    NGROK_URL = "https://e0bd-49-207-245-139.ngrok-free.app"
    
    print("🔧 JIRA Webhook Manager for MontyCloud")
    print("=" * 50)
    
    try:
        manager = JiraWebhookManager()
        
        while True:
            print("\n🔧 Choose an option:")
            print("1️⃣  Create new webhook")
            print("2️⃣  List existing webhooks")
            print("3️⃣  Update existing webhook")
            print("4️⃣  Delete webhook")
            print("5️⃣  Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                print(f"\n📡 Creating webhook for URL: {NGROK_URL}")
                result = manager.create_webhook(NGROK_URL)
                if result:
                    print(f"\n🎉 Webhook setup complete!")
            
            elif choice == "2":
                print(f"\n📋 Listing all webhooks...")
                manager.list_webhooks()
            
            elif choice == "3":
                webhook_id = input("\n🆔 Enter webhook ID to update: ").strip()
                if webhook_id:
                    print(f"\n🔄 Updating webhook {webhook_id} with URL: {NGROK_URL}")
                    result = manager.update_webhook(webhook_id, NGROK_URL)
                    if result:
                        print(f"\n🎉 Webhook updated successfully!")
            
            elif choice == "4":
                webhook_id = input("\n🆔 Enter webhook ID to delete: ").strip()
                if webhook_id:
                    confirm = input(f"⚠️  Are you sure you want to delete webhook {webhook_id}? (y/N): ").strip().lower()
                    if confirm == 'y':
                        manager.delete_webhook(webhook_id)
            
            elif choice == "5":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please try again.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure your environment variables are set:")
        print("   - ATLASSIAN_EMAIL")
        print("   - SECRET_ATLASSIAN_API_TOKEN")
        print("   - ATLASSIAN_BASE_URL")

if __name__ == "__main__":
    main()