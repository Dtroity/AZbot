import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Orders from './pages/Orders';
import Suppliers from './pages/Suppliers';
import Filters from './pages/Filters';
import Stats from './pages/Stats';
import Activity from './pages/Activity';

function App() {
  return (
    <Box sx={{ display: 'flex' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/suppliers" element={<Suppliers />} />
          <Route path="/filters" element={<Filters />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/activity" element={<Activity />} />
        </Routes>
      </Layout>
    </Box>
  );
}

export default App;
