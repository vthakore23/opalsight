import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,

  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Add as AddIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as StableIcon,
  Notifications as NotificationsIcon,
  NotificationsOff as NotificationsOffIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

function Watchlist() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [alertThreshold, setAlertThreshold] = useState(0.2);
  const [searchLoading, setSearchLoading] = useState(false);

  const { data: watchlistData, isLoading, error } = useQuery(
    'watchlist',
    () => apiService.getWatchlist()
  );



  const addToWatchlistMutation = useMutation(
    ({ ticker, threshold }) => apiService.addToWatchlist(ticker, threshold),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('watchlist');
        handleCloseAddDialog();
      },
    }
  );

  const removeFromWatchlistMutation = useMutation(
    (ticker) => apiService.removeFromWatchlist(ticker),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('watchlist');
      },
    }
  );

  const handleSearchCompanies = async (query) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearchLoading(true);
    try {
      const response = await apiService.searchCompanies(query);
      setSearchResults(response.data.results || []);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleAddToWatchlist = () => {
    if (selectedCompany) {
      addToWatchlistMutation.mutate({
        ticker: selectedCompany.ticker,
        threshold: alertThreshold,
      });
    }
  };

  const handleCloseAddDialog = () => {
    setOpenAddDialog(false);
    setSearchQuery('');
    setSearchResults([]);
    setSelectedCompany(null);
    setAlertThreshold(0.2);
  };

  const getTrendIcon = (trend) => {
    switch (trend?.trend_category) {
      case 'improving':
        return <TrendingUpIcon sx={{ color: '#4caf50' }} />;
      case 'declining':
        return <TrendingDownIcon sx={{ color: '#f44336' }} />;
      default:
        return <StableIcon sx={{ color: '#ff9800' }} />;
    }
  };

  const formatChange = (value) => {
    if (!value) return '0.00';
    const formatted = Math.abs(value).toFixed(2);
    return value > 0 ? `+${formatted}` : `-${formatted}`;
  };

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
        Error loading watchlist. Please try again later.
      </Alert>
    );
  }

  const watchlist = watchlistData?.data?.watchlist || [];

  return (
    <Box className="fade-in">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4">
            Watchlist
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Track your companies of interest and receive alerts
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenAddDialog(true)}
        >
          Add Company
        </Button>
      </Box>

      {watchlist.length === 0 ? (
        <Alert severity="info">
          Your watchlist is empty. Add companies to track their sentiment changes and receive alerts.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {watchlist.map((item) => (
            <Grid item xs={12} md={6} lg={4} key={item.id}>
              <Card
                sx={{
                  height: '100%',
                  cursor: 'pointer',
                  transition: 'transform 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 3,
                  },
                }}
                onClick={() => navigate(`/company/${item.company.ticker}`)}
              >
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                    <Box>
                      <Typography variant="h6">
                        {item.company.ticker}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {item.company.name}
                      </Typography>
                    </Box>
                    {getTrendIcon(item.company.latest_trend)}
                  </Box>

                  <Box mb={2}>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Latest Analysis
                    </Typography>
                    {item.company.latest_trend ? (
                      <Box>
                        <Box display="flex" justifyContent="space-between" mb={1}>
                          <Typography variant="body2">Sentiment Change:</Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              color: item.company.latest_trend.sentiment_change > 0 ? '#4caf50' : '#f44336',
                              fontWeight: 'bold',
                            }}
                          >
                            {formatChange(item.company.latest_trend.sentiment_change)}
                          </Typography>
                        </Box>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2">Confidence Change:</Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              color: item.company.latest_trend.confidence_change > 0 ? '#4caf50' : '#f44336',
                              fontWeight: 'bold',
                            }}
                          >
                            {formatChange(item.company.latest_trend.confidence_change)}
                          </Typography>
                        </Box>
                      </Box>
                    ) : (
                      <Typography variant="body2">No analysis available</Typography>
                    )}
                  </Box>

                  <Box display="flex" alignItems="center" gap={1}>
                    <Chip
                      icon={item.alert_threshold > 0 ? <NotificationsIcon /> : <NotificationsOffIcon />}
                      label={`Alert: ${item.alert_threshold > 0 ? `±${item.alert_threshold}` : 'Off'}`}
                      size="small"
                      color={item.alert_threshold > 0 ? 'primary' : 'default'}
                    />
                    <Chip
                      label={item.company.sector}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                </CardContent>

                <CardActions>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFromWatchlistMutation.mutate(item.company.ticker);
                    }}
                  >
                    <DeleteIcon />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Add Company Dialog */}
      <Dialog
        open={openAddDialog}
        onClose={handleCloseAddDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Company to Watchlist</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Search for a company"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                handleSearchCompanies(e.target.value);
              }}
              placeholder="Enter ticker or company name"
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
              sx={{ mb: 2 }}
            />

            {searchLoading && (
              <Box display="flex" justifyContent="center" p={2}>
                <CircularProgress size={24} />
              </Box>
            )}

            {searchResults.length > 0 && (
              <TableContainer component={Paper} sx={{ mb: 2, maxHeight: 200 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Ticker</TableCell>
                      <TableCell>Company</TableCell>
                      <TableCell>Sector</TableCell>
                      <TableCell>Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {searchResults.map((company) => (
                      <TableRow
                        key={company.ticker}
                        hover
                        selected={selectedCompany?.ticker === company.ticker}
                      >
                        <TableCell>{company.ticker}</TableCell>
                        <TableCell>{company.name}</TableCell>
                        <TableCell>{company.sector}</TableCell>
                        <TableCell>
                          <Button
                            size="small"
                            variant={selectedCompany?.ticker === company.ticker ? 'contained' : 'outlined'}
                            onClick={() => setSelectedCompany(company)}
                          >
                            Select
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}

            {selectedCompany && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Selected: {selectedCompany.ticker} - {selectedCompany.name}
                </Typography>

                <Box sx={{ mt: 2 }}>
                  <Typography gutterBottom>
                    Alert Threshold: ±{alertThreshold.toFixed(2)}
                  </Typography>
                  <Slider
                    value={alertThreshold}
                    onChange={(e, value) => setAlertThreshold(value)}
                    min={0}
                    max={0.5}
                    step={0.05}
                    marks={[
                      { value: 0, label: 'Off' },
                      { value: 0.1, label: '0.1' },
                      { value: 0.2, label: '0.2' },
                      { value: 0.3, label: '0.3' },
                      { value: 0.4, label: '0.4' },
                      { value: 0.5, label: '0.5' },
                    ]}
                    valueLabelDisplay="auto"
                  />
                  <Typography variant="caption" color="textSecondary">
                    You'll receive alerts when sentiment changes by more than this threshold
                  </Typography>
                </Box>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAddDialog}>Cancel</Button>
          <Button
            onClick={handleAddToWatchlist}
            variant="contained"
            disabled={!selectedCompany || addToWatchlistMutation.isLoading}
          >
            Add to Watchlist
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Watchlist; 