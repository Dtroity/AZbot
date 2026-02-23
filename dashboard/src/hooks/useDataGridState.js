import { useState, useCallback } from 'react';

const STORAGE_PREFIX = 'dataGridColumnWidths_';

/**
 * Persist column widths to localStorage and restore on load.
 * Uses onColumnWidthChange to save; applies saved widths by merging into columns.
 * @param {string} storageKey - e.g. 'orders', 'suppliers', 'filters'
 * @returns {{ columnWidths: Record<string, number>, onColumnWidthChange: function, columnsWithWidths: (columns: Array) => Array }}
 */
export function useDataGridState(storageKey) {
  const fullKey = `${STORAGE_PREFIX}${storageKey}`;
  const [columnWidths, setColumnWidths] = useState(() => {
    try {
      const saved = localStorage.getItem(fullKey);
      if (!saved) return {};
      const parsed = JSON.parse(saved);
      return typeof parsed === 'object' && parsed !== null ? parsed : {};
    } catch {
      return {};
    }
  });

  const onColumnWidthChange = useCallback(
    (params) => {
      const field = params?.colDef?.field ?? params?.field;
      const width = params?.width;
      if (field == null || typeof width !== 'number') return;
      setColumnWidths((prev) => {
        const next = { ...prev, [field]: width };
        try {
          localStorage.setItem(fullKey, JSON.stringify(next));
        } catch (e) {
          // ignore
        }
        return next;
      });
    },
    [fullKey]
  );

  const columnsWithWidths = useCallback(
    (columns) => {
      if (!columns?.length) return columns;
      return columns.map((col) => ({
        ...col,
        width: columnWidths[col.field] ?? col.width,
      }));
    },
    [columnWidths]
  );

  return { columnWidths, onColumnWidthChange, columnsWithWidths };
}
