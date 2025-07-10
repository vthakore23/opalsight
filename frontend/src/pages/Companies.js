import React, { useState, useCallback } from 'react';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  InputAdornment,
  IconButton,
  CircularProgress,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Grid,
  Button,
} from '@mui/material';
import {
  Search as SearchIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as StableIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { debounce } from 'lodash';
import apiService from '../services/api';

const TREND_COLORS = {
  improving: '#4caf50',
  stable: '#ff9800',
  declining: '#f44336',
};

function Companies() {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);
  const [searchQuery, setSearchQuery] = useState('');
  const [trendFilter, setTrendFilter] = useState('');
  const [sectorFilter, setSectorFilter] = useState('');

  const { data, isLoading, error } = useQuery(
    ['companies', page, rowsPerPage, searchQuery, trendFilter, sectorFilter],
    () => apiService.getCompanies({
      page: page + 1,
      per_page: rowsPerPage,
      search: searchQuery,
      trend: trendFilter,
      sector: sectorFilter,
    }),
    {
      keepPreviousData: true,
    }
  );

  const debouncedSearch = useCallback(
    debounce((value) => {
      setSearchQuery(value);
      setPage(0);
    }, 500),
    [setSearchQuery, setPage]
  );

  const handleSearchChange = (event) => {
    debouncedSearch(event.target.value);
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleTrendFilterChange = (event) => {
    setTrendFilter(event.target.value);
    setPage(0);
  };

  const handleSectorFilterChange = (event) => {
    setSectorFilter(event.target.value);
    setPage(0);
  };

  const getTrendIcon = (category) => {
    switch (category) {
      case 'improving':
        return <TrendingUpIcon sx={{ color: TREND_COLORS.improving, fontSize: 20 }} />;
      case 'declining':
        return <TrendingDownIcon sx={{ color: TREND_COLORS.declining, fontSize: 20 }} />;
      default:
        return <StableIcon sx={{ color: TREND_COLORS.stable, fontSize: 20 }} />;
    }
  };

  const formatMarketCap = (value) => {
    if (!value) return 'N/A';
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
    return `$${value.toLocaleString()}`;
  };

  const formatChange = (value) => {
    if (!value) return '0.00';
    const formatted = Math.abs(value).toFixed(2);
    return value > 0 ? `+${formatted}` : `-${formatted}`;
  };

  if (isLoading && !data) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Error loading companies. Please try again later.
      </Alert>
    );
  }

  const companies = data?.data?.companies || [];
  const total = data?.data?.total || 0;

  return (
    <Box className="fade-in">
      <Typography variant="h4" gutterBottom>
        Companies
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Search by ticker or name..."
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Trend Filter</InputLabel>
                <Select
                  value={trendFilter}
                  label="Trend Filter"
                  onChange={handleTrendFilterChange}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="improving">Improving</MenuItem>
                  <MenuItem value="stable">Stable</MenuItem>
                  <MenuItem value="declining">Declining</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Sector Filter</InputLabel>
                <Select
                  value={sectorFilter}
                  label="Sector Filter"
                  onChange={handleSectorFilterChange}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="Healthcare">Healthcare</MenuItem>
                  <MenuItem value="Biotechnology">Biotechnology</MenuItem>
                  <MenuItem value="Pharmaceuticals">Pharmaceuticals</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => {
                  setSearchQuery('');
                  setTrendFilter('');
                  setSectorFilter('');
                  setPage(0);
                }}
              >
                Clear Filters
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Companies Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Ticker</TableCell>
              <TableCell>Company Name</TableCell>
              <TableCell>Industry</TableCell>
              <TableCell align="right">Market Cap</TableCell>
              <TableCell align="center">Latest Trend</TableCell>
              <TableCell align="right">Sentiment Change</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {companies.map((company) => (
              <TableRow
                key={company.id}
                hover
                sx={{ cursor: 'pointer' }}
                onClick={() => navigate(`/company/${company.ticker}`)}
              >
                <TableCell>
                  <Typography variant="subtitle2" fontWeight="bold">
                    {company.ticker}
                  </Typography>
                </TableCell>
                <TableCell>{company.name}</TableCell>
                <TableCell>
                  <Typography variant="body2" color="textSecondary">
                    {company.industry}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  {formatMarketCap(company.market_cap)}
                </TableCell>
                <TableCell align="center">
                  {company.latest_trend ? (
                    <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                      {getTrendIcon(company.latest_trend.category)}
                      <Chip
                        label={company.latest_trend.category}
                        size="small"
                        sx={{
                          backgroundColor: TREND_COLORS[company.latest_trend.category],
                          color: 'white',
                        }}
                      />
                    </Box>
                  ) : (
                    <Typography variant="body2" color="textSecondary">
                      No data
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="right">
                  {company.latest_trend ? (
                    <Typography
                      variant="body2"
                      sx={{
                        color: company.latest_trend.sentiment_change > 0
                          ? TREND_COLORS.improving
                          : company.latest_trend.sentiment_change < 0
                          ? TREND_COLORS.declining
                          : 'inherit',
                      }}
                    >
                      {formatChange(company.latest_trend.sentiment_change)}
                    </Typography>
                  ) : (
                    '-'
                  )}
                </TableCell>
                <TableCell align="center">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/company/${company.ticker}`);
                    }}
                  >
                    <ViewIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[10, 20, 50]}
          component="div"
          count={total}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>
    </Box>
  );
}

export default Companies; 