"""
Test script for JIRA webhook + customer action integration
"""

import asyncio
import json
from app import extract_action_from_ticket, execute_customer_action_and_notify

async def test_action_extraction():
    """Test action extraction from mock JIRA tickets"""
    
    print("🧪 Testing JIRA Ticket Action Extraction\n")
    
    # Test cases
    test_tickets = [
        {
            "name": "Extend Trial Request",
            "ticket": {
                "issue": {
                    "key": "CST-123",
                    "fields": {
                        "summary": "Request to extend trial for customer trial@skyai.com",
                        "description": "Customer trial@skyai.com needs trial extension for 30 days"
                    }
                }
            }
        },
        {
            "name": "Enable Feature Request", 
            "ticket": {
                "issue": {
                    "key": "CST-124",
                    "fields": {
                        "summary": "Enable Copilot feature for admin@acmecorp.com",
                        "description": "Customer admin@acmecorp.com requesting Copilot feature activation"
                    }
                }
            }
        },
        {
            "name": "Upgrade Subscription Request",
            "ticket": {
                "issue": {
                    "key": "CST-125", 
                    "fields": {
                        "summary": "Upgrade subscription to enterprise plan",
                        "description": "Customer ops@nextgentech.com wants to upgrade to enterprise plan"
                    }
                }
            }
        },
        {
            "name": "Approve Signup Request",
            "ticket": {
                "issue": {
                    "key": "CST-126",
                    "fields": {
                        "summary": "Approve signup for new customer",
                        "description": "Please approve signup for new customer account"
                    }
                }
            }
        },
        {
            "name": "Unknown Action",
            "ticket": {
                "issue": {
                    "key": "CST-127",
                    "fields": {
                        "summary": "Some other customer request",
                        "description": "This is not a recognized action type"
                    }
                }
            }
        }
    ]
    
    for i, test_case in enumerate(test_tickets, 1):
        print(f"{i}. Testing: {test_case['name']}")
        
        action_type, action_details = extract_action_from_ticket(test_case['ticket'])
        
        print(f"   Action Type: {action_type}")
        print(f"   Action Details: {action_details}")
        
        if action_type:
            print(f"   ✅ Successfully identified action")
        else:
            print(f"   ⚠️ Could not identify action")
        
        print()

async def test_customer_action_execution():
    """Test full customer action execution flow"""
    
    print("🧪 Testing Customer Action Execution Flow\n")
    
    # Mock ticket for extend trial
    mock_ticket = {
        "issue": {
            "key": "CST-TEST",
            "fields": {
                "summary": "Extend trial for customer trial@skyai.com",
                "description": "Customer needs trial extension"
            }
        }
    }
    
    print("Testing with mock ticket:")
    print(f"Summary: {mock_ticket['issue']['fields']['summary']}")
    print(f"Description: {mock_ticket['issue']['fields']['description']}")
    print()
    
    # This would normally send to Teams, but for testing we'll just see the output
    print("Executing customer action and generating notification...")
    await execute_customer_action_and_notify("CST-TEST", mock_ticket)
    print()

if __name__ == "__main__":
    """Run the tests"""
    
    async def run_all_tests():
        await test_action_extraction()
        await test_customer_action_execution()
        print("✅ All tests completed!")
    
    asyncio.run(run_all_tests())
