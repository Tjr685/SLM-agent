# JIRA Webhook Setup Request

**To**: JIRA Administrator  
**From**: Tejasvini Ramaswamy  
**Date**: $(Get-Date)

## Request Summary
I need a JIRA webhook created to integrate our MontyCloud Customer Support Bot with Teams notifications.

## Webhook Configuration Needed:

**Webhook Name**: MontyCloud Teams Bot Webhook  
**URL**: https://5e48-2405-201-4008-a061-cd7e-c52e-8bff-6c9e.ngrok-free.app/webhook/jira  
**Events to Monitor**: 
- Issue Updated (specifically status changes)

**JQL Filter**: 
```
project = CST AND labels in ("trial-extension", "signup-approval", "beta-features", "subscription-upgrade")
```

**Security**: 
- No authentication required (webhook handler validates payloads)
- Public endpoint (secured via ngrok)

## Business Justification:
This webhook will enable automatic Teams notifications when JIRA tickets change status, improving our customer support response times and team coordination.

## Technical Details:
- The webhook endpoint is already implemented and tested
- Local testing has been completed successfully
- This integrates with our existing Microsoft Teams bot infrastructure

## Next Steps:
1. Create the webhook with above configuration
2. Test with a sample ticket status change
3. Verify Teams notifications are received

**Contact**: tejasvini.ramaswamy@montycloud.com for any questions or testing coordination.
