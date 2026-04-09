import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { 
  Download, 
  Share2, 
  AlertCircle, 
  CheckCircle2, 
  Brain, 
  BarChart3, 
  Layers, 
  Lightbulb,
  ArrowRight,
  TrendingUp,
  Search,
  Database,
  Activity,
  Cpu,
  Clock,
  Zap,
  AlertTriangle
} from 'lucide-react';
import { getAuditReport, applyMitigation } from '../services/api';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell,
  PieChart,
  Pie
} from 'recharts';

export default function Results() {
  const [activeTab, setActiveTab] = useState('overview');
  const [report, setReport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Thinking Experience State
  const [isThinking, setIsThinking] = useState(false);
  const [analysisStage, setAnalysisStage] = useState(0);
  const [showInsights, setShowInsights] = useState(false);
  
  // Mitigation States
  const [isMitigating, setIsMitigating] = useState(false);
  const [mitigationResult, setMitigationResult] = useState(null);
  const [mitigationError, setMitigationError] = useState(null);

  useEffect(() => {
    const loadReport = () => {
      try {
        setIsLoading(true);
        console.log("[Results] Loading audit data from session storage...");
        const saved = sessionStorage.getItem('lastAuditResult');
        
        if (saved) {
          const rawData = JSON.parse(saved);
          console.log("[Results] Raw data received:", rawData);
          
          if (rawData.status === 'error') {
            setError(rawData.message || 'Audit execution failed on the server.');
            setIsLoading(false);
            return;
          }

          const normalized = normalizeReportData(rawData);
          console.log("[Results] Normalized data:", normalized);
          setReport(normalized);
          
          // Trigger the thinking sequence if we have data
          if (normalized) {
            startAnalysisSequence();
          }
        } else {
          console.warn("[Results] No audit data found in session storage.");
          setError("No audit results found. Please run an audit first.");
        }
      } catch (err) {
        console.error("[Results] Error loading report:", err);
        setError("Failed to parse audit results.");
      } finally {
        setIsLoading(false);
      }
    };

    loadReport();
  }, []);

  const startAnalysisSequence = () => {
    setIsThinking(true);
    setAnalysisStage(0);
    
    const stages = [
      { msg: "Analyzing dataset structure...", delay: 700 },
      { msg: "Identifying sensitive attributes...", delay: 700 },
      { msg: "Evaluating outcome parity...", delay: 700 },
      { msg: "Synthesizing deep insights...", delay: 700 }
    ];

    let currentDelay = 0;
    stages.forEach((stage, index) => {
      currentDelay += stage.delay;
      setTimeout(() => {
        setAnalysisStage(index + 1);
        if (index === stages.length - 1) {
          // Final stage reached
          setTimeout(() => {
            setIsThinking(false);
            // After report is shown, wait 1.5s to show insights
            setTimeout(() => {
              setShowInsights(true);
            }, 1500);
          }, 400);
        }
      }, currentDelay);
    });
  };

  const normalizeReportData = (raw) => {
    // 1. Detect and handle New Deterministic Schema
    if (raw.summary && raw.attributes) {
      console.log("[Results] Using New Deterministic Schema");
      const metrics = {};
      raw.attributes.forEach(attr => {
        metrics[attr.name] = {
          dir: attr.dir ?? 1.0,
          spd: attr.spd ?? 0.0,
          risk: attr.risk ?? 'LOW',
          baseline: { 
            group: attr.baseline_group || 'Baseline', 
            rate: attr.baseline_rate || 0.0 
          },
          minority: { 
            group: attr.minority_group || 'Minority', 
            rate: attr.minority_rate || 0.0 
          },
          sample_sizes: attr.sample_sizes || {},
          deep_insight: attr.deep_insight || null,
          interpretation: attr.interpretation
        };
      });

      return {
        overall_grade: raw.summary.overall_grade || 'N/A',
        risk_score: raw.summary.score || 0,
        dataset_name: raw.dataset_name || 'Deterministic Fairness Audit',
        metrics: metrics,
        deep_analysis: raw.summary.deep_analysis || { overview: "Deterministic overview complete." },
        ai_analysis: {
          groq: raw.summary.deep_analysis?.overview || "Deterministic overview complete.",
          gemma: "LLM analysis disabled for strict determinism."
        },
        recommendations: raw.recommendations || [],
        file_id: raw.metadata?.file_id
      };
    }

    // 2. Fallback for Legacy Heuristic Schema
    const metrics = {};
    const rawMetrics = raw.bias_results || raw.bias_summary || {};
    
    Object.entries(rawMetrics).forEach(([attr, data]) => {
      metrics[attr] = {
        dir: data.disparate_impact_ratio ?? data.dir ?? 1.0,
        spd: data.statistical_parity_difference ?? data.spd ?? 0.0,
        risk: data.risk_level ?? data.risk ?? 'LOW',
        baseline: { 
          group: data.baseline_group ?? (data.baseline?.group || 'Baseline'), 
          rate: data.baseline_positive_rate ?? (data.baseline?.rate || 0.0)
        },
        minority: { 
          group: data.minority_group ?? (data.minority?.group || 'Minority'), 
          rate: data.minority_positive_rate ?? (data.minority?.rate || 0.0)
        }
      };
    });

    return {
      overall_grade: raw.overall_fairness_grade ?? raw.overall_grade ?? 'N/A',
      risk_score: raw.overall_risk_score ?? raw.risk_score ?? 0,
      dataset_name: raw.dataset_name || 'Audit Report',
      metrics: metrics,
      ai_analysis: {
        groq: raw.groq_explanation || raw.gemini_explanation || raw.ai_analysis?.groq || "AI analysis unavailable.",
        gemma: raw.gemma4_explanation || raw.ai_analysis?.gemma || "Additional insights pending."
      },
      recommendations: raw.recommendations || [],
      file_id: raw.metadata?.file_id || raw.file_id
    };
  };

  const safePercent = (val) => {
    if (val === null || val === undefined || isNaN(val) || !isFinite(val)) return "N/A";
    return (val * 100).toFixed(1) + "%";
  };

  const safeFloat = (val, decimals = 3) => {
    if (val === null || val === undefined || isNaN(val) || !isFinite(val)) return "N/A";
    return Number(val).toFixed(decimals);
  };

  const handleExportPDF = async () => {
    if (!report?.file_id) {
       alert("No file reference found for this audit. Please re-run the analysis.");
       return;
    }
    
    try {
      setIsLoading(true);
      const url = `http://localhost:8000/api/report/v2/generate/${report.file_id}`;
      console.log(`[Results] Exporting PDF from: ${url}`);
      
      const response = await fetch(url);
      if (!response.ok) throw new Error("PDF generation failed on server.");
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', `FairLens_Audit_${report.overall_grade}_${report.file_id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      console.error("[Results] PDF Export Error:", err);
      alert("Failed to download PDF report. Is the backend server running?");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: '24px' }}>
          <div className="loading-spinner" style={{ width: '48px', height: '48px' }}></div>
          <p style={{ color: 'var(--md-on-surface-variant)', fontSize: '16px', fontWeight: 500 }}>Retrieving analysis results...</p>
        </div>
        <style>{`
          .loading-spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--md-surface-container-high);
            border-top-color: var(--md-primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
          }
          @keyframes spin { to { transform: rotate(360deg); } }
        `}</style>
      </DashboardLayout>
    );
  }

  const handleApplyMitigation = async (methodName) => {
    setIsMitigating(true);
    setMitigationError(null);
    
    // Extract first sensitive attribute for mitigation demo
    const sensitiveAttr = report?.attributes?.[0]?.name;
    const targetCol = report?.metadata?.target_column;
    const fileId = report?.metadata?.file_id;

    if (!sensitiveAttr || !targetCol || !fileId) {
      setMitigationError("Missing required metadata to apply mitigation.");
      setIsMitigating(false);
      return;
    }

    try {
      // Map display name to backend method name
      const methodMap = {
        'Reweigh Training Data': 'reweigh',
        'Feature Anonymization': 'anonymize',
        'Threshold Optimization': 'threshold',
        'Model Retraining': 'retrain'
      };

      const result = await applyMitigation(
        fileId, 
        methodMap[methodName] || methodName.toLowerCase(), 
        targetCol, 
        sensitiveAttr
      );
      
      setMitigationResult(result);
      setActiveTab('recommendations'); // Ensure we stay/go to this tab
      
      // Smooth scroll to top of content to see results
      window.scrollTo({ top: 300, behavior: 'smooth' });
      
    } catch (err) {
      console.error("Mitigation failed", err);
      setMitigationError(err.response?.data?.detail || "Mitigation transformation failed.");
    } finally {
      setIsMitigating(false);
    }
  };

  const downloadMitigatedData = () => {
    if (!mitigationResult?.mitigated_file_id) return;
    
    const fileId = mitigationResult.mitigated_file_id;
    const url = `/api/audit/download/${fileId}`;
    
    console.log(`[Results] Triggering download: ${url}`);
    
    // Create a temporary link to trigger the download
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `FairLens_Mitigated_${fileId}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (error) {
    return (
      <DashboardLayout>
        <div style={{ maxWidth: '600px', margin: '60px auto', textAlign: 'center' }}>
          <div style={{ color: 'var(--md-error)', marginBottom: '24px' }}>
            <AlertCircle size={64} strokeWidth={1.5} />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 400, marginBottom: '12px' }}>Analysis Unavailable</h2>
          <p style={{ color: 'var(--md-on-surface-variant)', marginBottom: '32px', lineHeight: '1.6' }}>{error}</p>
          <button className="btn-filled" onClick={() => window.location.href = '/dashboard'}>
            Go Back to Dashboard
          </button>
        </div>
      </DashboardLayout>
    );
  }

  if (isThinking) {
    const stages = [
      { id: 0, label: "Initializing Engine", icon: Database },
      { id: 1, label: "Analyzing Dataset structure", icon: Search },
      { id: 2, label: "Identifying Attributes", icon: Activity },
      { id: 3, label: "Calculating Metrics", icon: Cpu },
      { id: 4, label: "Generating Insights", icon: Brain }
    ];

    return (
      <DashboardLayout>
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center', 
          minHeight: '60vh',
          padding: '40px'
        }}>
          <div style={{ maxWidth: '500px', width: '100%' }}>
            <div style={{ textAlign: 'center', marginBottom: '48px' }}>
              <div style={{ 
                width: '64px', 
                height: '64px', 
                background: 'var(--md-primary-container)', 
                color: 'var(--md-on-primary-container)',
                borderRadius: '16px', 
                display: 'inline-flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                marginBottom: '24px',
                animation: 'pulse 2s infinite'
              }}>
                <Brain size={32} />
              </div>
              <h2 style={{ fontSize: '24px', fontWeight: 500, color: 'var(--md-on-surface)' }}>
                Deep Fairness Audit in Progress
              </h2>
              <p style={{ color: 'var(--md-on-surface-variant)', marginTop: '8px' }}>
                Evaluating statistical parity and disparate impact ratios...
              </p>
            </div>

            <div style={{ 
              background: 'var(--md-surface-container-low)', 
              borderRadius: '24px', 
              padding: '32px',
              border: '1px solid var(--md-outline-variant)'
            }}>
              {stages.map((s, idx) => {
                const isComplete = analysisStage > idx;
                const isActive = analysisStage === idx;
                
                return (
                  <div key={s.id} style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '16px', 
                    marginBottom: idx === stages.length - 1 ? 0 : '24px',
                    opacity: isComplete || isActive ? 1 : 0.3,
                    transition: 'opacity 0.3s ease'
                  }}>
                    <div style={{ 
                      width: '32px', 
                      height: '32px', 
                      borderRadius: '50%', 
                      background: isComplete ? 'var(--md-success)' : isActive ? 'var(--md-primary)' : 'var(--md-surface-container-high)',
                      color: isComplete || isActive ? 'white' : 'var(--md-on-surface-variant)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transition: 'all 0.3s ease'
                    }}>
                      {isComplete ? <CheckCircle2 size={18} /> : <s.icon size={18} />}
                    </div>
                    <div style={{ flex: 1 }}>
                      <p style={{ 
                        fontSize: '15px', 
                        fontWeight: isActive ? 600 : 400,
                        color: isActive ? 'var(--md-primary)' : 'var(--md-on-surface)'
                      }}>
                        {s.label}
                      </p>
                    </div>
                    {isActive && (
                      <div className="dot-flashing"></div>
                    )}
                  </div>
                );
              })}
            </div>

            <div style={{ marginTop: '32px', height: '4px', background: 'var(--md-surface-container-high)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ 
                width: `${(analysisStage / (stages.length - 1)) * 100}%`, 
                height: '100%', 
                background: 'var(--md-primary)',
                transition: 'width 0.5s ease'
              }}></div>
            </div>
          </div>
        </div>
        <style>{`
          .dot-flashing {
            position: relative;
            width: 6px;
            height: 6px;
            border-radius: 5px;
            background-color: var(--md-primary);
            color: var(--md-primary);
            animation: dotFlashing 1s infinite linear alternate;
            animation-delay: .5s;
          }
          .dot-flashing::before, .dot-flashing::after {
            content: '';
            display: inline-block;
            position: absolute;
            top: 0;
          }
          .dot-flashing::before {
            left: -12px;
            width: 6px;
            height: 6px;
            border-radius: 5px;
            background-color: var(--md-primary);
            color: var(--md-primary);
            animation: dotFlashing 1s infinite alternate;
            animation-delay: 0s;
          }
          .dot-flashing::after {
            left: 12px;
            width: 6px;
            height: 6px;
            border-radius: 5px;
            background-color: var(--md-primary);
            color: var(--md-primary);
            animation: dotFlashing 1s infinite alternate;
            animation-delay: 1s;
          }
          @keyframes dotFlashing {
            0% { background-color: var(--md-primary); }
            50%, 100% { background-color: var(--md-surface-container-high); }
          }
          @keyframes pulse {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(var(--md-primary-rgb), 0.4); }
            70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(var(--md-primary-rgb), 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(var(--md-primary-rgb), 0); }
          }
          .animate-fade-in { animation: fadeIn 0.6s ease-out forwards; }
          @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
          
          .shimmer {
            background: linear-gradient(90deg, var(--md-surface-container) 25%, var(--md-surface-container-high) 50%, var(--md-surface-container) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
          }
          @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
        `}</style>
      </DashboardLayout>
    );
  }

  if (!report && !isLoading && !error) {
    return (
      <DashboardLayout>
        <div style={{ maxWidth: '600px', margin: '60px auto', textAlign: 'center' }}>
          <div style={{ color: 'var(--md-on-surface-variant)', marginBottom: '24px' }}>
            <BarChart3 size={64} strokeWidth={1.5} />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 400, marginBottom: '12px' }}>No Report Data</h2>
          <p style={{ color: 'var(--md-on-surface-variant)', marginBottom: '32px', lineHeight: '1.6' }}>
            We couldn't find any recent audit data. Please return to the dashboard and upload a file to start a new analysis.
          </p>
          <button className="btn-filled" onClick={() => window.location.href = '/dashboard'}>
            Go to Dashboard
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="animate-fade-in">
        {/* Top Summary Strip */}
        <div className="md-card" style={{ 
          marginBottom: '24px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          padding: '24px 32px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
            <div style={{ 
              width: '80px', 
              height: '80px', 
              borderRadius: '50%', 
              background: report?.overall_grade === 'A' ? 'var(--md-success-container)' : 
                          report?.overall_grade === 'C' ? 'var(--md-warning-container)' : 'var(--md-error-container)',
              color: report?.overall_grade === 'A' ? 'var(--md-on-success-container)' : 
                     report?.overall_grade === 'C' ? '#856404' : 'var(--md-on-error-container)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '40px',
              fontFamily: 'var(--md-font-display)',
              fontWeight: 700
            }}>
              {report?.overall_grade}
            </div>
            <div>
              <h1 style={{ fontSize: '22px', fontWeight: 500, marginBottom: '4px' }}>{report?.dataset_name}</h1>
              <p style={{ color: 'var(--md-on-surface-variant)', fontSize: '14px' }}>
                Audit completed • {Object.keys(report?.metrics || {}).length} attributes analyzed
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn-outlined"><Share2 size={18} /> Share</button>
            <button 
              className="btn-filled" 
              onClick={handleExportPDF}
              disabled={isLoading}
            >
              <Download size={18} /> {isLoading ? 'Generating...' : 'Export PDF'}
            </button>
          </div>
        </div>

        {/* Tab Bar */}
        <div className="md-tabs" style={{ marginBottom: '32px' }}>
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'technical', label: 'Technical Metrics', icon: Layers },
            { id: 'insights', label: 'AI Insights', icon: Brain },
            { id: 'recommendations', label: 'Recommendations', icon: Lightbulb }
          ].map(tab => (
            <div 
              key={tab.id}
              className={`md-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <tab.icon size={18} />
              {tab.label}
            </div>
          ))}
        </div>

        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
            {Object.entries(report?.metrics || {}).map(([attr, data]) => (
              <div key={attr} className="md-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
                  <h3 style={{ textTransform: 'capitalize', fontSize: '18px' }}>{attr}</h3>
                  <div style={{ 
                    padding: '4px 12px', 
                    borderRadius: '16px', 
                    fontSize: '12px', 
                    fontWeight: 500,
                    background: data.risk === 'HIGH' ? 'var(--md-error-container)' : 'var(--md-success-container)',
                    color: data.risk === 'HIGH' ? 'var(--md-on-error-container)' : 'var(--md-on-success-container)'
                  }}>
                    {data.risk} RISK
                  </div>
                </div>

                <div style={{ marginBottom: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px' }}>
                    <span>Disparate Impact Ratio</span>
                    <span style={{ fontWeight: 500, color: data.dir < 0.8 ? 'var(--md-error)' : 'var(--md-on-surface)' }}>
                      {safeFloat(data.dir)}
                    </span>
                  </div>
                  <div style={{ height: '8px', background: 'var(--md-surface-container-high)', borderRadius: '4px', overflow: 'hidden', position: 'relative' }}>
                    <div style={{ 
                      width: `${Math.min(data.dir * 100, 100)}%`, 
                      height: '100%', 
                      background: data.dir < 0.8 ? 'var(--md-error)' : 'var(--md-primary)' 
                    }}></div>
                    <div style={{ position: 'absolute', left: '80%', top: 0, bottom: 0, width: '2px', background: 'var(--md-on-surface-variant)', opacity: 0.3 }}></div>
                  </div>
                  <p style={{ fontSize: '11px', color: 'var(--md-on-surface-variant)', marginTop: '4px' }}>Threshold: 0.80 (80% Rule)</p>
                </div>

                <div style={{ 
                  background: 'var(--md-surface-container)', 
                  padding: '16px', 
                  borderRadius: '12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <p style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)' }}>Pos. Rate ({data.baseline.group})</p>
                    <p style={{ fontSize: '18px', fontWeight: 500 }}>{safePercent(data.baseline.rate)}</p>
                  </div>
                  <ArrowRight size={20} color="var(--md-on-surface-variant)" />
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)' }}>Pos. Rate ({data.minority.group})</p>
                    <p style={{ fontSize: '18px', fontWeight: 500, color: data.dir < 0.8 ? 'var(--md-error)' : 'var(--md-on-surface)' }}>
                      {safePercent(data.minority.rate)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TECHNICAL METRICS TAB */}
        {activeTab === 'technical' && (
          <div className="space-y-8 animate-fade-in">
            <div className="md-card">
              <h3 style={{ fontSize: '18px', fontWeight: 500, marginBottom: '24px' }}>Statistical Parity Difference (SPD)</h3>
              <div style={{ height: '300px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    layout="vertical" 
                    data={Object.entries(report?.metrics || {}).map(([name, m]) => ({ 
                      name, 
                      spd: m.spd,
                      fill: Math.abs(m.spd) > 0.1 ? 'var(--md-error)' : 'var(--md-primary)'
                    }))}
                    margin={{ left: 40, right: 40, top: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="var(--md-surface-container-high)" />
                    <XAxis type="number" domain={[-1, 1]} hide />
                    <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} width={100} style={{ fontSize: '12px' }} />
                    <Tooltip 
                      cursor={{ fill: 'transparent' }} 
                      contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                    />
                    <Bar dataKey="spd" radius={[0, 4, 4, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)', marginTop: '16px', textAlign: 'center' }}>
                SPD measures the gap in positive outcomes between groups. Ideal = 0.
              </p>
            </div>

            <div className="md-card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--md-surface-container-high)' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 500 }}>Attribute Deep Dive</h3>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                  <thead>
                    <tr style={{ background: 'var(--md-surface-container)', textAlign: 'left' }}>
                      <th style={{ padding: '16px 32px', fontWeight: 500 }}>Attribute</th>
                      <th style={{ padding: '16px 12px', fontWeight: 500 }}>Populations (B/M)</th>
                      <th style={{ padding: '16px 12px', fontWeight: 500 }}>Raw Rates (B/M)</th>
                      <th style={{ padding: '16px 12px', fontWeight: 500 }}>SPD</th>
                      <th style={{ padding: '16px 32px', fontWeight: 500, textAlign: 'right' }}>DIR Ratio</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(report?.metrics || {}).map(([attr, data]) => {
                       const bSize = data.sample_sizes?.baseline || 0;
                       const mSize = data.sample_sizes?.minority || 0;
                       return (
                        <tr key={attr} style={{ borderBottom: '1px solid var(--md-surface-container-high)' }}>
                          <td style={{ padding: '16px 32px', fontWeight: 500, textTransform: 'capitalize' }}>{attr}</td>
                          <td style={{ padding: '16px 12px', color: 'var(--md-on-surface-variant)' }}>
                            {bSize} / {mSize}
                          </td>
                          <td style={{ padding: '16px 12px' }}>
                            {safePercent(data.baseline.rate)} / {safePercent(data.minority.rate)}
                          </td>
                          <td style={{ padding: '16px 12px', fontWeight: 500, color: Math.abs(data.spd) > 0.1 ? 'var(--md-error)' : 'inherit' }}>
                            {safeFloat(data.spd)}
                          </td>
                          <td style={{ padding: '16px 32px', textAlign: 'right', fontWeight: 700, color: data.dir < 0.8 ? 'var(--md-error)' : 'var(--md-primary)' }}>
                            {safeFloat(data.dir)}
                          </td>
                        </tr>
                       );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* AI INSIGHTS TAB */}
        {activeTab === 'insights' && (
          <div className="space-y-6 animate-fade-in">
            {!showInsights ? (
              <>
                <div className="md-card shimmer" style={{ height: '120px', borderLeft: '4px solid var(--md-primary)' }}></div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                  <div className="md-card shimmer" style={{ height: '180px' }}></div>
                  <div className="md-card shimmer" style={{ height: '180px' }}></div>
                </div>
                <p style={{ textAlign: 'center', color: 'var(--md-on-surface-variant)', fontSize: '14px', fontStyle: 'italic' }}>
                  <Clock size={14} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />
                  Synthesizing deep interpretations based on calculated thresholds...
                </p>
              </>
            ) : (
              <>
                {/* Overview Card */}
                <div className="md-card animate-fade-in" style={{ borderLeft: '4px solid var(--md-primary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <div style={{ width: '32px', height: '32px', background: 'var(--md-primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
                      <TrendingUp size={18} />
                    </div>
                    <h3 style={{ fontSize: '18px', fontWeight: 500 }}>Audit Overview</h3>
                  </div>
                  <p style={{ fontSize: '16px', lineHeight: '1.6', color: 'var(--md-on-surface)' }}>
                    {report?.deep_analysis?.overview}
                  </p>
                </div>

                {/* Granular Insights Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                  {Object.entries(report?.metrics || {}).map(([attr, data], idx) => {
                    if (!data.deep_insight) return null;
                    const status = data.deep_insight.status || 'LOW';
                    
                    let accentColor = 'var(--md-success)';
                    if (status === 'SEVERE') accentColor = 'var(--md-error)';
                    else if (status === 'HIGH') accentColor = 'var(--md-error)';
                    else if (status === 'MEDIUM') accentColor = 'var(--md-warning)';

                    return (
                      <div key={attr} className="md-card animate-fade-in" style={{ 
                        borderTop: `4px solid ${accentColor}`,
                        animationDelay: `${idx * 0.1}s`
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: accentColor }}></div>
                            <h4 style={{ fontSize: '14px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{attr}</h4>
                          </div>
                          <span style={{ 
                            fontSize: '10px', 
                            fontWeight: 700, 
                            padding: '4px 8px', 
                            borderRadius: '4px',
                            background: accentColor,
                            color: 'white'
                          }}>
                            {status}
                          </span>
                        </div>
                        <p style={{ fontSize: '15px', fontWeight: 500, marginBottom: '8px', color: 'var(--md-on-surface)' }}>
                          {data.deep_insight.insight}
                        </p>
                        <p style={{ fontSize: '13px', color: 'var(--md-on-surface-variant)', lineHeight: '1.5' }}>
                          {data.deep_insight.reason}
                        </p>
                      </div>
                    );
                  })}
                </div>

                <div className="md-card" style={{ background: 'var(--md-surface-container-low)', border: '1px dashed var(--md-outline)' }}>
                  <p style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)', textAlign: 'center' }}>
                    Note: These insights are generated using a deterministic rules engine to ensure 100% audit reproducibility.
                  </p>
                </div>
              </>
            )}
          </div>
        )}

        {/* RECOMMENDATIONS TAB */}
        {activeTab === 'recommendations' && (
          <div className="space-y-8 animate-fade-in">
            {/* Mitigation Result Success Card */}
            {mitigationResult && (
              <div className="md-card animate-fade-in" style={{ 
                background: 'var(--md-success-container)', 
                border: '1px solid var(--md-success)',
                padding: '32px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
                  <div style={{ display: 'flex', gap: '16px' }}>
                    <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--md-success)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Zap size={24} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '20px', fontWeight: 600, color: '#1B5E20' }}>Mitigation Successful!</h3>
                      <p style={{ color: '#2E7D32', fontSize: '15px' }}>
                        The <strong>{mitigationResult.mitigation_applied}</strong> transformation has been applied to the dataset.
                      </p>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--md-success)' }}>
                      {mitigationResult.improvement}
                    </div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: '#2E7D32', textTransform: 'uppercase' }}>
                      Fairness Improvement
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
                   <div style={{ background: 'white', padding: '20px', borderRadius: '16px', border: '1px solid rgba(0,0,0,0.05)' }}>
                      <p style={{ fontSize: '12px', fontWeight: 700, color: 'var(--md-on-surface-variant)', marginBottom: '12px' }}>BEFORE MITIGATION</p>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontSize: '14px' }}>Disparate Impact Ratio</span>
                        <span style={{ fontWeight: 600 }}>{mitigationResult.before.DIR.toFixed(3)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '14px' }}>Stat. Parity Difference</span>
                        <span style={{ fontWeight: 600 }}>{mitigationResult.before.SPD.toFixed(3)}</span>
                      </div>
                   </div>
                   <div style={{ background: 'white', padding: '20px', borderRadius: '16px', border: '1px solid rgba(0,0,0,0.05)' }}>
                      <p style={{ fontSize: '12px', fontWeight: 700, color: 'var(--md-primary)', marginBottom: '12px' }}>AFTER MITIGATION ✨</p>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontSize: '14px' }}>Disparate Impact Ratio</span>
                        <span style={{ fontWeight: 600, color: 'var(--md-success)' }}>{mitigationResult.after.DIR.toFixed(3)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '14px' }}>Stat. Parity Difference</span>
                        <span style={{ fontWeight: 600, color: 'var(--md-success)' }}>{mitigationResult.after.SPD.toFixed(3)}</span>
                      </div>
                   </div>
                </div>

                <div style={{ display: 'flex', gap: '16px' }}>
                  <button onClick={downloadMitigatedData} className="btn-filled" style={{ gap: '8px', background: 'var(--md-success)' }}>
                    <Download size={18} /> Download Mitigated CSV
                  </button>
                  <button onClick={() => setMitigationResult(null)} className="btn-text">Dismiss</button>
                </div>
              </div>
            )}

            {mitigationError && (
              <div className="md-card" style={{ background: '#FFF5F5', border: '1px solid var(--md-error)', color: 'var(--md-error)', padding: '16px', display: 'flex', gap: '12px' }}>
                <AlertTriangle size={20} />
                <p style={{ fontWeight: 500 }}>{mitigationError}</p>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              {(report.recommendations && report.recommendations.length > 0 ? report.recommendations : [
                { title: 'Reweigh Training Data', desc: 'Apply sample weights to minority groups to balance protected class outcomes.', color: 'var(--md-primary)', p: 'P1' },
                { title: 'Feature Anonymization', desc: 'Remove proxy variables like Zip Code that correlate highly with sensitive attributes.', color: 'var(--md-success)', p: 'P2' },
                { title: 'Threshold Optimization', desc: 'Adjust classification cut-offs per group to achieve Equal Opportunity.', color: 'var(--md-warning)', p: 'P1' },
                { title: 'Model Retraining', desc: 'Incorporate fairness constraints into the loss function during model training.', color: 'var(--md-error)', p: 'P3' }
              ]).map(rec => (
                <div key={rec.title} className="md-card" style={{ display: 'flex', gap: '20px', minHeight: '160px', opacity: isMitigating ? 0.5 : 1 }}>
                  <div style={{ 
                    width: '48px', 
                    height: '48px', 
                    borderRadius: '12px', 
                    background: rec.color || 'var(--md-primary)', 
                    opacity: 0.1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}></div>
                  <div style={{ position: 'relative', flex: 1 }}>
                    <div style={{ 
                      position: 'absolute', 
                      top: '-36px', 
                      left: '-34px',
                      color: rec.color || 'var(--md-primary)'
                    }}>
                      <Lightbulb size={24} />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <h3 style={{ fontSize: '16px', fontWeight: 500 }}>{rec.title}</h3>
                      <span style={{ fontSize: '10px', fontWeight: 700, color: rec.color || 'var(--md-primary)' }}>{rec.p || 'P1'}</span>
                    </div>
                    <p style={{ fontSize: '14px', color: 'var(--md-on-surface-variant)', marginBottom: '16px', lineHeight: '1.5' }}>{rec.desc}</p>
                    <button 
                      className="btn-text" 
                      style={{ padding: 0 }}
                      onClick={() => handleApplyMitigation(rec.title)}
                      disabled={isMitigating}
                    >
                      {isMitigating ? 'Processing...' : 'Apply Mitigations'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
