import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
  Tab,
  Tabs,
  Paper,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField
} from '@mui/material';
import {
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Quote as QuoteIcon,
  Assessment as AssessmentIcon,
  Business as BusinessIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import axios from 'axios';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

function Q1Analytics() {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState(null);
  const [quotes, setQuotes] = useState([]);
  const [guidance, setGuidance] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [error, setError] = useState(null);
  const [pdfDownloadDialog, setPdfDownloadDialog] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState('');
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [collectionRunning, setCollectionRunning] = useState(false);

  // Filters
  const [quoteFilter, setQuoteFilter] = useState('all');
  const [guidanceFilter, setGuidanceFilter] = useState('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [insightsRes, quotesRes, guidanceRes, companiesRes] = await Promise.all([
        axios.get('/api/q1-2025/insights'),
        axios.get('/api/q1-2025/quotes?limit=20'),
        axios.get('/api/q1-2025/guidance?limit=20'),
        axios.get('/api/q1-2025/companies')
      ]);

      setInsights(insightsRes.data.insights);
      setQuotes(quotesRes.data.quotes || []);
      setGuidance(guidanceRes.data.guidance || []);
      setCompanies(companiesRes.data.companies || []);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load Q1 2025 data');
    } finally {
      setLoading(false);
    }
  };

  const runDataCollection = async () => {
    setCollectionRunning(true);
    try {
      await axios.post('/api/q1-2025/collect', { force_refresh: true });
      await loadData();
    } catch (err) {
      setError('Failed to run data collection');
    } finally {
      setCollectionRunning(false);
    }
  };

  const downloadCompanyReport = async () => {
    if (!selectedCompany) return;
    
    setDownloadingPdf(true);
    try {
      const response = await axios.get(`/api/q1-2025/report/company/${selectedCompany}?include_quotes=true`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `OpalSight_${selectedCompany}_Report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      setPdfDownloadDialog(false);
      setSelectedCompany('');
    } catch (err) {
      setError('Failed to download PDF report');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const getSentimentIcon = (sentiment) => {
    if (sentiment > 0.1) return <TrendingUpIcon color="success" />;
    if (sentiment < -0.1) return <TrendingDownIcon color="error" />;
    return <TrendingFlatIcon color="warning" />;
  };

  const getSentimentColor = (sentiment) => {
    if (sentiment > 0.1) return 'success';
    if (sentiment < -0.1) return 'error';
    return 'warning';
  };

  const filteredQuotes = quotes.filter(quote => {
    if (quoteFilter === 'all') return true;
    const sentiment = quote.sentiment_score || 0;
    if (quoteFilter === 'positive') return sentiment > 0.1;
    if (quoteFilter === 'neutral') return sentiment >= -0.1 && sentiment <= 0.1;
    if (quoteFilter === 'negative') return sentiment < -0.1;
    return true;
  });

  const filteredGuidance = guidance.filter(item => {
    if (guidanceFilter === 'all') return true;
    return item.metric === guidanceFilter;
  });

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={loadData}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      </Box>
    );
  }

  const pieData = insights?.sentiment_distribution ? [
    { name: 'Positive', value: insights.sentiment_distribution.positive, color: '#4caf50' },
    { name: 'Neutral', value: insights.sentiment_distribution.neutral, color: '#ff9800' },
    { name: 'Negative', value: insights.sentiment_distribution.negative, color: '#f44336' }
  ] : [];

  const trendData = insights?.trend_distribution ? Object.entries(insights.trend_distribution).map(([key, value]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    value
  })) : [];

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Q1 2025 Analytics
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AssessmentIcon />}
            onClick={runDataCollection}
            disabled={collectionRunning}
          >
            {collectionRunning ? 'Collecting...' : 'Run Collection'}
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={<DownloadIcon />}
            onClick={() => setPdfDownloadDialog(true)}
          >
            Download Reports
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Companies
              </Typography>
              <Typography variant="h4" component="div">
                {insights?.summary?.total_companies || 0}
              </Typography>
              <Typography variant="body2">
                Q1 2025 Analysis
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Avg Sentiment
              </Typography>
              <Typography variant="h4" component="div" color={getSentimentColor(insights?.summary?.avg_sentiment || 0)}>
                {insights?.summary?.avg_sentiment?.toFixed(3) || 'N/A'}
              </Typography>
              <Typography variant="body2">
                Overall Market
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Key Quotes
              </Typography>
              <Typography variant="h4" component="div">
                {insights?.summary?.total_quotes || 0}
              </Typography>
              <Typography variant="body2">
                Extracted
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Guidance Items
              </Typography>
              <Typography variant="h4" component="div">
                {insights?.summary?.total_guidance_items || 0}
              </Typography>
              <Typography variant="body2">
                Forward-Looking
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Sentiment Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Trend Categories
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <RechartsTooltip />
                  <Bar dataKey="value" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs for detailed data */}
      <Paper>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Key Quotes" icon={<QuoteIcon />} />
          <Tab label="Guidance & Outlook" icon={<TrendingUpIcon />} />
          <Tab label="Companies" icon={<BusinessIcon />} />
        </Tabs>

        {/* Key Quotes Tab */}
        {tabValue === 0 && (
          <Box p={3}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Management Quotes</Typography>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Filter</InputLabel>
                <Select
                  value={quoteFilter}
                  label="Filter"
                  onChange={(e) => setQuoteFilter(e.target.value)}
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="positive">Positive</MenuItem>
                  <MenuItem value="neutral">Neutral</MenuItem>
                  <MenuItem value="negative">Negative</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <List>
              {filteredQuotes.map((quote, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <Chip 
                          label={quote.company?.ticker || 'N/A'} 
                          size="small" 
                          color="primary" 
                        />
                        <Chip 
                          label={quote.topic?.replace('_', ' ') || 'General'} 
                          size="small" 
                          variant="outlined" 
                        />
                        <Chip 
                          icon={getSentimentIcon(quote.sentiment_score || 0)}
                          label={`${(quote.sentiment_score || 0).toFixed(2)}`}
                          size="small"
                          color={getSentimentColor(quote.sentiment_score || 0)}
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography 
                          variant="body1" 
                          sx={{ fontStyle: 'italic', my: 1 }}
                        >
                          "{quote.text}"
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {quote.speaker} - {quote.context?.replace('_', ' ')} context
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Guidance Tab */}
        {tabValue === 1 && (
          <Box p={3}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Forward-Looking Guidance</Typography>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Metric</InputLabel>
                <Select
                  value={guidanceFilter}
                  label="Metric"
                  onChange={(e) => setGuidanceFilter(e.target.value)}
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="revenue">Revenue</MenuItem>
                  <MenuItem value="earnings">Earnings</MenuItem>
                  <MenuItem value="patient_enrollment">Patient Enrollment</MenuItem>
                  <MenuItem value="regulatory_milestone">Regulatory</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <List>
              {filteredGuidance.map((item, index) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <Chip 
                          label={item.company?.ticker || 'N/A'} 
                          size="small" 
                          color="primary" 
                        />
                        <Chip 
                          label={item.metric?.replace('_', ' ') || 'Unknown'} 
                          size="small" 
                          variant="outlined" 
                        />
                        <Chip 
                          label={item.confidence || 'medium'}
                          size="small"
                          color={item.confidence === 'high' ? 'success' : item.confidence === 'low' ? 'error' : 'warning'}
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body1" sx={{ my: 1 }}>
                          <strong>Value:</strong> {item.value} 
                          {item.timeframe && ` (${item.timeframe})`}
                        </Typography>
                        {item.change_from_previous && (
                          <Typography variant="body2" color="textSecondary">
                            Change: {item.change_from_previous}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Companies Tab */}
        {tabValue === 2 && (
          <Box p={3}>
            <Typography variant="h6" gutterBottom>Companies with Q1 2025 Data</Typography>
            <Grid container spacing={2}>
              {companies.map((company) => (
                <Grid item xs={12} sm={6} md={4} key={company.id}>
                  <Card>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                        <Typography variant="h6">{company.ticker}</Typography>
                        {company.q1_2025_sentiment && getSentimentIcon(company.q1_2025_sentiment.overall_sentiment)}
                      </Box>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        {company.name}
                      </Typography>
                      {company.q1_2025_sentiment && (
                        <Box mt={2}>
                          <Typography variant="body2">
                            Sentiment: {company.q1_2025_sentiment.overall_sentiment?.toFixed(3)}
                          </Typography>
                          <Typography variant="body2">
                            Confidence: {company.q1_2025_sentiment.management_confidence?.toFixed(3)}
                          </Typography>
                          <Box display="flex" gap={1} mt={1}>
                            {company.q1_2025_sentiment.has_quotes && (
                              <Chip label="Has Quotes" size="small" color="info" />
                            )}
                            {company.q1_2025_sentiment.has_guidance && (
                              <Chip label="Has Guidance" size="small" color="success" />
                            )}
                          </Box>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}
      </Paper>

      {/* PDF Download Dialog */}
      <Dialog open={pdfDownloadDialog} onClose={() => setPdfDownloadDialog(false)}>
        <DialogTitle>Download Company Report</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Select Company</InputLabel>
            <Select
              value={selectedCompany}
              label="Select Company"
              onChange={(e) => setSelectedCompany(e.target.value)}
            >
              {companies.map((company) => (
                <MenuItem key={company.ticker} value={company.ticker}>
                  {company.ticker} - {company.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPdfDownloadDialog(false)}>Cancel</Button>
          <Button 
            onClick={downloadCompanyReport} 
            disabled={!selectedCompany || downloadingPdf}
            variant="contained"
          >
            {downloadingPdf ? 'Downloading...' : 'Download PDF'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Q1Analytics; 