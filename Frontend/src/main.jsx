import React from 'react';
import { createRoot } from 'react-dom/client'; // React 19 uses createRoot
import App from './App.jsx';
import './index.css'; // Optional global CSS

const root = createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);