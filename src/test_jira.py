#!/usr/bin/env python3
"""
Test JIRA API integration to check available issue types and priorities
"""
import os
import sys
import requests
import json
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env', '.env.local.user')
if os.path.exists(env_file_path):
    load_dotenv(env_file_path, override=True)

BASE_URL = os.environ.get("ATLASSIAN_BASE_URL", "https://montycloud.atlassian.net")
EMAIL = os.environ.get("ATLASSIAN_EMAIL", "")
TOKEN = os.environ.get("SECRET_ATLASSIAN_API_TOKEN", "")
PROJECT_KEY = "CST"

if not TOKEN or not EMAIL:
    print("Missing credentials")
    sys.exit(1)

auth = HTTPBasicAuth(EMAIL, TOKEN)
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def check_project_metadata():
    """Check available issue types and priorities for CST project"""
    try:
        # Get project metadata
        url = f"{BASE_URL}/rest/api/3/project/{PROJECT_KEY}"
        response = requests.get(url, headers=headers, auth=auth)
        
        if response.status_code == 200:
            project_data = response.json()
            print("✅ Project found:", project_data.get('name', 'Unknown'))
            print("Project Key:", project_data.get('key', 'Unknown'))
        else:
            print("❌ Project not found:", response.status_code, response.text)
            return

        # Get issue types for this project
        url = f"{BASE_URL}/rest/api/3/issuetype/project?projectId={project_data['id']}"
        response = requests.get(url, headers=headers, auth=auth)
        
        if response.status_code == 200:
            issue_types = response.json()
            print("\n📋 Available Issue Types:")
            for issue_type in issue_types:
                print(f"  - {issue_type['name']} (ID: {issue_type['id']})")
        
        # Get priorities
        url = f"{BASE_URL}/rest/api/3/priority"
        response = requests.get(url, headers=headers, auth=auth)
        
        if response.status_code == 200:
            priorities = response.json()
            print("\n⚡ Available Priorities:")
            for priority in priorities:
                print(f"  - {priority['name']} (ID: {priority['id']})")
        
        # Test creating a minimal ticket
        print("\n🧪 Testing ticket creation...")
        test_payload = {
            "fields": {
                "project": {"key": PROJECT_KEY},
                "summary": "Test ticket from MontyCloud Bot",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "text": "This is a test ticket to verify JIRA integration works correctly.",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {"name": "Task"},
                "assignee": {"emailAddress": EMAIL}
            }
        }
        
        url = f"{BASE_URL}/rest/api/3/issue"
        response = requests.post(url, headers=headers, auth=auth, data=json.dumps(test_payload))
        
        if response.status_code in (200, 201):
            result = response.json()
            ticket_key = result['key']
            ticket_url = f"{BASE_URL}/browse/{ticket_key}"
            print(f"✅ Test ticket created: {ticket_key}")
            print(f"🔗 URL: {ticket_url}")
        else:
            print(f"❌ Failed to create test ticket: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_project_metadata()
