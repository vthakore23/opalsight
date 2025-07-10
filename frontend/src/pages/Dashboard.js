import React from 'react';
import { useQuery } from 'react-query';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as StableIcon,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import apiService from '../services/api';
import ExportButton from '../components/ExportButton';

const COLORS = {
  improving: '#4caf50',
  stable: '#ff9800',
  declining: '#f44336',
};

function Dashboard() {
  const { data: dashboardData, isLoading, error } = useQuery(
    'dashboard',
    () => apiService.getDashboard(),
    {
      refetchInterval: 60000, // Refresh every minute
    }
  );

  const { data: marketData } = useQuery(
    'marketOverview',
    () => apiService.getMarketOverview()
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
        Error loading dashboard data. Please try again later.
      </Alert>
    );
  }

  const data = dashboardData?.data;
  const market = marketData?.data;

  // Prepare pie chart data
  const pieData = data?.summary ? [
    { name: 'Improving', value: data.summary.improving || 0 },
    { name: 'Stable', value: data.summary.stable || 0 },
    { name: 'Declining', value: data.summary.declining || 0 },
  ].filter(item => item.value > 0) : [];

  const getTrendIcon = (category) => {
    switch (category) {
      case 'improving':
        return <TrendingUpIcon sx={{ color: COLORS.improving }} />;
      case 'declining':
        return <TrendingDownIcon sx={{ color: COLORS.declining }} />;
      default:
        return <StableIcon sx={{ color: COLORS.stable }} />;
    }
  };

  const formatChange = (value) => {
    if (!value) return '0.00';
    const formatted = Math.abs(value).toFixed(2);
    return value > 0 ? `+${formatted}` : `-${formatted}`;
  };

  return (
    <Box className="fade-in">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Market Overview
        </Typography>
        <ExportButton 
          endpoint="/market-summary"
          filename="opalsight_market_summary"
          formats={['excel', 'json']}
        />
      </Box>
      
      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Improving
                  </Typography>
                  <Typography variant="h3" sx={{ color: COLORS.improving }}>
                    {data?.summary?.improving || 0}
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 48, color: COLORS.improving, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Stable
                  </Typography>
                  <Typography variant="h3" sx={{ color: COLORS.stable }}>
                    {data?.summary?.stable || 0}
                  </Typography>
                </Box>
                <StableIcon sx={{ fontSize: 48, color: COLORS.stable, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Declining
                  </Typography>
                  <Typography variant="h3" sx={{ color: COLORS.declining }}>
                    {data?.summary?.declining || 0}
                  </Typography>
                </Box>
                <TrendingDownIcon sx={{ fontSize: 48, color: COLORS.declining, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Pie Chart */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Trend Distribution
              </Typography>
              {pieData.length > 0 ? (
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
                        <Cell key={`cell-${index}`} fill={COLORS[entry.name.toLowerCase()]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Box display="flex" justifyContent="center" alignItems="center" height={300}>
                  <Typography color="textSecondary">No data available</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Notable Companies */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Notable Changes
              </Typography>
              <List>
                {data?.notable_companies?.slice(0, 5).map((company, index) => (
                  <ListItem key={index} divider={index < 4}>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          {getTrendIcon(company.trend_category)}
                          <Typography variant="subtitle1">
                            {company.ticker} - {company.name}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <Box display="flex" gap={2} mt={0.5}>
                          <Typography variant="caption" color="textSecondary">
                            Sentiment: {formatChange(company.sentiment_change)}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            Confidence: {formatChange(company.confidence_change)}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Chip
                        label={company.trend_category}
                        size="small"
                        sx={{
                          backgroundColor: COLORS[company.trend_category],
                          color: 'white',
                        }}
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Alerts */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Alerts
              </Typography>
              {data?.recent_alerts?.length > 0 ? (
                <List>
                  {data.recent_alerts.map((alert) => (
                    <ListItem key={alert.id} divider>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Chip
                              label={alert.severity}
                              size="small"
                              color={
                                alert.severity === 'high' ? 'error' :
                                alert.severity === 'medium' ? 'warning' : 'default'
                              }
                            />
                            <Typography variant="subtitle1">
                              {alert.company?.ticker} - {alert.message}
                            </Typography>
                          </Box>
                        }
                        secondary={`${alert.age_days} days ago`}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary">No recent alerts</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Top Movers (if market data available) */}
        {market?.top_movers?.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Top Movers This Week
                </Typography>
                <Grid container spacing={2}>
                  {market.top_movers.map((mover, index) => (
                    <Grid item xs={12} sm={6} md={4} key={index}>
                      <Paper sx={{ p: 2 }}>
                        <Box display="flex" alignItems="center" justifyContent="space-between">
                          <Box>
                            <Typography variant="subtitle2" color="textSecondary">
                              {mover.ticker}
                            </Typography>
                            <Typography variant="body2" noWrap>
                              {mover.name}
                            </Typography>
                          </Box>
                          {getTrendIcon(mover.trend)}
                        </Box>
                        <Box mt={1}>
                          <Typography variant="caption" color="textSecondary">
                            Sentiment: {formatChange(mover.sentiment_change)} | 
                            Confidence: {formatChange(mover.confidence_change)}
                          </Typography>
                        </Box>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}

export default Dashboard; 