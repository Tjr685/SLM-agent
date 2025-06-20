#!/usr/bin/env python3
"""
Test SLM API Integration
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from slm_api import SLMAPIClient

async def test_slm_api():
    """Test SLM API validation"""
    print("Testing SLM API Integration...")
    
    async with SLMAPIClient() as client:        # Test 1: Valid trial customer for extension
        print("\n=== Test 1: Valid trial customer for extension ===")
        result = await client.validate_customer("trial@acmecorp.com", "extend_trial")
        print(f"Result: {result}")
        
        # Test 2: Valid standard customer (ZenLabs)
        print("\n=== Test 2: Valid standard customer ===")
        result = await client.validate_customer("admin@zenlabs.com", "enable_beta_features")
        print(f"Result: {result}")
        
        # Test 3: Enterprise customer trying to upgrade (should fail)
        print("\n=== Test 3: Enterprise customer trying to upgrade ===")
        result = await client.validate_customer("ops@nextgentech.com", "upgrade_subscription")
        print(f"Result: {result}")
        
        # Test 4: Non-existent customer
        print("\n=== Test 4: Non-existent customer ===")
        result = await client.validate_customer("nonexistent@example.com", "extend_trial")
        print(f"Result: {result}")
        
        # Test 5: Valid standard customer for upgrade (AcmeCorp)
        print("\n=== Test 5: Valid standard customer for upgrade ===")
        result = await client.validate_customer("admin@acmecorp.com", "upgrade_subscription")
        print(f"Result: {result}")        
        # Test 6: Test individual API calls
        print("\n=== Test 6: Individual API calls ===")
        subscription = await client.fetch_subscription_plan("admin@skyai.com")
        print(f"Subscription for admin@skyai.com: {subscription}")
        
        tenant_details = await client.fetch_tenant_details("admin@wavecore.com")
        print(f"Tenant details for admin@wavecore.com: {tenant_details}")
        
        # Test 7: Trial customer details
        print("\n=== Test 7: Trial customer details ===")
        subscription = await client.fetch_subscription_plan("trial@skyai.com")
        print(f"Trial subscription: {subscription}")
        
        result = await client.validate_customer("trial@skyai.com", "extend_trial")
        print(f"Trial validation: {result}")

if __name__ == "__main__":
    asyncio.run(test_slm_api())
