# 🚀 Minimal Railway Setup

This is the simplified approach - just the essentials to get your app live!

## 📋 What You Need

### 1. **Railway Account**

- Sign up at [railway.app](https://railway.app)
- Connect your GitHub account

### 2. **Twilio Account** (for SMS verification)

- Sign up at [twilio.com](https://twilio.com)
- Get your Account SID, Auth Token, and Phone Number

## 🚀 Deployment Steps

### Step 1: Deploy Backend

1. **Go to Railway Dashboard**
2. **Click "New Project"**
3. **Select "Deploy from GitHub repo"**
4. **Choose your repository**
5. **Set the root directory to `backend`**

### Step 2: Add Database

1. **In your Railway project, click "New"**
2. **Select "Database" → "PostgreSQL"**
3. **Railway will create a managed PostgreSQL database**

### Step 3: Configure Environment Variables

In your Railway project dashboard, go to "Variables" and add ONLY these essential variables:

```bash
# Django Settings
DJANGO_SETTINGS_MODULE=api.settings.production_simple
DJANGO_SECRET_KEY=your-generated-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.railway.app

# Database (Railway provides this automatically)
DATABASE_URL=postgresql://... (Railway provides this)

# Twilio (for SMS verification)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-phone
TWILIO_VERIFY_SERVICE_SID=your-verify-service-sid

# API Keys (if you're using these features)
OPENAI_API_KEY=your-openai-key
LANGFUSE_SECRET_KEY=your-langfuse-secret
LANGFUSE_PUBLIC_KEY=your-langfuse-public
MIXPANEL_PROJECT_TOKEN=your-mixpanel-token
```

### Step 4: Deploy Frontend

1. **In the same Railway project, click "New"**
2. **Select "Deploy from GitHub repo"**
3. **Choose the same repository**
4. **Set the root directory to `frontend`**

### Step 5: Configure Frontend Environment

Add these variables to your frontend service:

```bash
NODE_ENV=production
NEXT_PUBLIC_API_BASE_URL=https://your-backend-service-url.railway.app
```

## 🎯 What This Gives You

✅ **Working backend API** with database
✅ **Working frontend** that connects to your API
✅ **SMS verification** via Twilio
✅ **Automatic HTTPS** and SSL
✅ **Auto-deployment** from GitHub

## ❌ What We're Skipping (For Now)

- AWS S3 (file storage)
- Mailgun (email service)
- Redis (caching)
- Custom domains

## 🔧 How to Generate Secret Key

Run this in your terminal:

```bash
cd Emmi/backend
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 🎉 You're Done!

Once deployed:

- Your backend will be at: `https://your-backend-service.railway.app`
- Your frontend will be at: `https://your-frontend-service.railway.app`
- Your API will be at: `https://your-backend-service.railway.app/api/v1/`

## 🔄 Adding More Services Later

When you're ready, you can add:

1. **AWS S3** for file uploads
2. **Mailgun** for email notifications
3. **Redis** for better performance
4. **Custom domain** for your app

But for now, this minimal setup will get you live and working! 🚀
