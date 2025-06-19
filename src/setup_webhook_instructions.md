# JIRA Webhook Setup - Manual Configuration

## 🎯 **CURRENT STATUS:**
- ✅ Webhook server running on `http://localhost:5000/webhook/jira`
- ✅ Teams bot already running (port 3978 in use)
- ✅ Webhook processing tested and working
- ❌ Need public URL for JIRA to reach webhook

## 🔧 **OPTION 1: Manual JIRA Webhook Setup (Recommended)**

Since you have JIRA admin access, let's configure the webhook directly:

### Step 1: Get a Public URL
Use one of these options:

#### Option A: Use ngrok (if available)
```bash
# Install ngrok if not already installed
choco install ngrok
# OR download from https://ngrok.com/download

# Start tunnel
ngrok http 5000
# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

#### Option B: Use webhook.site for testing
1. Go to https://webhook.site
2. Copy the unique URL
3. Modify webhook_handler.py to log payloads
4. Use this for initial testing

### Step 2: Configure JIRA Webhook
1. **Go to JIRA Project Settings**:
   - Visit: https://montycloud.atlassian.net/projects/CST
   - Click "Project Settings" (bottom left)

2. **Create Webhook**:
   - Look for "Webhooks" in the sidebar
   - Click "Create webhook"
   - Fill in:
     ```
     Name: MontyCloud Teams Bot Webhook
     URL: https://your-ngrok-url.ngrok.io/webhook/jira
     Events: ✅ Issue Updated
     JQL Filter: project = CST
     ```

### Step 3: Test the Integration
1. Create a test ticket through Teams bot
2. Change its status in JIRA
3. Check webhook server logs for incoming requests

## 🔧 **OPTION 2: Use Existing Infrastructure**

If you have existing Azure infrastructure:

### Deploy Webhook to Azure
```bash
# Deploy webhook server to Azure App Service
az webapp create --resource-group myResourceGroup --plan myPlan --name montycloud-webhook --runtime "PYTHON|3.11"
az webapp deployment source config --name montycloud-webhook --resource-group myResourceGroup --repo-url https://github.com/yourrepo --branch main
```

### Use Azure Function
Convert webhook_handler.py to Azure Function for serverless deployment.

## 🧪 **TESTING CURRENT SETUP**

While setting up the public URL, test the current system:

### Test 1: Create and Approve a Ticket
```bash
# 1. Create a ticket via Teams
# 2. Go to JIRA and change status to "Approved"
# 3. Run manual webhook test:
cd "c:\Users\Tejasvini Ramaswamy\AgentsToolkitProjects\slm_trial\src"
python test_webhook_manually.py
```

### Test 2: Monitor Webhook Server
```bash
# Watch the webhook server logs for incoming requests
# Terminal with webhook server should show:
# INFO:webhook_handler:Received JIRA webhook: jira:issue_updated
# INFO:webhook_handler:Processing status change for CST-X: Pending -> Approved
```

## 🎯 **RECOMMENDED IMMEDIATE STEPS:**

1. **Install ngrok**: 
   ```bash
   choco install ngrok
   # OR download from https://ngrok.com/download
   ```

2. **Start ngrok tunnel**:
   ```bash
   ngrok http 5000
   ```

3. **Configure JIRA webhook** with the ngrok HTTPS URL

4. **Test real status changes** in JIRA to trigger notifications

## 📞 **NEED HELP?**

If you need assistance with:
- Installing ngrok
- Configuring JIRA webhook
- Azure deployment
- Testing the integration

Let me know and I'll help with the specific step!
