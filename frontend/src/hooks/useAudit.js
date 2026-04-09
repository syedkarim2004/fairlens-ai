import { useState, useEffect, useRef, useCallback } from 'react';

/* ── useTypewriter ── */
export function useTypewriter(text, speed = 12) {
  const [displayed, setDisplayed] = useState('');
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    if (!text) { setDisplayed(''); setIsDone(true); return; }
    setDisplayed('');
    setIsDone(false);
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) { clearInterval(interval); setIsDone(true); }
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);

  return { displayed, isDone };
}

/* ── useTilt (3D hover) ── */
export function useTilt(maxTilt = 8) {
  const ref = useRef(null);

  const handleMove = useCallback((e) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    el.style.transform = `perspective(800px) rotateY(${x * maxTilt}deg) rotateX(${-y * maxTilt}deg) scale3d(1.02,1.02,1.02)`;
  }, [maxTilt]);

  const handleLeave = useCallback(() => {
    const el = ref.current;
    if (el) el.style.transform = 'perspective(800px) rotateY(0deg) rotateX(0deg) scale3d(1,1,1)';
  }, []);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.transition = 'transform 0.3s ease-out';
    el.addEventListener('mousemove', handleMove);
    el.addEventListener('mouseleave', handleLeave);
    return () => {
      el.removeEventListener('mousemove', handleMove);
      el.removeEventListener('mouseleave', handleLeave);
    };
  }, [handleMove, handleLeave]);

  return ref;
}

/* ── useAuditState ── */
export function useAuditState() {
  const [fileId, setFileId] = useState(null);
  const [fileName, setFileName] = useState('');
  const [columns, setColumns] = useState([]);
  const [targetColumn, setTargetColumn] = useState('decision');
  const [sensitiveColumns, setSensitiveColumns] = useState([]);
  const [auditResult, setAuditResult] = useState(null);
  const [compareResult, setCompareResult] = useState(null);
  const [positiveLabel, setPositiveLabel] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  return {
    fileId, setFileId,
    fileName, setFileName,
    columns, setColumns,
    targetColumn, setTargetColumn,
    positiveLabel, setPositiveLabel,
    sensitiveColumns, setSensitiveColumns,
    auditResult, setAuditResult,
    compareResult, setCompareResult,
    loading, setLoading,
    error, setError,
  };
}
