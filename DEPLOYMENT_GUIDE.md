# 🚀 OpalSight Cloud Deployment Guide

Deploy your comprehensive OpalSight application to the cloud with automated updates, real-time data collection, and a modern UI.

## 🌟 **What You'll Get**

### Production-Ready Features
- ✅ **Automated Monthly Data Collection** - Real Q1 2025 earnings transcripts
- ✅ **Beautiful Modern UI** - Interactive dashboards with charts and analytics
- ✅ **PDF Report Generation** - Professional reports with direct management quotes
- ✅ **Real-Time Updates** - Automated scheduling and notifications
- ✅ **Production Database** - PostgreSQL with Redis caching
- ✅ **CI/CD Pipeline** - Automated deployment on code changes

### Live URLs After Deployment
- **Backend API**: `https://your-app.railway.app`
- **Frontend Website**: `https://opalsight.vercel.app`
- **Real-time Analytics**: Access Q1 2025 insights, quotes, and PDF downloads

---

## 🏗️ **Deployment Architecture**

```
Frontend (Vercel)     →     Backend (Railway)     →     Database (Railway PostgreSQL)
                           │                      │
Modern React UI            │ Flask API Server     │     Redis Cache (Railway)
Charts & Analytics         │ Scheduled Tasks      │
PDF Downloads              │ Email Notifications  │
```

---

## 📋 **Prerequisites**

