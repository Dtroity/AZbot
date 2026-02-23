import { useState, useLayoutEffect } from 'react';
import { useGridApiRef } from '@mui/x-data-grid';

const STORAGE_PREFIX = 'dataGridState_';

/**
 * Hook for persisting Data Grid state (column widths, etc.) to localStorage.
 * @param {string} storageKey - Suffix for localStorage key (e.g. 'orders', 'suppliers', 'filters')
 * @returns {{ apiRef: React.MutableRefObject, initialState: object | undefined }}
 */
export function useDataGridState(storageKey) {
  const fullKey = `${STORAGE_PREFIX}${storageKey}`;
  const [initialState, setInitialState] = useState(() => {
    try {
      const saved = localStorage.getItem(fullKey);
      return saved ? JSON.parse(saved) : undefined;
    } catch {
      return undefined;
    }
  });
  const apiRef = useGridApiRef();

  useLayoutEffect(() => {
    return () => {
      try {
        if (apiRef.current?.exportState) {
          const state = apiRef.current.exportState();
          if (state && typeof state === 'object') {
            localStorage.setItem(fullKey, JSON.stringify(state));
          }
        }
      } catch (e) {
        // ignore
      }
    };
  }, [fullKey, apiRef]);

  return { apiRef, initialState };
}
