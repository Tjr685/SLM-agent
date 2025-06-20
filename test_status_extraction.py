#!/usr/bin/env python3
"""
Test script to verify status change extraction
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from webhook_handler import JiraWebhookHandler

# Test payload with status change
test_payload = {
    "webhookEvent": "jira:issue_updated",
    "issue": {
        "key": "TEST-123",
        "fields": {
            "status": {"name": "In Progress"},
            "summary": "Test issue"
        }
    },
    "changelog": {
        "items": [
            {
                "field": "status",
                "fromString": "To Do",
                "toString": "In Progress"
            }
        ]
    }
}

# Initialize handler
handler = JiraWebhookHandler()

# Test the extraction methods
print("Testing status change extraction...")
status_change = handler.extract_status_change(test_payload)
print(f"Status change: {status_change}")

issue_info = handler.extract_issue_info(test_payload)
print(f"Issue info: {issue_info}")
