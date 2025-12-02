# Render Deployment Checklist

## Pre-Deployment Checklist

### 1. GitHub Repository
- [ ] Push all code to GitHub
- [ ] Ensure `.gitignore` excludes:
  - `token.json`
  - `.env`
  - `credentials.json` (use env var instead)
  - `__pycache__/`
  - `uenv/` or `venv/`

### 2. API Keys & Credentials
- [ ] Have Gemini API key ready
- [ ] Have Gmail account with app password
- [ ] Have Google Calendar credentials (JSON)
- [ ] Have PostgreSQL connection string

### 3. Code Changes
- [ ] Reviewed and tested locally
- [ ] All imports are in `requirements.txt`
- [ ] Database migrations are working
- [ ] Email sending tested

---

## Render Deployment Steps

### Step 1: Create PostgreSQL Database
- [ ] Go to render.com
- [ ] Click "New +" → "PostgreSQL"
- [ ] Configure:
  - Name: `hiring-agent-db`
  - Database: `recruitment_ai`
  - User: `postgres`
- [ ] Copy connection string

### Step 2: Create Web Service
- [ ] Click "New +" → "Web Service"
- [ ] Connect GitHub repository
- [ ] Configure:
  - Name: `hiring-agent`
  - Environment: `Python 3`
  - Region: Closest to you
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add Environment Variables
In Render Settings → Environment, add:

```
DB_HOST=<from postgres service>
DB_PORT=5432
DB_NAME=recruitment_ai
DB_USER=postgres
DB_PASSWORD=<from postgres>

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-gmail>
SMTP_PASSWORD=<gmail-app-password>
FROM_EMAIL=<your-gmail>

GEMINI_API_KEY=<your-key>
CHAT_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=text-embedding-004

GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials.json
INTERVIEWER_EMAIL=<interviewer-email>
INTERVIEW_DURATION_MINUTES=60

BASE_URL=https://<your-service>.onrender.com
COMPANY_NAME=Tek Leaders
```

### Step 4: Upload Google Credentials
**Option A: Environment Variable**
1. Open `credentials.json` in text editor
2. Copy entire content
3. Create env var: `GOOGLE_CREDENTIALS_JSON` = (paste JSON)
4. Update config.py to read from env var

**Option B: File Storage**
1. Use Render's persistent disk feature
2. Upload `credentials.json` during deployment

### Step 5: Deploy
- [ ] Click "Deploy"
- [ ] Wait for build to complete
- [ ] Check logs for errors
- [ ] Test: visit `https://<service>.onrender.com/`

---

## Post-Deployment Verification

### Access Your App
- [ ] Visit frontend: `https://<service>.onrender.com/`
- [ ] Visit API docs: `https://<service>.onrender.com/docs`
- [ ] Check logs for errors

### Test Core Features
- [ ] Initialize database: POST `/init-db`
- [ ] Upload resume (Admin)
- [ ] Upload JD (Recruiter)
- [ ] Rank candidates (auto-sends emails)
- [ ] Verify emails sent
- [ ] Test interview scheduling flow

### Monitor
- [ ] Check Render dashboard logs regularly
- [ ] Monitor PostgreSQL logs
- [ ] Set up email alerts for errors

---

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Verify all packages in `requirements.txt`
- Ensure Python version is compatible

### Service Won't Start
- Check start command logs
- Verify environment variables are set
- Test migrations ran successfully

### Database Errors
- Verify PostgreSQL connection string
- Check user permissions
- Run migrations manually via logs

### Email Not Sending
- Verify Gmail app password (not regular password)
- Check 2FA is enabled
- Test SMTP credentials locally

### API Errors
- Check Render logs
- Verify all env vars are set
- Test endpoints via `/docs`

---

## Important Notes

1. **Free Tier Limits**:
   - Services spin down after 15 min inactivity
   - First deployment may take 3-5 minutes
   - Limited to 750 hours/month

2. **Persistent Data**:
   - PostgreSQL data persists
   - uploaded files stored in database
   - Use environment variables for secrets

3. **Production Tips**:
   - Upgrade to paid tier for always-on service
   - Enable automatic deployments from GitHub
   - Set up monitoring/alerts
   - Regularly backup database

---

## Support

- Render Docs: https://render.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com/
- GitHub Issues: Create issue in your repo

