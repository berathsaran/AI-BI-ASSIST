import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css"; // Optional global styles

// Error boundary component to catch rendering errors
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-container">
          <h1>Oops! Something Went Wrong</h1>
          <p>{this.state.error?.message || "An unexpected error occurred."}</p>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Create root and render with error boundary and strict mode
const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found. Ensure there is a <div id='root'></div> in your HTML.");
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);

// Optional: Enable hot module replacement in development
if (import.meta.hot) {
  import.meta.hot.accept(() => {
    root.render(
      <React.StrictMode>
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </React.StrictMode>
    );
  });
}

// Inline styles for ErrorBoundary (to match project theme)
const styleSheet = document.createElement("style");
styleSheet.textContent = `
  .error-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: #fff;
    padding: 20px;
    text-align: center;
    font-family: 'Poppins', sans-serif;
  }
  .error-container h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #ff4b4b;
    margin-bottom: 20px;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }
  .error-container p {
    font-size: 1.2rem;
    color: #e0e7ff;
    margin-bottom: 30px;
  }
  .error-container button {
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
  .error-container button:hover {
    background: #fff;
    transform: scale(1.05);
  }
  @media (max-width: 768px) {
    .error-container h1 {
      font-size: 2rem;
    }
    .error-container p {
      font-size: 1rem;
    }
    .error-container button {
      font-size: 1rem;
      padding: 10px 20px;
    }
  }
`;
document.head.appendChild(styleSheet);