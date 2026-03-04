import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './Extractor.css'; // Make sure this matches your CSS filename


const baseUrl = "https://babluprajapati3019-email-extractor-api.hf.space";

function Extractor() {
  const [file, setFile] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await fetch(`${baseUrl}/api/logout/`, {
        method: 'POST',
        credentials: 'include'
      });
      navigate('/login');
    } catch (error) {
      console.error("Logout failed", error);
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
    <div className="extractor-container">
      {/* Header */}
      <div className="extractor-header">
        <h2>Bulk Email Extractor</h2>
        <button onClick={handleLogout} className="btn btn-logout">
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
          className="btn btn-clear"
        >
          Clear All
        </button>
        
        <button 
          onClick={handleExtract} 
          disabled={!file || isExtracting} 
          className="btn btn-primary"
        >
          {isExtracting ? 'Extracting...' : 'Extract Emails'}
        </button>
        
        {downloadUrl ? (
          <a href={downloadUrl} download="extracted_emails.xlsx" className="btn btn-download">
            ⬇️ Download Results
          </a>
        ) : (
          <button disabled={true} className="btn btn-download-disabled">
            ⬇️ Download Results
          </button>
        )}
      </div>
    </div>
  );
}

export default Extractor;