import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import {
  Speed as SpeedIcon,
  Storage as StorageIcon,
  Api as ApiIcon,
  Psychology as PsychologyIcon,
  Memory as MemoryIcon,
  Assessment as AssessmentIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon
} from '@mui/icons-material';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { performanceAPI } from '../services/performanceAPI';

function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Performance() {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [testResults, setTestResults] = useState({});
  const [stressTestRunning, setStressTestRunning] = useState(false);
  const [metricsTimeline, setMetricsTimeline] = useState([]);

  // Test configurations
  const [dbTestConfig, setDbTestConfig] = useState({
    num_queries: 10,
    query_type: 'simple'
  });
  const [apiTestConfig, setApiTestConfig] = useState({
    num_requests: 5
  });
  const [sentimentTestConfig, setSentimentTestConfig] = useState({
    num_analyses: 5,
    text: 'We are pleased to report strong quarterly results...'
  });
  const [cacheTestConfig, setCacheTestConfig] = useState({
    num_operations: 100
  });
  const [concurrentTestConfig, setConcurrentTestConfig] = useState({
    num_concurrent: 10,
    test_type: 'mixed'
  });

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const status = await performanceAPI.getStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  const runDatabaseTest = async () => {
    setLoading(true);
    try {
      const result = await performanceAPI.testDatabase(dbTestConfig);
      setTestResults(prev => ({ ...prev, database: result }));
    } catch (error) {
      console.error('Database test failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const runAPITest = async () => {
    setLoading(true);
    try {
      const result = await performanceAPI.testAPI(apiTestConfig);
      setTestResults(prev => ({ ...prev, api: result }));
    } catch (error) {
      console.error('API test failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const runSentimentTest = async () => {
    setLoading(true);
    try {
      const result = await performanceAPI.testSentiment(sentimentTestConfig);
      setTestResults(prev => ({ ...prev, sentiment: result }));
    } catch (error) {
      console.error('Sentiment test failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const runCacheTest = async () => {
    setLoading(true);
    try {
      const result = await performanceAPI.testCache(cacheTestConfig);
      setTestResults(prev => ({ ...prev, cache: result }));
    } catch (error) {
      console.error('Cache test failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const runConcurrentTest = async () => {
    setLoading(true);
    try {
      const result = await performanceAPI.testConcurrent(concurrentTestConfig);
      setTestResults(prev => ({ ...prev, concurrent: result }));
    } catch (error) {
      console.error('Concurrent test failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const runStressTest = async () => {
    setStressTestRunning(true);
    setMetricsTimeline([]);
    try {
      const result = await performanceAPI.runStressTest({ duration_seconds: 30 });
      setMetricsTimeline(result.metrics_timeline);
    } catch (error) {
      console.error('Stress test failed:', error);
    } finally {
      setStressTestRunning(false);
    }
  };

  const runBenchmark = async () => {
    setLoading(true);
    try {
      const result = await performanceAPI.runBenchmark();
      setTestResults(result.tests);
    } catch (error) {
      console.error('Benchmark failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatLatency = (ms) => {
    if (ms === null || ms === undefined) return 'N/A';
    return `${ms.toFixed(2)} ms`;
  };

  const getHealthColor = (value, type) => {
    if (type === 'cpu' || type === 'memory') {
      if (value < 50) return 'success';
      if (value < 80) return 'warning';
      return 'error';
    }
    if (type === 'latency') {
      if (value < 50) return 'success';
      if (value < 200) return 'warning';
      return 'error';
    }
    return 'info';
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Performance Testing & Monitoring
      </Typography>

      {/* System Status Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            System Status
          </Typography>
          {systemStatus && (
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="body2" color="textSecondary">
                    CPU Usage
                  </Typography>
                  <Typography variant="h4">
                    {systemStatus.system_metrics.system.cpu_percent}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={systemStatus.system_metrics.system.cpu_percent}
                    color={getHealthColor(systemStatus.system_metrics.system.cpu_percent, 'cpu')}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="body2" color="textSecondary">
                    Memory Usage
                  </Typography>
                  <Typography variant="h4">
                    {systemStatus.system_metrics.system.memory_percent}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={systemStatus.system_metrics.system.memory_percent}
                    color={getHealthColor(systemStatus.system_metrics.system.memory_percent, 'memory')}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="body2" color="textSecondary">
                    Database Latency
                  </Typography>
                  <Typography variant="h4">
                    {formatLatency(systemStatus.service_latencies.database_ms)}
                  </Typography>
                  <Chip
                    label="PostgreSQL"
                    size="small"
                    color={getHealthColor(systemStatus.service_latencies.database_ms, 'latency')}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="body2" color="textSecondary">
                    Cache Latency
                  </Typography>
                  <Typography variant="h4">
                    {formatLatency(systemStatus.service_latencies.redis_ms)}
                  </Typography>
                  <Chip
                    label="Redis"
                    size="small"
                    color={getHealthColor(systemStatus.service_latencies.redis_ms, 'latency')}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Grid>
            </Grid>
          )}
        </CardContent>
      </Card>

      {/* Test Tabs */}
      <Paper>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
          <Tab label="Database" icon={<StorageIcon />} />
          <Tab label="API" icon={<ApiIcon />} />
          <Tab label="Sentiment" icon={<PsychologyIcon />} />
          <Tab label="Cache" icon={<MemoryIcon />} />
          <Tab label="Concurrent" icon={<AssessmentIcon />} />
          <Tab label="Stress Test" icon={<SpeedIcon />} />
        </Tabs>

        {/* Database Test */}
        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Database Test Configuration
                  </Typography>
                  <TextField
                    fullWidth
                    label="Number of Queries"
                    type="number"
                    value={dbTestConfig.num_queries}
                    onChange={(e) => setDbTestConfig({ ...dbTestConfig, num_queries: parseInt(e.target.value) })}
                    margin="normal"
                  />
                  <FormControl fullWidth margin="normal">
                    <InputLabel>Query Type</InputLabel>
                    <Select
                      value={dbTestConfig.query_type}
                      onChange={(e) => setDbTestConfig({ ...dbTestConfig, query_type: e.target.value })}
                    >
                      <MenuItem value="simple">Simple</MenuItem>
                      <MenuItem value="complex">Complex Joins</MenuItem>
                      <MenuItem value="aggregate">Aggregates</MenuItem>
                    </Select>
                  </FormControl>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={runDatabaseTest}
                    disabled={loading}
                    sx={{ mt: 2 }}
                  >
                    Run Test
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={8}>
              {testResults.database && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Database Test Results
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="textSecondary">
                          Average
                        </Typography>
                        <Typography variant="h6">
                          {testResults.database.statistics.avg_ms} ms
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="textSecondary">
                          Min
                        </Typography>
                        <Typography variant="h6">
                          {testResults.database.statistics.min_ms} ms
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="textSecondary">
                          Max
                        </Typography>
                        <Typography variant="h6">
                          {testResults.database.statistics.max_ms} ms
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="textSecondary">
                          Total
                        </Typography>
                        <Typography variant="h6">
                          {testResults.database.statistics.total_ms} ms
                        </Typography>
                      </Grid>
                    </Grid>
                    <Box sx={{ mt: 3, height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={testResults.database.queries}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="query_num" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="time_ms" fill="#8884d8" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        {/* API Test */}
        <TabPanel value={activeTab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    API Test Configuration
                  </Typography>
                  <TextField
                    fullWidth
                    label="Number of Requests"
                    type="number"
                    value={apiTestConfig.num_requests}
                    onChange={(e) => setApiTestConfig({ ...apiTestConfig, num_requests: parseInt(e.target.value) })}
                    margin="normal"
                  />
                  <Alert severity="info" sx={{ mt: 2 }}>
                    Tests FMP API with rate limiting
                  </Alert>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={runAPITest}
                    disabled={loading}
                    sx={{ mt: 2 }}
                  >
                    Run Test
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={8}>
              {testResults.api && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      API Test Results
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="textSecondary">
                          Average
                        </Typography>
                        <Typography variant="h6">
                          {testResults.api.statistics.avg_ms} ms
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="textSecondary">
                          Rate Limit
                        </Typography>
                        <Typography variant="h6">
                          {testResults.api.statistics.rate_limit_delay_ms} ms
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="textSecondary">
                          Success Rate
                        </Typography>
                        <Typography variant="h6">
                          {testResults.api.requests.filter(r => r.status === 'success').length}/{testResults.api.requests.length}
                        </Typography>
                      </Grid>
                    </Grid>
                    <Box sx={{ mt: 3, height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={testResults.api.requests}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="request_num" />
                          <YAxis />
                          <Tooltip />
                          <Line type="monotone" dataKey="time_ms" stroke="#82ca9d" />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        {/* Sentiment Test */}
        <TabPanel value={activeTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Sentiment Test Configuration
                  </Typography>
                  <TextField
                    fullWidth
                    label="Number of Analyses"
                    type="number"
                    value={sentimentTestConfig.num_analyses}
                    onChange={(e) => setSentimentTestConfig({ ...sentimentTestConfig, num_analyses: parseInt(e.target.value) })}
                    margin="normal"
                  />
                  <TextField
                    fullWidth
                    label="Test Text"
                    multiline
                    rows={4}
                    value={sentimentTestConfig.text}
                    onChange={(e) => setSentimentTestConfig({ ...sentimentTestConfig, text: e.target.value })}
                    margin="normal"
                  />
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={runSentimentTest}
                    disabled={loading}
                    sx={{ mt: 2 }}
                  >
                    Run Test
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={8}>
              {testResults.sentiment && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Sentiment Analysis Test Results
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="textSecondary">
                          Average Time
                        </Typography>
                        <Typography variant="h6">
                          {testResults.sentiment.statistics.avg_ms} ms
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="textSecondary">
                          Min Time
                        </Typography>
                        <Typography variant="h6">
                          {testResults.sentiment.statistics.min_ms} ms
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="textSecondary">
                          Max Time
                        </Typography>
                        <Typography variant="h6">
                          {testResults.sentiment.statistics.max_ms} ms
                        </Typography>
                      </Grid>
                    </Grid>
                    <List sx={{ mt: 2 }}>
                      {testResults.sentiment.analyses.map((analysis, idx) => (
                        <ListItem key={idx}>
                          <ListItemText
                            primary={`Analysis ${analysis.analysis_num}`}
                            secondary={
                              <>
                                Time: {analysis.time_ms} ms | 
                                Sentiment: {analysis.sentiment_score.toFixed(3)} | 
                                Confidence: {analysis.confidence_score.toFixed(3)}
                              </>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        {/* Cache Test */}
        <TabPanel value={activeTab} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Cache Test Configuration
                  </Typography>
                  <TextField
                    fullWidth
                    label="Number of Operations"
                    type="number"
                    value={cacheTestConfig.num_operations}
                    onChange={(e) => setCacheTestConfig({ ...cacheTestConfig, num_operations: parseInt(e.target.value) })}
                    margin="normal"
                  />
                  <Alert severity="info" sx={{ mt: 2 }}>
                    Tests SET, GET, and DELETE operations
                  </Alert>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={runCacheTest}
                    disabled={loading}
                    sx={{ mt: 2 }}
                  >
                    Run Test
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={8}>
              {testResults.cache && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Cache Test Results
                    </Typography>
                    <Grid container spacing={2}>
                      {['set', 'get', 'delete'].map(op => (
                        <Grid item xs={12} sm={4} key={op}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="h6" color="primary">
                                {op.toUpperCase()}
                              </Typography>
                              <Typography variant="body2">
                                Avg: {testResults.cache[`${op}_stats`].avg_ms} ms
                              </Typography>
                              <Typography variant="body2">
                                Min: {testResults.cache[`${op}_stats`].min_ms} ms
                              </Typography>
                              <Typography variant="body2">
                                Max: {testResults.cache[`${op}_stats`].max_ms} ms
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        {/* Concurrent Test */}
        <TabPanel value={activeTab} index={4}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Concurrent Test Configuration
                  </Typography>
                  <TextField
                    fullWidth
                    label="Number of Concurrent Tasks"
                    type="number"
                    value={concurrentTestConfig.num_concurrent}
                    onChange={(e) => setConcurrentTestConfig({ ...concurrentTestConfig, num_concurrent: parseInt(e.target.value) })}
                    margin="normal"
                  />
                  <FormControl fullWidth margin="normal">
                    <InputLabel>Test Type</InputLabel>
                    <Select
                      value={concurrentTestConfig.test_type}
                      onChange={(e) => setConcurrentTestConfig({ ...concurrentTestConfig, test_type: e.target.value })}
                    >
                      <MenuItem value="mixed">Mixed</MenuItem>
                      <MenuItem value="database">Database Only</MenuItem>
                      <MenuItem value="api">API Only</MenuItem>
                    </Select>
                  </FormControl>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={runConcurrentTest}
                    disabled={loading}
                    sx={{ mt: 2 }}
                  >
                    Run Test
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={8}>
              {testResults.concurrent && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Concurrent Test Results
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={4}>
                        <Typography variant="body2" color="textSecondary">
                          Total Tasks
                        </Typography>
                        <Typography variant="h6">
                          {testResults.concurrent.statistics.total_tasks}
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={4}>
                        <Typography variant="body2" color="textSecondary">
                          Total Time
                        </Typography>
                        <Typography variant="h6">
                          {testResults.concurrent.statistics.total_time_ms} ms
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={4}>
                        <Typography variant="body2" color="textSecondary">
                          Avg per Task
                        </Typography>
                        <Typography variant="h6">
                          {testResults.concurrent.statistics.avg_time_per_task_ms} ms
                        </Typography>
                      </Grid>
                    </Grid>
                    <Divider sx={{ my: 2 }} />
                    {Object.entries(testResults.concurrent.task_results || {}).map(([type, times]) => (
                      <Box key={type} sx={{ mb: 2 }}>
                        <Typography variant="subtitle1">
                          {type.toUpperCase()} Tasks
                        </Typography>
                        <Typography variant="body2">
                          Count: {times.length} | 
                          Avg: {testResults.concurrent.statistics[`${type}_avg_ms`]} ms
                        </Typography>
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        {/* Stress Test */}
        <TabPanel value={activeTab} index={5}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="h6">
                      Stress Test (30 seconds)
                    </Typography>
                    <Button
                      variant="contained"
                      color={stressTestRunning ? "error" : "primary"}
                      startIcon={stressTestRunning ? <StopIcon /> : <PlayIcon />}
                      onClick={runStressTest}
                      disabled={stressTestRunning}
                    >
                      {stressTestRunning ? 'Running...' : 'Start Stress Test'}
                    </Button>
                  </Box>
                  {stressTestRunning && <LinearProgress sx={{ mt: 2 }} />}
                  {metricsTimeline.length > 0 && (
                    <Box sx={{ mt: 3, height: 400 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={metricsTimeline}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="elapsed_seconds" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line type="monotone" dataKey="metrics.system.cpu_percent" stroke="#8884d8" name="CPU %" />
                          <Line type="monotone" dataKey="metrics.system.memory_percent" stroke="#82ca9d" name="Memory %" />
                          <Line type="monotone" dataKey="iteration_time_ms" stroke="#ffc658" name="Iteration Time (ms)" />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Quick Actions */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="outlined"
          startIcon={<AssessmentIcon />}
          onClick={runBenchmark}
          disabled={loading}
        >
          Run Complete Benchmark
        </Button>
      </Box>
    </Box>
  );
} 