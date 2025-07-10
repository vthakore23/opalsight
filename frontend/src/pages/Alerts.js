import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  ToggleButton,
  ToggleButtonGroup,
  TextField,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
  Search as SearchIcon,
  MoreVert as MoreIcon,
} from '@mui/icons-material';
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

function Alerts() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [severityFilter, setSeverityFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedAlert, setSelectedAlert] = useState(null);

  const { data: alertsData, isLoading, error } = useQuery(
    ['alerts', severityFilter],
    () => apiService.getAlerts(),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const resolveAlertMutation = useMutation(
    (alertId) => apiService.resolveAlert(alertId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('alerts');
        handleCloseMenu();
      },
    }
  );

  const handleSeverityChange = (event, newSeverity) => {
    if (newSeverity !== null) {
      setSeverityFilter(newSeverity);
    }
  };

  const handleOpenMenu = (event, alert) => {
    setAnchorEl(event.currentTarget);
    setSelectedAlert(alert);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
    setSelectedAlert(null);
  };

  const handleResolveAlert = () => {
    if (selectedAlert) {
      resolveAlertMutation.mutate(selectedAlert.id);
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'high':
        return <ErrorIcon sx={{ color: '#f44336' }} />;
      case 'medium':
        return <WarningIcon sx={{ color: '#ff9800' }} />;
      case 'low':
        return <InfoIcon sx={{ color: '#2196f3' }} />;
      default:
        return <InfoIcon sx={{ color: '#2196f3' }} />;
    }
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
        Error loading alerts. Please try again later.
      </Alert>
    );
  }

  const alerts = alertsData?.data?.alerts || [];

  // Filter alerts
  const filteredAlerts = alerts.filter((alert) => {
    const matchesSeverity = severityFilter === 'all' || alert.severity === severityFilter;
    const matchesSearch = searchQuery === '' || 
      alert.company.ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alert.company.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alert.message.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesSeverity && matchesSearch;
  });

  // Group alerts by date
  const groupedAlerts = filteredAlerts.reduce((groups, alert) => {
    const date = format(parseISO(alert.created_at), 'yyyy-MM-dd');
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(alert);
    return groups;
  }, {});

  const unresolvedCount = alerts.filter(a => !a.resolved).length;
  const highSeverityCount = alerts.filter(a => a.severity === 'high' && !a.resolved).length;

  return (
    <Box className="fade-in">
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          Alerts
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <Chip
            icon={<WarningIcon />}
            label={`${unresolvedCount} Active Alerts`}
            color={unresolvedCount > 0 ? 'warning' : 'default'}
          />
          {highSeverityCount > 0 && (
            <Chip
              icon={<ErrorIcon />}
              label={`${highSeverityCount} High Severity`}
              color="error"
            />
          )}
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
            <ToggleButtonGroup
              value={severityFilter}
              exclusive
              onChange={handleSeverityChange}
              size="small"
            >
              <ToggleButton value="all">
                All
              </ToggleButton>
              <ToggleButton value="high">
                <ErrorIcon sx={{ mr: 0.5, fontSize: 20 }} />
                High
              </ToggleButton>
              <ToggleButton value="medium">
                <WarningIcon sx={{ mr: 0.5, fontSize: 20 }} />
                Medium
              </ToggleButton>
              <ToggleButton value="low">
                <InfoIcon sx={{ mr: 0.5, fontSize: 20 }} />
                Low
              </ToggleButton>
            </ToggleButtonGroup>

            <TextField
              size="small"
              placeholder="Search alerts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              sx={{ flexGrow: 1, maxWidth: 400 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Alerts List */}
      {filteredAlerts.length === 0 ? (
        <Alert severity="info">
          {severityFilter === 'all' && searchQuery === '' 
            ? 'No active alerts. The system will notify you when significant changes occur.'
            : 'No alerts match your filters.'}
        </Alert>
      ) : (
        Object.entries(groupedAlerts).map(([date, dateAlerts]) => (
          <Box key={date} mb={3}>
            <Typography variant="subtitle2" color="textSecondary" gutterBottom>
              {format(parseISO(date), 'EEEE, MMMM d, yyyy')}
            </Typography>
            
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell width="40">Severity</TableCell>
                    <TableCell>Company</TableCell>
                    <TableCell>Alert</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Age</TableCell>
                    <TableCell width="40">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dateAlerts.map((alert) => (
                    <TableRow
                      key={alert.id}
                      hover
                      sx={{
                        cursor: 'pointer',
                        opacity: alert.resolved ? 0.6 : 1,
                      }}
                      onClick={() => navigate(`/company/${alert.company.ticker}`)}
                    >
                      <TableCell>
                        {getSeverityIcon(alert.severity)}
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="subtitle2">
                            {alert.company.ticker}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {alert.company.name}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {alert.message}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={alert.alert_type}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="textSecondary">
                          {formatDistanceToNow(parseISO(alert.created_at), { addSuffix: true })}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenMenu(e, alert);
                          }}
                        >
                          <MoreIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        ))
      )}

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
      >
        <MenuItem onClick={() => {
          navigate(`/company/${selectedAlert?.company.ticker}`);
          handleCloseMenu();
        }}>
          View Company Details
        </MenuItem>
        {selectedAlert && !selectedAlert.resolved && (
          <MenuItem onClick={handleResolveAlert}>
            <CheckIcon sx={{ mr: 1, fontSize: 20 }} />
            Mark as Resolved
          </MenuItem>
        )}
      </Menu>
    </Box>
  );
}

export default Alerts; 