# Firebase Authentication Setup

This document provides step-by-step instructions for setting up Firebase Authentication for the Volleyball Manager API.

## 1. Create Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or select an existing project
3. Follow the setup wizard to create your project
4. Once created, you'll be redirected to the project dashboard

## 2. Enable Authentication

1. In the Firebase Console, navigate to **Authentication** in the left sidebar
2. Click on the **Get started** button if this is your first time
3. Go to the **Sign-in method** tab
4. Enable the sign-in providers you want to use:
   - **Email/Password**: Most common for web apps
   - **Google**: For Google account integration
   - **Anonymous**: For guest users (optional)
   - Add other providers as needed

## 3. Generate Service Account Key

1. Go to **Project Settings** (gear icon in the left sidebar)
2. Navigate to the **Service accounts** tab
3. Click **Generate new private key**
4. A JSON file will be downloaded - **keep this file secure!**
5. The JSON file contains your Firebase Admin SDK credentials

## 4. Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Name: `FIREBASE_ADMIN_KEY`
5. Value: Copy and paste the **entire contents** of the service account JSON file
6. Click **Add secret**

## 5. Frontend Integration

Your frontend application needs to:

### Initialize Firebase Auth SDK

```javascript
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  // Your Firebase config object
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  // ... other config
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
```

### Sign in users and get ID tokens

```javascript
import { signInWithEmailAndPassword } from 'firebase/auth';

// Sign in user
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const user = userCredential.user;

// Get ID token
const idToken = await user.getIdToken();

// Use token in API requests
const response = await fetch('/api/matches/simulate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${idToken}`
  },
  body: JSON.stringify(requestData)
});
```

## 6. API Usage

All API endpoints (except `/health`) now require authentication:

### Protected Endpoints
- `POST /matches/simulate` - Simulate volleyball matches
- `GET /clubs` - Get club information
- `POST /clubs` - Create new clubs
- `GET /leagues/standings` - Get league standings
- `POST /start-season` - Start new seasons

### Public Endpoints
- `GET /health` - Health check (no authentication required)

### Request Format
```http
POST /matches/simulate
Authorization: Bearer <firebase_id_token>
Content-Type: application/json

{
  "homeClubId": "club123",
  "awayClubId": "club456"
}
```

### Error Responses
- `401 Unauthorized` - Missing or invalid authentication token
- `400 Bad Request` - Invalid request format
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## 7. Local Development

For local development, you have two options:

### Option 1: Use Service Account Key
1. Download the service account JSON file
2. Set the environment variable:
   ```bash
   export FIREBASE_ADMIN_KEY='{"type":"service_account","project_id":"..."}'
   ```

### Option 2: Use Application Default Credentials
1. Install Google Cloud SDK
2. Run `gcloud auth application-default login`
3. The application will use your default credentials

## 8. Testing

### Generate Test Tokens
You can use the Firebase Auth REST API to generate test tokens:

```bash
# Get ID token using REST API
curl -X POST \
  'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "testpassword",
    "returnSecureToken": true
  }'
```

### Test API Endpoints
```bash
# Test protected endpoint
curl -X GET \
  'http://localhost:8080/clubs?clubId=test123' \
  -H 'Authorization: Bearer YOUR_ID_TOKEN'

# Test without token (should return 401)
curl -X GET 'http://localhost:8080/clubs?clubId=test123'
```

## 9. Security Best Practices

1. **Never commit service account keys** to version control
2. **Use environment variables** for sensitive configuration
3. **Rotate service account keys** regularly
4. **Limit service account permissions** to minimum required
5. **Use HTTPS** in production
6. **Validate tokens** on every request
7. **Set appropriate CORS policies** for your frontend domain

## 10. Troubleshooting

### Common Issues

**"Invalid token" errors:**
- Check that the token hasn't expired (Firebase ID tokens expire after 1 hour)
- Verify the token is being sent in the correct format: `Bearer <token>`
- Ensure the service account key is correctly configured

**"Service unavailable" errors:**
- Check that `FIREBASE_ADMIN_KEY` environment variable is set
- Verify the JSON format of the service account key
- Ensure Firebase Admin SDK is properly initialized

**CORS errors:**
- Verify that your frontend domain is allowed in CORS configuration
- Check that `Authorization` header is included in allowed headers

### Debug Mode
Set `FLASK_ENV=development` to enable debug mode and get more detailed error messages.

## Support

For additional help:
- [Firebase Auth Documentation](https://firebase.google.com/docs/auth)
- [Firebase Admin SDK Documentation](https://firebase.google.com/docs/admin/setup)
- [Flask-CORS Documentation](https://flask-cors.readthedocs.io/)
