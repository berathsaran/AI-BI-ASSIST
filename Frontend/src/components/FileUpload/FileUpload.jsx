// Frontend/src/components/FileUpload/FileUpload.jsx
import React, { useState, useCallback } from "react";
import "../FileUpload/FileUpload.css";

const FileUpload = ({ setFileId, onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);

  const ALLOWED_TYPES = {
    "text/csv": "CSV",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel (.xlsx)",
    "application/json": "JSON",
    "application/x-parquet": "Parquet",
  };

  const handleFileChange = useCallback((e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) {
      setFile(null);
      setError("");
      setUploadProgress(0);
      return;
    }
    if (!ALLOWED_TYPES[selectedFile.type]) {
      setError(`Invalid file type. Supported: ${Object.values(ALLOWED_TYPES).join(", ")}`);
      setFile(null);
      setUploadProgress(0);
      return;
    }
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (selectedFile.size > maxSize) {
      setError(`File size exceeds ${maxSize / (1024 * 1024)}MB`);
      setFile(null);
      setUploadProgress(0);
      return;
    }
    setFile(selectedFile);
    setError("");
    setSuccess("");
    setUploadProgress(0);
  }, []);

  const handleSubmit = useCallback(
    (e) => {
      e.preventDefault();
      if (!file) {
        setError("Please select a file.");
        return;
      }
      setLoading(true);
      setError("");
      setSuccess("");
      setUploadProgress(0);

      const formData = new FormData();
      formData.append("file", file);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/upload", true);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(percentComplete);
        }
      };

      xhr.onload = () => {
        if (xhr.status === 200) {
          const data = JSON.parse(xhr.responseText);
          setFileId(data.file_id);
          setSuccess(`File "${data.filename}" uploaded successfully!`);
          setFile(null);
          setUploadProgress(100);
          if (onUploadSuccess) onUploadSuccess(data);
        } else {
          setError(`Upload failed: ${xhr.status} - ${xhr.statusText}`);
          setUploadProgress(0);
        }
        setLoading(false);
      };

      xhr.onerror = () => {
        console.error("Upload request failed:", xhr.status, xhr.statusText);
        setError(`Upload failed: ${xhr.status} - ${xhr.statusText}`);
        setUploadProgress(0);
        setLoading(false);
      };

      xhr.ontimeout = () => {
        setError("Upload timed out. Please try again.");
        setUploadProgress(0);
        setLoading(false);
      };

      xhr.timeout = 10000;
      xhr.send(formData);
    },
    [file, setFileId, onUploadSuccess]
  );

  return (
    <div className="file-upload-container">
      {!file && !loading && !success && (
        <button id="get-started-btn" onClick={() => document.getElementById("fileInput").click()} disabled={loading}>
          Get Started
        </button>
      )}
      <input
        type="file"
        id="fileInput"
        style={{ display: "none" }}
        onChange={handleFileChange}
        disabled={loading}
      />
      {file && !loading && !success && (
        <div className="file-selected">
          <p>Selected file: {file.name}</p>
          <div className="button-group">
            <button onClick={handleSubmit} className="upload-btn">
              Upload File
            </button>
            <button onClick={() => setFile(null)} className="cancel-btn">
              Cancel
            </button>
          </div>
        </div>
      )}
      {loading && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${uploadProgress}%` }}>
            {uploadProgress}%
          </div>
        </div>
      )}
      {error && <p className="error-message">{error}</p>}
      {success && (
        <div className="success-message">
          <p>{success}</p>
          <button onClick={() => { setSuccess(""); setFile(null); }} className="upload-another-btn">
            Upload Another File
          </button>
        </div>
      )}
    </div>
  );
};

export default FileUpload;