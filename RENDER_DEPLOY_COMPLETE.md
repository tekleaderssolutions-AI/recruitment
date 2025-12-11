# Deploy Hiring Agent to Render - Complete Guide

## Overview
This guide walks you through deploying your Hiring Agent application to Render.com for free.

---

## Part 1: Prepare Your Code

### 1.1 Ensure Code is on GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 1.2 Update .gitignore
Make sure your `.gitignore` includes:
```
token.json
.env
credentials.json
__pycache__/
uenv/
venv/
*.pyc
.DS_Store
```

### 1.3 Verify requirements.txt
All packages should be listed:
```bash
pip freeze > requirements.txt
```

---

## Part 2: Set Up Render Services

### 2.1 Create PostgreSQL Database on Render

1. Go to https://render.com
2. Sign up or log in
3. Dashboard → Click **"New +"** → **"PostgreSQL"**
4. Configure:
   - **Name**: `hiring-agent-db`
   - **Database**: `recruitment_ai` 
   - **User**: `postgres`
   - **Region**: Choose closest to you
   - **PostgreSQL Version**: Latest (14+)
5. Click **"Create Database"**
6. **Copy the connection string** (save somewhere safe)

Example connection string:
```
postgresql://postgres:PASSWORD@hiring-agent-db.xyz.postgres.render.com:5432/recruitment_ai
```

### 2.2 Create Web Service on Render

1. Click **"New +"** → **"Web Service"**
2. Choose **"Deploy an existing repository"**
3. Connect your GitHub account
4. Select your hiring-agent repository
5. Configure:
   - **Name**: `hiring-agent`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: Free (for testing)
   - **Auto-Deploy**: On (to auto-deploy on git push)

6. Click **"Create Web Service"**

---

## Part 3: Configure Environment Variables

### 3.1 Get Your API Keys Ready

Before adding environment variables, gather:

**Gmail (SMTP)**:
1. Enable 2-factor authentication: https://accounts.google.com/security
2. Generate app password: https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer"
4. Save the 16-character password

**Google Gemini API**:
1. Go to https://aistudio.google.com/
2. Click "Get API Key"
3. Create new API key
4. Copy the key

**Google Calendar OAuth**:
1. Go to https://console.cloud.google.com/
2. Create new project
3. Enable Calendar API
4. Create OAuth 2.0 Client ID (Desktop application)
5. Download JSON
6. Save credentials.json securely

### 3.2 Add Environment Variables to Render

In Render Dashboard:
1. Select your **hiring-agent** web service
2. Click **Settings**
3. Scroll to **Environment**
4. Click **"Add Environment Variable"** for each:

```
DB_HOST = hiring-agent-db.c123456.postgres.render.com
DB_PORT = 5432
DB_NAME = recruitment_ai
DB_USER = postgres
DB_PASSWORD = <your-postgres-password>

SMTP_HOST = smtp.gmail.com
SMTP_PORT = 587
SMTP_USER = your-email@gmail.com
SMTP_PASSWORD = <16-char-app-password>
FROM_EMAIL = your-email@gmail.com

GEMINI_API_KEY = <your-api-key>
CHAT_MODEL = gemini-2.5-flash
EMBEDDING_MODEL = text-embedding-004

GOOGLE_CALENDAR_CREDENTIALS_PATH = credentials.json
INTERVIEWER_EMAIL = interviewer@company.com
INTERVIEW_DURATION_MINUTES = 60

BASE_URL = https://hiring-agent.onrender.com
COMPANY_NAME = Tek Leaders
```

⚠️ **IMPORTANT**: Replace placeholder values with actual values

### 3.3 Add Google Credentials

**Option A: As Environment Variable** (Recommended for small files)
1. Open `credentials.json` in text editor
2. Copy entire JSON content
3. Add new environment variable:
   - **Name**: `GOOGLE_CREDENTIALS_JSON`
   - **Value**: (paste entire JSON)
4. Update `config.py`:
   ```python
   import json
   
   cred_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
   if cred_json:
       GOOGLE_CALENDAR_CREDENTIALS_PATH = json.loads(cred_json)
   ```

