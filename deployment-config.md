# 🚀 OpalSight Deployment Configuration Guide

## 📋 **Step 1: Railway Backend Deployment**

### 1.1 Create Railway Project
1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your opalsight repository
5. Railway will auto-detect Python and use the `railway.toml` configuration

### 1.2 Add Database Services
1. In your Railway project, click "+ New"
2. Add **PostgreSQL** service
3. Add **Redis** service
4. Railway will automatically set `DATABASE_URL` and `REDIS_URL` variables

### 1.3 Configure Environment Variables
In Railway dashboard → Variables, add these:

```bash
# Required API Keys
FMP_API_KEY=your_fmp_api_key_here
EARNINGS_CALL_API_KEY=your_earnings_call_api_key_here

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-in-production

# Application Settings
PORT=8000
AUTO_COLLECTION_ENABLED=true
COLLECTION_HOUR=2
COLLECTION_DAY_OF_MONTH=1

# Email Notifications (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 1.4 Deploy Backend
1. Railway will automatically deploy when you push to main branch
2. Your backend will be available at: `https://your-app-name.railway.app`

---

## 🎨 **Step 2: Vercel Frontend Deployment**

### 2.1 Create Vercel Project
1. Go to [Vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Set **Root Directory** to `frontend`
5. Framework preset should auto-detect as "Create React App"

### 2.2 Configure Environment Variables
In Vercel dashboard → Settings → Environment Variables:

```bash
REACT_APP_API_URL=https://your-app-name.railway.app
REACT_APP_API_VERSION=v1
REACT_APP_ENVIRONMENT=production
```

### 2.3 Deploy Frontend
1. Click "Deploy"
2. Your frontend will be available at: `https://your-app-name.vercel.app`

---

## 🔧 **Step 3: GitHub Actions Setup**

### 3.1 Required GitHub Secrets
Go to GitHub repository → Settings → Secrets and Variables → Actions:

```bash
# Railway Deployment
RAILWAY_TOKEN=your_railway_token

# Vercel Deployment
VERCEL_TOKEN=your_vercel_token
ORG_ID=your_vercel_org_id
PROJECT_ID=your_vercel_project_id
```

### 3.2 Get Required Tokens
- **Railway Token**: Railway Dashboard → Account Settings → Tokens
- **Vercel Token**: Vercel Dashboard → Settings → Tokens
- **Org/Project IDs**: Available in Vercel project settings

---

## 🧪 **Step 4: Test Your Deployment**

### 4.1 Backend API Tests
```bash
# Health check
curl https://your-app-name.railway.app/api/health

# Q1 2025 status
curl https://your-app-name.railway.app/api/q1-2025/status

# Test data collection
curl -X POST https://your-app-name.railway.app/api/q1-2025/collect
```

### 4.2 Frontend Tests
1. Visit `https://your-app-name.vercel.app`
2. Navigate to "Q1 2025 Analytics"
3. Test PDF download functionality
4. Verify charts load correctly

---

## 🎯 **Your Live URLs After Deployment**

- **Frontend**: `https://your-app-name.vercel.app`
- **Backend API**: `https://your-app-name.railway.app`
- **Q1 Analytics**: `https://your-app-name.vercel.app/q1-analytics`

---

## 🚀 **API Keys You'll Need**

### FMP API Key
1. Go to [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs)
2. Sign up for free account
3. Get your API key from dashboard

### Earnings Call API Key  
1. Go to [Earnings Call](https://earningscall.biz)
2. Sign up for free account
3. Get your API key from dashboard

---

## 🔄 **Automated Updates**

Once GitHub Actions is configured:
- **Push to main** → Automatically deploys backend to Railway
- **Push to main** → Automatically deploys frontend to Vercel
- **Monthly data collection** → Runs automatically on Railway
- **PDF reports** → Generated and available for download

---

## 💡 **Tips for Success**

1. **Start with Railway** - Set up backend first to get your API URL
2. **Test locally** - Make sure your API keys work before deploying
3. **Monitor logs** - Check Railway logs for any deployment issues
4. **Verify environment** - Make sure all variables are set correctly
5. **Test endpoints** - Verify API endpoints work before frontend deployment

**Your OpalSight is production-ready with real Q1 2025 data collection! 🎉** 