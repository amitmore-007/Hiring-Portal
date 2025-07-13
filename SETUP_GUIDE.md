# Hiring Portal Setup Guide

## Environment Variables Setup

Create a `.env` file in the project root with the following variables:

```bash
# GROQ API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Zoom API Configuration (for meeting scheduling)
ZOOM_ACCOUNT_ID=your_zoom_account_id
ZOOM_CLIENT_ID=your_zoom_client_id  
ZOOM_CLIENT_SECRET=your_zoom_client_secret

# Django Configuration
SECRET_KEY=your_django_secret_key
DEBUG=True
```

## Quick Fix for Current Issues

### 1. Resume Download Issue
The resume download issue has been fixed by:
- Updating main URL configuration to properly serve media files
- Removing conflicting custom resume URL routing
- Ensuring proper MEDIA_URL and MEDIA_ROOT settings

### 2. Generate Questions Error (500)
The generate questions error has been fixed by:
- Adding proper error handling in the `generate_interview_questions` function
- Validating file paths and API keys before processing
- Adding detailed error messages for troubleshooting

### 3. Meeting Scheduling
Meeting scheduling has been improved with:
- Enhanced error handling for Zoom API calls
- Input validation for required parameters
- Better timeout handling for network requests

## Authentication Fixes

### Issues Fixed:
1. **Login Redirect Loops**: Removed conflicting LOGIN_URL settings that caused redirect loops
2. **Dashboard Access**: Fixed authentication decorators to prevent redirect to login page when already logged in
3. **Session Management**: Improved session configuration for better authentication handling
4. **URL Conflicts**: Cleaned up URL patterns to avoid authentication conflicts

### Key Changes:
- Removed default LOGIN_URL from settings to prevent conflicts
- Added proper authentication checks in views
- Improved error handling and messaging
- Fixed redirect logic for authenticated users

## Installing Dependencies

```bash
pip install -r requirements.txt
```

## Setting Up GROQ API Key

1. Sign up at https://console.groq.com/
2. Get your API key
3. Add it to your environment variables or `.env` file

## Testing the Fixes

1. **Resume Download**: Upload a resume and try downloading it from both candidate and interviewer dashboards
2. **Generate Questions**: Click the "Generate AI Questions" button on interviewer dashboard
3. **Meeting Scheduling**: Try scheduling a meeting (requires valid Zoom credentials)
4. **Candidate Login**: 
   - Go to `/candidate/login/`
   - Enter credentials and click "Sign In"
   - Should redirect to `/candidate/dashboard/` successfully
5. **Interviewer Login**: 
   - Go to `/interviewer/login/`
   - Enter credentials and click "Access Dashboard"
   - Should redirect to `/interviewer/dashboard/` successfully
6. **Generate Questions**: 
   - Login as interviewer
   - Should stay on dashboard when generating questions
   - No redirect to login page

## Deployment Considerations

- Ensure `DEBUG=False` in production
- Set `CSRF_COOKIE_SECURE=True` and `SESSION_COOKIE_SECURE=True` for HTTPS
- Verify media file serving is configured correctly

## Troubleshooting

- If resume download still fails, check if the `media` folder has proper permissions
- If question generation fails, verify GROQ_API_KEY is correctly set
- If meeting scheduling fails, verify Zoom API credentials are valid
- If login still redirects to same page, clear browser cache and cookies
- Check Django logs for authentication errors
- Verify CSRF tokens are included in forms
- Ensure session middleware is enabled
