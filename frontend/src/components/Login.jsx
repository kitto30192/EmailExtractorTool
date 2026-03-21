import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';

const baseUrl="https://babluprajapati3019-emailextractortool.hf.space"

function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const endpoint = isLogin ? '/api/login/' : '/api/signup/';

    try {
      const response = await fetch(`${baseUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', 
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        if (isLogin) {
          navigate('/'); 
        } else {
          setIsLogin(true);
          alert("Signup successful! Please log in.");
        }
      } else {
        setError(data.detail || 'Authentication failed');
      }
    } catch (err) {
      setError('Network error. Is the server running?');
    }
  };

  return (
    <div className="login-page-wrapper">
      <div className="login-card">
        
       <div className="illustration-panel" style={{ flexDirection: 'column', textAlign: 'center' }}>
            <lord-icon
                src="https://cdn.lordicon.com/ljvjsnvh.json" 
                trigger="loop" 
                delay="2000"
                colors="primary:#272a46,secondary:#e1b372"
                style={{ width: '250px', height: '250px' }}>
            </lord-icon>
            
            <h3 style={{ 
              marginTop: '20px', 
              color: 'var(--navy-bg)', 
              fontSize: '1.8rem',
              fontWeight: '600'
            }}>
              Glad to see you!
            </h3>
            <p style={{ color: '#555', fontSize: '0.9rem', marginTop: '-10px' }}>
              Sign in to manage your extractions.
            </p>
        </div>
        
        <div className="form-panel">
          <div className="login-header">
            <h2>Welcome!</h2>
          </div>

          {error && <div className="error-banner">{error}</div>}
          
          <form onSubmit={handleSubmit} className="login-form">
            
           {/* --- PREMIUM ANIMATED EMAIL INPUT --- */}
            <div className="input-group">
              <div style={{ width: '28px', height: '28px', marginRight: '12px', display: 'flex' }}>
                  <lord-icon
                   src="https://cdn.lordicon.com/ozlkyfxg.json"
                    trigger="hover"
                   colors="primary:#110a5c,secondary:#e88c30"
                    style={{ width: '100%', height: '100%' }}> 
                </lord-icon>
              </div>
              <input 
                id="email"
                type="email" 
                placeholder="Your e-mail" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                required 
                className="form-input"
              />
            </div>

            {/* --- PREMIUM ANIMATED PASSWORD INPUT --- */}
            <div className="input-group">
              <lord-icon
                  src="https://cdn.lordicon.com/dicvhxpz.json"
                  trigger="hover"
                  colors="primary:#272a46,secondary:#e1b372"
                  style={{ width: '28px', height: '28px', marginRight: '12px' }}>
              </lord-icon>
              <input 
                id="password"
                type="password" 
                placeholder="Enter password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
                className="form-input"
              />
            </div>

            <div className="button-group">
              <button 
                type={!isLogin ? "submit" : "button"} 
                className={`btn-action ${!isLogin ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => { if (isLogin) { setIsLogin(false); setError(''); } }}
              >
                Create account
              </button>
              
              <button 
                type={isLogin ? "submit" : "button"} 
                className={`btn-action ${isLogin ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => { if (!isLogin) { setIsLogin(true); setError(''); } }}
              >
                Sign in
              </button>
            </div>

          </form>
        </div>

      </div>
    </div>
  );
}

export default Login;