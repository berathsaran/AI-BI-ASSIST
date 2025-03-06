import React, { useState } from "react";
import Dashboard from "./components/Dashboard";
import Chat from "./components/Chat";

const App = () => {
  const [fileId, setFileId] = useState(null);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    fetch("http://localhost:5000/upload", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        setFileId(data.file_id);
        alert(`File "${data.filename}" uploaded successfully!`);
      })
      .catch((err) => alert("Upload failed: " + err.message));
  };

  return (
    <div className="app">
      <header className="header">
        <div className="logo">AI-BI</div>
        <nav>
          <button onClick={() => document.getElementById("fileInput").click()}>
            Upload Dataset
          </button>
          <input
            type="file"
            id="fileInput"
            style={{ display: "none" }}
            onChange={handleFileUpload}
          />
        </nav>
      </header>
      <main>
        {fileId ? (
          <>
            <Dashboard fileId={fileId} />
            <Chat fileId={fileId} />
          </>
        ) : (
          <div className="welcome">
            <h1>Welcome to AI-BI</h1>
            <p>Upload a dataset to unlock powerful business insights!</p>
            <button onClick={() => document.getElementById("fileInput").click()}>
              Get Started
            </button>
          </div>
        )}
      </main>
      <footer className="footer">
        <p>&copy; 2025 AI-BI by xAI. All rights reserved.</p>
      </footer>
    </div>
  );
};

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: 'Poppins', sans-serif;
  }

  .app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    background: #f0f4f8;
  }

  .header {
    background: #1e3c72;
    padding: 20px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    position: sticky;
    top: 0;
    z-index: 1000;
  }

  .header .logo {
    font-size: 2rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .header nav button {
    padding: 12px 25px;
    background: #00d4ff;
    color: #1e3c72;
    border: none;
    border-radius: 30px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.3s ease, transform 0.3s ease;
  }

  .header nav button:hover {
    background: #fff;
    transform: scale(1.05);
  }

  main {
    flex: 1;
    padding: 20px;
  }

  .welcome {
    text-align: center;
    padding: 60px 20px;
    background: #fff;
    border-radius: 16px;
    max-width: 600px;
    margin: 40px auto;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    animation: fadeInUp 1s ease;
  }

  .welcome h1 {
    font-size: 2.5rem;
    color: #1e3c72;
    margin-bottom: 20px;
  }

  .welcome p {
    font-size: 1.2rem;
    color: #555;
    margin-bottom: 30px;
  }

  .welcome button {
    padding: 15px 40px;
    background: #2a5298;
    color: #fff;
    border: none;
    border-radius: 30px;
    font-size: 1.2rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.3s ease, transform 0.3s ease;
  }

  .welcome button:hover {
    background: #00d4ff;
    transform: scale(1.05);
  }

  .footer {
    background: #1e3c72;
    padding: 20px;
    text-align: center;
    color: #fff;
    font-size: 1rem;
    box-shadow: 0 -4px 15px rgba(0, 0, 0, 0.2);
  }

  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @media (max-width: 768px) {
    .header {
      padding: 15px 20px;
      flex-direction: column;
      gap: 15px;
    }
    .header .logo {
      font-size: 1.8rem;
    }
    .header nav button {
      font-size: 1rem;
      padding: 10px 20px;
    }
    .welcome h1 {
      font-size: 2rem;
    }
    .welcome p {
      font-size: 1rem;
    }
    .welcome button {
      font-size: 1rem;
      padding: 12px 30px;
    }
    .footer {
      font-size: 0.9rem;
    }
  }
`;

const styleSheet = document.createElement("style");
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);

export default App;