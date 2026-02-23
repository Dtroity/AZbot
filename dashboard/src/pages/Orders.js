import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Chip,
  IconButton,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Message as MessageIcon
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import { ordersAPI } from '../services/api';

const statusColors = {
  'NEW': '#2196f3',
  'ASSIGNED': '#ff9800',
  'ACCEPTED': '#4caf50',
  'COMPLETED': '#4caf50',
  'DECLINED': '#f44336',
  'CANCELLED': '#9e9e9e'
};

const statusLabels = {
  'NEW': 'Новый',
  'ASSIGNED': 'Назначен',
  'ACCEPTED': 'Принят',
  'COMPLETED': 'Завершен',
  'DECLINED': 'Отклонен',
  'CANCELLED': 'Отменен'
};

function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [messagesDialogOpen, setMessagesDialogOpen] = useState(false);
  const [newOrderText, setNewOrderText] = useState('');
  const [orderMessages, setOrderMessages] = useState([]);
  const [pagination, setPagination] = useState({ page: 0, pageSize: 25 });

  const columns = [
    {
      field: 'id',
      headerName: 'ID',
      width: 100,
      minWidth: 70,
      resizable: true,
    },
    {
      field: 'text',
      headerName: 'Описание',
      width: 300,
      minWidth: 150,
      flex: 1,
      resizable: true,
    },
    {
      field: 'status',
      headerName: 'Статус',
      width: 120,
      minWidth: 90,
      resizable: true,
      renderCell: (params) => (
        <Chip
          label={statusLabels[params.value] || params.value}
          size="small"
          style={{ backgroundColor: statusColors[params.value] || '#9e9e9e', color: 'white' }}
        />
      ),
    },
    {
      field: 'supplier',
      headerName: 'Поставщик',
      width: 150,
      minWidth: 100,
      resizable: true,
      renderCell: (params) => params.value?.name || 'Не назначен',
    },
    {
      field: 'created_at',
      headerName: 'Создан',
      width: 150,
      minWidth: 120,
      resizable: true,
      renderCell: (params) => new Date(params.value).toLocaleString('ru-RU'),
    },
    {
      field: 'actions',
      headerName: 'Действия',
      width: 150,
      minWidth: 120,
      resizable: true,
      renderCell: (params) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => handleViewOrder(params.row)}
            title="Просмотр"
          >
            <ViewIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleViewMessages(params.row)}
            title="Сообщения"
          >
            <MessageIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleDeleteOrder(params.row)}
            title="Удалить"
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      ),
    },
  ];

  useEffect(() => {
    fetchOrders();
  }, [pagination.page, pagination.pageSize]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await ordersAPI.getOrders({
        skip: pagination.page * pagination.pageSize,
        limit: pagination.pageSize,
      });
      setOrders(response.data);
    } catch (err) {
      setError('Ошибка загрузки заказов');
      console.error('Orders fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrder = async () => {
    try {
      await ordersAPI.createOrder({
        text: newOrderText,
        admin_id: 123456789, // Mock admin ID
      });
      setCreateDialogOpen(false);
      setNewOrderText('');
      fetchOrders();
    } catch (err) {
      setError('Ошибка создания заказа');
      console.error('Order creation error:', err);
    }
  };

  const handleViewOrder = (order) => {
    setSelectedOrder(order);
    setViewDialogOpen(true);
  };

  const handleViewMessages = async (order) => {
    try {
      const response = await ordersAPI.getOrderMessages(order.id);
      setOrderMessages(response.data);
      setSelectedOrder(order);
      setMessagesDialogOpen(true);
    } catch (err) {
      setError('Ошибка загрузки сообщений');
      console.error('Messages fetch error:', err);
    }
  };

  const handleDeleteOrder = async (order) => {
    if (window.confirm(`Удалить заказ #${order.id}?`)) {
      try {
        await ordersAPI.deleteOrder(order.id);
        fetchOrders();
      } catch (err) {
        setError('Ошибка удаления заказа');
        console.error('Order deletion error:', err);
      }
    }
  };

  const handleAddMessage = async (message) => {
    try {
      await ordersAPI.addOrderMessage(selectedOrder.id, message);
      const response = await ordersAPI.getOrderMessages(selectedOrder.id);
      setOrderMessages(response.data);
    } catch (err) {
      setError('Ошибка отправки сообщения');
      console.error('Message send error:', err);
    }
  };

  return (
    <Box sx={{ width: '100%', minWidth: 0 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Заказы</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Создать заказ
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ height: 'calc(100vh - 220px)', minHeight: 400, width: '100%', maxWidth: '100%' }}>
        <DataGrid
          rows={orders}
          columns={columns}
          pagination
          paginationModel={pagination}
          onPaginationModelChange={setPagination}
          loading={loading}
          pageSizeOptions={[25, 50, 100]}
          rowCount={orders.length}
          disableRowSelectionOnClick
          disableColumnResize={false}
          sx={{ border: 0 }}
        />
      </Paper>

      {/* Create Order Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Создать заказ</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Текст заказа"
            multiline
            rows={4}
            fullWidth
            variant="outlined"
            value={newOrderText}
            onChange={(e) => setNewOrderText(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleCreateOrder} variant="contained">Создать</Button>
        </DialogActions>
      </Dialog>

      {/* View Order Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Заказ #{selectedOrder?.id}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Typography variant="subtitle1">Описание:</Typography>
              <Typography>{selectedOrder?.text}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="subtitle1">Статус:</Typography>
              <Chip
                label={statusLabels[selectedOrder?.status] || selectedOrder?.status}
                style={{ backgroundColor: statusColors[selectedOrder?.status] || '#9e9e9e', color: 'white' }}
              />
            </Grid>
            <Grid item xs={6}>
              <Typography variant="subtitle1">Поставщик:</Typography>
              <Typography>{selectedOrder?.supplier?.name || 'Не назначен'}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="subtitle1">Создан:</Typography>
              <Typography>{selectedOrder?.created_at && new Date(selectedOrder.created_at).toLocaleString('ru-RU')}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="subtitle1">Обновлен:</Typography>
              <Typography>{selectedOrder?.updated_at && new Date(selectedOrder.updated_at).toLocaleString('ru-RU')}</Typography>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>

      {/* Messages Dialog */}
      <Dialog open={messagesDialogOpen} onClose={() => setMessagesDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Сообщения по заказу #{selectedOrder?.id}</DialogTitle>
        <DialogContent>
          <Box sx={{ maxHeight: 400, overflow: 'auto', mb: 2 }}>
            {orderMessages.map((message) => (
              <Box key={message.id} sx={{ mb: 1, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
                <Typography variant="caption" color="textSecondary">
                  {new Date(message.created_at).toLocaleString('ru-RU')} - ID: {message.sender_id}
                </Typography>
                <Typography>{message.message_text}</Typography>
              </Box>
            ))}
          </Box>
          <TextField
            fullWidth
            label="Новое сообщение"
            onKeyPress={(e) => {
              if (e.key === 'Enter' && e.target.value.trim()) {
                handleAddMessage(e.target.value);
                e.target.value = '';
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMessagesDialogOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Orders;
