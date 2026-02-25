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
  CircularProgress,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  FilterList as FiltersIcon
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import { suppliersAPI } from '../services/api';
import { useDataGridState } from '../hooks/useDataGridState';

const roleColors = {
  'admin': '#f44336',
  'supplier': '#2196f3'
};

const roleLabels = {
  'admin': 'Администратор',
  'supplier': 'Поставщик'
};

const dataGridSx = {
  border: 0,
  '& .MuiDataGrid-columnHeaders': { overflow: 'visible' },
  '& .MuiDataGrid-columnHeader': { overflow: 'visible', position: 'relative' },
  '& .MuiDataGrid-columnHeaderTitleContainer': { overflow: 'visible', position: 'relative', zIndex: 2 },
  '& .MuiDataGrid-columnHeaderTitleContainerContent': { overflow: 'visible', minWidth: 0 },
  '& .MuiDataGrid-columnSeparator': { zIndex: 1, pointerEvents: 'auto' },
};

function Suppliers() {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [filtersDialogOpen, setFiltersDialogOpen] = useState(false);
  const [supplierFilters, setSupplierFilters] = useState([]);
  const [newSupplier, setNewSupplier] = useState({
    name: '',
    telegram_id: '',
    role: 'supplier',
    active: true
  });
  const [pagination, setPagination] = useState({ page: 0, pageSize: 25 });
  const [rowCount, setRowCount] = useState(0);
  const [rowSelectionModel, setRowSelectionModel] = useState([]);
  const { onColumnWidthChange, columnsWithWidths } = useDataGridState('suppliers');

  const columns = [
    {
      field: 'id',
      headerName: 'ID',
      width: 80,
      minWidth: 60,
      resizable: true,
    },
    {
      field: 'name',
      headerName: 'Имя',
      width: 200,
      minWidth: 120,
      flex: 1,
      resizable: true,
    },
    {
      field: 'telegram_id',
      headerName: 'Telegram ID',
      width: 120,
      minWidth: 90,
      resizable: true,
    },
    {
      field: 'role',
      headerName: 'Роль',
      width: 120,
      minWidth: 90,
      resizable: true,
      renderCell: (params) => (
        <Chip
          label={roleLabels[params.value] || params.value}
          size="small"
          style={{ backgroundColor: roleColors[params.value] || '#9e9e9e', color: 'white' }}
        />
      ),
    },
    {
      field: 'active',
      headerName: 'Активен',
      width: 80,
      minWidth: 70,
      resizable: true,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Да' : 'Нет'}
          size="small"
          color={params.value ? 'success' : 'default'}
        />
      ),
    },
    {
      field: 'created_at',
      headerName: 'Создан',
      width: 150,
      minWidth: 100,
      resizable: true,
      renderCell: (params) => new Date(params.value).toLocaleDateString('ru-RU'),
    },
    {
      field: 'actions',
      headerName: 'Действия',
      width: 180,
      minWidth: 140,
      resizable: true,
      renderCell: (params) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => handleViewSupplier(params.row)}
            title="Просмотр"
          >
            <ViewIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleEditSupplier(params.row)}
            title="Редактировать"
          >
            <EditIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleViewFilters(params.row)}
            title="Фильтры"
          >
            <FiltersIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleDeleteSupplier(params.row)}
            title="Удалить"
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      ),
    },
  ];

  useEffect(() => {
    fetchSuppliers();
  }, [pagination.page, pagination.pageSize]);

  const fetchSuppliers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await suppliersAPI.getSuppliers({
        skip: pagination.page * pagination.pageSize,
        limit: pagination.pageSize,
      });
      const data = response.data?.items != null ? response.data : { items: response.data, total: response.data?.length ?? 0 };
      setSuppliers(Array.isArray(data.items) ? data.items : []);
      setRowCount(typeof data.total === 'number' ? data.total : data.items?.length ?? 0);
    } catch (err) {
      setError('Ошибка загрузки поставщиков');
      console.error('Suppliers fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSupplier = async () => {
    try {
      await suppliersAPI.createSupplier(newSupplier);
      setCreateDialogOpen(false);
      setNewSupplier({
        name: '',
        telegram_id: '',
        role: 'supplier',
        active: true
      });
      fetchSuppliers();
    } catch (err) {
      setError('Ошибка создания поставщика');
      console.error('Supplier creation error:', err);
    }
  };

  const handleEditSupplier = async () => {
    try {
      await suppliersAPI.updateSupplier(selectedSupplier.id, {
        name: selectedSupplier.name,
        active: selectedSupplier.active,
        role: selectedSupplier.role,
      });
      setEditDialogOpen(false);
      setSelectedSupplier(null);
      fetchSuppliers();
    } catch (err) {
      setError('Ошибка обновления поставщика');
      console.error('Supplier update error:', err);
    }
  };

  const handleViewSupplier = (supplier) => {
    setSelectedSupplier(supplier);
    setEditDialogOpen(true);
  };

  const handleViewFilters = async (supplier) => {
    try {
      const response = await suppliersAPI.getSupplierFilters(supplier.id);
      setSupplierFilters(response.data);
      setSelectedSupplier(supplier);
      setFiltersDialogOpen(true);
    } catch (err) {
      setError('Ошибка загрузки фильтров');
      console.error('Filters fetch error:', err);
    }
  };

  const handleDeleteSupplier = async (supplier) => {
    if (window.confirm(`Удалить поставщика "${supplier.name}"?`)) {
      try {
        await suppliersAPI.deleteSupplier(supplier.id);
        fetchSuppliers();
      } catch (err) {
        setError('Ошибка удаления поставщика');
        console.error('Supplier deletion error:', err);
      }
    }
  };

  const handleToggleActive = async (supplier) => {
    try {
      if (supplier.active) {
        await suppliersAPI.deactivateSupplier(supplier.id);
      } else {
        await suppliersAPI.activateSupplier(supplier.id);
      }
      fetchSuppliers();
    } catch (err) {
      setError('Ошибка изменения статуса поставщика');
      console.error('Supplier status toggle error:', err);
    }
  };

  const handleDeleteSelected = async () => {
    if (rowSelectionModel.length === 0) return;
    if (!window.confirm(`Удалить выбранных поставщиков (${rowSelectionModel.length})?`)) return;
    try {
      setError(null);
      const results = await Promise.allSettled(
        rowSelectionModel.map((id) => suppliersAPI.deleteSupplier(id))
      );
      const failed = results.filter((r) => r.status === 'rejected');
      if (failed.length) {
        setError(`Удалено: ${results.length - failed.length}. Ошибок: ${failed.length}.`);
      }
      setRowSelectionModel([]);
      fetchSuppliers();
    } catch (err) {
      setError('Ошибка удаления поставщиков');
      console.error('Bulk delete error:', err);
    }
  };

  return (
    <Box sx={{ width: '100%', minWidth: 0 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3} flexWrap="wrap" gap={1}>
        <Typography variant="h4">Поставщики</Typography>
        <Box display="flex" alignItems="center" gap={1}>
          {rowSelectionModel.length > 0 && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleDeleteSelected}
            >
              Удалить выбранные ({rowSelectionModel.length})
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Добавить поставщика
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ height: 'calc(100vh - 220px)', minHeight: 400, width: '100%', maxWidth: '100%' }}>
        <DataGrid
          rows={suppliers}
          columns={columnsWithWidths(columns)}
          onColumnWidthChange={onColumnWidthChange}
          pagination
          paginationMode="server"
          paginationModel={pagination}
          onPaginationModelChange={setPagination}
          loading={loading}
          pageSizeOptions={[25, 50, 100]}
          rowCount={rowCount}
          checkboxSelection
          rowSelectionModel={rowSelectionModel}
          onRowSelectionModelChange={setRowSelectionModel}
          disableRowSelectionOnClick
          disableColumnResize={false}
          sx={dataGridSx}
        />
      </Paper>

      {/* Create Supplier Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Добавить поставщика</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Имя"
                value={newSupplier.name}
                onChange={(e) => setNewSupplier({ ...newSupplier, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Telegram ID"
                type="number"
                value={newSupplier.telegram_id}
                onChange={(e) => setNewSupplier({ ...newSupplier, telegram_id: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Роль</InputLabel>
                <Select
                  value={newSupplier.role}
                  label="Роль"
                  onChange={(e) => setNewSupplier({ ...newSupplier, role: e.target.value })}
                >
                  <MenuItem value="supplier">Поставщик</MenuItem>
                  <MenuItem value="admin">Администратор</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={newSupplier.active}
                    onChange={(e) => setNewSupplier({ ...newSupplier, active: e.target.checked })}
                  />
                }
                label="Активен"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleCreateSupplier} variant="contained">Создать</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Supplier Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Редактировать поставщика</DialogTitle>
        <DialogContent>
          {selectedSupplier && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Имя"
                  value={selectedSupplier.name}
                  onChange={(e) => setSelectedSupplier({ ...selectedSupplier, name: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Telegram ID"
                  type="number"
                  value={selectedSupplier.telegram_id}
                  onChange={(e) => setSelectedSupplier({ ...selectedSupplier, telegram_id: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Роль</InputLabel>
                  <Select
                    value={selectedSupplier.role}
                    label="Роль"
                    onChange={(e) => setSelectedSupplier({ ...selectedSupplier, role: e.target.value })}
                  >
                    <MenuItem value="supplier">Поставщик</MenuItem>
                    <MenuItem value="admin">Администратор</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={selectedSupplier.active}
                      onChange={(e) => setSelectedSupplier({ ...selectedSupplier, active: e.target.checked })}
                    />
                  }
                  label="Активен"
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleEditSupplier} variant="contained">Сохранить</Button>
        </DialogActions>
      </Dialog>

      {/* Filters Dialog */}
      <Dialog open={filtersDialogOpen} onClose={() => setFiltersDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Фильтры поставщика: {selectedSupplier?.name}</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1">Ключевые слова:</Typography>
            {supplierFilters.map((filter) => (
              <Chip
                key={filter.id}
                label={filter.keyword}
                sx={{ m: 0.5 }}
                color={filter.active ? 'primary' : 'default'}
              />
            ))}
            {supplierFilters.length === 0 && (
              <Typography color="textSecondary">Нет фильтров</Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFiltersDialogOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Suppliers;
