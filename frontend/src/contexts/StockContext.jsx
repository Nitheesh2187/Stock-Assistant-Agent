import { createContext, useState, useCallback } from 'react';

export const StockContext = createContext(null);

export function StockProvider({ children }) {
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [selectedStockName, setSelectedStockName] = useState(null);
  const [chatDraft, setChatDraft] = useState('');

  const setSelectedStock = useCallback((symbol, name) => {
    setSelectedSymbol(symbol);
    setSelectedStockName(name);
  }, []);

  const clearSelectedStock = useCallback(() => {
    setSelectedSymbol(null);
    setSelectedStockName(null);
  }, []);

  return (
    <StockContext.Provider value={{ selectedSymbol, selectedStockName, setSelectedStock, clearSelectedStock, chatDraft, setChatDraft }}>
      {children}
    </StockContext.Provider>
  );
}
