"""
SLM (Service Level Management) API Integration
Mock APIs for customer validation and tenant management
"""

import logging
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SLMAPIClient:
    """Client for SLM API operations"""
    
    def __init__(self, base_url: str = "https://api.montycloud.com"):
        """Initialize SLM API client"""
        self.base_url = base_url
        self.session = None
        
        # Mock data for testing - all customers map to CUST001
        self.mock_customers = {
            "admin@acmecorp.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "standard",
                "end_date": "2025-07-10",
                "tenant": "acme-prod",
                "customer": "AcmeCorp",
                "features": ["Copilot", "Multitenancy"]
            },
            "devadmin@acmecorp.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "enterprise",
                "end_date": "2026-01-01",
                "tenant": "acme-dev",
                "customer": "AcmeCorp",
                "features": ["Copilot", "Terraform", "OrgOnboarding", "MAP"]
            },
            "admin@zenlabs.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "standard",
                "end_date": "2025-06-28",
                "tenant": "zenlabs-us",
                "customer": "ZenLabs",
                "features": []
            },
            "euadmin@zenlabs.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "enterprise",
                "end_date": "2025-12-01",
                "tenant": "zenlabs-eu",
                "customer": "ZenLabs",
                "features": ["Azure", "FBP", "MAP"]
            },
            "ops@nextgentech.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "enterprise",
                "end_date": "2025-10-15",
                "tenant": "nextgen-prod",
                "customer": "NextGenTech",
                "features": ["Multitenancy", "OrgOnboarding", "Terraform"]
            },
            "qa@nextgentech.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "standard",
                "end_date": "2025-08-15",
                "tenant": "nextgen-test",
                "customer": "NextGenTech",
                "features": ["Copilot"]
            },
            "admin@skyai.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "standard",
                "end_date": "2025-07-30",
                "tenant": "skyai",
                "customer": "SkyAI",
                "features": ["FBP"]
            },
            "admin@orbitalsoft.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "enterprise",
                "end_date": "2025-11-30",
                "tenant": "orbital",
                "customer": "OrbitalSoft",
                "features": ["Copilot", "Azure", "MAP", "Terraform"]
            },
            "alpha@quanta.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "enterprise",
                "end_date": "2025-12-31",
                "tenant": "quanta-alpha",
                "customer": "Quanta",
                "features": ["Multitenancy", "OrgOnboarding"]
            },
            "beta@quanta.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "standard",
                "end_date": "2025-08-01",
                "tenant": "quanta-beta",
                "customer": "Quanta",
                "features": ["Copilot"]
            },
            "root@helios.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "enterprise",
                "end_date": "2026-02-15",
                "tenant": "helios-root",
                "customer": "Helios",
                "features": ["Azure", "FBP", "MAP", "Terraform"]
            },
            "staging@helios.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "standard",
                "end_date": "2025-09-10",
                "tenant": "helios-staging",
                "customer": "Helios",
                "features": []
            },
            "admin@wavecore.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "enterprise",
                "end_date": "2025-12-05",
                "tenant": "wavecore",
                "customer": "WaveCore",
                "features": ["Copilot", "FBP", "Multitenancy"]
            },
            "prod@neuronx.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "standard",
                "end_date": "2025-07-20",
                "tenant": "neuronx-prod",
                "customer": "NeuronX",
                "features": ["OrgOnboarding"]
            },
            "labs@neuronx.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "enterprise",
                "end_date": "2025-11-01",
                "tenant": "neuronx-labs",
                "customer": "NeuronX",
                "features": ["MAP", "Azure"]
            },
            # Add some trial customers for testing trial extensions
            "trial@acmecorp.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "trial",
                "end_date": "2025-07-01",
                "tenant": "acme-trial",
                "customer": "AcmeCorp",
                "features": ["Copilot"]
            },
            "trial@zenlabs.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "trial",
                "end_date": "2025-06-25",
                "tenant": "zenlabs-trial",
                "customer": "ZenLabs",
                "features": []
            },
            "trial@skyai.com": {
                "customer_id": "CUST001",
                "signup_date": "2024-01-01",
                "plan": "trial",
                "end_date": "2025-07-05",
                "tenant": "skyai-trial",
                "customer": "SkyAI",
                "features": ["FBP"]
            }
        }
        
        self.allowed_features = [
            "Multitenancy", "Azure", "Copilot", "FBP", 
            "OrgOnboarding", "MAP", "Terraform"
        ]

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def get_customer(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Mock for GET /get-customer?email=<email>
        Returns: {"CustomerID": "CUST001", "Name": "abc", "signup_date": "2024-01-01"}
        """
        try:
            logger.info(f"Mock GET /get-customer?email={email}")
            
            # Mock implementation for /get-customer endpoint
            if email in self.mock_customers:
                customer_data = self.mock_customers[email]
                result = {
                    "CustomerID": "CUST001",  # Always use CUST001 for now
                    "Name": customer_data["customer"],
                    "signup_date": "2024-01-01"
                }
                logger.info(f"Found customer: {result}")
                return result
            else:
                logger.warning(f"Customer not found: {email}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching customer: {e}")
            return None

    async def get_subscription_details(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Mock for GET /get-subscription-details?customerid=<customerid>
        Returns: {"plan": "enterprise", "start_date": "2024-12-01", "end_date": "2025-11-01"}
        """
        try:
            logger.info(f"Mock GET /get-subscription-details?customerid={customer_id}")
            
            # Since we're using CUST001 for all customers, find the first customer in mock_customers
            # In real implementation, this would be based on the actual customer_id
            for email, customer_data in self.mock_customers.items():
                if customer_id == "CUST001":  # Always match CUST001
                    result = {
                        "plan": customer_data["plan"],
                        "start_date": "2024-12-01",  # Mock start date
                        "end_date": customer_data["end_date"]
                    }
                    logger.info(f"Found subscription details: {result}")
                    return result
                break  # Only return first match since we're using fixed customer ID
            
            logger.warning(f"Subscription not found for customer ID: {customer_id}")
            return None
                
        except Exception as e:
            logger.error(f"Error fetching subscription details: {e}")
            return None
        

    async def get_enabled_features(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Mock for GET /get-enabled-features?customerid=<customerid>
        Returns: {"tenant": "nextgen-prod", "customer": "NextGenTech", "features": ["Multitenancy", "Terraform"]}
        """
        try:
            logger.info(f"Mock GET /get-enabled-features?customerid={customer_id}")
            
            # Since we're using CUST001 for all customers, find the first customer in mock_customers
            # In real implementation, this would be based on the actual customer_id
            for email, customer_data in self.mock_customers.items():
                if customer_id == "CUST001":  # Always match CUST001
                    result = {
                        "tenant": customer_data["tenant"],
                        "customer": customer_data["customer"],
                        "features": customer_data["features"]
                    }
                    logger.info(f"Found enabled features: {result}")
                    return result
                break  # Only return first match since we're using fixed customer ID
            
            logger.warning(f"Features not found for customer ID: {customer_id}")
            return None
                
        except Exception as e:
            logger.error(f"Error fetching enabled features: {e}")
            return None
        

    async def fetch_subscription_plan(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Wrapper that uses the new endpoint structure
        """
        try:
            # Step 1: Get customer info
            customer = await self.get_customer(email)
            if not customer:
                return None
            
            # Step 2: Get subscription details using customer ID
            # Pass the original email so we can find the right customer data
            subscription = await self.get_subscription_details_by_email(email)
            return subscription
                
        except Exception as e:
            logger.error(f"Error fetching subscription plan: {e}")
            return None
        

    async def get_subscription_details_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Helper function to get subscription details by email (for mock purposes)
        """
        try:
            if email in self.mock_customers:
                customer_data = self.mock_customers[email]
                result = {
                    "plan": customer_data["plan"],
                    "start_date": "2024-12-01",  # Mock start date
                    "end_date": customer_data["end_date"]
                }
                return result
            return None
        except Exception as e:
            logger.error(f"Error fetching subscription by email: {e}")
            return None
        

    async def get_enabled_features_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Helper function to get enabled features by email (for mock purposes)
        """
        try:
            if email in self.mock_customers:
                customer_data = self.mock_customers[email]
                result = {
                    "tenant": customer_data["tenant"],
                    "customer": customer_data["customer"],
                    "features": customer_data["features"]
                }
                return result
            return None
        except Exception as e:
            logger.error(f"Error fetching features by email: {e}")
            return None
        

    async def validate_customer(self, email: str, action_type: str) -> Dict[str, Any]:
        """
        Validate customer for a specific action and return relevant details
        """
        try:
            logger.info(f"Validating customer {email} for action: {action_type}")
            
            # Fetch basic customer info
            subscription = await self.fetch_subscription_plan(email)
            tenant_details = await self.get_enabled_features_by_email(email)
            
            if not subscription or not tenant_details:
                return {
                    "valid": False,
                    "error": f"Customer {email} not found in system",
                    "suggestion": "Please verify the email address is correct"
                }
            
            # Validate based on action type
            validation_result = {
                "valid": True,
                "customer_email": email,
                "customer_name": tenant_details["customer"],
                "tenant": tenant_details["tenant"],
                "current_plan": subscription["plan"],
                "plan_end_date": subscription["end_date"],
                "features": tenant_details["features"]
            }
            
            # Action-specific validations
            if action_type == "extend_trial":
                if subscription["plan"] != "trial":
                    validation_result["valid"] = False
                    validation_result["error"] = f"Customer is on '{subscription['plan']}' plan, not trial"
                    validation_result["suggestion"] = "Trial extension is only available for trial customers"
                    
            elif action_type == "upgrade_subscription":
                if subscription["plan"] == "enterprise":
                    validation_result["valid"] = False
                    validation_result["error"] = "Customer is already on enterprise plan"
                    validation_result["suggestion"] = "Customer is already on the highest plan available"
                    
            elif action_type == "enable_beta_features":
                # Any customer can request beta features
                pass
                
            elif action_type == "approve_signup":
                # Signup approval is always valid
                pass
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating customer: {e}")
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}",
                "suggestion": "Please try again or contact support"
            }

# Convenience function for creating client
async def create_slm_client() -> SLMAPIClient:
    """Create and return an SLM API client"""
    return SLMAPIClient()