**Option B: As File** (If Render supports file uploads)
1. Create `/var/data/credentials.json`
2. Upload via Render dashboard

---

## Part 4: Deploy & Test

### 4.1 Deploy
1. Click **"Deploy"** on Render service page
2. Watch build logs in **"Events"** tab
3. Wait for status to show "Live" (green)
4. Takes 2-5 minutes typically

### 4.2 Verify Deployment
1. Visit your app: `https://hiring-agent.onrender.com/`
2. Should see the resume ranking portal
3. Check API docs: `https://hiring-agent.onrender.com/docs`

### 4.3 Initialize Database
1. Go to Admin Portal
2. Click **"Initialize Database"** button
3. Should show: `{"status": "ok", "message": "migrations run"}`

### 4.4 Test Upload
1. Upload a resume (Admin Portal)
2. Upload a JD (Recruiter Portal)
3. Verify files are processed
4. Check that emails would be sent

---

## Part 5: Monitor & Maintain

### 5.1 Check Logs
Render Dashboard → Services → **hiring-agent** → **Logs**

Look for:
- Build errors
- Runtime errors
- API responses

### 5.2 Database Monitoring
Render Dashboard → Databases → **hiring-agent-db** → **Query Console**

Run queries to verify data:
```sql
SELECT * FROM memories LIMIT 5;
SELECT * FROM resumes LIMIT 5;
SELECT * FROM candidate_outreach LIMIT 5;
```

### 5.3 Email Testing
From your deployed app:
1. Upload a JD
2. Upload resumes
3. Rank candidates
4. Check email inbox for outreach emails

### 5.4 Interview Flow
1. Click "Interested" in outreach email
2. Should receive interview invitation
3. Click time slot selection
4. Verify calendar event created (if Google Calendar enabled)

---

## Troubleshooting

### Build Fails: "Module not found"
**Solution**:
1. Check `requirements.txt` has all packages
2. Add missing package: `pip install <package-name>`
3. Update requirements: `pip freeze > requirements.txt`
4. Push to GitHub
5. Render auto-redeploys

### "Database connection refused"
**Solution**:
1. Verify `DB_HOST`, `DB_USER`, `DB_PASSWORD` are correct
2. Check PostgreSQL service is running (Render dashboard)
3. Wait a few minutes if service just started

### "No available email scopes" or "Calendar API error"
**Solution**:
1. Delete `token.json` file
2. Ensure correct Google credentials
3. Check API is enabled in Google Cloud Console
4. Add both scopes: `calendar.readonly` and `calendar.events`

### "Email not sending"
**Solution**:
1. Use **Gmail App Password** (not regular password)
2. Enable 2FA on Gmail account
3. Test SMTP: Visit `/send-emails` with test data
4. Check spam folder

### Service spins down after inactivity
**Normal on free tier**: 
- Service automatically pauses after 15 minutes
- Wakes up when you visit URL (takes 30 seconds)
- Upgrade to paid tier for always-on

---

## Free Tier Limits

- **Compute**: 750 hours/month (enough for always-on service)
- **Storage**: 500MB
- **Database**: PostgreSQL with limits
- **Bandwidth**: 100GB/month

Upgrade to paid tier for:
- Always-on service (no spindown)
- Larger databases
- More bandwidth
- Priority support

---

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test all features
3. 📧 Set up production email
4. 🔐 Enable HTTPS (automatic on Render)
5. 📊 Monitor logs daily
6. 🔄 Set up GitHub auto-deploy

---

## Quick Reference

| Task | Command/Link |
|------|--------------|
| Check Logs | Render Dashboard → Logs tab |
| View Database | Render Dashboard → Databases → Query Console |
| Restart Service | Render Dashboard → Manual Deploy |
| View Status | Render Dashboard → Status indicator |
| Get Public URL | Render Dashboard → service page |

---

## Support Resources

- **Render Docs**: https://render.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/deployment/
- **GitHub**: Create issue in your repo
- **Email Support**: support@render.com

---

**Ready to deploy? Start with Part 2 above!** 🚀

