import React, { useState } from "react";
import "../Chat/Chat.css";

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

export default Chat;