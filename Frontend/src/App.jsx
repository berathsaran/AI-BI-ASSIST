import React, { useState } from "react";
import Dashboard from "./components/Dashboard/Dashboard";
import FileUpload from "./components/FileUpload/FileUpload";
import Chat from "./components/Chat/Chat";
import "./App.css";

function App() {
  const [fileId, setFileId] = useState(null);
  const [isDarkMode, setIsDarkMode] = useState(true);

  const handleUploadSuccess = (data) => {
    setFileId(data.file_id);
    console.log("Upload successful:", data);
  };

  return (
    <div className={`app ${isDarkMode ? "dark" : "light"}`}>
      <header className="header">
        <div className="logo">AI-Business Intelligence</div>
        <nav>
          <button onClick={() => setIsDarkMode(prev => !prev)} className="theme-toggle">
            {isDarkMode ? "☀️ Light" : "🌙 Dark"}
          </button>
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