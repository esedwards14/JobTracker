# Job Application Tracker

Track your job applications, automatically import them from Gmail, and manage your job search.

## Features

- **Gmail Integration**: Automatically scan and import job application emails
- **Response Detection**: Detect rejections, interviews, and offers from emails
- **Status Tracking**: Applied, Interviewing, Offered, Rejected, Withdrawn
- **Connections**: Save contacts from recruiters who respond
- **Dashboard**: View stats and response rates

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/esedwards14/JobTracker.git
cd JobTracker
pip install -r requirements.txt
```

### 2. Set up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the **Gmail API**
3. Create **OAuth 2.0 credentials** (Web application)
4. Add redirect URI: `http://127.0.0.1:3000/oauth/callback`

### 3. Create `.env` file

```
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 4. Run

```bash
python run.py
```

Open http://127.0.0.1:3000

## Deploy to Render

1. Fork this repo
2. Create a **PostgreSQL** database on Render
3. Create a **Web Service** connected to your fork
4. Add environment variables:
   - `FLASK_ENV=production`
   - `SECRET_KEY=generate-a-random-string`
   - `DATABASE_URL=your-postgres-internal-url`
   - `GOOGLE_CLIENT_ID=your-client-id`
   - `GOOGLE_CLIENT_SECRET=your-client-secret`
5. Add `https://your-app.onrender.com/oauth/callback` to Google OAuth redirect URIs

## License

MIT
