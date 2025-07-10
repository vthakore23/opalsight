# OpalSight Analytics

A sophisticated earnings intelligence platform that automatically analyzes biotech/medtech earnings call transcripts to provide actionable insights through sentiment analysis, trend detection, and automated reporting.

## 🚀 Key Features

### Automated Data Collection
- **Monthly Transcript Retrieval**: Automatically fetches new earnings call transcripts on the last Friday of each month
- **Earnings Call API Integration**: Uses premium API access for reliable transcript data
- **Historical Data Support**: One-time ingestion script for past transcripts

### Advanced Analysis
- **AI-Powered Sentiment Analysis**: FinBERT model tuned for financial text
- **Biotech/Medtech Specific**: Enhanced analysis for industry-specific terminology
- **Trend Detection**: Compares current sentiment against historical data
- **Guidance Extraction**: Identifies and tracks management guidance changes

### Comprehensive Reporting
- **Monthly PDF Reports**: Automatically generated and emailed to stakeholders
- **Real-time Dashboard**: Interactive web interface with live data
- **Export Capabilities**: CSV, JSON, Excel, and PDF export options
- **Email Notifications**: Alerts for significant sentiment changes

### User Features
- **Company Watchlist**: Track specific companies with custom alert thresholds
- **Alert Management**: Severity-based alerts with resolution tracking
- **Performance Monitoring**: Built-in system performance dashboard
- **Responsive Design**: Works on desktop and mobile devices

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis (for caching)
- Node.js 16+ and npm
- Docker and Docker Compose (optional)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/opalsight.git
cd opalsight
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration:
# - EARNINGS_CALL_API_KEY=premium_44REQ4tOEr0T7ADdkEogjw
# - DATABASE_URL=postgresql://user:password@localhost:5432/opalsight
# - SMTP settings for email notifications
# - MONTHLY_REPORT_RECIPIENTS=email1@example.com,email2@example.com
```

### 3. Database Setup

```bash
# Create database
createdb opalsight

# Run migrations
cd backend
python -m flask db upgrade

# Initialize database schema
psql -U your_user -d opalsight -f database/schema.sql
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo "REACT_APP_API_URL=http://localhost:5000" > .env
```

### 5. Historical Data Ingestion (One-time)

```bash
cd backend
python scripts/historical_ingestion.py --years 2
```

## 🚀 Running the Application

### Development Mode

#### Backend:
```bash
cd backend
python run.py
```

#### Frontend:
```bash
cd frontend
npm start
```

#### Scheduler (for automated collection):
```bash
cd backend
python scheduler.py
```

### Production Mode with Docker

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 📱 Accessing the Application

- **Demo Landing Page**: http://localhost:3000/demo
- **Main Dashboard**: http://localhost:3000/dashboard
- **API Documentation**: http://localhost:5000/api/docs

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/opalsight
EARNINGS_CALL_API_KEY=premium_44REQ4tOEr0T7ADdkEogjw
REDIS_URL=redis://localhost:6379/0

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@opalsight.com
MONTHLY_REPORT_RECIPIENTS=analyst1@company.com,analyst2@company.com

# Optional OpenAI for enhanced analysis
OPENAI_API_KEY=your-openai-key
USE_GPT_ENHANCEMENT=true
```

#### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:5000
```

## 📊 API Endpoints

### Companies
- `GET /api/companies` - List all companies
- `GET /api/company/{ticker}` - Get company details
- `GET /api/company/{ticker}/sentiment-timeline` - Get sentiment history

### Reports
- `GET /api/reports` - List monthly reports
- `GET /api/reports/{id}` - Get specific report
- `GET /api/export/monthly-report/{id}/pdf` - Download report PDF

### Watchlist
- `GET /api/watchlist` - Get user watchlist
- `POST /api/watchlist` - Add to watchlist
- `DELETE /api/watchlist/{ticker}` - Remove from watchlist

### Alerts
- `GET /api/alerts` - List active alerts
- `POST /api/alerts/{id}/resolve` - Resolve alert

## 🔐 Security Features

- API authentication (implement as needed)
- SQL injection protection via SQLAlchemy ORM
- XSS protection in React
- CORS configuration
- Environment variable management
- SSL/TLS support in production

## 📈 Performance Optimization

- Redis caching for frequently accessed data
- Database indexes on key columns
- Pagination for large datasets
- Lazy loading in frontend
- Batch processing for transcript analysis

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📝 Monthly Automation

The system automatically runs on the last Friday of each month to:
1. Fetch new earnings call transcripts
2. Analyze sentiment and extract insights
3. Compare with historical data
4. Generate trend analyses
5. Create and email monthly reports

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For support, email support@opalsight.com or create an issue in the repository.

## 🎯 Roadmap

- [ ] Real-time transcript processing
- [ ] Multi-language support
- [ ] Advanced visualization options
- [ ] API rate limiting
- [ ] User authentication system
- [ ] Mobile app
- [ ] Webhook integrations
- [ ] Custom alert rules engine 