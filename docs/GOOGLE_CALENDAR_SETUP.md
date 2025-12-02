# Google Calendar Setup

Step-by-step setup for Google Calendar integration (OAuth & Service Account)

1. Create a Google Cloud project
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials (Desktop app) and download `credentials.json`
4. Place `credentials.json` in the project root (or set `GOOGLE_CREDENTIALS_JSON` env var)
5. Ensure `SCOPES` include both `https://www.googleapis.com/auth/calendar.readonly` and `https://www.googleapis.com/auth/calendar.events`
6. If using a service account, share calendar with service account email and use service account JSON

Example: delete old `token.json` after changing scopes to force re-authentication.
