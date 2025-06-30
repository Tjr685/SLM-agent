"""
Customer Actions Handler
Mock implementation of customer action APIs that get called after JIRA approval
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CustomerActionsHandler:
    """Handler for executing customer actions after JIRA approval"""
    
    def __init__(self):
        """Initialize customer actions handler"""
        self.allowed_features = [
            "Multitenancy", "Azure", "Copilot", "FBP", 
            "OrgOnboarding", "MAP", "Terraform"
        ]
        
        # Mock customer ID - all customers use CUST001
        self.mock_customer_id = "CUST001"
        self.mock_customer_name = "MockCustomer"
        
    async def enable_feature(self, customer_id: str, feature: str) -> Dict[str, Any]:
        """
        Enable a Feature
        POST /enable-feature?customerid=<customerid>
        Request Body: {"feature": "Copilot"}
        """
        try:
            logger.info(f"Enabling feature '{feature}' for customer {customer_id}")
            
            # Mock customer_id to CUST001
            customer_id = self.mock_customer_id
            customer_name = self.mock_customer_name
            
            # Validate feature is allowed
            if feature not in self.allowed_features:
                return {
                    "status": "failure",
                    "message": f"Feature '{feature}' is not in allowed features list: {self.allowed_features}"
                }
            
            # Mock successful feature enablement
            logger.info(f"Feature '{feature}' enabled successfully for customer '{customer_name}'")
            return {
                "status": "success",
                "message": f"Feature '{feature}' enabled successfully for customer '{customer_name}'"
            }
            
        except Exception as e:
            logger.error(f"Error enabling feature {feature} for customer {customer_id}: {e}")
            return {
                "status": "failure",
                "message": f"Error enabling feature: {str(e)}"
            }

    async def get_signup_status(self, customer_id: str) -> Dict[str, Any]:
        """
        Fetch Account Activation Status
        GET /get-signup-status?customerid=<customerid>
        """
        try:
            logger.info(f"Fetching signup status for customer {customer_id}")
            
            # Mock customer_id to CUST001
            customer_id = self.mock_customer_id
            customer_name = self.mock_customer_name
            
            # Mock signup status - assume all customers are active
            logger.info(f"Signup status retrieved for customer '{customer_name}': Active")
            return {
                "signup_status": "Active",
                "customer_name": customer_name
            }
            
        except Exception as e:
            logger.error(f"Error fetching signup status for customer {customer_id}: {e}")
            return {
                "status": "failure",
                "message": f"Error fetching signup status: {str(e)}"
            }

    async def approve_signup(self, customer_id: str) -> Dict[str, Any]:
        """
        Approve Signup
        POST /approve-signup?customerid=<customerid>
        """
        try:
            logger.info(f"Approving signup for customer {customer_id}")
            
            # Mock customer_id to CUST001
            customer_id = self.mock_customer_id
            customer_name = self.mock_customer_name
            
            # Mock successful signup approval (always succeed for testing)
            logger.info(f"Signup approved successfully for customer '{customer_name}'")
            return {
                "status": "success",
                "message": f"Signup for customer '{customer_name}' approved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error approving signup for customer {customer_id}: {e}")
            return {
                "status": "failure",
                "message": f"Error approving signup: {str(e)}"
            }

    async def update_subscription_plan(self, customer_id: str, plan: str) -> Dict[str, Any]:
        """
        Convert Customer to Enterprise Plan
        POST /update-subscription-plan?customerid=<customerid>
        Request Body: {"plan": "enterprise"}
        """
        try:
            logger.info(f"Updating subscription plan to '{plan}' for customer {customer_id}")
            
            # Mock customer_id to CUST001
            customer_id = self.mock_customer_id
            customer_name = self.mock_customer_name
            
            # Validate plan
            allowed_plans = ["trial", "standard", "enterprise"]
            if plan not in allowed_plans:
                return {
                    "status": "failure",
                    "message": f"Invalid plan '{plan}'. Allowed plans: {allowed_plans}"
                }
            
            # Mock successful plan update
            logger.info(f"Subscription plan updated to '{plan}' for customer '{customer_name}'")
            return {
                "status": "success",
                "message": f"Customer '{customer_name}' converted to {plan} plan successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating subscription plan for customer {customer_id}: {e}")
            return {
                "status": "failure",
                "message": f"Error updating subscription plan: {str(e)}"
            }

    async def update_subscription_period(self, customer_id: str, end_date: str) -> Dict[str, Any]:
        """
        Extend subscription period
        POST /update-subscription-period?customerid=<customerid>
        Request Body: {"subscription-end-date": "2026-06-28"}
        """
        try:
            logger.info(f"Updating subscription period to '{end_date}' for customer {customer_id}")
            
            # Mock customer_id to CUST001
            customer_id = self.mock_customer_id
            customer_name = self.mock_customer_name
            
            # Validate date format and ensure it's in the future
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                current_date = datetime.now()
                
                if end_date_obj <= current_date:
                    return {
                        "status": "failure",
                        "message": "The provided subscription end date is a past date"
                    }
                    
            except ValueError:
                return {
                    "status": "failure",
                    "message": "Invalid date format. Expected format: YYYY-MM-DD"
                }
            
            # Mock successful subscription period update
            logger.info(f"Subscription period updated to '{end_date}' for customer '{customer_name}'")
            return {
                "status": "success",
                "message": f"Subscription for customer '{customer_name}' is updated successfully to end on {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Error updating subscription period for customer {customer_id}: {e}")
            return {
                "status": "failure",
                "message": f"Error updating subscription period: {str(e)}"
            }

    async def execute_customer_action(self, action_type: str, customer_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a customer action based on the action type
        This is the main entry point that gets called after JIRA approval
        """
        try:
            logger.info(f"Executing customer action: {action_type} for customer {customer_id}")
            
            if action_type == "enable_feature":
                feature = kwargs.get("feature")
                if not feature:
                    return {
                        "status": "failure",
                        "message": "Feature parameter is required for enable_feature action"
                    }
                return await self.enable_feature(customer_id, feature)
                
            elif action_type == "approve_signup":
                return await self.approve_signup(customer_id)
                
            elif action_type == "upgrade_subscription":
                plan = kwargs.get("plan", "enterprise")  # Default to enterprise
                return await self.update_subscription_plan(customer_id, plan)
                
            elif action_type == "extend_trial" or action_type == "extend_subscription":
                end_date = kwargs.get("end_date")
                if not end_date:
                    # Default to extending by 30 days from current date
                    new_end = datetime.now() + timedelta(days=30)
                    end_date = new_end.strftime("%Y-%m-%d")
                
                return await self.update_subscription_period(customer_id, end_date)
                
            elif action_type == "get_signup_status":
                return await self.get_signup_status(customer_id)
                
            else:
                return {
                    "status": "failure",
                    "message": f"Unknown action type: {action_type}. Supported actions: enable_feature, approve_signup, upgrade_subscription, extend_trial, extend_subscription, get_signup_status"
                }
                
        except Exception as e:
            logger.error(f"Error executing customer action {action_type} for customer {customer_id}: {e}")
            return {
                "status": "failure",
                "message": f"Error executing action: {str(e)}"
            }

