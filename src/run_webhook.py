#!/usr/bin/env python3
"""
Run the JIRA webhook server
Usage: python run_webhook.py [port]
"""

import sys
import os
from webhook_handler import start_webhook_server

if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    print(f"Starting JIRA webhook server on port {port}")
    print(f"Webhook URL will be: http://localhost:{port}/webhook/jira")
    print("Health check URL: http://localhost:{port}/webhook/health")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        start_webhook_server(port)
    except KeyboardInterrupt:
        print("\nWebhook server stopped")
