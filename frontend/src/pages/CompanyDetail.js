import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Tabs,
  Tab,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  BookmarkBorder as BookmarkIcon,
  Bookmark as BookmarkedIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import apiService from '../services/api';
import ExportButton from '../components/ExportButton';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function CompanyDetail() {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tabValue, setTabValue] = React.useState(0);

  const { data: companyData, isLoading, error } = useQuery(
    ['company', ticker],
    () => apiService.getCompany(ticker)
  );

  const { data: watchlistData } = useQuery(
    'watchlist',
    () => apiService.getWatchlist()
  );

  const addToWatchlistMutation = useMutation(
    () => apiService.addToWatchlist(ticker),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('watchlist');
      },
    }
  );

  const removeFromWatchlistMutation = useMutation(
    () => apiService.removeFromWatchlist(ticker),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('watchlist');
      },
    }
  );

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Error loading company data. Please try again later.
      </Alert>
    );
  }

  const company = companyData?.data?.company;
  const transcripts = companyData?.data?.transcripts || [];
  const trend = companyData?.data?.trend;
  const alerts = companyData?.data?.alerts || [];
  const timeline = companyData?.data?.sentiment_timeline || [];

  const isWatchlisted = watchlistData?.data?.watchlist?.some(
    (item) => item.company.ticker === ticker
  );

  const handleWatchlistToggle = () => {
    if (isWatchlisted) {
      removeFromWatchlistMutation.mutate();
    } else {
      addToWatchlistMutation.mutate();
    }
  };

  const formatChange = (value) => {
    if (!value) return '0.00';
    const formatted = Math.abs(value).toFixed(2);
    return value > 0 ? `+${formatted}` : `-${formatted}`;
  };

  const getSentimentColor = (value) => {
    if (value > 0.1) return '#4caf50';
    if (value < -0.1) return '#f44336';
    return '#ff9800';
  };

  return (
    <Box className="fade-in">
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/companies')}>
            <BackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4">
              {company?.ticker} - {company?.name}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {company?.industry} • Market Cap: ${(company?.market_cap_billions || 0).toFixed(1)}B
            </Typography>
          </Box>
        </Box>
        <Box display="flex" gap={2}>
          <ExportButton 
            endpoint={`/company/${ticker}/timeline`}
            filename={`${ticker}_sentiment_timeline`}
            formats={['csv', 'json', 'excel']}
          />
          <Button
            variant={isWatchlisted ? 'contained' : 'outlined'}
            startIcon={isWatchlisted ? <BookmarkedIcon /> : <BookmarkIcon />}
            onClick={handleWatchlistToggle}
          >
            {isWatchlisted ? 'In Watchlist' : 'Add to Watchlist'}
          </Button>
        </Box>
      </Box>

      {/* Current Status */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Current Trend
              </Typography>
              {trend ? (
                <Box display="flex" alignItems="center" gap={1}>
                  {trend.trend_category === 'improving' ? (
                    <TrendingUpIcon sx={{ color: '#4caf50', fontSize: 32 }} />
                  ) : trend.trend_category === 'declining' ? (
                    <TrendingDownIcon sx={{ color: '#f44336', fontSize: 32 }} />
                  ) : (
                    <div />
                  )}
                  <Typography variant="h5" sx={{ textTransform: 'capitalize' }}>
                    {trend.trend_category}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="h5">No Data</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Sentiment Change
              </Typography>
              <Typography
                variant="h5"
                sx={{
                  color: trend?.sentiment_change > 0 ? '#4caf50' : '#f44336',
                }}
              >
                {formatChange(trend?.sentiment_change)}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                vs. historical average
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Confidence Change
              </Typography>
              <Typography
                variant="h5"
                sx={{
                  color: trend?.confidence_change > 0 ? '#4caf50' : '#f44336',
                }}
              >
                {formatChange(trend?.confidence_change)}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Management confidence
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ mt: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Sentiment Timeline" />
          <Tab label="Recent Transcripts" />
          <Tab label="Key Changes" />
          <Tab label="Alerts" />
        </Tabs>

        {/* Sentiment Timeline */}
        <TabPanel value={tabValue} index={0}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Sentiment Evolution
              </Typography>
              {timeline.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={timeline}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[-1, 1]} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="sentiment"
                      stroke="#1976d2"
                      name="Overall Sentiment"
                      strokeWidth={2}
                    />
                    <Line
                      type="monotone"
                      dataKey="confidence"
                      stroke="#dc004e"
                      name="Management Confidence"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <Typography color="textSecondary">No timeline data available</Typography>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        {/* Recent Transcripts */}
        <TabPanel value={tabValue} index={1}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Earnings Calls
              </Typography>
              <List>
                {transcripts.map((transcript, index) => (
                  <React.Fragment key={transcript.id}>
                    <ListItem>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={2}>
                            <Typography variant="subtitle1">
                              {transcript.fiscal_period}
                            </Typography>
                            {transcript.sentiment && (
                              <>
                                <Chip
                                  label={`Sentiment: ${transcript.sentiment.overall_sentiment?.toFixed(2)}`}
                                  size="small"
                                  sx={{
                                    backgroundColor: getSentimentColor(transcript.sentiment.overall_sentiment),
                                    color: 'white',
                                  }}
                                />
                                <Chip
                                  label={`Confidence: ${transcript.sentiment.management_confidence?.toFixed(2)}`}
                                  size="small"
                                  variant="outlined"
                                />
                              </>
                            )}
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="textSecondary">
                              Call Date: {new Date(transcript.call_date).toLocaleDateString()}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Word Count: {transcript.word_count?.toLocaleString()}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < transcripts.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Key Changes */}
        <TabPanel value={tabValue} index={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Notable Changes
              </Typography>
              {trend?.key_changes?.length > 0 ? (
                <List>
                  {trend.key_changes.map((change, index) => (
                    <ListItem key={index}>
                      <ListItemText
                        primary={change.description}
                        secondary={
                          <Box>
                            <Chip
                              label={change.magnitude}
                              size="small"
                              color={
                                change.magnitude === 'high' ? 'error' :
                                change.magnitude === 'medium' ? 'warning' : 'default'
                              }
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary">No significant changes detected</Typography>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        {/* Alerts */}
        <TabPanel value={tabValue} index={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Alerts
              </Typography>
              {alerts.length > 0 ? (
                <List>
                  {alerts.map((alert) => (
                    <ListItem key={alert.id}>
                      <ListItemText
                        primary={alert.message}
                        secondary={
                          <Box display="flex" gap={1} mt={0.5}>
                            <Chip
                              label={alert.severity}
                              size="small"
                              color={
                                alert.severity === 'high' ? 'error' :
                                alert.severity === 'medium' ? 'warning' : 'default'
                              }
                            />
                            <Typography variant="caption" color="textSecondary">
                              {alert.age_days} days ago
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary">No active alerts</Typography>
              )}
            </CardContent>
          </Card>
        </TabPanel>
      </Box>
    </Box>
  );
}

export default CompanyDetail; 