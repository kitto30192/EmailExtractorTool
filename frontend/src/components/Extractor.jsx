import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './Extractor.css';

const baseUrl = "https://babluprajapati3019-Email-Extractor-v2.hf.space";

//const baseUrl = " http://127.0.0.1:8000";

function Extractor() {
  const [file, setFile] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleLogout = async () => {
      try {
          const response = await fetch(`${baseUrl}/api/logout/`, {
              method: 'POST',
              credentials: 'include', // <-- CRITICAL FOR DELETING COOKIES
          });

          if (response.ok) {
              console.log("Logged out successfully");
              // Redirect user back to the login page here
              navigate('/login');
          }
      } catch (error) {
          console.error("Logout failed:", error);
      }
  };

  const handleBrowse = () => fileInputRef.current.click();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setDownloadUrl(null); 
    }
  };

  const handleClearAll = () => {
    setFile(null);
    setDownloadUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleExtract = async () => {
    if (!file) return;
    
    setIsExtracting(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${baseUrl}/api/extract/`, {
        method: 'POST',
        credentials: 'include', 
        body: formData,
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        setDownloadUrl(url);
      } else if (response.status === 401) {
         alert('Session expired or unauthorized. Please log in again.');
         navigate('/login');
      } else {
        alert('Extraction failed. Please ensure the Excel format is correct.');
      }
    } catch (error) {
      console.log(error);
      console.error('Error during extraction:', error);
      alert('Network error. Is the backend server running?');
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <div className="extractor-page-wrapper">
      <div className="extractor-card">
        
        {/* Header */}
        <div className="extractor-header">
          <h2>Bulk Email Extractor</h2>
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
        
        {/* Interactive Upload Zone */}
        <div 
          className={`upload-zone ${file ? 'has-file' : ''}`} 
          onClick={handleBrowse}
        >
          <p className="file-status">
            {file ? (
              <span className="file-status-success">
                📄 <strong>{file.name}</strong> loaded. Ready to extract.
              </span>
            ) : (
              <span>📁 Click here to browse and upload your domain list (.xlsx, .xls)</span>
            )}
          </p>
          {isExtracting && (
            <p className="extracting-text">
              ⏳ Extracting emails... This process takes time depending on the list size.
            </p>
          )}
        </div>

        {/* Hidden File Input */}
        <input 
          type="file" 
          accept=".xlsx, .xls" 
          style={{ display: 'none' }} 
          ref={fileInputRef} 
          onChange={handleFileChange} 
        />

        {/* Action Buttons */}
        <div className="button-group">
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
          
          {/* Download Button drops to full width on a new line */}
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
  );
}

export default Extractor;