1. **GitHub Account** (for code repository)
2. **Railway Account** (for backend + database) - [Sign up free](https://railway.app)
3. **Vercel Account** (for frontend) - [Sign up free](https://vercel.com)
4. **API Keys**:
   - FMP API Key - [Get here](https://financialmodelingprep.com/developer/docs)
   - Earnings Call API Key - [Get here](https://earningscall.biz)

---

## 🚀 **Step 1: Deploy Backend to Railway**

### 1.1 Create Railway Project

1. Go to [Railway.app](https://railway.app) and sign in
2. Click "**New Project**"
3. Select "**Deploy from GitHub repo**"
4. Connect your GitHub account and select your OpalSight repository
5. Railway will automatically detect the Python application

### 1.2 Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```bash
# Required API Keys
FMP_API_KEY=your_fmp_api_key_here
EARNINGS_CALL_API_KEY=your_earnings_call_api_key_here

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database (will be auto-configured by Railway)
DATABASE_URL=${{ Railway.DATABASE_URL }}

# Redis Cache (will be auto-configured by Railway)
REDIS_URL=${{ Railway.REDIS_URL }}
CACHE_TYPE=redis

# Application Settings
PORT=8000
AUTO_COLLECTION_ENABLED=true
COLLECTION_HOUR=2
COLLECTION_DAY_OF_MONTH=1

# Email Notifications (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 1.3 Add Database Services

1. In Railway project, click "**+ New**"
2. Add "**PostgreSQL**" (for main database)
3. Add "**Redis**" (for caching)
4. Railway will automatically configure `DATABASE_URL` and `REDIS_URL`

### 1.4 Deploy

1. Railway will automatically deploy when you push to your main branch
2. Wait for deployment to complete (~5-10 minutes)
3. Your backend will be available at `https://your-app.railway.app`

---

## 🎨 **Step 2: Deploy Frontend to Vercel**

### 2.1 Prepare Frontend

1. Update `frontend/package.json` to add build script:
```json
{
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
```

2. Create `frontend/.env.production`:
```bash
REACT_APP_API_URL=https://your-app.railway.app
REACT_APP_API_VERSION=v1
```

### 2.2 Deploy to Vercel

1. Go to [Vercel.com](https://vercel.com) and sign in
2. Click "**New Project**"
3. Import your GitHub repository
4. Set **Root Directory** to `frontend`
5. Configure environment variables:
   - `REACT_APP_API_URL=https://your-app.railway.app`
6. Click "**Deploy**"

### 2.3 Configure Custom Domain (Optional)

1. In Vercel dashboard, go to **Domains**
2. Add your custom domain (e.g., `opalsight.com`)
3. Follow DNS configuration instructions

---

## ⚡ **Step 3: Configure Automated Updates**

### 3.1 GitHub Actions Setup

The included `.github/workflows/deploy.yml` will automatically:
- Run tests on every push
- Deploy backend to Railway on main branch
- Deploy frontend to Vercel on main branch

### 3.2 Required GitHub Secrets

Add these secrets in GitHub repository settings → Secrets and variables → Actions:

```bash
# Railway Deployment
RAILWAY_TOKEN=your_railway_token

# Vercel Deployment  
VERCEL_TOKEN=your_vercel_token
ORG_ID=your_vercel_org_id
PROJECT_ID=your_vercel_project_id
```

To get these tokens:
- **Railway Token**: Railway Dashboard → Account Settings → Tokens
- **Vercel Token**: Vercel Dashboard → Settings → Tokens
- **Org/Project IDs**: Available in Vercel project settings

---

## 📊 **Step 4: Verify Deployment**

### 4.1 Test Backend API

```bash
# Health check
curl https://your-app.railway.app/api/health

# Q1 2025 status
curl https://your-app.railway.app/api/q1-2025/status

# Trigger data collection
curl -X POST https://your-app.railway.app/api/q1-2025/collect
```

### 4.2 Test Frontend

1. Visit `https://your-app.vercel.app`
2. Navigate to "**Q1 2025 Analytics**"
3. Test PDF download functionality
4. Verify charts and data visualization

### 4.3 Test Automated Features

1. **Scheduler**: Check Railway logs for scheduled tasks
2. **Data Collection**: Monitor API logs during collection
3. **Email Notifications**: Verify email delivery (if configured)

---

## 🔧 **Step 5: Configure Production Features**

### 5.1 Enable Automated Data Collection

The system will automatically:
- **Monthly**: Collect new transcripts (1st of month, 2 AM UTC)
- **Weekly**: Update existing data (Fridays, 6 AM UTC)  
- **Daily**: Run health checks (12 PM UTC)

### 5.2 Monitor System Health

Railway provides built-in monitoring:
- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time application logs
- **Alerts**: Configurable alerts for downtime

### 5.3 Backup Strategy

Railway automatically handles:
- **Database backups**: Daily automated backups
- **Point-in-time recovery**: Available for PostgreSQL
- **Version control**: All code changes tracked in GitHub

---

## 🎯 **Step 6: Access Your Live Application**

### 6.1 Main Application
- **URL**: `https://your-app.vercel.app`
- **Features**: Complete OpalSight dashboard with modern UI

### 6.2 Q1 2025 Analytics
- **URL**: `https://your-app.vercel.app/q1-analytics`
- **Features**: Real-time insights, quotes, guidance, PDF downloads

### 6.3 API Documentation
- **URL**: `https://your-app.railway.app/api/health`
- **Endpoints**: Full REST API for programmatic access

---

## 📈 **Step 7: Scale and Optimize**

### 7.1 Performance Optimization

Railway automatically scales based on usage:
- **Auto-scaling**: Horizontal scaling during high traffic
- **Resource monitoring**: CPU/Memory optimization
- **Global CDN**: Fast content delivery worldwide

### 7.2 Cost Management

**Free Tier Limits**:
- Railway: $5/month free credit (sufficient for moderate usage)
- Vercel: Free for personal projects, unlimited bandwidth
- Total estimated cost: **$5-15/month** for production usage

### 7.3 Advanced Features

Enable additional features:
- **Custom domain**: Professional branding
- **SSL certificates**: Automatic HTTPS
- **Analytics**: User tracking and insights
- **Error tracking**: Sentry integration

---

## 🆘 **Troubleshooting**

### Common Issues

**1. Database Connection Errors**
```bash
# Check Railway database status
railway status

# Verify DATABASE_URL environment variable
railway env
```

**2. API Rate Limiting**
- Ensure API keys are correctly configured
- Check API usage limits in provider dashboards

**3. Build Failures**
```bash
# Check Railway build logs
railway logs

# Local testing
cd backend
pip install -r requirements.txt
python run.py
```

**4. Frontend Build Issues**
```bash
cd frontend
npm install
npm run build
```

### Get Help

- **Railway Support**: [Railway Discord](https://discord.gg/railway)
- **Vercel Support**: [Vercel Discord](https://discord.gg/vercel)
- **GitHub Issues**: Create issues in your repository

---

## 🎉 **Success! Your OpalSight is Live**

You now have a fully-featured, production-ready OpalSight deployment with:

✅ **Real-time data collection** from actual Q1 2025 earnings calls  
✅ **Beautiful modern UI** with interactive charts and analytics  
✅ **Automated PDF reports** with direct management quotes  
✅ **Scheduled updates** running monthly/weekly automatically  
✅ **Professional deployment** with monitoring and scaling  
✅ **Cost-effective hosting** under $15/month  

**Your live URLs:**
- 🌐 **Website**: `https://your-app.vercel.app`
- 🔗 **API**: `https://your-app.railway.app`
- 📊 **Analytics**: `https://your-app.vercel.app/q1-analytics`

**Next Steps:**
1. Share your live OpalSight with stakeholders
2. Monitor the automated data collection
3. Download PDF reports with real quotes
4. Scale as your usage grows

**Congratulations! 🎊 You've successfully deployed a comprehensive, production-ready earnings analysis platform!** 