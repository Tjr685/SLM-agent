"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from http import HTTPStatus
import json
import logging
from datetime import datetime

from aiohttp import web
from botbuilder.core.integration import aiohttp_error_middleware

from bot import bot_app
from webhook_handler import JiraWebhookHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize webhook handler
webhook_handler = JiraWebhookHandler()

routes = web.RouteTableDef()

@routes.post("/api/messages")
async def on_messages(req: web.Request) -> web.Response:
    res = await bot_app.process(req)

    if res is not None:
        return res

    return web.Response(status=HTTPStatus.OK)

@routes.post("/webhook/jira")
async def jira_webhook(req: web.Request) -> web.Response:
    """Handle JIRA webhook events"""
    try:
        # Get the webhook payload
        data = await req.json()
        
        if not data:
            logger.warning("Received empty webhook payload")
            return web.json_response({"error": "Empty payload"}, status=400)
        
        # Log the webhook event
        logger.info(f"Received JIRA webhook: {data.get('webhookEvent', 'unknown')}")
        
        # Check if this is an issue update event
        webhook_event = data.get('webhookEvent')
        if webhook_event != 'jira:issue_updated':
            logger.info(f"Ignoring webhook event: {webhook_event}")
            return web.json_response({"status": "ignored"}, status=200)
        
        # Extract issue information
        issue_info = webhook_handler.extract_issue_info(data)
        if not issue_info:
            logger.warning("Could not extract issue information from webhook")
            return web.json_response({"error": "Invalid issue data"}, status=400)
        
        # Check if status changed
        status_change = webhook_handler.extract_status_change(data)
        if not status_change:
            logger.info("No status change detected, ignoring")
            return web.json_response({"status": "no_status_change"}, status=200)
        
        # Process the status change
        webhook_handler.handle_status_change(issue_info, status_change)
        
        return web.json_response({"status": "processed"}, status=200)
        
    except Exception as e:
        logger.error(f"Error processing JIRA webhook: {e}")
        return web.json_response({"error": "Processing failed"}, status=500)

@routes.get("/webhook/health")
async def webhook_health(req: web.Request) -> web.Response:
    """Health check for webhook"""
    return web.json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})

app = web.Application(middlewares=[aiohttp_error_middleware])
app.add_routes(routes)

from config import Config

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=Config.PORT)