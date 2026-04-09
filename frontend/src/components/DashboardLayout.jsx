import React from 'react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function DashboardLayout({ children }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <div style={{ display: 'flex', flex: 1 }}>
        <Sidebar />
        <main style={{ 
          flex: 1, 
          padding: '24px 32px', 
          background: 'var(--md-background)',
          maxWidth: '1200px',
          margin: '0 auto'
        }}>
          {children}
        </main>
      </div>
    </div>
  );
}
