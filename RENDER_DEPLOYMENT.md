# Hiring Agent - Render Deployment Guide

## Quick Start on Render

### Step 1: Connect GitHub Repository
1. Go to [render.com](https://render.com)
2. Create a new account or log in
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repository
5. Fill in the service details:
   - **Name**: `hiring-agent`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 2: Add PostgreSQL Database
1. Click **"New +"** → **"PostgreSQL"**
2. Create a PostgreSQL instance
   - **Name**: `hiring-agent-db`
   - **Database**: `recruitment_ai`
   - Copy the connection string

### Step 3: Set Environment Variables
In the Render dashboard, add these environment variables to your web service:

```
# Database
DB_HOST=<your-postgres-host>
DB_PORT=5432
DB_NAME=recruitment_ai
DB_USER=<postgres-user>
DB_PASSWORD=<postgres-password>

# Email (Gmail SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-gmail>
SMTP_PASSWORD=<gmail-app-password>
FROM_EMAIL=<your-gmail>

# API Keys
GEMINI_API_KEY=<your-gemini-key>
CHAT_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=text-embedding-004

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_PATH=/var/data/credentials.json
INTERVIEWER_EMAIL=<interviewer-email>
INTERVIEW_DURATION_MINUTES=60

# Application
BASE_URL=https://<your-render-url>.onrender.com
COMPANY_NAME=Tek Leaders
```

### Step 4: Upload Google Credentials
The `credentials.json` file should be stored securely:

**Option 1: Environment Variable**
1. Add as environment variable:
   - **Key**: `GOOGLE_CREDENTIALS_JSON`
   - **Value**: (paste entire JSON content)
2. Update config.py to read from env var

**Option 2: File Upload**
If Render supports file uploads, place `credentials.json` in the root directory.

### Step 5: Deploy
1. Click **"Deploy"** - Render will automatically:
   - Install dependencies
   - Run database migrations
   - Start the FastAPI server

### Step 6: Access Your App
- Frontend: `https://<your-render-url>.onrender.com/`
- API: `https://<your-render-url>.onrender.com/docs`

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | `postgresql-xxxx.onrender.com` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `recruitment_ai` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | (secure password) |
| `SMTP_USER` | Gmail address | `your-email@gmail.com` |
| `SMTP_PASSWORD` | Gmail app password | (see below) |
| `FROM_EMAIL` | Sender email | `your-email@gmail.com` |
| `GEMINI_API_KEY` | Google Gemini API key | (from Google Cloud) |
| `GOOGLE_CALENDAR_CREDENTIALS_PATH` | Path to credentials | `credentials.json` |
| `INTERVIEWER_EMAIL` | Interviewer email | `interviewer@company.com` |
| `BASE_URL` | Public app URL | `https://hiring-agent.onrender.com` |
| `COMPANY_NAME` | Your company name | `Tek Leaders` |

---

## Getting Required API Keys

### Gmail App Password
1. Enable 2-factor authentication on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Select Mail and Windows Computer
4. Generate app password (copy the 16-character password)
5. Use this password in `SMTP_PASSWORD`

### Google Gemini API
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create API key
3. Copy key to `GEMINI_API_KEY`

### Google Calendar Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 Client ID (Desktop app)
3. Download JSON and save as `credentials.json`
4. Upload or store in environment variable

---

## Database Setup

After deployment, the database migrations will run automatically:

```bash
python -c "import migrations; migrations.init_db()"
```

This creates:
- `memories` table (for JDs)
- `resumes` table (for resumes)
- `candidate_outreach` table (for candidate tracking)
- `interview_schedules` table (for interview scheduling)

---

## First-Time Setup

1. **Initialize Database**: Visit `/init-db` endpoint (auto-runs on deploy)
2. **Upload Resumes**: Admin Portal → Upload Resumes
3. **Upload JD**: Recruiter Portal → Upload Job Description
4. **Rank Candidates**: Auto-sends emails to top matches
5. **Candidates Respond**: Click "Interested" link in email
6. **Interview Emails Sent**: Automatic to interested candidates
7. **Confirm Slots**: Candidates select preferred time

---

## Troubleshooting

### "No available time slots"
- Check Google Calendar API is enabled
- Verify `INTERVIEWER_EMAIL` has free time blocks
- Ensure `GOOGLE_CALENDAR_CREDENTIALS_PATH` is correct

### "Failed to send email"
- Verify Gmail app password (not regular password)
- Check 2FA is enabled on Gmail account
- Ensure `SMTP_USER` and `SMTP_PASSWORD` match

### "Database connection failed"
- Verify PostgreSQL instance is running
- Check connection string in environment variables
- Ensure IP whitelist includes Render's IP

### "Migrations failed"
- Check PostgreSQL user has proper permissions
- Try running migrations manually
- Check database logs in Render dashboard

---

## Support

For issues, check:
1. Render logs: Dashboard → Services → Logs
2. Database: Dashboard → Databases → Query Console
3. GitHub Issues: Create issue with error logs

