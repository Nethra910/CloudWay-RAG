import { useState } from "react";

import Header from "./components/Header";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";

import { askQuestion } from "./services/api";

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleAsk = async (question) => {
    if (loading) {
      return;
    }

    // Build history BEFORE adding the current question
    const history = messages.map((message) => ({
      role: message.role,
      content: message.content,
    }));

    // Add current user message to UI
    const userMessage = {
      role: "user",
      content: question,
    };

    setMessages((previousMessages) => [...previousMessages, userMessage]);

    try {
      setLoading(true);

      const data = await askQuestion(question, history, "");

      const assistantMessage = {
        role: "assistant",
        content: data.answer,
        sources: data.sources,
      };

      setMessages((previousMessages) => [
        ...previousMessages,
        assistantMessage,
      ]);
    } catch (error) {
      console.error("API error:", error);

      const errorMessage = {
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
      };

      setMessages((previousMessages) => [...previousMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-slate-50">
      <Header />

      <ChatWindow messages={messages} loading={loading} />

      <ChatInput onAsk={handleAsk} loading={loading} />
    </div>
  );
}

export default App;
