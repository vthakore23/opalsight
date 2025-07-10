import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';

// Layout
import Layout from './components/Layout/Layout';

// Pages
import Dashboard from './pages/Dashboard';
import Companies from './pages/Companies';
import CompanyDetail from './pages/CompanyDetail';
import Reports from './pages/Reports';
import Alerts from './pages/Alerts';
import Watchlist from './pages/Watchlist';
import Performance from './pages/Performance';
import Q1Analytics from './pages/Q1Analytics';
import Demo from './pages/Demo';

function App() {
  return (
    <Routes>
      {/* Public demo route without layout */}
      <Route path="/demo" element={<Demo />} />
      
      {/* App routes with layout */}
      <Route
        path="/*"
        element={
          <Box sx={{ display: 'flex', minHeight: '100vh' }}>
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/companies" element={<Companies />} />
                <Route path="/company/:ticker" element={<CompanyDetail />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/watchlist" element={<Watchlist />} />
                <Route path="/performance" element={<Performance />} />
                <Route path="/q1-analytics" element={<Q1Analytics />} />
              </Routes>
            </Layout>
          </Box>
        }
      />
    </Routes>
  );
}

export default App; 