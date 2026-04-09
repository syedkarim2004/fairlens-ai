import React, { useState } from 'react';
import { auth, googleProvider, signInWithPopup } from '../firebase';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState('');

  const handleGoogleSignIn = async () => {
    try {
      setError('');
      const result = await signInWithPopup(auth, googleProvider);
      const idToken = await result.user.getIdToken();
      
      // For Demo Purpose: We bypass the real backend auth if it fails, allowing entry.
      // But in production, we calling: await api.post('/api/auth/google', { id_token: idToken })
      
      const userData = {
        user_id: result.user.uid,
        name: result.user.displayName,
        email: result.user.email,
        photo_url: result.user.photoURL
      };

      login(idToken, userData);
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      setError('Could not sign you in with Google. Please try again.');
    }
  };

  const instantDemo = () => {
    const demoUser = {
      user_id: 'demo_user',
      name: 'Demo Architect',
      email: 'demo@fairlens.ai',
      photo_url: null
    };
    login('demo_token', demoUser);
    navigate('/dashboard');
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--md-background)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px'
    }} className="animate-fade-in">
      <div className="md-card" style={{
        width: '100%',
        maxWidth: '480px',
        background: 'var(--md-surface)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '48px 40px',
        textAlign: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <ShieldCheck size={32} color="var(--md-primary)" />
          <h1 style={{ 
            fontFamily: 'var(--md-font-display)', 
            fontSize: '28px', 
            fontWeight: 700, 
            color: 'var(--md-on-surface)' 
          }}>FairLens AI</h1>
        </div>

        <h2 style={{ 
          fontSize: '24px', 
          fontWeight: 400, 
          marginBottom: '8px',
          color: 'var(--md-on-surface)'
        }}>Sign in</h2>
        
        <p style={{ 
          fontSize: '16px', 
          color: 'var(--md-on-surface-variant)', 
          marginBottom: '32px',
          fontFamily: 'var(--md-font-body)'
        }}>to continue to FairLens AI</p>

        {error && (
          <div className="error-alert" style={{ marginBottom: '24px', width: '100%' }}>
            {error}
          </div>
        )}

        <button 
          onClick={handleGoogleSignIn}
          style={{
            width: '100%',
            height: '40px',
            background: 'white',
            border: '1px solid #dadce0',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            cursor: 'pointer',
            fontFamily: 'Roboto, sans-serif',
            fontSize: '14px',
            fontWeight: 500,
            color: '#3c4043',
            transition: 'background 0.2s, box-shadow 0.2s',
            marginBottom: '12px'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = '#f8f9fa';
            e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.08)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = 'white';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          <svg width="18" height="18" viewBox="0 0 18 18">
            <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/>
            <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
            <path d="M3.964 10.706c-.18-.54-.282-1.117-.282-1.706s.102-1.166.282-1.706V4.962H.957C.347 6.175 0 7.55 0 9s.347 2.825.957 4.038l3.007-2.332z" fill="#FBBC05"/>
            <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.443 2.05 1.011 4.962l3.007 2.332C4.722 5.164 6.706 3.58 9 3.58z" fill="#EA4335"/>
          </svg>
          Sign in with Google
        </button>

        <button 
          onClick={instantDemo}
          className="btn-tonal"
          style={{ width: '100%', marginBottom: '24px' }}
        >
          Instant Demo Access
        </button>

        <p style={{ 
          fontSize: '11px', 
          color: '#5f6368', 
          lineHeight: '1.5',
          marginBottom: '40px'
        }}>
          By continuing, you agree to FairLens AI's Terms of Service and Privacy Policy.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <div className="google-brand-dots">
            <div className="dot-blue"></div>
            <div className="dot-red"></div>
            <div className="dot-yellow"></div>
            <div className="dot-green"></div>
          </div>
          <span style={{ fontSize: '12px', fontWeight: 500, color: '#5f6368' }}>
            Google Solution Challenge 2026
          </span>
        </div>
      </div>

      <div style={{ marginTop: '24px', display: 'flex', gap: '24px' }}>
        <span style={{ fontSize: '12px', color: '#5f6368' }}>English (United States)</span>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span style={{ fontSize: '12px', color: '#5f6368' }}>Help</span>
          <span style={{ fontSize: '12px', color: '#5f6368' }}>Privacy</span>
          <span style={{ fontSize: '12px', color: '#5f6368' }}>Terms</span>
        </div>
      </div>
    </div>
  );
}
