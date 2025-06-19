#!/usr/bin/env python3
"""
JIRA Integration for MontyCloud Customer Support Bot
Integrates with Atlassian JIRA API v3 to create and manage support tickets
"""

import os
import sys
import requests
import json
import logging
from typing import Dict, Any, Optional, Tuple
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from urllib.parse import quote_plus
from datetime import datetime

# Load environment variables
load_dotenv()
# Also try loading from the specific env file
env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env', '.env.local.user')
if os.path.exists(env_file_path):
    load_dotenv(env_file_path, override=True)

# JIRA Configuration
JIRA_BASE_URL = os.environ.get("ATLASSIAN_BASE_URL", "https://montycloud.atlassian.net")
JIRA_EMAIL = os.environ.get("ATLASSIAN_EMAIL", "")
JIRA_API_TOKEN = os.environ.get("SECRET_ATLASSIAN_API_TOKEN", "") or os.environ.get("ATLASSIAN_API_TOKEN", "")
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "CST")  # Customer Support Team project

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JiraIntegration:
    """JIRA API integration for customer support ticket management"""
    
    def __init__(self):
        """Initialize JIRA client with configuration"""
        self.base_url = JIRA_BASE_URL
        self.email = JIRA_EMAIL
        self.api_token = JIRA_API_TOKEN
        self.project_key = JIRA_PROJECT_KEY
        
        if not self.api_token or not self.email:
            logger.warning("JIRA API credentials not configured. Using mock mode.")
            self.mock_mode = True
        else:
            self.mock_mode = False
            
        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def create_customer_support_ticket(self, action: str, email: str, details: Dict[str, Any]) -> Tuple[bool, str, str]:
        """
        Create a JIRA ticket for customer support actions
        
        Args:
            action: Type of action (approve_signup, extend_trial, etc.)
            email: Customer email address
            details: Additional details about the action
            
        Returns:
            Tuple of (success: bool, ticket_key: str, ticket_url: str)
        """
        if self.mock_mode:
            return self._create_mock_ticket(action, email, details)
        
        try:
            # Map actions to JIRA ticket types and priorities
            action_config = self._get_action_config(action)
            
            # Create ticket summary and description
            summary = f"{action_config['title']} - {email}"
            description = self._build_ticket_description(action, email, details)            # Build JIRA ticket payload
            ticket_payload = {
                "fields": {
                    "project": {"key": self.project_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "text": description,
                                        "type": "text"
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {"name": action_config["issue_type"]},
                    "priority": {"name": action_config["priority"]},
                    "labels": [action_config["label"], "customer-support", "automated"],
                    "assignee": {"emailAddress": "tejasvini.ramaswamy@montycloud.com"},  # Assign specifically to you
                    # Add custom fields if they exist in your JIRA instance
                    # "customfield_10001": email,  # Customer email field
                }
            }
            
            # Create the ticket
            url = f"{self.base_url}/rest/api/3/issue"
            response = requests.post(
                url, 
                headers=self.headers, 
                auth=self.auth, 
                data=json.dumps(ticket_payload)            )
            
            if response.status_code in (200, 201):
                result = response.json()
                ticket_key = result['key']
                ticket_url = f"{self.base_url}/browse/{ticket_key}"
                
                # Set initial status to "Pending" if it exists
                self._set_initial_status(ticket_key, "Pending")
                
                logger.info(f"Created JIRA ticket: {ticket_key}")
                return True, ticket_key, ticket_url
            else:
                logger.error(f"Failed to create JIRA ticket: {response.status_code} - {response.text}")
                return False, "", ""
                
        except Exception as e:
            logger.error(f"Error creating JIRA ticket: {e}")
            return False, "", ""
    
    def update_ticket_status(self, ticket_key: str, status: str, comment: str = "") -> bool:
        """
        Update JIRA ticket status
        
        Args:
            ticket_key: JIRA ticket key (e.g., CST-123)
            status: New status (In Progress, Done, etc.)
            comment: Optional comment to add
            
        Returns:
            bool: Success status
        """
        if self.mock_mode:
            logger.info(f"Mock: Updated ticket {ticket_key} to status {status}")
            return True
        
        try:
            # Add comment if provided
            if comment:
                self._add_comment(ticket_key, comment)
            
            # Get available transitions
            transitions_url = f"{self.base_url}/rest/api/3/issue/{ticket_key}/transitions"
            response = requests.get(transitions_url, headers=self.headers, auth=self.auth)
            
            if response.status_code == 200:
                transitions = response.json().get('transitions', [])
                
                # Find the transition that matches the desired status
                target_transition = None
                for transition in transitions:
                    if transition['to']['name'].lower() == status.lower():
                        target_transition = transition['id']
                        break
                
                if target_transition:
                    # Perform the transition
                    transition_payload = {
                        "transition": {"id": target_transition}
                    }
                    
                    response = requests.post(
                        transitions_url,
                        headers=self.headers,
                        auth=self.auth,
                        data=json.dumps(transition_payload)
                    )
                    
                    if response.status_code == 204:
                        logger.info(f"Updated ticket {ticket_key} to status {status}")
                        return True
                    else:
                        logger.error(f"Failed to update ticket status: {response.text}")
                        return False
                else:
                    logger.warning(f"No transition found for status: {status}")
                    return False
            else:
                logger.error(f"Failed to get transitions: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating ticket status: {e}")
            return False
    def _add_comment(self, ticket_key: str, comment: str) -> bool:
        """Add a comment to a JIRA ticket"""
        try:
            comment_payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "text": comment,
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                }
            }
            
            url = f"{self.base_url}/rest/api/3/issue/{ticket_key}/comment"
            response = requests.post(
                url,
                headers=self.headers,
                auth=self.auth,
                data=json.dumps(comment_payload)
            )
            
            return response.status_code in (200, 201)
            
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return False
    
    def get_ticket_comments(self, ticket_key: str) -> str:
        """Get comments from a JIRA ticket for rejection notifications"""
        if self.mock_mode:
            return "Mock: Please check JIRA for detailed comments."
        
        try:
            url = f"{self.base_url}/rest/api/3/issue/{ticket_key}/comment"
            response = requests.get(url, headers=self.headers, auth=self.auth)
            
            if response.status_code == 200:
                comments_data = response.json()
                comments = comments_data.get('comments', [])
                
                # Get the latest comment (for rejection reason)
                if comments:
                    latest_comment = comments[-1]
                    body = latest_comment.get('body', {})
                    
                    # Extract text from comment body
                    if isinstance(body, dict) and 'content' in body:
                        text_parts = []
                        for content in body['content']:
                            if content.get('type') == 'paragraph':
                                for item in content.get('content', []):
                                    if item.get('type') == 'text':
                                        text_parts.append(item.get('text', ''))
                        return '\n'.join(text_parts)
                    
                    return str(body)
                else:
                    return "No comments found on this ticket."
            else:
                logger.error(f"Failed to get comments: {response.text}")
                return "Unable to retrieve comments from JIRA."
                
        except Exception as e:
            logger.error(f"Error getting ticket comments: {e}")
            return "Error retrieving comments from JIRA."
    def _get_action_config(self, action: str) -> Dict[str, str]:
        """Get JIRA configuration for different actions"""
        action_configs = {
            "approve_signup": {
                "title": "Customer Signup Approval",
                "issue_type": "Task",
                "priority": "P1",
                "label": "customer-onboarding"
            },
            "extend_trial": {
                "title": "Trial Extension Request",
                "issue_type": "Task", 
                "priority": "P2",
                "label": "trial-extension"
            },
            "enable_beta_features": {
                "title": "Beta Features Enablement",
                "issue_type": "Task",
                "priority": "P3",
                "label": "feature-enablement"
            },            
            "upgrade_subscription": {
                "title": "Subscription Upgrade",
                "issue_type": "Task",
                "priority": "P1", 
                "label": "subscription-upgrade"
            }
        }
        
        return action_configs.get(action, {
            "title": "Customer Support Request",
            "issue_type": "Task",
            "priority": "P2",
            "label": "customer-support"
        })
    
    def _build_ticket_description(self, action: str, email: str, details: Dict[str, Any]) -> str:
        """Build detailed ticket description"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        description_parts = [
            f"Automated ticket created by MontyCloud Customer Support Bot",
            f"",
            f"Action: {action.replace('_', ' ').title()}",
            f"Customer Email: {email}",
            f"Timestamp: {timestamp}",
            f"",
            f"Details:",
        ]
        
        for key, value in details.items():
            if value:
                description_parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        description_parts.extend([
            f"",
            f"Status: Pending processing",
            f"",
            f"This ticket was automatically created and requires manual review and processing."
        ])
        
        return "\n".join(description_parts)
    
    def _create_mock_ticket(self, action: str, email: str, details: Dict[str, Any]) -> Tuple[bool, str, str]:
        """Create a mock ticket for testing purposes"""
        # Generate a mock ticket key
        ticket_key = f"CST-{hash(email + action + str(datetime.now())) % 10000}"
        ticket_url = f"{self.base_url}/browse/{ticket_key}"
        
        logger.info(f"Mock JIRA ticket created: {ticket_key}")
        return True, ticket_key, ticket_url
    
    def get_ticket_status(self, ticket_key: str) -> Optional[str]:
        """Get the current status of a JIRA ticket"""
        if self.mock_mode:
            return "In Progress"
        
        try:
            url = f"{self.base_url}/rest/api/3/issue/{ticket_key}?fields=status"
            response = requests.get(url, headers=self.headers, auth=self.auth)
            
            if response.status_code == 200:
                ticket_data = response.json()
                return ticket_data['fields']['status']['name']
            else:
                logger.error(f"Failed to get ticket status: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting ticket status: {e}")
            return None
    def _set_initial_status(self, ticket_key: str, status: str) -> bool:
        """Set the initial status of a newly created ticket"""
        try:
            # Try to transition to the desired status
            return self.update_ticket_status(ticket_key, status, "Ticket created and set to pending status")
        except Exception as e:
            logger.warning(f"Could not set initial status to {status} for {ticket_key}: {e}")
            return False

# Convenience function for easy integration
def create_support_ticket(action: str, email: str, **kwargs) -> Tuple[bool, str, str]:
    """
    Convenience function to create a support ticket
    
    Returns:
        Tuple of (success: bool, ticket_key: str, ticket_url: str)
    """
    jira = JiraIntegration()
    return jira.create_customer_support_ticket(action, email, kwargs)

def update_support_ticket(ticket_key: str, status: str, comment: str = "") -> bool:
    """
    Convenience function to update a support ticket
    
    Returns:
        bool: Success status
    """
    jira = JiraIntegration()
    return jira.update_ticket_status(ticket_key, status, comment)