# Convenience function for creating handler
async def create_customer_actions_handler() -> CustomerActionsHandler:
    """Create and return a customer actions handler"""
    return CustomerActionsHandler()


# Test functions for verifying the mock APIs
async def test_customer_actions():
    """Test all customer action APIs with mock data"""
    handler = CustomerActionsHandler()
    
    print("🧪 Testing Customer Actions Handler\n")
    
    # Test customer ID - using CUST001 (hardcoded mock)
    test_customer_id = "CUST001"
    
    # Test 1: Enable Feature
    print("1. Testing Enable Feature (Copilot):")
    result = await handler.enable_feature(test_customer_id, "Copilot")
    print(f"   Result: {json.dumps(result, indent=2)}\n")
    
    # Test 2: Enable Feature (Invalid)
    print("2. Testing Enable Feature (Invalid Feature):")
    result = await handler.enable_feature(test_customer_id, "InvalidFeature")
    print(f"   Result: {json.dumps(result, indent=2)}\n")
    
    # Test 3: Get Signup Status
    print("3. Testing Get Signup Status:")
    result = await handler.get_signup_status(test_customer_id)
    print(f"   Result: {json.dumps(result, indent=2)}\n")
    
    # Test 4: Approve Signup
    print("4. Testing Approve Signup:")
    result = await handler.approve_signup(test_customer_id)
    print(f"   Result: {json.dumps(result, indent=2)}\n")
    
    # Test 5: Update Subscription Plan
    print("5. Testing Update Subscription Plan (Enterprise):")
    result = await handler.update_subscription_plan(test_customer_id, "enterprise")
    print(f"   Result: {json.dumps(result, indent=2)}\n")
    
    # Test 6: Update Subscription Period
    print("6. Testing Update Subscription Period:")
    future_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    result = await handler.update_subscription_period(test_customer_id, future_date)
    print(f"   Result: {json.dumps(result, indent=2)}\n")
    
    # Test 7: Execute Customer Action (Main Entry Point)
    print("7. Testing Execute Customer Action (extend_trial):")
    result = await handler.execute_customer_action("extend_trial", test_customer_id)
    print(f"   Result: {json.dumps(result, indent=2)}\n")
    
    # Test 8: Execute Customer Action with feature
    print("8. Testing Execute Customer Action (enable_feature):")
    result = await handler.execute_customer_action("enable_feature", test_customer_id, feature="Azure")
    print(f"   Result: {json.dumps(result, indent=2)}\n")
    
    print("✅ All tests completed!")


if __name__ == "__main__":
    """Run tests when script is executed directly"""
    import asyncio
    asyncio.run(test_customer_actions())
