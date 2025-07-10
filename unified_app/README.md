# OpalSight - Unified Application

**Automated Earnings Call Analysis Platform for Biotech/Medtech Companies**

This is a single-file application that combines all OpalSight functionality into one easy-to-run Python application.

## 🎯 Features

- **✅ Complete React Frontend** - Professional UI with Material-UI
- **✅ Flask Backend API** - All endpoints and functionality
- **✅ SQLite Database** - Embedded database with sample data
- **✅ In-Memory Caching** - Fast response times
- **✅ FinBERT Sentiment Analysis** - Financial sentiment analysis
- **✅ Performance Monitoring** - Real-time system metrics
- **✅ Export Functionality** - CSV data export
- **✅ Sample Data** - 5 biotech companies pre-loaded

## 🚀 Quick Start

### Option 1: Using the Startup Script (Recommended)
```bash
cd unified_app
./start_opalsight.sh
```

### Option 2: Manual Setup
```bash
cd unified_app

# Install dependencies
pip3 install -r requirements.txt

# Run the application
python3 opalsight_app.py
```

## 🌐 Access the Application

Once started, access the application at:
- **Frontend**: http://localhost:3000
- **API Health**: http://localhost:3000/api/health
- **Performance**: http://localhost:3000/api/performance/status
- **Companies API**: http://localhost:3000/api/companies

## 📋 Requirements

- Python 3.8 or later
- pip3
- Internet connection (for downloading FinBERT model on first run)

## 🔧 Application Structure

The unified application includes:

### Frontend Pages
- **Dashboard** - Market overview and analytics
- **Companies** - Browse biotech/medtech companies
- **Performance** - System monitoring and testing
- **Company Details** - Individual company analysis

### API Endpoints
- `/api/health` - Application health status
- `/api/companies` - Company listings and details
- `/api/performance/status` - System performance metrics
- `/api/performance/test/*` - Performance testing
- `/api/analyze/sentiment` - Sentiment analysis
- `/api/export/companies/csv` - Data export

### Technologies Used
- **Frontend**: React, Material-UI, Recharts
- **Backend**: Flask, SQLite, FinBERT
- **ML**: Transformers, PyTorch
- **Monitoring**: psutil for system metrics

## 📊 Sample Data

The application comes pre-loaded with 5 biotech companies:
- Moderna Inc. (MRNA)
- Pfizer Inc. (PFE)
- Johnson & Johnson (JNJ)
- Gilead Sciences Inc. (GILD)
- Amgen Inc. (AMGN)

## 🛠 Configuration

Environment variables (optional):
```bash
export SECRET_KEY="your-secret-key"
export FMP_API_KEY="your-fmp-api-key"
export SMTP_USERNAME="your-email@gmail.com"  # For email features
export SMTP_PASSWORD="your-app-password"     # For email features
```

## 📈 Performance Features

The application includes comprehensive performance monitoring:
- Real-time CPU, memory, and disk usage
- Database and cache latency testing
- Sentiment analysis performance testing
- System health checks

## 🔒 Security Notes

- Uses SQLite database (single file)
- All data stored locally
- No external database connections required
- Sample data only for demonstration

## 🆘 Troubleshooting

### Common Issues

1. **"Python 3 not found"**
   - Install Python 3.8+ from python.org

2. **"Module not found" errors**
   - Run: `pip3 install -r requirements.txt`

3. **"Port 3000 already in use"**
   - Stop other applications using port 3000
   - Or modify the port in `opalsight_app.py`

4. **Slow first startup**
   - Normal - FinBERT model downloads on first run (~500MB)

### Performance Tips

- First run will be slower due to model download
- Application uses ~1GB RAM when fully loaded
- SQLite database file will be created in the same directory

## 📝 License

This application includes all the features from the original OpalSight project, consolidated into a single file for easy deployment and testing.
