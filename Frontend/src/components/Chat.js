import React, { useState } from "react";

const Chat = ({ fileId }) => {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }
    setLoading(true);
    setError(null);
    setAnswer("");
    try {
      const response = await fetch("http://localhost:5000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: fileId, question }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to get an answer.");
      }
      const data = await response.json();
      setAnswer(data.answer);
    } catch (err) {
      setError(err.message);
      setAnswer("");
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = () => {
    setQuestion("");
    setAnswer("");
    setError(null);
  };

  return (
    <div className="chat">
      <h2>Instant Business Insights</h2>
      <div className="input-section">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="E.g., What’s the top category?"
          disabled={loading}
        />
        <button onClick={handleAskQuestion} disabled={loading}>
          {loading ? "Thinking..." : "Ask"}
        </button>
        <button onClick={handleClearHistory} disabled={loading}>Clear</button>
      </div>
      {error && <div className="error">{error}</div>}
      {answer && (
        <div className="answer">
          <p><strong>You:</strong> {question}</p>
          <p><strong>Insight:</strong> {answer}</p>
        </div>
      )}
    </div>
  );
};

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

  .chat {
    padding: 40px 20px;
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    color: #fff;
  }

  .chat h2 {
    font-size: 2.8rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 40px;
    text-transform: uppercase;
    letter-spacing: 2px;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    animation: fadeInDown 1s ease;
  }

  .input-section {
    display: flex;
    gap: 15px;
    width: 100%;
    max-width: 800px;
    margin-bottom: 30px;
    flex-wrap: wrap;
    justify-content: center;
  }

  .input-section input {
    flex: 1;
    min-width: 250px;
    padding: 15px 25px;
    border: none;
    border-radius: 30px;
    font-size: 1.2rem;
    background: #fff;
    color: #1e3c72;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    transition: box-shadow 0.3s ease, transform 0.3s ease;
  }

  .input-section input:focus {
    outline: none;
    box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
    transform: translateY(-2px);
  }

  .input-section button {
    padding: 15px 30px;
    background: #2a5298;
    color: #fff;
    border: none;
    border-radius: 30px;
    font-size: 1.2rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.3s ease, transform 0.3s ease;
  }

  .input-section button:hover:not(:disabled) {
    background: #00d4ff;
    transform: scale(1.05);
  }

  .input-section button:disabled {
    background: #b0c4de;
    cursor: not-allowed;
  }

  .error {
    background: rgba(255, 75, 75, 0.1);
    color: #ff4b4b;
    padding: 20px;
    border-radius: 12px;
    font-size: 1.2rem;
    margin-bottom: 30px;
    max-width: 800px;
    width: 100%;
    text-align: center;
    border: 2px solid #ff4b4b;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    animation: fadeInUp 0.5s ease;
  }

  .answer {
    background: #fff;
    padding: 25px;
    border-radius: 16px;
    max-width: 800px;
    width: 100%;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    animation: fadeInUp 0.8s ease;
    transition: transform 0.3s ease;
  }

  .answer:hover {
    transform: translateY(-5px);
  }

  .answer p {
    margin: 15px 0;
    font-size: 1.2rem;
    color: #1e3c72;
  }

  .answer strong {
    color: #2a5298;
    font-weight: 600;
  }

  @keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @media (max-width: 768px) {
    .chat h2 {
      font-size: 2rem;
    }
    .input-section input, .input-section button {
      font-size: 1rem;
      padding: 12px 20px;
    }
    .error, .answer p {
      font-size: 1rem;
    }
  }
`;

const styleSheet = document.createElement("style");
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);

export default Chat;