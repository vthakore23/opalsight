import React, { useState } from 'react';
import { useQuery } from 'react-query';
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
  Pagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
} from '@mui/material';
import {
  PictureAsPdf as PdfIcon,
  Visibility as ViewIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as StableIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';
import apiService from '../services/api';

function Reports() {
  const [page, setPage] = useState(1);
  const [selectedReport, setSelectedReport] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);

  const { data: reportsData, isLoading, error } = useQuery(
    ['reports', page],
    () => apiService.getReports({ page, per_page: 12 }),
    {
      keepPreviousData: true,
    }
  );

  const { data: reportDetails, isLoading: loadingDetails } = useQuery(
    ['report', selectedReport?.id],
    () => selectedReport ? apiService.getReport(selectedReport.id) : null,
    {
      enabled: !!selectedReport,
    }
  );

  const handleViewReport = (report) => {
    setSelectedReport(report);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedReport(null);
  };

  const handleDownloadPDF = async (reportId, reportDate) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/export/monthly-report/${reportId}/pdf`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('authToken')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `OpalSight_Monthly_Report_${format(parseISO(reportDate), 'yyyy_MM')}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('PDF download error:', error);
      alert('Failed to download PDF. Please try again.');
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
        Error loading reports. Please try again later.
      </Alert>
    );
  }

  const reports = reportsData?.data?.reports || [];
  const totalPages = reportsData?.data?.pages || 1;

  const getSentimentIcon = (improving, stable, declining) => {
    const total = improving + stable + declining;
    if (total === 0) return <StableIcon />;
    
    const improvingPct = (improving / total) * 100;
    const decliningPct = (declining / total) * 100;
    
    if (improvingPct > 50) return <TrendingUpIcon sx={{ color: '#4caf50' }} />;
    if (decliningPct > 50) return <TrendingDownIcon sx={{ color: '#f44336' }} />;
    return <StableIcon sx={{ color: '#ff9800' }} />;
  };

  return (
    <Box className="fade-in">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Monthly Reports
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Comprehensive analysis delivered monthly
        </Typography>
      </Box>

      {reports.length === 0 ? (
        <Alert severity="info">
          No reports available yet. Reports are generated automatically on the last Friday of each month.
        </Alert>
      ) : (
        <>
          <Grid container spacing={3}>
            {reports.map((report) => (
              <Grid item xs={12} sm={6} md={4} key={report.id}>
                <Card 
                  sx={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 3,
                    },
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Typography variant="h6">
                        {format(parseISO(report.report_date), 'MMMM yyyy')}
                      </Typography>
                      {getSentimentIcon(
                        report.improving_count,
                        report.stable_count,
                        report.declining_count
                      )}
                    </Box>
                    
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      {report.companies_analyzed} Companies Analyzed
                    </Typography>
                    
                    <Box mt={2}>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Chip
                          label={`${report.improving_count} Improving`}
                          size="small"
                          sx={{ 
                            backgroundColor: '#e8f5e9',
                            color: '#4caf50',
                            fontWeight: 'medium',
                          }}
                        />
                        <Typography variant="caption" color="textSecondary">
                          {Math.round((report.improving_count / report.companies_analyzed) * 100)}%
                        </Typography>
                      </Box>
                      
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Chip
                          label={`${report.stable_count} Stable`}
                          size="small"
                          sx={{ 
                            backgroundColor: '#fff3e0',
                            color: '#ff9800',
                            fontWeight: 'medium',
                          }}
                        />
                        <Typography variant="caption" color="textSecondary">
                          {Math.round((report.stable_count / report.companies_analyzed) * 100)}%
                        </Typography>
                      </Box>
                      
                      <Box display="flex" justifyContent="space-between">
                        <Chip
                          label={`${report.declining_count} Declining`}
                          size="small"
                          sx={{ 
                            backgroundColor: '#ffebee',
                            color: '#f44336',
                            fontWeight: 'medium',
                          }}
                        />
                        <Typography variant="caption" color="textSecondary">
                          {Math.round((report.declining_count / report.companies_analyzed) * 100)}%
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                  
                  <CardActions>
                    <Button
                      size="small"
                      startIcon={<ViewIcon />}
                      onClick={() => handleViewReport(report)}
                    >
                      View Details
                    </Button>
                    <Button
                      size="small"
                      startIcon={<PdfIcon />}
                      onClick={() => handleDownloadPDF(report.id, report.report_date)}
                    >
                      Download PDF
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>

          {totalPages > 1 && (
            <Box display="flex" justifyContent="center" mt={4}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(e, value) => setPage(value)}
                color="primary"
              />
            </Box>
          )}
        </>
      )}

      {/* Report Details Dialog */}
      <Dialog
        open={openDialog}
        onClose={handleCloseDialog}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h5">
              {selectedReport && format(parseISO(selectedReport.report_date), 'MMMM yyyy')} Report
            </Typography>
            <IconButton
              onClick={() => selectedReport && handleDownloadPDF(selectedReport.id, selectedReport.report_date)}
            >
              <DownloadIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent dividers>
          {loadingDetails ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : reportDetails?.data?.report ? (
            <Box>
              {/* Summary Stats */}
              <Grid container spacing={3} mb={3}>
                <Grid item xs={12} md={4}>
                  <Card sx={{ backgroundColor: '#e8f5e9' }}>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Improving
                      </Typography>
                      <Typography variant="h4" sx={{ color: '#4caf50' }}>
                        {reportDetails.data.report.improving_count}
                      </Typography>
                      <Typography variant="body2">
                        {reportDetails.data.report.improving_percentage}% of companies
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card sx={{ backgroundColor: '#fff3e0' }}>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Stable
                      </Typography>
                      <Typography variant="h4" sx={{ color: '#ff9800' }}>
                        {reportDetails.data.report.stable_count}
                      </Typography>
                      <Typography variant="body2">
                        {reportDetails.data.report.stable_percentage}% of companies
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card sx={{ backgroundColor: '#ffebee' }}>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Declining
                      </Typography>
                      <Typography variant="h4" sx={{ color: '#f44336' }}>
                        {reportDetails.data.report.declining_count}
                      </Typography>
                      <Typography variant="body2">
                        {reportDetails.data.report.declining_percentage}% of companies
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Top Performers */}
              {reportDetails.data.report.report_data?.top_performers && (
                <Box mb={3}>
                  <Typography variant="h6" gutterBottom>
                    Top Performers
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Company</TableCell>
                          <TableCell>Ticker</TableCell>
                          <TableCell align="right">Sentiment Change</TableCell>
                          <TableCell align="right">Confidence Change</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {reportDetails.data.report.report_data.top_performers.map((company, index) => (
                          <TableRow key={index}>
                            <TableCell>{company.name}</TableCell>
                            <TableCell>
                              <Chip label={company.ticker} size="small" />
                            </TableCell>
                            <TableCell align="right" sx={{ color: '#4caf50' }}>
                              +{company.sentiment_change.toFixed(2)}
                            </TableCell>
                            <TableCell align="right">
                              {company.confidence_change > 0 ? '+' : ''}{company.confidence_change.toFixed(2)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}

              {/* Areas of Concern */}
              {reportDetails.data.report.report_data?.worst_performers && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Areas of Concern
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Company</TableCell>
                          <TableCell>Ticker</TableCell>
                          <TableCell align="right">Sentiment Change</TableCell>
                          <TableCell align="right">Confidence Change</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {reportDetails.data.report.report_data.worst_performers.map((company, index) => (
                          <TableRow key={index}>
                            <TableCell>{company.name}</TableCell>
                            <TableCell>
                              <Chip label={company.ticker} size="small" />
                            </TableCell>
                            <TableCell align="right" sx={{ color: '#f44336' }}>
                              {company.sentiment_change.toFixed(2)}
                            </TableCell>
                            <TableCell align="right">
                              {company.confidence_change > 0 ? '+' : ''}{company.confidence_change.toFixed(2)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
            </Box>
          ) : (
            <Typography>No report details available</Typography>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Reports; 