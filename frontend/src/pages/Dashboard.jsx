import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import { 
  FileSearch, 
  CheckCircle2, 
  AlertTriangle, 
  Database,
  MoreVertical,
  FileText,
  Plus
} from 'lucide-react';
import { getAuditHistory } from '../services/api';

export default function Dashboard() {
  const { user } = useAuth();
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAudits = async () => {
      try {
        const data = await getAuditHistory();
        setAudits(data || []);
      } catch (err) {
        console.error("Failed to fetch audits", err);
        // Fallback mock data for demo if API fails
        setAudits([
          { id: '1', name: 'Loan_Applicant_2026.csv', owner: 'Me', modified: 'Oct 12, 2026', grade: 'A', risk: 'Low' },
          { id: '2', name: 'Recruitment_Dataset_v2.csv', owner: 'HR Dept', modified: 'Oct 10, 2026', grade: 'C', risk: 'Medium' },
          { id: '3', name: 'Healthcare_Outcomes.csv', owner: 'Me', modified: 'Oct 05, 2026', grade: 'F', risk: 'High' },
        ]);
      } finally {
        setLoading(false);
      }
    };
    fetchAudits();
  }, []);

  const stats = [
    { label: 'Total Audits', value: audits.length, icon: FileSearch, color: 'var(--md-primary)' },
    { label: 'Avg Fairness', value: 'B+', icon: CheckCircle2, color: 'var(--md-success)' },
    { label: 'Biases Caught', value: '12', icon: AlertTriangle, color: 'var(--md-error)' },
    { label: 'Capacity', value: '45%', icon: Database, color: 'var(--md-warning)' },
  ];

  return (
    <DashboardLayout>
      <div className="animate-fade-in">
        <header style={{ marginBottom: '32px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: 400, color: 'var(--md-on-surface)', marginBottom: '4px' }}>
            Welcome back, {user?.name?.split(' ')[0] || 'User'}
          </h1>
          <p style={{ color: 'var(--md-on-surface-variant)', fontSize: '14px' }}>
            Monitor and mitigate algorithmic bias across your datasets.
          </p>
        </header>

        <section style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', 
          gap: '16px',
          marginBottom: '40px'
        }}>
          {stats.map((stat) => (
            <div key={stat.label} className="md-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <p style={{ fontSize: '12px', fontWeight: 500, color: 'var(--md-on-surface-variant)', marginBottom: '4px' }}>
                    {stat.label}
                  </p>
                  <p style={{ fontSize: '24px', fontWeight: 500, color: 'var(--md-on-surface)' }}>
                    {stat.value}
                  </p>
                </div>
                <div style={{ 
                  padding: '8px', 
                  borderRadius: '12px', 
                  background: 'var(--md-surface-container-high)',
                  color: stat.color 
                }}>
                  <stat.icon size={24} />
                </div>
              </div>
            </div>
          ))}
        </section>

        <section className="md-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--md-outline-variant)' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 500 }}>Recent Audits</h2>
          </div>
          
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--md-outline-variant)', background: 'var(--md-surface-container)' }}>
                <th style={{ padding: '12px 24px', fontSize: '13px', fontWeight: 500, color: 'var(--md-on-surface-variant)' }}>Name</th>
                <th style={{ padding: '12px 24px', fontSize: '13px', fontWeight: 500, color: 'var(--md-on-surface-variant)' }}>Owner</th>
                <th style={{ padding: '12px 24px', fontSize: '13px', fontWeight: 500, color: 'var(--md-on-surface-variant)' }}>Last modified</th>
                <th style={{ padding: '12px 24px', fontSize: '13px', fontWeight: 500, color: 'var(--md-on-surface-variant)' }}>Fairness Grade</th>
                <th style={{ padding: '12px 24px', fontSize: '13px', fontWeight: 500, color: 'var(--md-on-surface-variant)' }}></th>
              </tr>
            </thead>
            <tbody>
              {audits.map((audit) => (
                <tr key={audit.id} style={{ borderBottom: '1px solid var(--md-outline-variant)', cursor: 'pointer' }} className="hover-row">
                  <style>{`
                    .hover-row:hover { background: var(--md-surface-container); }
                  `}</style>
                  <td style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <FileText size={20} color="#5f6368" />
                    <span style={{ fontSize: '14px', color: 'var(--md-on-surface)' }}>{audit.name}</span>
                  </td>
                  <td style={{ padding: '16px 24px', fontSize: '14px', color: 'var(--md-on-surface-variant)' }}>{audit.owner}</td>
                  <td style={{ padding: '16px 24px', fontSize: '14px', color: 'var(--md-on-surface-variant)' }}>{audit.modified}</td>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ 
                      display: 'inline-flex', 
                      padding: '4px 12px', 
                      borderRadius: '16px',
                      fontSize: '12px',
                      fontWeight: 500,
                      background: audit.grade === 'A' ? 'var(--md-success-container)' : 
                                 audit.grade === 'C' ? 'var(--md-warning-container)' : 
                                 'var(--md-error-container)',
                      color: audit.grade === 'A' ? 'var(--md-on-success-container)' : 
                             audit.grade === 'C' ? '#856404' : 
                             'var(--md-on-error-container)'
                    }}>
                      {audit.grade}
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px', textAlign: 'right' }}>
                    <button className="btn-text" style={{ padding: '4px' }}>
                      <MoreVertical size={20} color="var(--md-on-surface-variant)" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {loading && (
            <div style={{ padding: '40px', textAlign: 'center' }}>
              <div className="skeleton" style={{ height: '20px', width: '200px', margin: '0 auto' }}></div>
            </div>
          )}
        </section>

        <section style={{ marginTop: '40px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 500, marginBottom: '16px' }}>Suggested</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
            <div className="md-card" style={{ display: 'flex', alignItems: 'center', gap: '16px', cursor: 'pointer' }}>
              <div style={{ padding: '12px', borderRadius: '12px', background: 'var(--md-primary-container)' }}>
                <Plus size={24} color="var(--md-primary)" />
              </div>
              <div>
                <p style={{ fontWeight: 500, fontSize: '14px' }}>Tutorial: First Audit</p>
                <p style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)' }}>Learn to detect bias in 5 mins</p>
              </div>
            </div>
            <div className="md-card" style={{ display: 'flex', alignItems: 'center', gap: '16px', cursor: 'pointer' }}>
              <div style={{ padding: '12px', borderRadius: '12px', background: 'var(--md-secondary-container)' }}>
                <FileText size={24} color="var(--md-secondary)" />
              </div>
              <div>
                <p style={{ fontWeight: 500, fontSize: '14px' }}>Sample Dataset</p>
                <p style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)' }}>Recruitment_History_2024.csv</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </DashboardLayout>
  );
}
