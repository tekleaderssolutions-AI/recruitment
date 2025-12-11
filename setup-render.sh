#!/bin/bash
# setup-render.sh - Helper script to configure Render deployment

echo "=========================================="
echo "Render Deployment Setup Helper"
echo "=========================================="
echo ""
echo "This script helps you set up environment variables for Render deployment."
echo ""

# Prompt for database info
echo "=== PostgreSQL Database ==="
read -p "PostgreSQL Host (from Render): " DB_HOST
read -p "PostgreSQL User (usually 'postgres'): " DB_USER
read -s -p "PostgreSQL Password: " DB_PASSWORD
echo ""

# Prompt for email config
echo ""
echo "=== Gmail Configuration ==="
read -p "Gmail Address (your email): " SMTP_USER
read -s -p "Gmail App Password (16-char password): " SMTP_PASSWORD
echo ""

# Prompt for API keys
echo ""
echo "=== API Keys ==="
read -p "Gemini API Key: " GEMINI_API_KEY
read -p "Interviewer Email: " INTERVIEWER_EMAIL
read -p "Base URL (your Render URL, e.g., https://hiring-agent.onrender.com): " BASE_URL

# Generate environment file
cat > .env.render << EOF
# Database
DB_HOST=$DB_HOST
DB_PORT=5432
DB_NAME=recruitment_ai
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASSWORD
FROM_EMAIL=$SMTP_USER

# API Keys
GEMINI_API_KEY=$GEMINI_API_KEY
CHAT_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=text-embedding-004

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials.json
INTERVIEWER_EMAIL=$INTERVIEWER_EMAIL
INTERVIEW_DURATION_MINUTES=60

# Application
BASE_URL=$BASE_URL
COMPANY_NAME=Tek Leaders
EOF

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Environment file created: .env.render"
echo ""
echo "Next steps:"
echo "1. Copy all variables from .env.render"
echo "2. Add them to Render dashboard (Settings → Environment)"
echo "3. Also add credentials.json via Render file upload"
echo "4. Deploy your service"
echo ""
