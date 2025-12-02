# Quick Deploy to Render - Summary

## Files Created for Deployment

✅ **render.yaml** - Render configuration
✅ **Procfile** - Process definition for web service
✅ **start.sh** - Bash startup script
✅ **RENDER_DEPLOYMENT.md** - Detailed environment variables guide
✅ **RENDER_CHECKLIST.md** - Step-by-step deployment checklist
✅ **RENDER_DEPLOY_COMPLETE.md** - Complete end-to-end guide

## 3-Minute Quick Start

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Deploy to Render"
git push origin main
```

### Step 2: Create Services on Render
1. **PostgreSQL**: render.com → New → PostgreSQL → Create
   - Save connection string
   
2. **Web Service**: render.com → New → Web Service → Connect GitHub
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add Environment Variables
Copy these to Render Environment:

```
# Database (from PostgreSQL service)
DB_HOST=<postgres-host>
DB_PORT=5432
DB_NAME=recruitment_ai
DB_USER=postgres
DB_PASSWORD=<postgres-password>

# Gmail SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<gmail-app-password>
FROM_EMAIL=your-email@gmail.com

# APIs
GEMINI_API_KEY=<your-key>
GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials.json
INTERVIEWER_EMAIL=interviewer@company.com

# App
BASE_URL=https://<your-service>.onrender.com
COMPANY_NAME=Tek Leaders
```

### Step 4: Deploy
Click **"Deploy"** and wait 2-5 minutes

### Step 5: Test
- Visit `https://<your-service>.onrender.com/`
- Go to Admin → Initialize Database
- Test upload and ranking

---

## Important: Gmail App Password

⚠️ Use **Gmail App Password** (not regular password):

1. Enable 2FA: https://accounts.google.com/security
2. Get app password: https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer"
4. Copy 16-char password
5. Use in `SMTP_PASSWORD`

---

## Getting Help

- **Build errors?** Check Render logs tab
- **Database errors?** Check PostgreSQL status
- **Email not working?** Verify app password
- **Detailed guide?** Read `RENDER_DEPLOY_COMPLETE.md`

---

## What's Included

Your app automatically gets:
- ✅ Automatic database migrations on startup
- ✅ Environment variable support
- ✅ Proper PORT handling (for Render)
- ✅ HTTPS (free SSL certificate)
- ✅ GitHub auto-deploy (on git push)
- ✅ 750 hours/month free tier

---

## After Deployment

1. ✅ Initialize database (Admin → Init DB)
2. ✅ Upload resumes and JDs
3. ✅ Test email sending
4. ✅ Test interview flow
5. ✅ Monitor logs daily

---

**You're ready to deploy! 🚀**

Follow `RENDER_DEPLOY_COMPLETE.md` for detailed instructions.
