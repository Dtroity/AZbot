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
  InputLabel,
  InputAdornment
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import { filtersAPI, suppliersAPI } from '../services/api';
import { useDataGridState } from '../hooks/useDataGridState';

const dataGridSx = {
  border: 0,
  '& .MuiDataGrid-columnHeaders': { overflow: 'visible' },
  '& .MuiDataGrid-columnHeader': { overflow: 'visible', position: 'relative' },
  '& .MuiDataGrid-columnHeaderTitleContainer': { overflow: 'visible', position: 'relative', zIndex: 2 },
  '& .MuiDataGrid-columnHeaderTitleContainerContent': { overflow: 'visible', minWidth: 0 },
  '& .MuiDataGrid-columnSeparator': { zIndex: 1, pointerEvents: 'auto' },
};

function Filters() {
  const [filters, setFilters] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false);
  const [newFilter, setNewFilter] = useState({
    keyword: '',
    supplier_id: '',
    priority: 0,
    active: true
  });
  const [bulkKeywords, setBulkKeywords] = useState('');
  const [bulkSupplierId, setBulkSupplierId] = useState('');
  const [pagination, setPagination] = useState({ page: 0, pageSize: 25 });
  const { onColumnWidthChange, columnsWithWidths } = useDataGridState('filters');

  const columns = [
    {
      field: 'id',
      headerName: 'ID',
      width: 80,
      minWidth: 60,
      resizable: true,
    },
    {
      field: 'keyword',
      headerName: 'Ключевое слово',
      width: 200,
      minWidth: 120,
      flex: 1,
      resizable: true,
    },
    {
      field: 'supplier_id',
      headerName: 'Поставщик',
      width: 150,
      minWidth: 100,
      resizable: true,
      renderCell: (params) => {
        const supplier = suppliers.find(s => s.id === params.value);
        return supplier ? supplier.name : `ID: ${params.value}`;
      },
    },
    {
      field: 'priority',
      headerName: 'Приоритет',
      width: 100,
      minWidth: 80,
      resizable: true,
      renderCell: (params) => (
        <Chip
          label={params.value}
          size="small"
          color={params.value > 5 ? 'secondary' : 'default'}
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
      width: 150,
      minWidth: 120,
      resizable: true,
      renderCell: (params) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => handleEditFilter(params.row)}
            title="Редактировать"
          >
            <EditIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleDeleteFilter(params.row)}
            title="Удалить"
          >
            <DeleteIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleToggleActive(params.row)}
            title={params.row.active ? 'Деактивировать' : 'Активировать'}
          >
            {params.row.active ? '🔴' : '🟢'}
          </IconButton>
        </Box>
      ),
    },
  ];

  useEffect(() => {
    fetchData();
  }, [pagination.page, pagination.pageSize]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [filtersResponse, suppliersResponse] = await Promise.all([
        filtersAPI.getFilters({
          skip: pagination.page * pagination.pageSize,
          limit: pagination.pageSize,
        }),
        suppliersAPI.getSuppliers({ active_only: false })
      ]);
      
      setFilters(filtersResponse.data);
      setSuppliers(suppliersResponse.data);
    } catch (err) {
      setError('Ошибка загрузки данных');
      console.error('Data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFilter = async () => {
    try {
      await filtersAPI.createFilter(newFilter);
      setCreateDialogOpen(false);
      setNewFilter({
        keyword: '',
        supplier_id: '',
        priority: 0,
        active: true
      });
      fetchData();
    } catch (err) {
      setError('Ошибка создания фильтра');
      console.error('Filter creation error:', err);
    }
  };

  const handleEditFilter = async () => {
    try {
      await filtersAPI.updateFilter(selectedFilter.id, selectedFilter);
      setEditDialogOpen(false);
      setSelectedFilter(null);
      fetchData();
    } catch (err) {
      setError('Ошибка обновления фильтра');
      console.error('Filter update error:', err);
    }
  };

  const handleDeleteFilter = async (filter) => {
    if (window.confirm(`Удалить фильтр "${filter.keyword}"?`)) {
      try {
        await filtersAPI.deleteFilter(filter.id);
        fetchData();
      } catch (err) {
        setError('Ошибка удаления фильтра');
        console.error('Filter deletion error:', err);
      }
    }
  };

  const handleToggleActive = async (filter) => {
    try {
      if (filter.active) {
        await filtersAPI.deactivateFilter(filter.id);
      } else {
        await filtersAPI.activateFilter(filter.id);
      }
      fetchData();
    } catch (err) {
      setError('Ошибка изменения статуса фильтра');
      console.error('Filter status toggle error:', err);
    }
  };

  const handleCreateBulkFilters = async () => {
    try {
      const keywords = bulkKeywords.split(',').map(k => k.trim()).filter(k => k);
      await filtersAPI.createBulkFilters(bulkSupplierId, keywords);
      setBulkDialogOpen(false);
      setBulkKeywords('');
      setBulkSupplierId('');
      fetchData();
    } catch (err) {
      setError('Ошибка создания фильтров');
      console.error('Bulk filters creation error:', err);
    }
  };

  return (
    <Box sx={{ width: '100%', minWidth: 0 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Фильтры</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => setBulkDialogOpen(true)}
            sx={{ mr: 2 }}
          >
            Массовое добавление
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Добавить фильтр
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
          rows={filters}
          columns={columnsWithWidths(columns)}
          onColumnWidthChange={onColumnWidthChange}
          pagination
          paginationModel={pagination}
          onPaginationModelChange={setPagination}
          loading={loading}
          pageSizeOptions={[25, 50, 100]}
          rowCount={filters.length}
          disableRowSelectionOnClick
          disableColumnResize={false}
          sx={dataGridSx}
        />
      </Paper>

      {/* Create Filter Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Добавить фильтр</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Ключевое слово"
                value={newFilter.keyword}
                onChange={(e) => setNewFilter({ ...newFilter, keyword: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Поставщик</InputLabel>
                <Select
                  value={newFilter.supplier_id}
                  label="Поставщик"
                  onChange={(e) => setNewFilter({ ...newFilter, supplier_id: e.target.value })}
                >
                  {suppliers.map((supplier) => (
                    <MenuItem key={supplier.id} value={supplier.id}>
                      {supplier.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Приоритет"
                type="number"
                value={newFilter.priority}
                onChange={(e) => setNewFilter({ ...newFilter, priority: parseInt(e.target.value) || 0 })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">🎯</InputAdornment>,
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={newFilter.active}
                    onChange={(e) => setNewFilter({ ...newFilter, active: e.target.checked })}
                  />
                }
                label="Активен"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleCreateFilter} variant="contained">Создать</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Filter Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Редактировать фильтр</DialogTitle>
        <DialogContent>
          {selectedFilter && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Ключевое слово"
                  value={selectedFilter.keyword}
                  onChange={(e) => setSelectedFilter({ ...selectedFilter, keyword: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Поставщик</InputLabel>
                  <Select
                    value={selectedFilter.supplier_id}
                    label="Поставщик"
                    onChange={(e) => setSelectedFilter({ ...selectedFilter, supplier_id: e.target.value })}
                  >
                    {suppliers.map((supplier) => (
                      <MenuItem key={supplier.id} value={supplier.id}>
                        {supplier.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Приоритет"
                  type="number"
                  value={selectedFilter.priority}
                  onChange={(e) => setSelectedFilter({ ...selectedFilter, priority: parseInt(e.target.value) || 0 })}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={selectedFilter.active}
                      onChange={(e) => setSelectedFilter({ ...selectedFilter, active: e.target.checked })}
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
          <Button onClick={handleEditFilter} variant="contained">Сохранить</Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Create Dialog */}
      <Dialog open={bulkDialogOpen} onClose={() => setBulkDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Массовое добавление фильтров</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Поставщик</InputLabel>
                <Select
                  value={bulkSupplierId}
                  label="Поставщик"
                  onChange={(e) => setBulkSupplierId(e.target.value)}
                >
                  {suppliers.map((supplier) => (
                    <MenuItem key={supplier.id} value={supplier.id}>
                      {supplier.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Ключевые слова (через запятую)"
                multiline
                rows={4}
                value={bulkKeywords}
                onChange={(e) => setBulkKeywords(e.target.value)}
                placeholder="ноутбук, компьютер, техника, монитор"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleCreateBulkFilters} variant="contained">Создать</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Filters;
