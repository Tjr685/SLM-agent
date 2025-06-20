#!/usr/bin/env python3
"""
Test the get_customer_info functionality
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from slm_api import SLMAPIClient

async def test_customer_info():
    """Test customer info retrieval"""
    
    print("Testing Customer Information Queries...")
    
    test_customers = [
        "trial@acmecorp.com",
        "admin@acmecorp.com", 
        "ops@nextgentech.com",
        "admin@skyai.com",
        "nonexistent@example.com"
    ]
    
    async with SLMAPIClient() as client:
        for email in test_customers:
            print(f"\n=== Customer Info: {email} ===")
            
            subscription = await client.fetch_subscription_plan(email)
            tenant_details = await client.fetch_tenant_details(email)
            
            if subscription and tenant_details:
                features_list = tenant_details['features']
                features_display = ', '.join(features_list) if features_list else "None"
                
                # Calculate days until plan expires
                from datetime import datetime
                try:
                    end_date = datetime.strptime(subscription['end_date'], '%Y-%m-%d')
                    current_date = datetime.now()
                    days_remaining = (end_date - current_date).days
                    
                    if days_remaining > 0:
                        expiry_info = f"Plan expires in {days_remaining} days ({subscription['end_date']})"
                    elif days_remaining == 0:
                        expiry_info = f"Plan expires today! ({subscription['end_date']})"
                    else:
                        expiry_info = f"Plan expired {abs(days_remaining)} days ago ({subscription['end_date']})"
                except:
                    expiry_info = f"Plan end date: {subscription['end_date']}"
                
                print(f"Company: {tenant_details['customer']}")
                print(f"Tenant: {tenant_details['tenant']}")
                print(f"Plan: {subscription['plan'].title()}")
                print(f"Expiry: {expiry_info}")
                print(f"Features: {features_display}")
            else:
                print("Customer not found")

if __name__ == "__main__":
    asyncio.run(test_customer_info())
