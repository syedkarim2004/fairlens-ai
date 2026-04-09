import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Home, 
  Files, 
  Users, 
  Clock, 
  Star, 
  Plus, 
  Database,
  AlertCircle
} from 'lucide-react';

export default function Sidebar() {
  const menuItems = [
    { name: 'Home', icon: Home, path: '/dashboard' },
    { name: 'My Audits', icon: Files, path: '/history' },
    { name: 'Shared with me', icon: Users, path: '/shared' },
    { name: 'Recent', icon: Clock, path: '/recent' },
    { name: 'Starred', icon: Star, path: '/starred' },
  ];

  return (
    <aside style={{
      width: '256px',
      background: 'var(--md-surface)',
      height: 'calc(100vh - 64px)',
      padding: '16px 8px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      position: 'sticky',
      top: '64px',
      borderRight: '1px solid var(--md-outline-variant)'
    }}>
      <div style={{ padding: '0 8px 16px 8px' }}>
        <NavLink 
          to="/audit" 
          style={{ textDecoration: 'none' }}
        >
          <button className="md-card-elevated" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 24px',
            borderRadius: '16px',
            background: 'var(--md-surface)',
            border: 'none',
            boxShadow: 'var(--md-elevation-1)',
            cursor: 'pointer',
            transition: 'box-shadow 0.2s',
            width: 'fit-content'
          }}>
            <div style={{ display: 'flex', gap: '2px' }}>
              <Plus size={24} color="var(--md-primary)" />
            </div>
            <span style={{ 
              fontFamily: 'var(--md-font-body)', 
              fontWeight: 500, 
              color: 'var(--md-on-surface)',
              fontSize: '14px'
            }}>New Audit</span>
          </button>
        </NavLink>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {menuItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            style={({ isActive }) => ({
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '10px 24px',
              borderRadius: '0 24px 24px 0',
              marginRight: '8px',
              background: isActive ? 'var(--md-primary-container)' : 'transparent',
              color: isActive ? 'var(--md-on-primary-container)' : 'var(--md-on-surface-variant)',
              transition: 'background 0.2s',
            })}
          >
            <item.icon size={20} />
            <span style={{ fontSize: '14px', fontWeight: 500 }}>{item.name}</span>
          </NavLink>
        ))}
      </nav>

      <div style={{ marginTop: 'auto', padding: '16px 24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--md-on-surface-variant)' }}>
            <Database size={18} />
            <span style={{ fontSize: '13px' }}>Storage</span>
          </div>
          <div style={{ 
            height: '4px', 
            background: 'var(--md-surface-container-high)', 
            borderRadius: '2px',
            overflow: 'hidden'
          }}>
            <div style={{ width: '45%', height: '100%', background: 'var(--md-primary)' }}></div>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--md-on-surface-variant)' }}>
            4.2 GB of 15 GB used
          </span>
          <button className="btn-outlined" style={{ 
            marginTop: '8px', 
            fontSize: '12px', 
            padding: '6px 16px',
            borderColor: 'var(--md-outline)'
          }}>
            Buy storage
          </button>
        </div>
      </div>

      <div style={{ padding: '16px 24px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div className="google-brand-dots">
            <div className="dot-blue"></div>
            <div className="dot-red"></div>
            <div className="dot-yellow"></div>
            <div className="dot-green"></div>
        </div>
        <span className="google-brand-text">Solution Challenge 2026</span>
      </div>
    </aside>
  );
}
