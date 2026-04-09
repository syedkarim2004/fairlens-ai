import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { 
  CloudUpload, 
  Settings, 
  Play, 
  CheckCircle2, 
  AlertCircle,
  Search,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  ChevronRight,
  Edit2
} from 'lucide-react';
import { uploadCSV, runFullAudit, detectAuditConfig } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function Audit() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1: Upload, 2: Analyzing, 3: Review/Run
  const [file, setFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [autoConfig, setAutoConfig] = useState(null);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);

  // Loading checklist state
  const [checklist, setChecklist] = useState([
    { id: 1, text: 'Detecting target variable', status: 'pending' },
    { id: 2, text: 'Identifying sensitive attributes', status: 'pending' },
    { id: 3, text: 'Evaluating fairness risks', status: 'pending' }
  ]);

  const updateChecklist = (id, status) => {
    setChecklist(prev => prev.map(item => item.id === id ? { ...item, status } : item));
  };

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    
    setError(null);
    setFile(selectedFile);
    setIsUploading(true);
    
    try {
      // Step 1: Upload
      const resp = await uploadCSV(selectedFile);
      const fid = resp.file_id || resp.id;
      console.log(`[Zero-Click] File uploaded. ID: ${fid}`);
      setFileId(fid);
      setIsUploading(false);
      setStep(2);

      // Step 2: Auto Analysis
      await runAutonomousAnalysis(fid);
    } catch (err) {
      console.error(err);
      setError('Upload failed. Please check your network connection.');
      setIsUploading(false);
    }
  };

  const runAutonomousAnalysis = async (fid) => {
    // Fake progress for visual polish
    setTimeout(() => updateChecklist(1, 'active'), 500);
    
    try {
      const config = await detectAuditConfig(fid);
      
      // Simulate analysis steps
      setTimeout(() => updateChecklist(1, 'completed'), 1500);
      setTimeout(() => updateChecklist(2, 'active'), 1600);
      
      setTimeout(() => updateChecklist(2, 'completed'), 3000);
      setTimeout(() => updateChecklist(3, 'active'), 3100);
      
      setTimeout(() => {
        updateChecklist(3, 'completed');
        setAutoConfig(config);
        setStep(3);
      }, 4500);

    } catch (err) {
      console.error(err);
      setError('Auto-analysis failed. Please try a manual configuration or check your dataset format.');
      setStep(1);
    }
  };

  const handleStartAudit = async () => {
    if (!autoConfig) return;
    setIsRunning(true);
    try {
      console.log("[Zero-Click] Running full audit...", { fileId, autoConfig });
      const results = await runFullAudit(
        fileId, 
        autoConfig.target_column, 
        autoConfig.sensitive_attributes, 
        autoConfig.positive_value
      );
      
      const enrichedResults = {
        ...results,
        dataset_name: file?.name || 'Uploaded Dataset',
        timestamp: new Date().toISOString()
      };

      console.log("[Zero-Click] Audit complete. Navigating to results.", enrichedResults);
      sessionStorage.setItem('lastAuditResult', JSON.stringify(enrichedResults));
      navigate('/results');
    } catch (err) {
      console.error(err);
      setError('Audit execution failed. Please verify your dataset content.');
      setIsRunning(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="animate-fade-in" style={{ maxWidth: '840px', margin: '0 auto', paddingBottom: '40px' }}>
        <header style={{ marginBottom: '40px', textAlign: 'center' }}>
          <div style={{ 
            display: 'inline-flex', 
            alignItems: 'center', 
            gap: '8px', 
            padding: '4px 12px', 
            borderRadius: '20px', 
            background: 'var(--md-primary-container)', 
            color: 'var(--md-on-primary-container)', 
            fontSize: '12px', 
            fontWeight: 600, 
            marginBottom: '16px'
          }}>
            <Sparkles size={14} /> NEW: AUTONOMOUS CONFIGURATION
          </div>
          <h1 style={{ fontSize: '32px', fontWeight: 400, marginBottom: '8px', letterSpacing: '-0.02em' }}>Autonomous Fairness Audit</h1>
          <p style={{ color: 'var(--md-on-surface-variant)', fontSize: '16px' }}>
            Upload your dataset and let FairLens AI handle the configuration, trait detection, and risk evaluation.
          </p>
        </header>

        {error && (
            <div style={{ 
                background: '#FEEBEE', 
                color: 'var(--md-error)', 
                padding: '16px', 
                borderRadius: '12px', 
                marginBottom: '32px', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px',
                border: '1px solid #FFCDD2'
            }}>
                <AlertCircle size={20} />
                <span style={{ fontSize: '14px', fontWeight: 500 }}>{error}</span>
            </div>
        )}

        {/* STEP 1: UPLOAD */}
        {step === 1 && (
          <div className="md-card" style={{ 
            padding: '80px 40px', 
            border: '2px dashed var(--md-outline)',
            textAlign: 'center',
            background: 'white',
            transition: 'all 0.3s ease'
          }}>
            <div style={{ 
              width: '96px', 
              height: '96px', 
              borderRadius: '24px', 
              background: 'var(--md-surface-variant)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--md-primary)',
              margin: '0 auto 24px'
            }}>
              <CloudUpload size={48} strokeWidth={1.5} />
            </div>
            <h2 style={{ fontSize: '22px', fontWeight: 500, marginBottom: '8px', color: 'var(--md-on-surface)' }}>Ready for analysis?</h2>
            <p style={{ color: 'var(--md-on-surface-variant)', marginBottom: '32px', maxWidth: '400px', margin: '0 auto 32px' }}>
              Drop your CSV file here or select from your device. We'll automatically identify decision variables and sensitive traits.
            </p>
            
            <input 
              type="file" 
              accept=".csv" 
              id="csv-upload" 
              style={{ display: 'none' }} 
              onChange={handleFileUpload}
            />
            {isUploading ? (
               <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                 <div className="loading-spinner" style={{ width: '32px', height: '32px' }}></div>
                 <span style={{ fontSize: '15px', color: 'var(--md-primary)', fontWeight: 500 }}>Ingesting dataset...</span>
               </div>
            ) : (
              <label htmlFor="csv-upload" className="btn-filled" style={{ cursor: 'pointer', padding: '12px 32px' }}>
                Select Dataset
              </label>
            )}
          </div>
        )}

        {/* STEP 2: ANALYZING (Google-style Loading Screen) */}
        {step === 2 && (
          <div className="md-card animate-fade-in" style={{ padding: '64px 40px', textAlign: 'center' }}>
            <div className="loading-spinner" style={{ width: '56px', height: '56px', margin: '0 auto 32px' }}></div>
            <h3 style={{ fontSize: '24px', fontWeight: 400, marginBottom: '40px' }}>Analyzing your dataset...</h3>
            
            <div style={{ maxWidth: '320px', margin: '0 auto', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {checklist.map((item) => (
                <div key={item.id} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '16px',
                  opacity: item.status === 'pending' ? 0.3 : 1,
                  transition: 'opacity 0.3s ease'
                }}>
                  {item.status === 'completed' ? (
                    <CheckCircle2 size={22} color="var(--md-success)" />
                  ) : item.status === 'active' ? (
                    <div className="loading-spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div>
                  ) : (
                    <div style={{ width: '22px', height: '22px', border: '2px solid var(--md-outline)', borderRadius: '50%' }}></div>
                  )}
                  <span style={{ 
                    fontSize: '16px', 
                    fontWeight: item.status === 'active' ? 500 : 400,
                    color: item.status === 'completed' ? 'var(--md-on-surface)' : 'var(--md-on-surface-variant)'
                  }}>
                    {item.text}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* STEP 3: REVIEW / START */}
        {step === 3 && autoConfig && (
          <div className="animate-fade-in">
            <div className="md-card" style={{ padding: '40px', marginBottom: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
                <h3 style={{ fontSize: '20px', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <ShieldCheck size={24} color="var(--md-primary)" /> AI Detected Configuration
                </h3>
                <button className="btn-text" style={{ gap: '8px' }}>
                  <Edit2 size={16} /> Edit Manual
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '40px' }}>
                <div style={{ padding: '20px', background: 'var(--md-surface-variant)', borderRadius: '16px' }}>
                  <p style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '8px' }}>Target Variable</p>
                  <p style={{ fontSize: '18px', fontWeight: 500 }}>{autoConfig.target_column}</p>
                </div>
                <div style={{ padding: '20px', background: 'var(--md-surface-variant)', borderRadius: '16px' }}>
                  <p style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '8px' }}>Sensitive Traits</p>
                  <p style={{ fontSize: '18px', fontWeight: 500 }}>{autoConfig.sensitive_attributes.length} Detected</p>
                </div>
                <div style={{ padding: '20px', background: 'var(--md-surface-variant)', borderRadius: '16px' }}>
                  <p style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '8px' }}>Favorable Outcome</p>
                  <p style={{ fontSize: '18px', fontWeight: 500 }}>{autoConfig.positive_value}</p>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--md-outline-variant)', paddingTop: '32px' }}>
                 <p style={{ fontSize: '14px', color: 'var(--md-on-surface-variant)', marginBottom: '24px' }}>
                   {autoConfig.explanation}
                 </p>
                 <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '32px' }}>
                   {autoConfig.sensitive_attributes.map(trait => (
                     <span key={trait} style={{ 
                       padding: '6px 14px', 
                       background: 'var(--md-primary-container)', 
                       color: 'var(--md-on-primary-container)', 
                       borderRadius: '16px', 
                       fontSize: '13px', 
                       fontWeight: 500 
                     }}>
                       {trait}
                     </span>
                   ))}
                 </div>
              </div>

              <div style={{ textAlign: 'center' }}>
                {isRunning ? (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                    <div className="loading-spinner"></div>
                    <span style={{ fontWeight: 500 }}>Running Fairness Audit...</span>
                  </div>
                ) : (
                  <button className="btn-filled" onClick={handleStartAudit} style={{ width: '100%', height: '56px', fontSize: '16px' }}>
                    Continue to Results <ArrowRight size={20} style={{ marginLeft: '8px' }} />
                  </button>
                )}
              </div>
            </div>

            {autoConfig.risk_flags && autoConfig.risk_flags.length > 0 && (
                <div style={{ padding: '24px', borderRadius: '16px', background: '#FFFDF0', border: '1px solid #FFE082' }}>
                    <h4 style={{ fontSize: '15px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px', color: '#827717', marginBottom: '12px' }}>
                        <AlertCircle size={18} /> High-Level Risk Observations
                    </h4>
                    <ul style={{ paddingLeft: '20px', color: 'var(--md-on-surface-variant)', fontSize: '14px', lineHeight: '1.6' }}>
                        {autoConfig.risk_flags.map((risk, idx) => (
                            <li key={idx} style={{ marginBottom: '4px' }}>{risk}</li>
                        ))}
                    </ul>
                </div>
            )}
          </div>
        )}

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
          
          .animate-fade-in {
            animation: fadeIn 0.4s ease-out;
          }
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}</style>

      </div>
    </DashboardLayout>
  );
}

