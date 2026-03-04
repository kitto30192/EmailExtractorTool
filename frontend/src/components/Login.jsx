import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css'; // Make sure this matches your CSS filename

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
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // REQUIRED: tells the browser to accept the incoming HttpOnly cookie
        credentials: 'include', 
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        if (isLogin) {
          // The backend set the cookie automatically! No need to save anything here.
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
        
        <div className="login-header">
          <h2>{isLogin ? 'Welcome Back' : 'Create an Account'}</h2>
          <p>{isLogin ? 'Please enter your details to sign in.' : 'Fill in the form below to get started.'}</p>
        </div>

        {error && <div className="error-banner">{error}</div>}
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label htmlFor="email">Email</label>
            <input 
              id="email"
              type="email" 
              placeholder="you@example.com" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              required 
              className="form-input"
            />
          </div>

          <div className="input-group">
            <label htmlFor="password">Password</label>
            <input 
              id="password"
              type="password" 
              placeholder="••••••••" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              required 
              className="form-input"
            />
          </div>

          <button type="submit" className="btn-submit">
            {isLogin ? 'Sign In' : 'Sign Up'}
          </button>
        </form>

        <div className="toggle-container">
          {isLogin ? "Don't have an account?" : "Already have an account?"}
          <span 
            onClick={() => {
              setIsLogin(!isLogin);
              setError(''); // Clear errors when switching tabs
            }} 
            className="toggle-link"
          >
            {isLogin ? 'Sign up' : 'Log in'}
          </span>
        </div>

      </div>
    </div>
  );
}

export default Login;