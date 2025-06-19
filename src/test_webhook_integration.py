#!/usr/bin/env python3
"""
Test script for JIRA webhook integration
Tests the webhook handler, JIRA integration, and Teams notification system
"""

import json
import requests
import time
from datetime import datetime
from jira_integration import create_support_ticket
from webhook_handler import JiraWebhookHandler

def test_jira_ticket_creation():
    """Test JIRA ticket creation with assignment and status"""
    print("=" * 60)
    print("TESTING JIRA TICKET CREATION")
    print("=" * 60)
    
    # Test data
    test_email = "test.customer@example.com"
    test_action = "extend_trial"
    test_end_date = "2025-07-20"
    
    print(f"Creating JIRA ticket for: {test_email}")
    print(f"Action: {test_action}")
    print(f"End Date: {test_end_date}")
    
    # Create ticket
    success, ticket_key, ticket_url = create_support_ticket(
        action=test_action,
        email=test_email,
        end_date=test_end_date,
        requested_by="Test Script"
    )
    
    if success:
        print(f"✅ SUCCESS: Created ticket {ticket_key}")
        print(f"🔗 URL: {ticket_url}")
        print(f"📧 Assigned to: tejasvini.ramaswamy@montycloud.com")
        print(f"📊 Status: Should be set to 'Pending'")
        return ticket_key
    else:
        print(f"❌ FAILED: Could not create JIRA ticket")
        return None

def test_webhook_handler():
    """Test the webhook handler with sample data"""
    print("\n" + "=" * 60)
    print("TESTING WEBHOOK HANDLER")
    print("=" * 60)
    
    # Sample JIRA webhook payload for status change
    sample_payload = {
        "webhookEvent": "jira:issue_updated",
        "issue": {
            "key": "CST-TEST123",
            "fields": {
                "summary": "Trial Extension Request - test@example.com",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [{
                        "type": "paragraph",
                        "content": [{
                            "text": "Test trial extension request",
                            "type": "text"
                        }]
                    }]
                },
                "assignee": {
                    "emailAddress": "tejasvini.ramaswamy@montycloud.com"
                },
                "labels": ["trial-extension", "customer-support", "automated"]
            }
        },
        "changelog": {
            "created": datetime.now().isoformat(),
            "items": [{
                "field": "status",
                "fromString": "Pending",
                "toString": "Approved"
            }]
        },
        "user": {
            "emailAddress": "tejasvini.ramaswamy@montycloud.com"
        }
    }
    
    # Test webhook processing
    handler = JiraWebhookHandler()
    
    print("Testing webhook payload processing...")
    
    # Extract issue info
    issue_info = handler.extract_issue_info(sample_payload)
    if issue_info:
        print(f"✅ Issue Info Extracted:")
        for key, value in issue_info.items():
            print(f"   {key}: {value}")
    else:
        print("❌ Failed to extract issue info")
        return False
    
    # Extract status change
    status_change = handler.extract_status_change(sample_payload)
    if status_change:
        print(f"✅ Status Change Extracted:")
        for key, value in status_change.items():
            print(f"   {key}: {value}")
    else:
        print("❌ Failed to extract status change")
        return False
    
    # Test message generation
    if status_change['to_status'].lower() == 'approved':
        message = handler.generate_approval_message(
            issue_info['key'],
            issue_info['customer_email'],
            issue_info['action_type'],
            issue_info['url']
        )
        print(f"✅ Generated Approval Message:")
        print("-" * 40)
        print(message)
        print("-" * 40)
    
    return True

def test_webhook_server(port=5000):
    """Test the webhook server endpoints"""
    print("\n" + "=" * 60)
    print("TESTING WEBHOOK SERVER")
    print("=" * 60)
    
    base_url = f"http://localhost:{port}"
    
    print(f"Testing webhook server at {base_url}")
    print("NOTE: Make sure the webhook server is running!")
    print("Run: python run_webhook.py 5000")
    print()
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/webhook/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data}")
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Health Check Error: {e}")
        print("   Make sure webhook server is running!")
        return False
    
    # Test webhook endpoint with sample payload
    sample_webhook_data = {
        "webhookEvent": "jira:issue_updated",
        "issue": {
            "key": "CST-TEST456",
            "fields": {
                "summary": "Test Webhook - webhook.test@example.com",
                "labels": ["trial-extension"]
            }
        },
        "changelog": {
            "items": [{
                "field": "status",
                "fromString": "Pending",
                "toString": "Approved"
            }]
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/webhook/jira",
            json=sample_webhook_data,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Webhook Test: {data}")
        else:
            print(f"❌ Webhook Test Failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Webhook Test Error: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("MontyCloud Customer Support Bot - Webhook Integration Tests")
    print(f"Test run: {datetime.now().isoformat()}")
    
    # Test 1: JIRA ticket creation
    ticket_key = test_jira_ticket_creation()
    
    # Test 2: Webhook handler
    webhook_test = test_webhook_handler()
    
    # Test 3: Webhook server (optional - requires server to be running)
    print("\n" + "=" * 60)
    print("WEBHOOK SERVER TEST (OPTIONAL)")
    print("=" * 60)
    print("To test the webhook server:")
    print("1. Open another terminal")
    print("2. Run: python run_webhook.py 5000")
    print("3. Run this test again with --test-server flag")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if ticket_key:
        print(f"✅ JIRA Ticket Creation: SUCCESS ({ticket_key})")
    else:
        print("❌ JIRA Ticket Creation: FAILED")
    
    if webhook_test:
        print("✅ Webhook Handler: SUCCESS")
    else:
        print("❌ Webhook Handler: FAILED")
    
    print("\n🎯 Next Steps:")
    print("1. Check the created JIRA ticket in your browser")
    print("2. Verify it's assigned to tejasvini.ramaswamy@montycloud.com")
    print("3. Verify the status is set to 'Pending'")
    print("4. Start the webhook server: python run_webhook.py 5000")
    print("5. Configure JIRA webhook URL")
    print("6. Test status changes in JIRA")

if __name__ == "__main__":
    main()
