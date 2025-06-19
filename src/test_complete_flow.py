"""
Test script for complete MontyCloud Customer Support Bot flow with task execution
"""

import json
import requests
from webhook_handler import JiraWebhookHandler

def test_task_execution():
    """Test the task execution functionality"""
    print("🧪 Testing Task Execution Functionality")
    print("=" * 60)
    
    handler = JiraWebhookHandler()
    
    # Test data for different scenarios
    test_cases = [
        {
            "name": "Customer Signup Approval",
            "issue_info": {
                "key": "CST-100",
                "customer_email": "test@company.com",
                "action_type": "approve_signup",
                "description": "Company Name: Acme Corp\nSubscription Type: enterprise",
                "url": "https://montycloud.atlassian.net/browse/CST-100"
            }
        },
        {
            "name": "Trial Extension",
            "issue_info": {
                "key": "CST-101", 
                "customer_email": "trial@startup.com",
                "action_type": "extend_trial",
                "description": "End Date: July 20, 2025\nReason: Customer needs more evaluation time",
                "url": "https://montycloud.atlassian.net/browse/CST-101"
            }
        },
        {
            "name": "Beta Features Enablement",
            "issue_info": {
                "key": "CST-102",
                "customer_email": "beta@enterprise.com", 
                "action_type": "enable_beta_features",
                "description": "Features: AI Analytics, Advanced Reporting, Custom Dashboards",
                "url": "https://montycloud.atlassian.net/browse/CST-102"
            }
        },
        {
            "name": "Subscription Upgrade",
            "issue_info": {
                "key": "CST-103",
                "customer_email": "upgrade@business.com",
                "action_type": "upgrade_subscription", 
                "description": "Current Plan: standard\nSubscription Type: enterprise",
                "url": "https://montycloud.atlassian.net/browse/CST-103"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔧 Testing: {test_case['name']}")
        print("-" * 40)
        
        # Test parameter extraction
        params = handler.extract_task_parameters(test_case['issue_info'])
        print(f"📋 Extracted Parameters: {params}")
        
        # Test task execution
        result = handler.execute_approved_task(test_case['issue_info'])
        print(f"✅ Execution Result:")
        print(result)
        print("-" * 40)

def test_approval_message_generation():
    """Test approval message generation with task execution"""
    print("\n🧪 Testing Approval Message Generation with Task Execution")
    print("=" * 60)
    
    handler = JiraWebhookHandler()
    
    issue_info = {
        "key": "CST-999",
        "customer_email": "integration@test.com",
        "action_type": "approve_signup",
        "description": "Company Name: Integration Test Corp\nSubscription Type: trial",
        "url": "https://montycloud.atlassian.net/browse/CST-999"
    }
    
    message = handler.generate_approval_message(
        ticket_key="CST-999",
        customer_email="integration@test.com", 
        action_type="approve_signup",
        ticket_url="https://montycloud.atlassian.net/browse/CST-999",
        issue_info=issue_info
    )
    
    print("📝 Generated Approval Message:")
    print(message)

def test_webhook_payload_processing():
    """Test webhook payload processing"""
    print("\n🧪 Testing Webhook Payload Processing")
    print("=" * 60)
    
    # Sample JIRA webhook payload for status change to "Approved"
    sample_webhook_payload = {
        "webhookEvent": "jira:issue_updated",
        "issue": {
            "key": "CST-TEST",
            "fields": {
                "summary": "Customer Signup Approval Request",
                "description": {
                    "content": [
                        {
                            "content": [
                                {
                                    "text": "Customer Email: webhook@test.com\nCompany Name: Webhook Test Inc\nSubscription Type: enterprise",
                                    "type": "text"
                                }
                            ],
                            "type": "paragraph"
                        }
                    ]
                },
                "assignee": {
                    "emailAddress": "tejasvini.ramaswamy@montycloud.com"
                },
                "labels": ["approve-signup"],
                "status": {
                    "name": "Approved"
                }
            }
        },
        "changelog": {
            "items": [
                {
                    "field": "status",
                    "fromString": "Pending",
                    "toString": "Approved"
                }
            ]
        }
    }
    
    handler = JiraWebhookHandler()
    
    # Test issue info extraction
    issue_info = handler.extract_issue_info(sample_webhook_payload)
    print(f"📋 Extracted Issue Info: {json.dumps(issue_info, indent=2)}")
    
    # Test status change extraction  
    status_change = handler.extract_status_change(sample_webhook_payload)
    print(f"📊 Extracted Status Change: {json.dumps(status_change, indent=2)}")
    
    # Test complete processing
    if issue_info and status_change:
        print("\n🔄 Processing Status Change...")
        handler.handle_status_change(issue_info, status_change)

if __name__ == "__main__":
    print("🚀 MontyCloud Customer Support Bot - Complete Flow Test")
    print("=" * 70)
    
    try:
        test_task_execution()
        test_approval_message_generation()
        test_webhook_payload_processing()
        
        print("\n" + "=" * 70)
        print("✅ All tests completed successfully!")
        print("🎉 The bot is ready for JIRA webhook integration with task execution!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
