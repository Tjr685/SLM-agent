# MontyCloud Customer Support Bot - JIRA Integration & Webhook Setup 🎫

## 🎯 NEW FEATURES IMPLEMENTED:

### ✅ 1. JIRA Ticket Assignment & Status
- **Automatic Assignment**: All tickets now assigned to `tejasvini.ramaswamy@montycloud.com`
- **Initial Status**: Tickets automatically set to "Pending" status after creation
- **Single Ticket**: Fixed duplicate ticket creation - now only ONE ticket per workflow

### ✅ 2. JIRA Webhook Integration
- **Status Change Detection**: Monitors JIRA for status changes (Pending → Approved/Rejected)
- **Teams Notifications**: Automatically notifies Teams when status changes
- **Smart Messaging**: Different messages for approved, rejected, or other status changes

---

## 🔧 SETUP INSTRUCTIONS:

### Step 1: Install Flask (for webhook server)
```bash
cd "c:\Users\Tejasvini Ramaswamy\AgentsToolkitProjects\slm_trial\src"
pip install flask
```

### Step 2: Configure JIRA Webhook

#### Option A: Project-Level Webhook (Recommended)
1. Go to your JIRA project: https://montycloud.atlassian.net/projects/CST
2. Click **Project Settings** (bottom left)
3. Click **Webhooks** in the left sidebar
4. Click **Create webhook**

#### Option B: System-Level Webhook (Admin required)
1. Go to **JIRA Settings** → **System** → **Webhooks**
2. Click **Create webhook**

#### Webhook Configuration:
```
Name: MontyCloud Teams Bot Webhook
URL: http://your-server:5000/webhook/jira
Events: ✅ Issue Updated
JQL Filter: project = CST
```

**⚠️ IMPORTANT**: You need to replace `http://your-server:5000` with your actual server URL. Options:
- **Local testing**: Use ngrok to expose local server
- **Azure**: Deploy webhook to your Azure infrastructure
- **Public server**: Any publicly accessible server

### Step 3: Create "Pending" Status in JIRA (if not exists)

1. Go to **Project Settings** → **Statuses**
2. Check if "Pending" status exists
3. If not, create it:
   - **Name**: Pending
   - **Category**: To Do
   - **Description**: Awaiting review and approval

---

## 🚀 HOW TO RUN:

### Start the Webhook Server:
```bash
cd "c:\Users\Tejasvini Ramaswamy\AgentsToolkitProjects\slm_trial\src"
python run_webhook.py 5000
```

### Start the Teams Bot (in another terminal):
```bash
cd "c:\Users\Tejasvini Ramaswamy\AgentsToolkitProjects\slm_trial\src"
python app.py
```

---

## 🎭 WORKFLOW EXAMPLES:

### Example 1: Trial Extension Approved
```
1. User: "extend trial for john@acme.com to next month"
2. Bot creates JIRA ticket CST-X, assigns to you, sets status "Pending"
3. You change status in JIRA: Pending → Approved
4. Teams gets notification:

🎉 **GREAT! REQUEST APPROVED**
✅ **Ticket**: CST-X
📧 **Customer**: john@acme.com
🔗 **JIRA Link**: https://montycloud.atlassian.net/browse/CST-X

This ticket has been **APPROVED**! I will now go ahead and extend the trial period.
```

### Example 2: Subscription Upgrade Rejected
```
1. User: "upgrade abc@corp.com from trial to enterprise effective 20th June 2025"
2. Bot creates JIRA ticket CST-Y, assigns to you, sets status "Pending"
3. You change status in JIRA: Pending → Rejected (with comments)
4. Teams gets notification:

❌ **REQUEST REJECTED**
🎫 **Ticket**: CST-Y
📧 **Customer**: abc@corp.com
🔗 **JIRA Link**: https://montycloud.atlassian.net/browse/CST-Y

The request has been **REJECTED**. Please check the JIRA ticket for detailed comments and reasoning.
```

---

## 🔍 TESTING THE WEBHOOK:

### Test 1: Health Check
```bash
curl http://localhost:5000/webhook/health
```
**Expected Response:**
```json
{"status": "healthy", "timestamp": "2025-06-19T11:30:00"}
```

### Test 2: Webhook Payload (simulate JIRA)
```bash
curl -X POST http://localhost:5000/webhook/jira \
  -H "Content-Type: application/json" \
  -d '{
    "webhookEvent": "jira:issue_updated",
    "issue": {
      "key": "CST-TEST",
      "fields": {
        "summary": "Trial Extension Request - test@example.com",
        "labels": ["trial-extension"]
      }
    },
    "changelog": {
      "items": [{
        "field": "status",
        "fromString": "Pending",
        "toString": "Approved"
      }]
    }
  }'
```

---

## 📋 QUESTIONS FOR YOU:

### For Webhook URL:
1. **Local Development**: Do you want to use ngrok for local testing?
   - Install: `npm install -g ngrok`
   - Run: `ngrok http 5000`
   - Use the ngrok URL in JIRA webhook

2. **Production**: Where should I deploy the webhook server?
   - Azure App Service?
   - Azure Functions?
   - Your existing infrastructure?

### For Teams Notifications:
1. **Notification Target**: Where should notifications go?
   - Specific Teams channel?
   - Direct message to you?
   - Same conversation where request originated?

2. **Channel Details**: If using a specific channel, what's the:
   - Team ID?
   - Channel ID?
   - Or should I use a webhook URL?

---

## 🎯 CURRENT STATUS:

✅ **COMPLETED**:
- JIRA tickets assigned to you
- Initial status set to "Pending"
- Single ticket creation (no duplicates)
- Webhook server infrastructure
- Teams notification system
- Natural language date parsing working

🔄 **NEEDS YOUR INPUT**:
- JIRA webhook URL configuration
- Teams notification target details
- "Pending" status creation in JIRA (if needed)

---

## 🚀 NEXT STEPS:

1. **Test Current Features**: Try creating a ticket and verify assignment + status
2. **Configure Webhook**: Set up JIRA webhook with your chosen URL
3. **Test Notifications**: Change a ticket status and verify Teams notification
4. **Production Setup**: Deploy webhook server to production environment

Let me know:
1. How you want to handle the webhook URL (ngrok, Azure, etc.)
2. Where Teams notifications should go
3. If you need help setting up the "Pending" status in JIRA

The infrastructure is ready - we just need to connect the final pieces! 🎉
