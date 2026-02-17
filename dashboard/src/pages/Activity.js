import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material';
import { activityAPI } from '../services/api';

const actionColors = {
  'order_created': '#2196f3',
  'order_accepted': '#4caf50',
  'order_declined': '#f44336',
  'order_completed': '#4caf50',
  'order_cancelled': '#9e9e9e',
  'supplier_created': '#ff9800',
  'supplier_activated': '#4caf50',
  'supplier_deactivated': '#f44336',
  'filter_created': '#9c27b0',
  'filter_updated': '#ff9800',
  'filter_deleted': '#f44336'
};

const actionLabels = {
  'order_created': 'Заказ создан',
  'order_accepted': 'Заказ принят',
  'order_declined': 'Заказ отклонен',
  'order_completed': 'Заказ завершен',
  'order_cancelled': 'Заказ отменен',
  'supplier_created': 'Поставщик создан',
  'supplier_activated': 'Поставщик активирован',
  'supplier_deactivated': 'Поставщик деактивирован',
  'filter_created': 'Фильтр создан',
  'filter_updated': 'Фильтр обновлен',
  'filter_deleted': 'Фильтр удален'
};

function Activity() {
  const [logs, setLogs] = useState([]);
  const [availableActions, setAvailableActions] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    action: '',
    user_id: '',
    hours: 24
  });
  const [totalCount, setTotalCount] = useState(0);

  const rowsPerPage = 50;

  useEffect(() => {
    fetchActivityData();
  }, [page, filters]);

  const fetchActivityData = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        skip: (page - 1) * rowsPerPage,
        limit: rowsPerPage,
        ...filters
      };

      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null) {
          delete params[key];
        }
      });

      const [logsResponse, actionsResponse, recentResponse] = await Promise.all([
        activityAPI.getActivityLogs(params),
        activityAPI.getAvailableActions(),
        activityAPI.getRecentActivity({ limit: 10 })
      ]);

      setLogs(logsResponse.data);
      setAvailableActions(actionsResponse.data.actions);
      setRecentActivity(recentResponse.data);
      
      // For pagination, we'd need the total count from the API
      // For now, we'll use the current logs length
      setTotalCount(logsResponse.data.length);
    } catch (err) {
      setError('Ошибка загрузки данных активности');
      console.error('Activity data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPage(1); // Reset to first page when filters change
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Активность системы
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Recent Activity Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Последняя активность
              </Typography>
              {recentActivity.slice(0, 5).map((log) => (
                <Box key={log.id} sx={{ mb: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Chip
                      label={actionLabels[log.action] || log.action}
                      size="small"
                      style={{ 
                        backgroundColor: actionColors[log.action] || '#9e9e9e', 
                        color: 'white',
                        fontSize: '0.7rem'
                      }}
                    />
                    <Typography variant="caption" color="textSecondary">
                      {formatDate(log.created_at)}
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ mt: 0.5 }}>
                    Пользователь ID: {log.user_id}
                  </Typography>
                  {log.details && (
                    <Typography variant="caption" color="textSecondary">
                      {log.details}
                    </Typography>
                  )}
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Фильтры
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Действие</InputLabel>
                    <Select
                      value={filters.action}
                      label="Действие"
                      onChange={(e) => handleFilterChange('action', e.target.value)}
                    >
                      <MenuItem value="">Все действия</MenuItem>
                      {availableActions.map((action) => (
                        <MenuItem key={action} value={action}>
                          {actionLabels[action] || action}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="ID пользователя"
                    size="small"
                    value={filters.user_id}
                    onChange={(e) => handleFilterChange('user_id', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Период (часов)</InputLabel>
                    <Select
                      value={filters.hours}
                      label="Период (часов)"
                      onChange={(e) => handleFilterChange('hours', e.target.value)}
                    >
                      <MenuItem value={1}>1 час</MenuItem>
                      <MenuItem value={6}>6 часов</MenuItem>
                      <MenuItem value={24}>24 часа</MenuItem>
                      <MenuItem value={168}>Неделя</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Activity Logs Table */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Журнал активности
        </Typography>
        
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Время</TableCell>
                    <TableCell>Действие</TableCell>
                    <TableCell>Пользователь</TableCell>
                    <TableCell>Детали</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>{formatDate(log.created_at)}</TableCell>
                      <TableCell>
                        <Chip
                          label={actionLabels[log.action] || log.action}
                          size="small"
                          style={{ 
                            backgroundColor: actionColors[log.action] || '#9e9e9e', 
                            color: 'white' 
                          }}
                        />
                      </TableCell>
                      <TableCell>{log.user_id}</TableCell>
                      <TableCell>
                        {log.details && (
                          <Typography variant="body2" color="textSecondary">
                            {log.details}
                          </Typography>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            
            {totalCount > rowsPerPage && (
              <Box display="flex" justifyContent="center" mt={2}>
                <Pagination
                  count={Math.ceil(totalCount / rowsPerPage)}
                  page={page}
                  onChange={(e, value) => setPage(value)}
                  color="primary"
                />
              </Box>
            )}
          </>
        )}
      </Paper>
    </Box>
  );
}

export default Activity;
