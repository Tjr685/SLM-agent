#!/usr/bin/env python3
"""
Manual test for webhook with real CST-28 ticket data
"""

import requests
import json
from datetime import datetime

def test_cst28_approved():
    """Test webhook with CST-28 approval data"""
    
    # Simulate JIRA webhook payload for CST-28 being approved
    webhook_payload = {
        "webhookEvent": "jira:issue_updated",
        "issue": {
            "key": "CST-28",
            "fields": {
                "summary": "Subscription Upgrade - customer success team",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [{
                        "type": "paragraph",
                        "content": [{
                            "text": "Current Plan: trial\nTarget Plan: enterprise\nEffective Date: 2025-06-26\nRequested By: Customer Success Bot",
                            "type": "text"
                        }]
                    }]
                },
                "assignee": {
                    "emailAddress": "tejasvini.ramaswamy@montycloud.com"
                },
                "labels": ["subscription-upgrade", "customer-support", "automated"]
            }
        },
        "changelog": {
            "created": datetime.now().isoformat(),
            "items": [{
                "field": "status",
                "fromString": "Pending processing",
                "toString": "Approved"
            }]
        },
        "user": {
            "emailAddress": "tejasvini.ramaswamy@montycloud.com"
        }
    }    # Send to webhook
    try:
        response = requests.post(
            "http://localhost:3978/webhook/jira",
            headers={"Content-Type": "application/json"},
            json=webhook_payload,
            timeout=10
        )
        
        print(f"Webhook Response Status: {response.status_code}")
        print(f"Webhook Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Webhook processed the status change!")
            print("🔔 Check your console for Teams notification (fallback mode)")
        else:
            print(f"❌ ERROR: Webhook failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: Could not send webhook: {e}")

if __name__ == "__main__":
    print("🧪 Testing CST-28 Approval Webhook")
    print("=" * 50)
    test_cst28_approved()
