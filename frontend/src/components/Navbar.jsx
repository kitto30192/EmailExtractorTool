import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

// Notice all 4 props are correctly listed here!
function Navbar({ onToggleGuidelines, showGuidelines, onToggleHistory, onLogout }) {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          <span className="logo-icon">❖</span> BulkEmail Extractor
        </Link>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          
          {/* --- GUIDELINES BUTTON --- */}
          <button 
            onClick={onToggleGuidelines} 
            style={{ 
              padding: '6px 15px', fontSize: '14px', border: '2px solid var(--navy-bg)', 
              backgroundColor: 'transparent', cursor: 'pointer', borderRadius: '6px', 
              fontWeight: '600', color: 'var(--navy-bg)', fontFamily: 'Poppins, sans-serif'
            }}
          >
            {showGuidelines ? 'Hide Guidelines' : '📋 Guidelines'}
          </button>
          
          {/* --- LOGOUT BUTTON --- */}
          <button 
            onClick={onLogout} 
            style={{ 
              padding: '6px 15px', fontSize: '14px', backgroundColor: 'transparent', 
              border: '2px solid #c62828', color: '#c62828', cursor: 'pointer', 
              borderRadius: '6px', fontWeight: '600', fontFamily: 'Poppins, sans-serif'
            }}
            onMouseOver={(e) => { e.target.style.backgroundColor = '#c62828'; e.target.style.color = 'white'; }}
            onMouseOut={(e) => { e.target.style.backgroundColor = 'transparent'; e.target.style.color = '#c62828'; }}
          >
            Logout
          </button>

            {/* --- HISTORY BUTTON --- */}
          <button 
            onClick={onToggleHistory} 
            style={{ 
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '6px 15px', fontSize: '14px', border: '2px solid var(--navy-bg)', 
              backgroundColor: 'transparent', cursor: 'pointer', borderRadius: '6px', 
              fontWeight: '600', color: 'var(--navy-bg)', fontFamily: 'Poppins, sans-serif',
              transition: '0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(39, 42, 70, 0.1)'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <lord-icon
                src="https://cdn.lordicon.com/bhfjfgqz.json"
                trigger="hover"
                colors="primary:#272a46"
                style={{ width: '20px', height: '20px' }}>
            </lord-icon>
            History
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;