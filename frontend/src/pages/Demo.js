import React from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Analytics as AnalyticsIcon,
  AutorenewOutlined as AutomationIcon,
  NotificationsActive as AlertIcon,
  Assessment as ReportIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  CloudDone as CloudIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

function Demo() {
  const navigate = useNavigate();

  const features = [
    {
      icon: <AutomationIcon />,
      title: 'Automated Data Collection',
      description: 'Automatically retrieves and processes new earnings call transcripts every month',
    },
    {
      icon: <AnalyticsIcon />,
      title: 'Advanced Sentiment Analysis',
      description: 'AI-powered analysis specifically tuned for biotech/medtech terminology',
    },
    {
      icon: <TrendingUpIcon />,
      title: 'Trend Tracking',
      description: 'Compares current sentiment against historical data to identify trends',
    },
    {
      icon: <AlertIcon />,
      title: 'Smart Alerts',
      description: 'Receive notifications when significant sentiment changes occur',
    },
    {
      icon: <ReportIcon />,
      title: 'Monthly Reports',
      description: 'Comprehensive PDF reports delivered automatically each month',
    },
    {
      icon: <SecurityIcon />,
      title: 'Enterprise Security',
      description: 'Bank-level encryption and secure data handling',
    },
  ];

  const benefits = [
    'Save hours of manual transcript analysis',
    'Never miss important sentiment shifts',
    'Track unlimited companies',
    'Historical trend analysis',
    'Export data in multiple formats',
    'Email notifications',
    'API access for integration',
    'Regular feature updates',
  ];

  const sampleData = {
    improving: 23,
    stable: 45,
    declining: 12,
    totalCompanies: 80,
  };

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
          color: 'white',
          py: 10,
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography variant="h2" component="h1" gutterBottom fontWeight="bold">
                OpalSight Analytics
              </Typography>
              <Typography variant="h5" gutterBottom sx={{ opacity: 0.9 }}>
                Automated Biotech/Medtech Earnings Intelligence
              </Typography>
              <Typography variant="body1" paragraph sx={{ opacity: 0.8, mb: 4 }}>
                Transform earnings call transcripts into actionable insights with our AI-powered 
                platform. Track sentiment changes, identify trends, and receive automated alerts 
                for the companies that matter to you.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  size="large"
                  sx={{
                    backgroundColor: 'white',
                    color: '#1976d2',
                    '&:hover': {
                      backgroundColor: '#f5f5f5',
                    },
                  }}
                  onClick={() => navigate('/dashboard')}
                >
                  Try Demo Dashboard
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  sx={{
                    borderColor: 'white',
                    color: 'white',
                    '&:hover': {
                      borderColor: 'white',
                      backgroundColor: 'rgba(255,255,255,0.1)',
                    },
                  }}
                >
                  Watch Video
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper elevation={10} sx={{ p: 4, borderRadius: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Current Market Sentiment
                </Typography>
                <Box sx={{ mb: 3 }}>
                  <Box display="flex" justifyContent="space-between" mb={2}>
                    <Box textAlign="center">
                      <Typography variant="h3" color="success.main">
                        {sampleData.improving}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Improving
                      </Typography>
                    </Box>
                    <Box textAlign="center">
                      <Typography variant="h3" color="warning.main">
                        {sampleData.stable}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Stable
                      </Typography>
                    </Box>
                    <Box textAlign="center">
                      <Typography variant="h3" color="error.main">
                        {sampleData.declining}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Declining
                      </Typography>
                    </Box>
                  </Box>
                  <Divider />
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                    Tracking {sampleData.totalCompanies} biotech/medtech companies
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography variant="h3" align="center" gutterBottom fontWeight="bold">
          Powerful Features
        </Typography>
        <Typography variant="h6" align="center" color="textSecondary" paragraph>
          Everything you need to stay ahead of market sentiment
        </Typography>
        <Grid container spacing={4} sx={{ mt: 4 }}>
          {features.map((feature, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  transition: 'transform 0.2s',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: 6,
                  },
                }}
              >
                <CardContent sx={{ textAlign: 'center', p: 4 }}>
                  <Box
                    sx={{
                      display: 'inline-flex',
                      p: 2,
                      borderRadius: '50%',
                      backgroundColor: '#e3f2fd',
                      color: '#1976d2',
                      mb: 2,
                    }}
                  >
                    {React.cloneElement(feature.icon, { fontSize: 'large' })}
                  </Box>
                  <Typography variant="h6" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* How It Works */}
      <Box sx={{ backgroundColor: 'white', py: 8 }}>
        <Container maxWidth="lg">
          <Typography variant="h3" align="center" gutterBottom fontWeight="bold">
            How It Works
          </Typography>
          <Grid container spacing={4} sx={{ mt: 4 }}>
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    backgroundColor: '#1976d2',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto',
                    mb: 2,
                    fontSize: 24,
                    fontWeight: 'bold',
                  }}
                >
                  1
                </Box>
                <Typography variant="h6" gutterBottom>
                  Data Collection
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Automatically retrieve earnings call transcripts on the last Friday of each month
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    backgroundColor: '#1976d2',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto',
                    mb: 2,
                    fontSize: 24,
                    fontWeight: 'bold',
                  }}
                >
                  2
                </Box>
                <Typography variant="h6" gutterBottom>
                  AI Analysis
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Process transcripts with advanced NLP tuned for biotech/medtech terminology
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    backgroundColor: '#1976d2',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto',
                    mb: 2,
                    fontSize: 24,
                    fontWeight: 'bold',
                  }}
                >
                  3
                </Box>
                <Typography variant="h6" gutterBottom>
                  Trend Detection
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Compare against historical data to identify significant sentiment changes
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box textAlign="center">
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    backgroundColor: '#1976d2',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto',
                    mb: 2,
                    fontSize: 24,
                    fontWeight: 'bold',
                  }}
                >
                  4
                </Box>
                <Typography variant="h6" gutterBottom>
                  Instant Insights
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Receive reports, alerts, and access real-time dashboards
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Benefits Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h3" gutterBottom fontWeight="bold">
              Why Choose OpalSight?
            </Typography>
            <List>
              {benefits.map((benefit, index) => (
                <ListItem key={index} sx={{ px: 0 }}>
                  <ListItemIcon>
                    <CheckIcon color="success" />
                  </ListItemIcon>
                  <ListItemText primary={benefit} />
                </ListItem>
              ))}
            </List>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper elevation={3} sx={{ p: 4 }}>
              <Typography variant="h5" gutterBottom>
                Ready to Get Started?
              </Typography>
              <Typography variant="body1" paragraph color="textSecondary">
                Join leading biotech and medtech analysts who trust OpalSight for their 
                earnings intelligence needs.
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  onClick={() => navigate('/dashboard')}
                >
                  Explore Demo Dashboard
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  fullWidth
                  onClick={() => navigate('/reports')}
                >
                  View Sample Reports
                </Button>
              </Box>
              <Box sx={{ mt: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip icon={<SecurityIcon />} label="SOC 2 Compliant" size="small" />
                <Chip icon={<CloudIcon />} label="Cloud Native" size="small" />
                <Chip icon={<SpeedIcon />} label="Real-time Updates" size="small" />
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Container>

      {/* Footer */}
      <Box sx={{ backgroundColor: '#1976d2', color: 'white', py: 6, mt: 8 }}>
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom>
                OpalSight Analytics
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                Transforming earnings calls into actionable intelligence for the 
                biotech and medtech industry.
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom>
                Features
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                • Automated Transcript Collection<br />
                • AI-Powered Sentiment Analysis<br />
                • Historical Trend Tracking<br />
                • Smart Alert System<br />
                • Monthly PDF Reports
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="h6" gutterBottom>
                Contact
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                Email: demo@opalsight.com<br />
                Phone: 1-800-OPALSIGHT<br />
                <br />
                © 2024 OpalSight Analytics. All rights reserved.
              </Typography>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </Box>
  );
}

export default Demo; 