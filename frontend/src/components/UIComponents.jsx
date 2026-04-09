import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { 
  ShieldCheck, 
  Database, 
  Layers, 
  Zap, 
  Brain, 
  Check, 
  Loader2,
  FileSearch,
  Activity
} from 'lucide-react';

/**
 * Utility for Tailwind class merging
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// ── Google Style Skeleton ──
export function Skeleton({ className, ...props }) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

// ── Counting Stat (Material Style) ──
export function CountingStat({ value, duration = 1.5 }) {
  const [count, setCount] = useState(0);
  const nodeRef = useRef(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) setIsVisible(true);
    });
    if (nodeRef.current) observer.observe(nodeRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!isVisible) return;
    let start = 0;
    const end = parseFloat(value) || 0;
    if (start === end) { setCount(end); return; }
    
    let startTime = null;
    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / (duration * 1000), 1);
      const current = progress * (end - start) + start;
      setCount(current);
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [value, duration, isVisible]);

  return <span ref={nodeRef}>{count.toFixed(count % 1 === 0 ? 0 : 2)}</span>;
}

// ── Google style Loading Overlay ──
export const LoadingOverlay = ({ stage = 'ingest' }) => {
  const stages = [
    { id: 'ingest', text: 'Preparing dataset ingestion', icon: <Database /> },
    { id: 'detect', text: 'Scanning for sensitive attributes', icon: <FileSearch /> },
    { id: 'config', text: 'Configuring fairness protocols', icon: <Layers /> },
    { id: 'audit_groq', text: 'Executing bias detection engine', icon: <Zap /> },
    { id: 'audit_gemma', text: 'Deep reasoning optimization', icon: <Brain /> },
  ];

  const currentStageIndex = stages.findIndex(s => s.id === stage);
  const safeIndex = currentStageIndex === -1 ? 0 : currentStageIndex;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center p-6 bg-white/80 backdrop-blur-md"
    >
      <div className="w-full max-w-lg">
        <div className="flex flex-col items-center text-center mb-12">
          <div className="relative mb-6">
            <div className="h-20 w-20 rounded-full border-4 border-muted flex items-center justify-center">
              <Activity className="h-10 w-10 text-primary animate-pulse" />
            </div>
            <div className="absolute inset-0 h-20 w-20 rounded-full border-t-4 border-primary animate-spin" />
          </div>
          <h3 className="text-2xl font-medium text-foreground mb-2">Analyzing Fairness</h3>
          <p className="text-muted-foreground text-sm">Please wait while our neural engines process your data.</p>
        </div>

        <div className="space-y-3 bg-secondary/50 p-6 rounded-2xl border">
          {stages.map((s, idx) => (
            <div
              key={s.id}
              className={cn(
                "flex items-center gap-4 transition-all duration-300",
                idx === safeIndex ? "opacity-100 translate-x-2" : "opacity-40"
              )}
            >
              <div className={cn(
                "p-2 rounded-lg",
                idx === safeIndex ? "bg-primary text-white" : "bg-muted text-muted-foreground"
              )}>
                {React.cloneElement(s.icon, { size: 18 })}
              </div>
              <span className="text-sm font-medium">{s.text}</span>
              {idx < safeIndex && <Check size={16} className="ml-auto text-success" />}
              {idx === safeIndex && <Loader2 size={16} className="ml-auto text-primary animate-spin" />}
            </div>
          ))}
        </div>
        
        {/* Progress Bar */}
        <div className="mt-8 w-full bg-muted h-1 rounded-full overflow-hidden">
          <motion.div 
            className="bg-primary h-full"
            initial={{ width: 0 }}
            animate={{ width: `${((safeIndex + 1) / stages.length) * 100}%` }}
          />
        </div>
      </div>
    </motion.div>
  );
};

// ── Google style Risk Badge ──
export function RiskBadge({ level }) {
  const config = {
    HIGH: 'bg-red-50 text-red-700 border-red-200',
    MEDIUM: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    LOW: 'bg-green-50 text-green-700 border-green-200',
  };
  const c = config[level] || config.LOW;
  return (
    <span className={cn("px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border", c)}>
      {level} Risk
    </span>
  );
}
