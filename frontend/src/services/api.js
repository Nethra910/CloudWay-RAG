import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL;

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const askQuestion = async (
  question,
  history = [],
  conversationSummary = "",
) => {
  const response = await api.post("/chat", {
    message: question,
    history,
    summary: conversationSummary,
  });

  return response.data;
};

export default api;
