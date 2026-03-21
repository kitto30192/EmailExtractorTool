import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from './Navbar';

import './Extractor.css';

const baseUrl="https://babluprajapati3019-emailextractortool.hf.space"

function Extractor() {
  const [file, setFile] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);
  
  const [taskId, setTaskId] = useState(null);
  const [logs, setLogs] = useState([]);
  const [jobStatus, setJobStatus] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [historyData, setHistoryData] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const [showGuidelines, setShowGuidelines] = useState(false);
  const [userEmail, setUserEmail] = useState("");

  const fileInputRef = useRef(null);
  const logsEndRef = useRef(null);
  const navigate = useNavigate();


  const fetchUserHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const response = await fetch(`${baseUrl}/api/history/`, {
        method: 'GET',
        credentials: 'include'
      });
     if (response.ok) {
        const data = await response.json();
        setHistoryData(data.history || []);
        setUserEmail(data.user_email || ""); // <-- ADD THIS LINE
      }
    } catch (error) {
      console.error("Failed to fetch history", error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleToggleHistory = () => {
    const willShow = !showHistory;
    setShowHistory(willShow);
    if (willShow) {
      fetchUserHistory(); // Fetch fresh data every time we open it
    }
  };

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  useEffect(() => {
    let intervalId;

    const checkStatus = async () => {
      if (!taskId) return;

      try {
        const response = await fetch(`${baseUrl}/api/extract/status/${taskId}`, {
          method: 'GET',
          credentials: 'include'
        });

        if (response.ok) {
          const data = await response.json();
          setLogs(data.logs || []);
          setJobStatus(data.status);

          if (data.status === 'Completed' || data.status === 'Failed') {
            setIsExtracting(false);
            clearInterval(intervalId);

            if (data.status === 'Completed') {
              fetchDownloadBlob(taskId);
            }
          }
        } else if (response.status === 401) {
          clearInterval(intervalId);
          alert('Session expired. Please log in again.');
          navigate('/login');
        }
      } catch (error) {
        console.error("Polling error:", error);
      }
    };

    if (taskId && jobStatus === 'Processing') {
      intervalId = setInterval(checkStatus, 3000);
    }

    return () => clearInterval(intervalId);
  }, [taskId, jobStatus, navigate]);

  const fetchDownloadBlob = async (id) => {
    try {
      const response = await fetch(`${baseUrl}/api/extract/download/${id}`, {
        method: 'GET',
        credentials: 'include'
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        setDownloadUrl(url);
      }
    } catch (error) {
      console.error("Error fetching download:", error);
    }
  };

  const handleLogout = async () => {
    try {
      const response = await fetch(`${baseUrl}/api/logout/`, {
        method: 'POST',
        credentials: 'include',
      });
      if (response.ok) {
        navigate('/login');
      }
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  const handleBrowse = () => {
    if (!isExtracting) fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setDownloadUrl(null);
      setTaskId(null);
      setLogs([]);
      setJobStatus(null);
    }
  };

  const handleClearAll = () => {
    setFile(null);
    setDownloadUrl(null);
    setTaskId(null);
    setLogs([]);
    setJobStatus(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleExtract = async () => {
    if (!file) return;
    
    setIsExtracting(true);
    setLogs(["Uploading file to server..."]);
    setJobStatus("Processing");
    setDownloadUrl(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${baseUrl}/api/extract/`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setTaskId(data.task_id);
      } else if (response.status === 401) {
        alert('Session expired or unauthorized. Please log in again.');
        navigate('/login');
      } else {
        const errData = await response.json();
        alert(`Extraction failed: ${errData.detail || 'Unknown error'}`);
        setIsExtracting(false);
        setJobStatus('Failed');
      }
    } catch (error) {
      console.error('Error during extraction:', error);
      alert('Network error. Is the backend server running?');
      setIsExtracting(false);
      setJobStatus('Failed');
    }
  };

  return (
    <>
      {/* --- NAVBAR IS NOW RENDERED HERE --- */}
      <Navbar 
        onToggleGuidelines={() => setShowGuidelines(!showGuidelines)} 
        showGuidelines={showGuidelines} 
        onToggleHistory={handleToggleHistory} 
        onLogout={handleLogout} 
      />

      {/* --- HISTORY MODAL OVERLAY --- */}
      {showHistory && (
        <div className="history-modal-overlay" onClick={() => setShowHistory(false)}>
          <div className="history-modal-content" onClick={(e) => e.stopPropagation()}>
            
            {/* --- UPDATED HEADER --- */}
            <div className="history-header" style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              borderBottom: '2px solid rgba(39, 42, 70, 0.1)',
              paddingBottom: '15px',
              marginBottom: '20px'
            }}>
              {/* Left Side: Large Username */}
              <div className="header-left">
                <h2 style={{ 
                  margin: 0, 
                  color: 'var(--navy-bg)', 
                  fontSize: '1.6rem', 
                  fontFamily: 'Playfair Display, serif',
                  textTransform: 'capitalize' 
                }}>
                  {/* If you only have the email, this splits it to show just the name before the '@' */}
                  {/* REPLACE 'userEmail' WITH YOUR ACTUAL USER VARIABLE */}
                  {userEmail ? userEmail.split('@')[0] : "My Account"} 
                </h2>
              </div>

              {/* Right Side: Smaller Title & Close Button */}
              <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                <h3 style={{ 
                  margin: 0, 
                  color: '#666', 
                  fontSize: '1rem', 
                  fontFamily: 'Poppins, sans-serif',
                  fontWeight: '500'
                }}>
                  Recent Extractions
                </h3>
                <button 
                  className="close-btn" 
                  onClick={() => setShowHistory(false)}
                  style={{ fontSize: '1.2rem', padding: '0 5px' }}
                >
                  ✕
                </button>
              </div>
            </div>
            {/* --- END UPDATED HEADER --- */}

            <div className="history-list">
              {isLoadingHistory ? (
                <p style={{ textAlign: 'center', color: '#666' }}>Loading history...</p>
              ) : historyData.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#666' }}>No past extractions found.</p>
              ) : (
                historyData.map((item, index) => (
                  <div key={index} className="history-item">
                    <div className="history-icon">📄</div>
                    <div className="history-details">
                      <div className="history-filename">{item.filename || "Unknown File"}</div>
                      <div className="history-meta">
                        <span>📅 {item.date}</span>
                        <span>⏰ {item.time}</span>
                      </div>
                    </div>
                    <div className={`history-status ${item.status === 'Completed' ? 'status-green' : 'status-orange'}`}>
                      {item.status}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      <div className="extractor-page-wrapper">
        <div className="extractor-card">
          
          {/* Old inner header is completely gone! */}

          {showGuidelines && (
            <div className="upload-guidance" style={{
              backgroundColor: 'rgba(0, 123, 255, 0.05)',
              borderLeft: '4px solid #007bff',
              padding: '15px',
              marginBottom: '20px',
              borderRadius: '4px',
              textAlign: 'left',
              fontSize: '14px',
              animation: 'fadeIn 0.3s ease-in-out'
            }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#007bff' }}>📋 Excel Sheet Guidelines</h4>
              <ul style={{ margin: '0', paddingLeft: '20px', lineHeight: '1.6' }}>
                <li><strong>Exact Columns Required:</strong> Your sheets must contain exactly 4 columns: <code style={{backgroundColor:'rgba(0,0,0,0.1)', padding:'2px 5px', borderRadius:'3px'}}>SRL</code>, <code style={{backgroundColor:'rgba(0,0,0,0.1)', padding:'2px 5px', borderRadius:'3px'}}>Domains</code>, <code style={{backgroundColor:'rgba(0,0,0,0.1)', padding:'2px 5px', borderRadius:'3px'}}>Email</code>, and <code style={{backgroundColor:'rgba(0,0,0,0.1)', padding:'2px 5px', borderRadius:'3px'}}>Status</code>.</li>
                <li><strong>Row Limit:</strong> Maximum <strong>500 domains</strong> per sheet. If you have more, split them across multiple sheets within the same file.</li>
                <li><strong>Multiple Sheets:</strong> The extractor processes all sheets automatically. If a sheet is formatted incorrectly, it will be skipped, but the others will process normally.</li>
                <li><strong>Leave Empty:</strong> You can leave the <i>Email</i> and <i>Status</i> columns completely blank. The extractor will fill them in for you.</li>
              </ul>
            </div>
          )}
          
          <div 
            className={`upload-zone ${file ? 'has-file' : ''} ${isExtracting ? 'disabled' : ''}`} 
            onClick={handleBrowse}
          >
            <p className="file-status">
              {file ? (
                <span className="file-status-success">
                  📄 <strong>{file.name}</strong> loaded.
                </span>
              ) : (
                <span>📁 Click here to browse and upload your domain list (.xlsx, .xls)</span>
              )}
            </p>
          </div>

          <input 
            type="file" 
            accept=".xlsx, .xls" 
            style={{ display: 'none' }} 
            ref={fileInputRef} 
            onChange={handleFileChange} 
          />

          {(logs.length > 0 || isExtracting) && (
            <div className="log-console" style={{
              backgroundColor: '#1e1e1e', color: '#00ff00', padding: '10px', 
              borderRadius: '5px', marginTop: '15px', height: '150px', 
              overflowY: 'auto', fontFamily: 'monospace', fontSize: '12px',
              textAlign: 'left'
            }}>
              {logs.map((log, index) => (
                <div key={index} style={{ marginBottom: '4px' }}>
                 {log}
                </div>
              ))}
              {isExtracting && (
                <div style={{ color: '#00ccff', marginTop: '10px' }}>
                  <span className="blink">⏳ Polling server for updates...</span>
                </div>
              )}
              <div ref={logsEndRef} />
            </div>
          )}

          <div className="button-group" style={{ marginTop: '20px' }}>
            <button 
              onClick={handleClearAll} 
              disabled={isExtracting || (!file && !downloadUrl)} 
              className="btn-action btn-secondary"
            >
              Clear
            </button>
            
            <button 
              onClick={handleExtract} 
              disabled={!file || isExtracting} 
              className="btn-action btn-primary"
            >
              {isExtracting ? 'Extracting...' : 'Extract Emails'}
            </button>
            
            {downloadUrl ? (
              <a href={downloadUrl} download="extracted_emails.xlsx" className="btn-action btn-download">
                ⬇️ Download Results
              </a>
            ) : (
              <button disabled={true} className="btn-action btn-download-disabled">
                ⬇️ Download Results
              </button>
            )}
          </div>

        </div>
      </div>
    </>
  );
}

export default Extractor;