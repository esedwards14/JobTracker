# Job Application Tracker

Track your job applications with Gmail integration. Automatically import applications and detect responses.

## Quick Start

```bash
git clone https://github.com/esedwards14/JobTracker.git
cd JobTracker
pip install -r requirements.txt
```

Set up [Google OAuth credentials](https://console.cloud.google.com/) with Gmail API enabled, then:

```bash
export GOOGLE_CLIENT_ID=your-client-id
export GOOGLE_CLIENT_SECRET=your-client-secret
python run.py
```

Add `http://127.0.0.1:3000/oauth/callback` as a redirect URI in Google Cloud Console.

## Deploy to Render

1. Fork this repo
2. Create PostgreSQL database and Web Service on Render
3. Set environment variables: `FLASK_ENV`, `SECRET_KEY`, `DATABASE_URL`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
4. Add your Render URL to Google OAuth redirect URIs

## License

MIT
