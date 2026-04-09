import React, { useState } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { 
  AlertTriangle, 
  ChevronRight, 
  Terminal, 
  Play, 
  Settings2, 
  ShieldAlert,
  Search
} from 'lucide-react';

export default function Remediate() {
  const [selectedIssue, setSelectedIssue] = useState(0);

  const issues = [
    { 
      id: 0, 
      title: 'Disparate Impact: Gender', 
      severity: 'Critical', 
      desc: 'Hiring rate for Females is 34% lower than Males.',
      steps: [
        { title: 'Calculate Reweighing Weights', code: 'weights = df.groupby(["Gender", "Hired"]).size() / len(df)' },
        { title: 'Apply Weights to Training Data', code: 'model.fit(X, y, sample_weight=weights)' },
        { title: 'Re-evaluate Disparate Impact', code: 'new_dir = compute_disparate_impact(model, test_data)' }
      ]
    },
    { 
      id: 1, 
      title: 'Proxy Column Detected: ZipCode', 
      severity: 'High', 
      desc: 'ZipCode correlates 0.92 with sensitive attribute Race.',
      steps: [
        { title: 'Identify Proxy Correlations', code: 'corr_matrix = df.corr(method="spearman")' },
        { title: 'Drop Proxy Columns', code: 'df_clean = df.drop(columns=["ZipCode", "DistrictID"])' }
      ]
    },
    { 
      id: 2, 
      title: 'Statistical Parity Gap: Age', 
      severity: 'Medium', 
      desc: 'Outcome disparity of 0.12 found for group Age > 55.',
      steps: [
        { title: 'Adjust Decision Threshold', code: 'thresholds = {"Age > 55": 0.45, "Default": 0.5}' }
      ]
    }
  ];

  return (
    <DashboardLayout>
      <div className="animate-fade-in" style={{ height: 'calc(100vh - 112px)', display: 'flex', flexDirection: 'column' }}>
        <header style={{ marginBottom: '24px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: 400, marginBottom: '4px' }}>Remediation Center</h1>
          <p style={{ color: 'var(--md-on-surface-variant)' }}>Apply algorithmic fixes to resolve detected biases in your models.</p>
        </header>

        <div className="md-card" style={{ 
          flex: 1, 
          padding: 0, 
          display: 'flex', 
          overflow: 'hidden',
          borderRadius: '16px'
        }}>
          {/* Left Panel: Issue List */}
          <div style={{ 
            width: '360px', 
            borderRight: '1px solid var(--md-outline-variant)',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{ padding: '16px', borderBottom: '1px solid var(--md-outline-variant)' }}>
              <div style={{ position: 'relative' }}>
                <Search size={16} style={{ position: 'absolute', left: '12px', top: '10px', color: 'var(--md-on-surface-variant)' }} />
                <input 
                  type="text" 
                  placeholder="Search issues..." 
                  style={{
                    width: '100%',
                    padding: '8px 12px 8px 36px',
                    borderRadius: '8px',
                    border: '1px solid var(--md-outline)',
                    fontSize: '14px',
                    outline: 'none',
                    background: 'var(--md-surface-container)'
                  }}
                />
              </div>
            </div>

            <div style={{ flex: 1, overflowY: 'auto' }}>
              {issues.map((issue) => (
                <div 
                  key={issue.id}
                  onClick={() => setSelectedIssue(issue.id)}
                  style={{
                    padding: '20px 16px',
                    cursor: 'pointer',
                    background: selectedIssue === issue.id ? 'var(--md-primary-container)' : 'transparent',
                    borderBottom: '1px solid var(--md-outline-variant)',
                    transition: 'background 0.2s'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ 
                      fontSize: '14px', 
                      fontWeight: 600, 
                      color: selectedIssue === issue.id ? 'var(--md-on-primary-container)' : 'var(--md-on-surface)' 
                    }}>
                      {issue.title}
                    </span>
                    <span style={{ 
                      fontSize: '10px', 
                      fontWeight: 700, 
                      color: issue.severity === 'Critical' ? 'var(--md-error)' : 'var(--md-on-surface-variant)'
                    }}>
                      {issue.severity.toUpperCase()}
                    </span>
                  </div>
                  <p style={{ 
                    fontSize: '12px', 
                    color: selectedIssue === issue.id ? 'var(--md-on-primary-container)' : 'var(--md-on-surface-variant)',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden'
                  }}>
                    {issue.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Right Panel: Detail Panel */}
          <div style={{ flex: 1, padding: '32px', overflowY: 'auto', background: 'var(--md-surface)' }}>
            <div style={{ marginBottom: '32px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                 <div style={{ 
                   padding: '12px', 
                   borderRadius: '12px', 
                   background: issues[selectedIssue].severity === 'Critical' ? 'var(--md-error-container)' : 'var(--md-warning-container)',
                   color: issues[selectedIssue].severity === 'Critical' ? 'var(--md-error)' : 'var(--md-warning)'
                 }}>
                   <ShieldAlert size={24} />
                 </div>
                 <h2 style={{ fontSize: '22px', fontWeight: 500 }}>{issues[selectedIssue].title}</h2>
              </div>
              <p style={{ fontSize: '15px', color: 'var(--md-on-surface)', lineHeight: '1.6' }}>
                {issues[selectedIssue].desc}
              </p>
            </div>

            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--md-on-surface-variant)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Remediation Workflow
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {issues[selectedIssue].steps.map((step, idx) => (
                <div key={idx} style={{ position: 'relative', paddingLeft: '40px' }}>
                  <div style={{ 
                    position: 'absolute', 
                    left: 0, 
                    top: '2px', 
                    width: '24px', 
                    height: '24px', 
                    borderRadius: '50%', 
                    background: 'var(--md-surface-container-high)',
                    fontSize: '12px',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    {idx + 1}
                  </div>
                  <h4 style={{ fontSize: '15px', fontWeight: 500, marginBottom: '8px' }}>{step.title}</h4>
                  <div style={{ 
                    background: '#202124', 
                    borderRadius: '8px', 
                    padding: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    marginBottom: '12px'
                  }}>
                    <Terminal size={16} color="#34a853" />
                    <code style={{ fontSize: '13px', color: '#e8eaed', fontFamily: 'monospace' }}>{step.code}</code>
                  </div>
                  <button className="btn-tonal" style={{ fontSize: '12px', padding: '6px 16px' }}>
                    <Play size={14} style={{ marginRight: '8px' }} /> Apply Step
                  </button>
                </div>
              ))}
            </div>

            <div style={{ marginTop: '48px', paddingTop: '32px', borderTop: '1px solid var(--md-outline-variant)', display: 'flex', justifyContent: 'flex-end', gap: '16px' }}>
               <button className="btn-outlined">Download Fix Script</button>
               <button className="btn-filled">Commit Remediation</button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
