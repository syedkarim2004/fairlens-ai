import React from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { 
  ArrowLeftRight, 
  CheckCircle2, 
  AlertCircle, 
  ShieldCheck, 
  Zap,
  Check
} from 'lucide-react';

export default function Compare() {
  const categories = [
    { 
      name: 'Primary Bias Type', 
      groq: 'Historical Gender Bias', 
      gemma: 'Historical Gender Bias', 
      match: true 
    },
    { 
      name: 'Severity Assessment', 
      groq: 'Critical (Violation of 80% Rule)', 
      gemma: 'High Risk (Disparate Impact Found)', 
      match: true 
    },
    { 
      name: 'Confidence Level', 
      groq: '94%', 
      gemma: '89%', 
      match: false 
    },
    { 
      name: 'Key Recommendation', 
      groq: 'Reweigh minority samples', 
      gemma: 'Anonymize proxy variables', 
      match: false 
    }
  ];

  return (
    <DashboardLayout>
      <div className="animate-fade-in">
        <header style={{ marginBottom: '40px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: 400, marginBottom: '8px' }}>Model Comparison</h1>
          <p style={{ color: 'var(--md-on-surface-variant)' }}>Comparing Groq Llama-3 and Google Gemma fairness interpretations.</p>
        </header>

        {/* Comparison Grid */}
        <div style={{ position: 'relative' }}>
          {/* Header Row */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '1fr 60px 1fr', 
            gap: '24px',
            marginBottom: '32px'
          }}>
            <div className="md-card" style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '16px', 
              borderTop: '4px solid #000',
              padding: '24px'
            }}>
              <div style={{ width: '40px', height: '40px', background: '#000', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 700 }}>G</div>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 500 }}>Groq Analysis</h3>
                <p style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)' }}>Llama-3.3 70B Engine</p>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ 
                width: '40px', 
                height: '40px', 
                borderRadius: '50%', 
                background: 'var(--md-surface-container-high)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '12px',
                color: 'var(--md-on-surface-variant)'
              }}>VS</div>
            </div>

            <div className="md-card" style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '16px', 
              borderTop: '4px solid var(--md-primary)',
              padding: '24px'
            }}>
              <div style={{ width: '40px', height: '40px', background: 'var(--md-primary)', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
                <Zap size={24} />
              </div>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 500 }}>Gemma Engine</h3>
                <p style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)' }}>Google Cloud ML Services</p>
              </div>
            </div>
          </div>

          {/* Rows */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {categories.map((cat) => (
              <div key={cat.name} style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr 60px 1fr', 
                gap: '24px',
                padding: '20px 0',
                borderBottom: '1px solid var(--md-outline-variant)'
              }}>
                <div style={{ textAlign: 'center', padding: '0 16px' }}>
                  <p style={{ fontSize: '11px', fontWeight: 500, color: 'var(--md-on-surface-variant)', marginBottom: '8px', textTransform: 'uppercase' }}>{cat.name}</p>
                  <p style={{ fontSize: '15px', fontWeight: 500 }}>{cat.groq}</p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {cat.match ? (
                    <div style={{ color: 'var(--md-success)' }}><Check size={20} /></div>
                  ) : (
                    <div style={{ color: 'var(--md-warning)' }}><AlertCircle size={20} /></div>
                  )}
                </div>

                <div style={{ textAlign: 'center', padding: '0 16px' }}>
                  <p style={{ fontSize: '11px', fontWeight: 500, color: 'var(--md-on-surface-variant)', marginBottom: '8px', textTransform: 'uppercase' }}>{cat.name}</p>
                  <p style={{ fontSize: '15px', fontWeight: 500 }}>{cat.gemma}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Consensus Section */}
          <div className="md-card" style={{ marginTop: '40px', background: 'var(--md-success-container)', border: 'none' }}>
            <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
                <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <ShieldCheck size={32} color="var(--md-success)" />
                </div>
                <div>
                    <h3 style={{ fontSize: '18px', fontWeight: 500, color: 'var(--md-on-success-container)', marginBottom: '4px' }}>Model Consensus Reached</h3>
                    <p style={{ fontSize: '14px', color: 'var(--md-on-success-container)', opacity: 0.8 }}>
                        Both Groq and Gemma agree on the presence of **Critical Gender Bias**. 
                        Automated remediation is recommended.
                    </p>
                </div>
                <button className="btn-filled" style={{ marginLeft: 'auto', background: 'var(--md-success)', color: 'white' }}>
                    View Remediation Steps
                </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
