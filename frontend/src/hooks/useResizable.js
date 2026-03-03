import { useState, useCallback, useEffect, useRef } from 'react';

export function useResizable({
  direction = 'horizontal',
  initialSize = 300,
  minSize = 100,
  maxSize = 800,
  storageKey = null,
  invertDelta = false,
}) {
  const [size, setSize] = useState(() => {
    if (storageKey) {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        const parsed = Number(stored);
        if (!isNaN(parsed) && parsed >= minSize && parsed <= maxSize) return parsed;
      }
    }
    return initialSize;
  });

  const isDraggingRef = useRef(false);
  const [isDragging, setIsDragging] = useState(false);
  const startPosRef = useRef(0);
  const startSizeRef = useRef(0);

  useEffect(() => {
    if (storageKey) {
      localStorage.setItem(storageKey, String(size));
    }
  }, [size, storageKey]);

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    isDraggingRef.current = true;
    setIsDragging(true);
    startPosRef.current = direction === 'horizontal' ? e.clientX : e.clientY;
    startSizeRef.current = size;
    document.body.classList.add('resizing');
    document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize';
  }, [direction, size]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDraggingRef.current) return;
      const currentPos = direction === 'horizontal' ? e.clientX : e.clientY;
      let delta = currentPos - startPosRef.current;
      if (invertDelta) delta = -delta;
      const newSize = Math.min(maxSize, Math.max(minSize, startSizeRef.current + delta));
      setSize(newSize);
    };

    const handleMouseUp = () => {
      if (!isDraggingRef.current) return;
      isDraggingRef.current = false;
      setIsDragging(false);
      document.body.classList.remove('resizing');
      document.body.style.cursor = '';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [direction, invertDelta, minSize, maxSize]);

  return { size, isDragging, handleMouseDown };
}
