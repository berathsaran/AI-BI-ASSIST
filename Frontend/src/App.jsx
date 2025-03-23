import React, { useState } from "react";
import Dashboard from "./components/Dashboard/Dashboard";
import FileUpload from "./components/FileUpload/FileUpload";
import Chat from "./components/Chat/Chat";
import "./App.css";

function App() {
  const [fileId, setFileId] = useState(null);
  const [isDarkMode, setIsDarkMode] = useState(true); // Default to dark mode

  const handleUploadSuccess = (data) => {
    console.log("Upload successful:", data);
  };

  const toggleTheme = () => setIsDarkMode(prev => !prev);

  return (
    <div className={`app ${isDarkMode ? "dark" : "light"}`}>
      <header className="header">
        <div className="logo">AI-Business Intelligence</div>
        <nav>
          <button onClick={toggleTheme} className="theme-toggle">
            {isDarkMode ? "☀️ Light" : "🌙 Dark"}
          </button>
          {!fileId && (
            <button onClick={() => document.getElementById("fileInput").click()}>
              Upload Your Dataset
            </button>
          )}
          <input
            type="file"
            id="fileInput"
            style={{ display: "none" }}
            onChange={(e) => {
              const file = e.target.files[0];
              if (file) {
                const formData = new FormData();
                formData.append("file", file);
                fetch("http://localhost:5000/upload", { method: "POST", body: formData })
                  .then(res => res.json())
                  .then(data => setFileId(data.file_id))
                  .catch(err => console.error("Upload failed:", err));
              }
            }}
          />
        </nav>
      </header>
      <main>
        {!fileId ? (
          <div className="welcome">
            <h1>Welcome to AI-BI</h1>
            <p>Upload a dataset to unlock business insights!</p>
            <FileUpload setFileId={setFileId} onUploadSuccess={handleUploadSuccess} />
          </div>
        ) : (
          <>
            <Dashboard fileId={fileId} />
            <Chat fileId={fileId} />
          </>
        )}
      </main>
      <footer className="footer">
        <p>© 2025 AI-BI by Berath</p>
      </footer>
    </div>
  );
}

export default App;