import requests
import json
import time

# The ngrok URL from your JIRA automation rule
WEBHOOK_URL = "https://e39a-49-207-245-139.ngrok-free.app/webhook/jira"

def simulate_jira_approval():
    """
    Simulate a JIRA ticket status change specifically for CST-57 
    (the exact ticket shown in your screenshot)
    """
    # Create webhook payload matching your exact ticket
    payload = {
        "webhookEvent": "jira:issue_updated",
        "issue": {
            "key": "CST-57",  # This is your actual ticket number
            "fields": {
                "summary": "Trial Extension Request - trial@acmecorp.com",
                "status": {"name": "Approved"},
                "description": "Automated ticket created by MontyCloud Customer Support Bot",
                "labels": ["trial-extension", "automated", "customer-support"]
            }
        },
        "changelog": {
            "items": [{
                "field": "status",
                "fromString": "Approval Required", 
                "toString": "Approved"
            }],
            "created": "2025-06-20T15:37:59.000Z"
        },
        "user": {
            "emailAddress": "tejasvini.ramaswamy@montycloud.com"  # The person approving
        }
    }
    
    print("\n" + "="*50)
    print("🚀 SIMULATING MANUAL APPROVAL OF JIRA TICKET")
    print("="*50)
    print(f"Ticket: CST-57")
    print(f"Customer: trial@acmecorp.com")
    print(f"Status Change: Approval Required → Approved")
    print(f"Action: Trial Extension")
    print("="*50)
    
    try:
        # Send the webhook
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Print the result
        if response.status_code == 200:
            print(f"✅ Webhook sent successfully!")
            print(f"Response: {response.text}")
            print("\n⏱️ Teams notification should appear momentarily...")
        else:
            print(f"❌ Error sending webhook. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    simulate_jira_approval()