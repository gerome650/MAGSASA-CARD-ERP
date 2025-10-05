# 🔑 Stage 7.3.1 - Notion API Key Setup Guide

## ❌ Current Issue
All API keys provided are returning **401 Unauthorized** errors, which means:
- The API keys are invalid
- The integration might not exist or is revoked
- The keys might be copied incorrectly

## ✅ Step-by-Step Solution

### Step 1: Access Notion Integrations
1. Open your browser
2. Go to: **https://www.notion.so/my-integrations**
3. Sign in with your Notion account

### Step 2: Check Existing Integrations
**What you should see:**
- A list of your integrations (if any exist)
- Each integration will show its name and status
- Look for "AI Studio Master Automation" or similar

**Check the status:**
- ✅ **Active** - Good!
- ❌ **Revoked/Suspended** - Need to reactivate or create new one
- ❌ **Not found** - Need to create a new integration

### Step 3: Create a NEW Integration (Recommended)
Since existing keys aren't working, let's create a fresh one:

1. Click **"+ New integration"** button (top right)
2. Fill in the form:
   - **Name**: `AI Studio Master Automation`
   - **Logo**: (optional)
   - **Associated workspace**: Select your workspace (the one with your databases)
3. Click **"Submit"**

### Step 4: Configure Integration Capabilities
After creating the integration:

1. You'll be on the integration settings page
2. Under **"Capabilities"** section:
   - ✅ Check **"Read content"**
   - ✅ Check **"Update content"**
   - ✅ Check **"Insert content"**
   - ✅ Check **"Read comments"** (if available)
   - ✅ Check **"Create comments"** (if available)
3. Click **"Save changes"** if needed

### Step 5: Get the Secret Key
**This is the most important step:**

1. On the integration settings page, scroll to **"Secrets"** section
2. You'll see a masked secret like: `secret_••••••••••••••••••••••••••••`
3. Click the **"Show"** button next to it
4. The full secret will be revealed
5. Click **"Copy"** or manually select and copy the ENTIRE secret
6. **IMPORTANT**: The secret should start with `secret_` and be very long

**Example of what a real secret looks like:**
```
secret_ntn_ABCD1234efgh5678IJKL9012mnop3456QRST7890uvwx
```

### Step 6: Verify You Copied the Correct Value
Before providing the key, verify:
- ✅ It starts with `secret_ntn_` (or just `secret_`)
- ✅ It's approximately 50-100 characters long
- ✅ It contains random-looking letters and numbers
- ✅ You copied it from the "Secrets" section (NOT the integration ID)
- ✅ There are no extra spaces before or after

### Step 7: Share Databases with Integration
**CRITICAL STEP** - Even with a valid key, you MUST share each database:

1. **Open each database in Notion** (in the Notion app or web):
   - CI Intelligence Reports
   - MAGSASA-CARD ERP Roadmap
   - AI Studio Strategic Milestones
   - Control Center (if it's a database)

2. **For each database:**
   - Click the **"..."** (three dots) menu at the top right
   - Select **"Add connections"** or **"Connect to"**
   - Find and select **"AI Studio Master Automation"**
   - Click **"Confirm"**

3. **Verify the connection:**
   - You should see a small icon/badge showing the integration is connected
   - The integration name should appear in the connections list

### Step 8: Provide the Secret Key
Once you've:
- ✅ Created/verified the integration
- ✅ Copied the secret key from the "Secrets" section
- ✅ Shared all databases with the integration

**Provide the secret key** and I'll update the system and run validation.

---

## 🔍 Common Mistakes to Avoid

### ❌ Wrong: Copying the Integration ID
The integration ID (found in the URL) is NOT the API key:
```
https://www.notion.so/my-integrations/internal/abcd1234-efgh-5678-ijkl-9012mnop3456
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                            This is NOT the API key!
```

### ✅ Right: Copying from the Secrets Section
The API key is in the "Secrets" section and looks like:
```
secret_ntn_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### ❌ Wrong: Not Sharing Databases
Having a valid API key is not enough. You MUST share each database with the integration.

### ✅ Right: Share ALL Databases
Each database must be individually connected to the integration.

---

## 🧪 Test Your API Key

After getting your API key, you can test it quickly:

```bash
python3 scripts/fix_notion_api_key.py YOUR_API_KEY
```

Or test manually:
```bash
python3 -c "
import requests
api_key = 'YOUR_API_KEY_HERE'
headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json', 'Notion-Version': '2022-06-28'}
response = requests.post('https://api.notion.com/v1/search', headers=headers, json={'page_size': 1})
print(f'Status: {response.status_code}')
print('✅ Key is valid!' if response.status_code == 200 else f'❌ Error: {response.json()}')
"
```

---

## 📊 Current Status

### API Keys Tested (All Failed):
1. `secret_ntn_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` ❌
2. `secret_ntn_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY` ❌
3. `secret_ntn_ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ` ❌

### Next Steps:
1. Create a NEW integration following steps above
2. Get a FRESH secret key from the Secrets section
3. Share ALL databases with the integration
4. Provide the new secret key for testing

---

## 🆘 Still Having Issues?

If you're still getting 401 errors after following all steps:

1. **Verify workspace access**: Make sure the integration has access to the workspace
2. **Check Notion status**: Visit https://status.notion.so/ to check if Notion is experiencing issues
3. **Try a different browser**: Sometimes caching issues can cause problems
4. **Contact Notion support**: If the integration appears active but keys don't work

---

## 📞 Support

If you need help:
1. Share a screenshot of your integration settings page (with the secret masked)
2. Confirm which workspace the integration is associated with
3. Confirm that you can see the databases in Notion
4. Verify that the integration appears in the database connections list

