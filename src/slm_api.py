#!/usr/bin/env python3
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
          # Mock data for testing (will be replaced with real API calls)
        self.mock_customers = {
            "admin@acmecorp.com": {
                "plan": "standard",
                "end_date": "2025-07-10",
                "tenant": "acme-prod",
                "customer": "AcmeCorp",
                "features": ["Copilot", "Multitenancy"]
            },
            "devadmin@acmecorp.com": {
                "plan": "enterprise",
                "end_date": "2026-01-01",
                "tenant": "acme-dev",
                "customer": "AcmeCorp",
                "features": ["Copilot", "Terraform", "OrgOnboarding", "MAP"]
            },
            "admin@zenlabs.com": {
                "plan": "standard",
                "end_date": "2025-06-28",
                "tenant": "zenlabs-us",
                "customer": "ZenLabs",
                "features": []
            },
            "euadmin@zenlabs.com": {
                "plan": "enterprise",
                "end_date": "2025-12-01",
                "tenant": "zenlabs-eu",
                "customer": "ZenLabs",
                "features": ["Azure", "FBP", "MAP"]
            },
            "ops@nextgentech.com": {
                "plan": "enterprise",
                "end_date": "2025-10-15",
                "tenant": "nextgen-prod",
                "customer": "NextGenTech",
                "features": ["Multitenancy", "OrgOnboarding", "Terraform"]
            },
            "qa@nextgentech.com": {
                "plan": "standard",
                "end_date": "2025-08-15",
                "tenant": "nextgen-test",
                "customer": "NextGenTech",
                "features": ["Copilot"]
            },
            "admin@skyai.com": {
                "plan": "standard",
                "end_date": "2025-07-30",
                "tenant": "skyai",
                "customer": "SkyAI",
                "features": ["FBP"]
            },
            "admin@orbitalsoft.com": {
                "plan": "enterprise",
                "end_date": "2025-11-30",
                "tenant": "orbital",
                "customer": "OrbitalSoft",
                "features": ["Copilot", "Azure", "MAP", "Terraform"]
            },
            "alpha@quanta.com": {
                "plan": "enterprise",
                "end_date": "2025-12-31",
                "tenant": "quanta-alpha",
                "customer": "Quanta",
                "features": ["Multitenancy", "OrgOnboarding"]
            },
            "beta@quanta.com": {
                "plan": "standard",
                "end_date": "2025-08-01",
                "tenant": "quanta-beta",
                "customer": "Quanta",
                "features": ["Copilot"]
            },
            "root@helios.com": {
                "plan": "enterprise",
                "end_date": "2026-02-15",
                "tenant": "helios-root",
                "customer": "Helios",
                "features": ["Azure", "FBP", "MAP", "Terraform"]
            },
            "staging@helios.com": {
                "plan": "standard",
                "end_date": "2025-09-10",
                "tenant": "helios-staging",
                "customer": "Helios",
                "features": []
            },
            "admin@wavecore.com": {
                "plan": "enterprise",
                "end_date": "2025-12-05",
                "tenant": "wavecore",
                "customer": "WaveCore",
                "features": ["Copilot", "FBP", "Multitenancy"]
            },
            "prod@neuronx.com": {
                "plan": "standard",
                "end_date": "2025-07-20",
                "tenant": "neuronx-prod",
                "customer": "NeuronX",
                "features": ["OrgOnboarding"]
            },            "labs@neuronx.com": {
                "plan": "enterprise",
                "end_date": "2025-11-01",
                "tenant": "neuronx-labs",
                "customer": "NeuronX",
                "features": ["MAP", "Azure"]
            },
            # Add some trial customers for testing trial extensions
            "trial@acmecorp.com": {
                "plan": "trial",
                "end_date": "2025-07-01",
                "tenant": "acme-trial",
                "customer": "AcmeCorp",
                "features": ["Copilot"]
            },
            "trial@zenlabs.com": {
                "plan": "trial",
                "end_date": "2025-06-25",
                "tenant": "zenlabs-trial",
                "customer": "ZenLabs",
                "features": []
            },
            "trial@skyai.com": {
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

    async def fetch_subscription_plan(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Fetch subscription plan and end date for a customer
        GET /subscription?email=<email>
        """
        try:
            logger.info(f"Fetching subscription plan for: {email}")
            
            # Mock implementation - replace with real API call
            if email in self.mock_customers:
                customer_data = self.mock_customers[email]
                result = {
                    "plan": customer_data["plan"],
                    "end_date": customer_data["end_date"]
                }
                logger.info(f"Found subscription: {result}")
                return result
            else:
                logger.warning(f"Customer not found: {email}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching subscription plan: {e}")
            return None

    async def fetch_tenant_details(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Fetch tenant details for a customer
        GET /details?email=<email>
        """
        try:
            logger.info(f"Fetching tenant details for: {email}")
            
            # Mock implementation - replace with real API call
            if email in self.mock_customers:
                customer_data = self.mock_customers[email]
                result = {
                    "tenant": customer_data["tenant"],
                    "customer": customer_data["customer"],
                    "features": customer_data["features"]
                }
                logger.info(f"Found tenant details: {result}")
                return result
            else:
                logger.warning(f"Tenant not found: {email}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching tenant details: {e}")
            return None

    async def validate_customer(self, email: str, action_type: str) -> Dict[str, Any]:
        """
        Validate customer for a specific action and return relevant details
        """
        try:
            logger.info(f"Validating customer {email} for action: {action_type}")
            
            # Fetch basic customer info
            subscription = await self.fetch_subscription_plan(email)
            tenant_details = await self.fetch_tenant_details(email)
            
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
