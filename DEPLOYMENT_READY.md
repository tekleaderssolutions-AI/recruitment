# ✅ Render Deployment - Ready to Deploy!

## What I've Done For You

I've prepared your entire Hiring Agent application for deployment to Render.com. All you need to do is follow the quick steps below.

### Files Created:

1. **render.yaml** - Render's native deployment config
2. **Procfile** - Traditional web server process definition
3. **start.sh** - Bash startup script with migrations
4. **QUICK_DEPLOY.md** - 3-minute quick start guide ⭐ START HERE
5. **RENDER_DEPLOY_COMPLETE.md** - Detailed step-by-step guide
6. **RENDER_DEPLOYMENT.md** - Environment variables reference
7. **RENDER_CHECKLIST.md** - Pre/post deployment checklist

### Code Changes:

- ✅ Added startup block to `main.py` to handle PORT environment variable
- ✅ Verified all dependencies in `requirements.txt`
- ✅ Database migrations configured to run automatically
- ✅ Static files (HTML/CSS/JS) configured to serve from `/static`

---

## Next: Get API Keys (Takes 5-10 minutes)

### Gmail App Password (for email sending)
1. Go to https://accounts.google.com/security
2. Enable "2-Step Verification" if not already done
3. Go to https://myaccount.google.com/apppasswords
4. Select "Mail" and "Windows Computer"
5. Google will generate a 16-character password
6. ✅ Save this for `SMTP_PASSWORD`

### Google Gemini API Key (for AI analysis)
1. Go to https://aistudio.google.com/
2. Click "Get API Key" → "Create new API key"
3. ✅ Copy the key for `GEMINI_API_KEY`

### Google Calendar OAuth (optional, for calendar events)
1. Go to https://console.cloud.google.com/
2. Create new project → Enable "Google Calendar API"
3. Create OAuth 2.0 Client ID (Desktop application)
4. Download JSON and save as `credentials.json`
5. ✅ Have this ready for upload to Render

---

## Deploy to Render (Takes 5 minutes)

### 1️⃣ Push Code to GitHub
```bash
cd path/to/hiring_agent/hiring
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2️⃣ Create PostgreSQL on Render
- Go to https://render.com (create account if needed)
- New → PostgreSQL
- Name: `hiring-agent-db`
- Database: `recruitment_ai`
- Click Create
- **Copy the connection string**

### 3️⃣ Create Web Service on Render
- New → Web Service
- Connect your GitHub repository
- Name: `hiring-agent`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Click Create Web Service

### 4️⃣ Add Environment Variables
In Render dashboard → Settings → Environment:

**Required (from your email/APIs):**
```
SMTP_USER = your-email@gmail.com
SMTP_PASSWORD = <16-char-password>
FROM_EMAIL = your-email@gmail.com
GEMINI_API_KEY = <your-api-key>
INTERVIEWER_EMAIL = interviewer@company.com
BASE_URL = https://hiring-agent.onrender.com
```

**From PostgreSQL:**
```
DB_HOST = <copy from postgres service>
DB_PORT = 5432
DB_NAME = recruitment_ai
DB_USER = postgres
DB_PASSWORD = <copy from postgres service>
```

**Defaults (can copy as-is):**
```
SMTP_HOST = smtp.gmail.com
SMTP_PORT = 587
CHAT_MODEL = gemini-2.0-flash
EMBEDDING_MODEL = text-embedding-004
GOOGLE_CALENDAR_CREDENTIALS_PATH = credentials.json
INTERVIEW_DURATION_MINUTES = 60
COMPANY_NAME = Tek Leaders
```

### 5️⃣ Deploy
- Click "Deploy"
- Wait 2-5 minutes
- Status should turn Green (Live)

### 6️⃣ Test
- Visit https://hiring-agent.onrender.com/
- Click Admin → Initialize Database
- Upload a resume and JD
- Test the ranking and email flow

---

## Your App is Live! 🎉

After deployment, you can:
- ✅ Upload resumes and JDs
- ✅ Rank candidates automatically
- ✅ Send interview invitations
- ✅ Track interview schedules
- ✅ Manage the entire recruitment workflow

---

## Helpful Docs

- **Quick Start**: Read `QUICK_DEPLOY.md` in project root
- **Detailed Guide**: Read `RENDER_DEPLOY_COMPLETE.md`
- **Checklist**: Follow `RENDER_CHECKLIST.md`
- **Environment Vars**: See `RENDER_DEPLOYMENT.md`

---

## Troubleshooting

**"Build fails"**
- Check: pip install -r requirements.txt works locally
- Verify all imports are in requirements.txt

**"Database won't connect"**
- Verify DB_HOST, DB_USER, DB_PASSWORD are correct
- Wait 1-2 minutes for PostgreSQL to initialize

**"Email not sending"**
- Use Gmail App Password (NOT regular password)
- Enable 2FA on Google account
- Check SMTP_USER and SMTP_PASSWORD match

**"Service won't start"**
- Check Render logs tab for errors
- Verify all environment variables are set
- Ensure BASE_URL matches your Render domain

---

## Support

- 📖 Render Docs: https://render.com/docs
- 🐍 FastAPI Docs: https://fastapi.tiangolo.com/
- 💬 GitHub Issues: Create in your repository

---

## Summary

You now have:
- ✅ Production-ready code
- ✅ Deployment configuration files
- ✅ Complete step-by-step guides
- ✅ Troubleshooting documentation

**Ready to deploy? Start with `QUICK_DEPLOY.md`!** 🚀

