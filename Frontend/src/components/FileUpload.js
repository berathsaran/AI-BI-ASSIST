import React, { useState, useCallback } from "react";

const FileUpload = ({ setFileId, onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Supported MIME types and their descriptions
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
      return;
    }

    if (!ALLOWED_TYPES[selectedFile.type]) {
      setError(
        `Invalid file type. Supported types: ${Object.values(ALLOWED_TYPES).join(", ")}`
      );
      setFile(null);
      return;
    }

    // Optional: Check file size (e.g., max 16MB)
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (selectedFile.size > maxSize) {
      setError(`File size exceeds limit of ${maxSize / (1024 * 1024)}MB`);
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setError("");
    setSuccess("");
  }, []);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();

      if (!file) {
        setError("Please select a file to upload.");
        return;
      }

      setLoading(true);
      setError("");
      setSuccess("");

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch("http://localhost:5000/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Upload failed: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        setFileId(data.file_id);
        setSuccess(`File "${data.filename}" uploaded successfully!`);
        setFile(null); // Reset file input
        if (onUploadSuccess) onUploadSuccess(data); // Callback for parent component
      } catch (err) {
        setError(err.message || "Failed to upload file. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    [file, setFileId, onUploadSuccess]
  );

  const resetMessages = () => {
    setError("");
    setSuccess("");
  };

  return (
    <div className="file-upload-container">
      <h2>Upload Dataset</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          onChange={handleFileChange}
          onClick={resetMessages} // Clear messages when selecting a new file
          disabled={loading}
          accept={Object.keys(ALLOWED_TYPES)
            .map((type) => `.${type.split("/")[1]}`)
            .join(",")}
          className="file-input"
        />
        <button type="submit" disabled={loading || !file} className="upload-button">
          {loading ? "Uploading..." : "Upload"}
        </button>
      </form>
      {error && <p className="error-message">{error}</p>}
      {success && <p className="success-message">{success}</p>}
    </div>
  );
};

// Inline CSS (can be moved to a separate file)
const styles = `
  .file-upload-container {
    padding: 20px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    max-width: 400px;
    margin: 20px auto;
  }
  .file-upload-container h2 {
    color: #333;
    text-align: center;
    margin-bottom: 15px;
    font-size: 1.5em;
  }
  .file-upload-container form {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .file-input {
    padding: 5px;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  .upload-button {
    padding: 10px;
    background-color: #007BFF;
    color: #fff;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s;
  }
  .upload-button:disabled {
    background-color: #ddd;
    cursor: not-allowed;
  }
  .upload-button:hover:not(:disabled) {
    background-color: #0056b3;
  }
  .error-message {
    color: red;
    text-align: center;
    margin-top: 10px;
    font-size: 0.9em;
  }
  .success-message {
    color: green;
    text-align: center;
    margin-top: 10px;
    font-size: 0.9em;
  }
`;

const styleSheet = document.createElement("style");
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);

export default FileUpload;