#!/usr/bin/env python3
"""
MCP-based SLM API Client
Integrates with MontyCloud MCP Server to access Day2 platform
"""

import os
import json
import asyncio
import subprocess
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class MCPSLMClient:
    """MCP-based client for SLM operations using MontyCloud MCP Server"""
    
    def __init__(self):
        """Initialize MCP SLM client"""
        # Load environment variables
        load_dotenv('env/.env.local.user', override=True)
        
        self.mcp_environment = os.getenv('MCP_ENVIRONMENT', 'dev')
        self.api_key = os.getenv('SECRET_MCP_API_KEY', '')
        self.api_secret = os.getenv('SECRET_MCP_API_SECRET', '')
        
        # Environment URLs
        self.environment_urls = {
            'dev': 'https://dev-api.montycloud.com/cortex-mcp',
            'staging': 'https://stg1-api.montycloud.com/cortex-mcp',
            'prod': 'https://api.montycloud.com/cortex-mcp'
        }
        
        self.endpoint_url = self.environment_urls.get(self.mcp_environment)
        
        # if not self.api_key or not self.api_secret:
        #     logger.warning("MCP API credentials not configured. Using fallback mode.")
        #     self.fallback_mode = True
        # else:
        #     self.fallback_mode = False
            
        logger.info(f"MCP Client initialized - Environment: {self.mcp_environment}, Endpoint: {self.endpoint_url}")

    async def _call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool and return the result
        """
        try:
            # if self.fallback_mode:
            #     logger.warning(f"MCP credentials not available, using fallback for {tool_name}")
            #     return await self._fallback_handler(tool_name, parameters)
            
            # Prepare MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": parameters
                }
            }
            
            # Execute MCP call using curl
            curl_command = [
                'curl', '-X', 'POST', '--location', self.endpoint_url,
                '--header', 'Accept: application/json, text/event-stream',
                '--header', 'Content-Type: application/json',
                '--header', f'x-api-key: {self.api_key}',
                '--header', f'Authorization: {self.api_secret}',
                '--data', json.dumps(mcp_request)
            ]

            print(f"Executing MCP tool: {tool_name} with parameters: {parameters}")
            
            logger.info(f"Calling MCP tool: {tool_name} with parameters: {parameters}")
            result = subprocess.run(curl_command, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"Raw MCP response: {result.stdout}")
                try:
                    # Handle Server-Sent Events (SSE) format
                    response_text = result.stdout.strip()
                    if response_text.startswith('event: message\ndata: '):
                        # Extract JSON from SSE format
                        json_line = response_text.split('data: ', 1)[1].split('\n\n')[0]
                        response_data = json.loads(json_line)
                    else:
                        # Regular JSON response
                        response_data = json.loads(response_text)
                    
                    if 'result' in response_data:
                        result_data = response_data['result']
                        
                        # Handle MCP tool response format - extract from content if needed
                        if 'content' in result_data and isinstance(result_data['content'], list):
                            if result_data['content'] and 'text' in result_data['content'][0]:
                                # Parse the JSON text content
                                tool_result = json.loads(result_data['content'][0]['text'])
                                print(f"MCP tool {tool_name} response: {tool_result}")
                                logger.info(f"MCP tool {tool_name} succeeded")
                                return tool_result
                        
                        print(f"MCP tool {tool_name} response: {result_data}")
                        logger.info(f"MCP tool {tool_name} succeeded")
                        return result_data
                    else:
                        print(f"MCP tool {tool_name} failed: {response_data}")
                        logger.error(f"MCP tool {tool_name} failed: {response_data}")
                        return {"error": response_data.get('error', 'Unknown error')}
                except json.JSONDecodeError as e:
                    print(f"Failed to parse MCP response: {e}")
                    print(f"Raw response was: {repr(result.stdout)}")
                    logger.error(f"Failed to parse MCP response: {e}")
                    return {"error": "Invalid JSON response from MCP server"}
            else:
                print(f"MCP call failed with stderr: {result.stderr}")
                logger.error(f"MCP call failed: {result.stderr}")
                return {"error": f"MCP call failed: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            print(f"MCP call timeout for tool: {tool_name}")
            logger.error(f"MCP call timeout for tool: {tool_name}")
            return {"error": "MCP call timeout"}
        except Exception as e:
            print(f"Error calling MCP tool {tool_name}: {e}")
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return {"error": str(e)}

    # async def _fallback_handler(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Fallback handler when MCP credentials are not available
    #     Uses the same mock data as the original slm_api.py
    #     """
    #     logger.info(f"Using fallback data for {tool_name}")
        
    #     # Import the mock data from original slm_api
    #     from slm_api import SLMAPIClient
        
    #     fallback_client = SLMAPIClient()
        
    #     if tool_name == "validate_customer":
    #         email = parameters.get('email', '')
    #         if email in fallback_client.mock_customers:
    #             customer_data = fallback_client.mock_customers[email]
    #             return {
    #                 "Name": customer_data["customer"],
    #                 "signup_date": "2024-01-01"  # Mock signup date
    #             }
    #         else:
    #             return {"error": "Customer not found"}
                
    #     elif tool_name == "fetch_subscription":
    #         email = parameters.get('email', '')
    #         if email in fallback_client.mock_customers:
    #             customer_data = fallback_client.mock_customers[email]
    #             return {
    #                 "plan": customer_data["plan"],
    #                 "start_date": "2024-12-01",  # Mock start date
    #                 "end_date": customer_data["end_date"]
    #             }
    #         else:
    #             return {"error": "Customer not found"}
                
    #     elif tool_name == "fetch_enabled_features":
    #         email = parameters.get('email', '')
    #         if email in fallback_client.mock_customers:
    #             customer_data = fallback_client.mock_customers[email]
    #             return {
    #                 "tenant": customer_data["tenant"],
    #                 "customer": customer_data["customer"],
    #                 "features": customer_data["features"]
    #             }
    #         else:
    #             return {"error": "Customer not found"}
                
    #     else:
    #         return {"error": f"Unknown tool: {tool_name}"}

    async def validate_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate customer existence using customer_id
        Maps to MCP tool: get_customer_summary with customer_id parameter
        Returns customer information including email, name, status, etc.
        """
        try:
            # Call get_customer_summary with customer_id
            result = await self._call_mcp_tool("get_customer_summary", {"customer_id": customer_id})
            
            if "error" in result:
                print(f"Customer validation failed for customer_id {customer_id}: {result['error']}")
                logger.warning(f"Customer validation failed for customer_id {customer_id}: {result['error']}")
                return None
            
            # Extract customer details from the result
            if result and isinstance(result, dict):
                # The MCP tool returns customer info directly
                customer_info = result
                print(f"✅ Customer validated: {customer_info.get('name', 'Unknown')} ({customer_info.get('email', 'No email')})")
                return customer_info
            else:
                print(f"❌ Invalid response format for customer_id {customer_id}")
                return None
                
        except Exception as e:
            print(f"Error validating customer {customer_id}: {e}")
            logger.error(f"Error validating customer {customer_id}: {e}")
            return None

    async def fetch_subscription_status(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Fetch subscription status
        Maps to MCP tool or API: GET /subscription?email=<email>
        """
        try:
            result = await self._call_mcp_tool("fetch_subscription", {"email": email})
            
            if "error" in result:
                print(f"Subscription fetch failed for {email}: {result['error']}")
                logger.warning(f"Subscription fetch failed for {email}: {result['error']}")
                return None
                
            return result
            
        except Exception as e:
            print(f"Error fetching subscription for {email}: {e}")
            logger.error(f"Error fetching subscription for {email}: {e}")
            return None

    async def fetch_enabled_features(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Fetch enabled feature details
        Maps to MCP tool or API: GET /enabled-features?email=<email>
        """
        try:
            result = await self._call_mcp_tool("fetch_enabled_features", {"email": email})
            
            if "error" in result:
                print(f"Feature fetch failed for {email}: {result['error']}")
                logger.warning(f"Feature fetch failed for {email}: {result['error']}")
                return None
                
            return result
            
        except Exception as e:
            print(f"Error fetching features for {email}: {e}")
            logger.error(f"Error fetching features for {email}: {e}")
            return None

    async def enable_feature(self, email: str, feature: str) -> Dict[str, Any]:
        """
        Enable a feature for customer
        Maps to MCP tool or API: POST /enable-feature?email=<email>
        """
        try:
            result = await self._call_mcp_tool("enable_feature", {
                "email": email,
                "feature": feature
            })
            
            return result
            
        except Exception as e:
            print(f"Error enabling feature {feature} for {email}: {e}")
            logger.error(f"Error enabling feature {feature} for {email}: {e}")
            return {"error": str(e)}

    async def fetch_signup_status(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Fetch account activation status
        Maps to MCP tool or API: GET /signup-status?email=<email>
        """
        try:
            result = await self._call_mcp_tool("fetch_signup_status", {"email": email})
            
            if "error" in result:
                print(f"Signup status fetch failed for {email}: {result['error']}")
                logger.warning(f"Signup status fetch failed for {email}: {result['error']}")
                return None
                
            return result
            
        except Exception as e:
            print(f"Error fetching signup status for {email}: {e}")
            logger.error(f"Error fetching signup status for {email}: {e}")
            return None

    async def approve_signup(self, email: str) -> Dict[str, Any]:
        """
        Approve customer signup
        Maps to MCP tool or API: POST /approve-signup?email=<email>
        """
        try:
            result = await self._call_mcp_tool("approve_signup", {"email": email})
            
            return result
            
        except Exception as e:
            print(f"Error approving signup for {email}: {e}")
            logger.error(f"Error approving signup for {email}: {e}")
            return {"error": str(e)}

    async def update_subscription_plan(self, email: str, plan: str) -> Dict[str, Any]:
        """
        Convert customer to enterprise plan
        Maps to MCP tool or API: POST /update-subscription-plan?email=<email>
        """
        try:
            result = await self._call_mcp_tool("update_subscription_plan", {
                "email": email,
                "plan": plan
            })
            
            return result
            
        except Exception as e:
            print(f"Error updating subscription plan for {email}: {e}")
            logger.error(f"Error updating subscription plan for {email}: {e}")
            return {"error": str(e)}

    async def extend_subscription_period(self, email: str, end_date: str) -> Dict[str, Any]:
        """
        Extend subscription period
        Maps to MCP tool or API: POST /update-subscription-period?email=<email>
        """
        try:
            result = await self._call_mcp_tool("extend_subscription_period", {
                "email": email,
                "subscription-end-date": end_date
            })
            
            return result
            
        except Exception as e:
            print(f"Error extending subscription for {email}: {e}")
            logger.error(f"Error extending subscription for {email}: {e}")
            return {"error": str(e)}

    async def validate_customer_for_action(self, email: str, action_type: str) -> Dict[str, Any]:
        """
        Comprehensive customer validation for specific actions
        This combines multiple MCP calls to validate and gather all necessary information
        """
        try:
            logger.info(f"Validating customer {email} for action: {action_type}")
            
            # For testing, hardcode customer_id
            cust_id = 'CUST001'
            print(f"🔍 Using hardcoded customer_id for testing: {cust_id}")
            
            # Step 1: Validate customer exists and get customer details (including email)
            customer_info = await self.validate_customer(cust_id)
            if not customer_info:
                return {
                    "valid": False,
                    "error": f"Customer with ID {cust_id} not found in system",
                    "suggestion": "Please verify the customer ID is correct"
                }
            
            # Extract the email from MCP response - this is the "real" email from the system
            mcp_email = customer_info.get('email', customer_info.get('Email', ''))
            if not mcp_email:
                return {
                    "valid": False,
                    "error": f"No email found for customer ID {cust_id}",
                    "suggestion": "Customer record may be incomplete"
                }
            
            # Step 2: Email validation - check if input email matches MCP email
            if email.lower() != mcp_email.lower():
                return {
                    "valid": False,
                    "error": f"Email mismatch - provided email does not match customer record",
                    "suggestion": "Please verify the email address is correct"
                }
            
            print(f"✅ Email validation passed - customer found in MCP system")
            
            # Step 3: For testing, use mock subscription and feature data since MCP tools don't exist yet
            # TODO: Replace with actual MCP calls when tools become available
            mock_subscription = {
                "plan": "trial",
                "start_date": "2024-12-01",
                "end_date": "2025-01-01"
            }
            
            mock_features = {
                "tenant": "test-tenant",
                "customer": customer_info.get("name", "Test Customer"),
                "features": ["basic_monitoring", "cloud_deployment"]
            }
            
            # Step 4: Build comprehensive validation result
            validation_result = {
                "valid": True,
                "customer_email": mcp_email,  # Email from MCP system (for bot internal use)
                "customer_name": customer_info.get("name", mock_features.get("customer", "Unknown")),
                "tenant": mock_features.get("tenant", "Unknown"),
                "current_plan": mock_subscription.get("plan", "Unknown"),
                "plan_end_date": mock_subscription.get("end_date", "Unknown"),
                "features": mock_features.get("features", [])
            }
            
            # Step 5: Action-specific validations
            if action_type == "extend_trial":
                if mock_subscription.get("plan") != "trial":
                    validation_result["valid"] = False
                    validation_result["error"] = f"Customer is on '{mock_subscription.get('plan')}' plan, not trial"
                    validation_result["suggestion"] = "Trial extension is only available for trial customers"
                    
            elif action_type == "upgrade_subscription":
                if mock_subscription.get("plan") == "enterprise":
                    validation_result["valid"] = False
                    validation_result["error"] = "Customer is already on enterprise plan"
                    validation_result["suggestion"] = "Customer is already on the highest plan available"
            
            return validation_result
            
        except Exception as e:
            print(f"Error validating customer {email} for action {action_type}: {e}")
            logger.error(f"Error validating customer: {e}")
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}",
                "suggestion": "Please try again or contact support"
            }

# Convenience function for creating client
async def create_mcp_slm_client() -> MCPSLMClient:
    """Create and return an MCP SLM client"""
    return MCPSLMClient()
