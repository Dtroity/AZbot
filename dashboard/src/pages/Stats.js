import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { statsAPI } from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

function Stats() {
  const [period, setPeriod] = useState('today');
  const [stats, setStats] = useState(null);
  const [dailyStats, setDailyStats] = useState([]);
  const [supplierPerformance, setSupplierPerformance] = useState([]);
  const [statusDistribution, setStatusDistribution] = useState([]);
  const [activityStats, setActivityStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStatsData();
  }, [period]);

  const fetchStatsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [
        statsResponse,
        dailyResponse,
        performanceResponse,
        statusResponse,
        activityResponse
      ] = await Promise.all([
        statsAPI.getStats({ period }),
        statsAPI.getDailyStats({ days: period === 'today' ? 1 : period === 'week' ? 7 : 30 }),
        statsAPI.getSupplierPerformance({ limit: 10 }),
        statsAPI.getOrderStatusDistribution({ period }),
        statsAPI.getActivityStats({ hours: period === 'today' ? 24 : period === 'week' ? 168 : 720 })
      ]);

      setStats(statsResponse.data);
      setDailyStats(dailyResponse.data);
      setSupplierPerformance(performanceResponse.data);
      setStatusDistribution(statusResponse.data.distribution);
      setActivityStats(activityResponse.data);
    } catch (err) {
      setError('Ошибка загрузки статистики');
      console.error('Stats fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Статистика</Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Период</InputLabel>
          <Select
            value={period}
            label="Период"
            onChange={(e) => setPeriod(e.target.value)}
          >
            <MenuItem value="today">Сегодня</MenuItem>
            <MenuItem value="week">Неделя</MenuItem>
            <MenuItem value="month">Месяц</MenuItem>
            <MenuItem value="all">Все время</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="overline">
                Всего заказов
              </Typography>
              <Typography variant="h4" component="div">
                {stats?.orders?.total || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="overline">
                Выполнено
              </Typography>
              <Typography variant="h4" component="div" color="success.main">
                {stats?.orders?.completed || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="overline">
                В работе
              </Typography>
              <Typography variant="h4" component="div" color="warning.main">
                {stats?.orders?.pending || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="overline">
                Процент выполнения
              </Typography>
              <Typography variant="h4" component="div" color="primary.main">
                {stats?.orders?.completion_rate?.toFixed(1) || 0}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Daily Orders Chart */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Динамика заказов
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyStats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(value) => new Date(value).toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' })}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleDateString('ru-RU')}
                />
                <Line 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#1976d2" 
                  strokeWidth={2}
                  name="Заказы"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Status Distribution */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Распределение статусов
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {statusDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Supplier Performance */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Топ поставщиков
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={supplierPerformance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="completed_orders" fill="#4caf50" name="Выполнено" />
                <Bar dataKey="total_orders" fill="#2196f3" name="Всего" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Activity Stats */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Активность системы
            </Typography>
            {activityStats && (
              <Box>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Действия за последние {activityStats.period_hours} часов:
                </Typography>
                {Object.entries(activityStats.action_counts).map(([action, count]) => (
                  <Box key={action} display="flex" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography variant="body2">{action}</Typography>
                    <Typography variant="body2" fontWeight="bold">{count}</Typography>
                  </Box>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Supplier Stats */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Статистика поставщиков
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Box textAlign="center">
                  <Typography variant="h3" color="primary.main">
                    {stats?.suppliers?.total || 0}
                  </Typography>
                  <Typography color="textSecondary">
                    Всего поставщиков
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box textAlign="center">
                  <Typography variant="h3" color="success.main">
                    {stats?.suppliers?.active || 0}
                  </Typography>
                  <Typography color="textSecondary">
                    Активных
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box textAlign="center">
                  <Typography variant="h3" color="error.main">
                    {stats?.suppliers?.inactive || 0}
                  </Typography>
                  <Typography color="textSecondary">
                    Неактивных
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Stats;
