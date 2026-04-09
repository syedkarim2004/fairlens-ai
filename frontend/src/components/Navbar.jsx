import React from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Search, HelpCircle, LayoutGrid, LogOut } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="workspace-navbar" style={{
      height: '64px',
      background: 'var(--md-surface)',
      borderBottom: '1px solid var(--md-outline-variant)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 16px',
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      justifyContent: 'space-between'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <button className="btn-text" style={{ padding: '8px' }}>
          <LayoutGrid size={24} color="var(--md-on-surface-variant)" />
        </button>
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={28} color="var(--md-primary)" />
          <span style={{ 
            fontFamily: 'var(--md-font-display)', 
            fontSize: '20px', 
            fontWeight: 500, 
            color: 'var(--md-on-surface)' 
          }}>
            FairLens <span style={{ color: 'var(--md-primary)' }}>AI</span>
          </span>
        </Link>
      </div>

      <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
        <div style={{ 
          maxWidth: '720px', 
          width: '100%', 
          position: 'relative',
          display: 'flex',
          alignItems: 'center'
        }}>
          <div style={{
            position: 'absolute',
            left: '16px',
            display: 'flex',
            alignItems: 'center',
            color: 'var(--md-on-surface-variant)'
          }}>
            <Search size={20} />
          </div>
          <input 
            type="text" 
            placeholder="Search audits, datasets, or documentation"
            style={{
              width: '100%',
              height: '48px',
              borderRadius: '24px',
              border: 'none',
              background: 'var(--md-surface-container)',
              padding: '0 56px',
              fontSize: '16px',
              fontFamily: 'var(--md-font-ui)',
              outline: 'none',
              transition: 'background 0.2s, box-shadow 0.2s',
              color: 'var(--md-on-surface)'
            }}
          />
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <button className="btn-text" style={{ padding: '8px' }}>
          <HelpCircle size={24} color="var(--md-on-surface-variant)" />
        </button>
        <button className="btn-text" style={{ padding: '8px' }}>
          <LayoutGrid size={24} color="var(--md-on-surface-variant)" />
        </button>
        
        {user ? (
          <div style={{ marginLeft: '8px', position: 'relative' }}>
             <div 
               onClick={logout}
               title="Click to Logout"
               style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: 'var(--md-primary)',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '14px',
                fontWeight: 500,
                cursor: 'pointer',
                overflow: 'hidden'
              }}>
                {user.photo_url ? (
                  <img src={user.photo_url} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  user.name?.[0]?.toUpperCase() || 'U'
                )}
             </div>
          </div>
        ) : (
          <Link to="/login" className="btn-filled">Sign In</Link>
        )}
      </div>
    </nav>
  );
}
