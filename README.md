# Job Application Tracker

A web application to track your job applications, automatically import them from Gmail, and manage your job search process.

## Features

- **Application Tracking**: Track job applications with company, position, status, salary expectations, and notes
- **Gmail Integration**: Automatically scan and import job application emails via Google OAuth
- **Response Detection**: Detect rejections, interview requests, and offers from email responses
- **Status Management**: Track application status (Applied, Interviewing, Offered, Rejected, Withdrawn)
- **Connections**: Save contacts from recruiters and hiring managers who respond to your applications
- **Dashboard**: View stats, response rates, and recent activity
- **Multi-User Support**: Data is tied to your Google account - sign in to access your data from anywhere

## Tech Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: HTMX, Jinja2 templates, Tailwind CSS
- **Authentication**: Google OAuth 2.0
- **Deployment**: Render (or any WSGI-compatible host)

## Local Development

### Prerequisites

- Python 3.11+
- Google Cloud project with Gmail API enabled

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/esedwards14/JobTracker.git
   cd JobTracker
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Google OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API
   - Create OAuth 2.0 credentials (Web application)
   - Add `http://127.0.0.1:3000/oauth/callback` to Authorized redirect URIs

5. Create a `.env` file:
   ```
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

6. Run the application:
   ```bash
   python run.py
   ```

7. Open http://127.0.0.1:3000 in your browser

## Deployment to Render

### 1. Create PostgreSQL Database

- In Render dashboard, click **New** → **PostgreSQL**
- Note the **Internal Database URL**

### 2. Create Web Service

- Click **New** → **Web Service**
- Connect your GitHub repository
- Configure:
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn run:app`

### 3. Set Environment Variables

Add these in your web service settings:

| Variable | Value |
|----------|-------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | Generate a secure random string |
| `DATABASE_URL` | Your PostgreSQL Internal Database URL |
| `GOOGLE_CLIENT_ID` | Your Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Your Google OAuth client secret |

### 4. Update Google OAuth

Add your Render URL to Google Cloud Console:
- Go to **APIs & Services** → **Credentials**
- Edit your OAuth client
- Add `https://your-app.onrender.com/oauth/callback` to Authorized redirect URIs

## Usage

### Importing Applications from Gmail

1. Click **Email Settings** in the navigation
2. Sign in with Google to connect your Gmail
3. Click **Scan for Applications** to find job-related emails
4. Review and import detected applications

### Scanning for Responses

1. Go to **Email Settings**
2. Click **Scan for Responses**
3. The system will detect rejections, interview requests, and offers
4. Application statuses will be updated automatically
5. Contacts from personal emails will be saved to your Connections

### Managing Applications

- **Add manually**: Click **New Application** to add an application by hand
- **Edit**: Click on any application to view/edit details
- **Status updates**: Change status from the application list or detail page
- **Bulk actions**: Select multiple applications for bulk status updates or deletion

## License

MIT
