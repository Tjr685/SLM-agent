"""
Quick test script to send a simulated JIRA webhook to your local bot
"""
import requests
import sys
from datetime import datetime

def test_webhook(ticket_key="CST-123", action="extend_trial"):
    """Send a test webhook to the local server"""
    print(f"\n📬 Sending test JIRA webhook for ticket {ticket_key} ({action})...\n")
    
    # Call the test endpoint
    resp = requests.get(f"http://localhost:3978/test/webhook/jira?ticket={ticket_key}&action={action}")
    
    if resp.status_code == 200:
        print(f"✅ Success! Response: {resp.json()}")
    else:
        print(f"❌ Error: {resp.status_code} - {resp.text}")
    
    print("\n💡 To test in Teams, send a message containing 'jira', 'update', or 'status'")
    print("   The bot should respond with the JIRA ticket approval notification\n")

if __name__ == "__main__":
    # Allow passing ticket ID as argument
    ticket = sys.argv[1] if len(sys.argv) > 1 else f"CST-{datetime.now().strftime('%m%d')}"
    
    # Allow passing action type as argument
    action = sys.argv[2] if len(sys.argv) > 2 else "extend_trial"
    
    test_webhook(ticket, action)
