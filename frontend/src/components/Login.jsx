import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';
import extractorImage from './extractor-bg.png';

//const baseUrl = "https://babluprajapati3019-email-extractor-api.hf.space";
const baseUrl = " http://127.0.0.1:8000";

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
        
        {/* Left Panel: Illustration */}
        {/* Left Panel: Illustration */}
        <div className="illustration-panel">
            <img 
              src={extractorImage} 
              alt="Email Extractor Concept" 
              style={{ width: '100%', height: 'auto', objectFit: 'contain' }} 
            />
        </div>
        {/* Right Panel: Form */}
        <div className="form-panel">
          <div className="login-header">
            <h2>Welcome!</h2>
          </div>

          {error && <div className="error-banner">{error}</div>}
          
          <form onSubmit={handleSubmit} className="login-form">
            
            {/* Email Input with Icon */}
            <div className="input-group">
              <svg className="input-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 4H4C2.9 4 2.01 4.9 2.01 6L2 18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6C22 4.9 21.1 4 20 4ZM20 18H4V8L12 13L20 8V18ZM12 11L4 6H20L12 11Z" />
              </svg>
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

            {/* Password Input with Icon */}
            <div className="input-group">
              <svg className="input-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 8H17V6C17 3.24 14.76 1 12 1C9.24 1 7 3.24 7 6V8H6C4.9 8 4 8.9 4 10V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V10C20 8.9 19.1 8 18 8ZM9 6C9 4.34 10.34 3 12 3C13.66 3 15 4.34 15 6V8H9V6ZM18 20H6V10H18V20ZM12 17C13.1 17 14 16.1 14 15C14 13.9 13.1 13 12 13C10.9 13 10 13.9 10 15C10 16.1 10.9 17 12 17Z" />
              </svg>
              <input 
                id="password"
                type="password" 
                placeholder="Create password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
                className="form-input"
              />
            </div>

            {/* Side-by-Side Buttons */}
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