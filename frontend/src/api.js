import axios from "axios";

const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();
const API_DEBUG = import.meta.env.DEV;

const api = axios.create({
  baseURL: configuredApiUrl || "http://localhost:8000",
});

// Keep these logs in development while the frontend/backend contract is being verified.
api.interceptors.response.use(
  (response) => {
    if (API_DEBUG) {
      console.debug(`[Fraud API] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data);
    }
    return response;
  },
  (error) => {
    if (API_DEBUG) {
      console.error(`[Fraud API] ${error.config?.method?.toUpperCase() || "REQUEST"} ${error.config?.url || ""} failed`, error.response?.data || error.message);
    }
    return Promise.reject(error);
  }
);

export function getApiErrorMessage(error, fallback = "Unable to reach the fraud detection service.") {
  const detail = error.response?.data?.detail;
  return typeof detail === "string" ? detail : detail?.message || error.message || fallback;
}

export async function getMetrics() {
  const { data } = await api.get("/api/metrics");
  return data;
}

export async function getTransactions() {
  const { data } = await api.get("/api/transactions");
  return data;
}

export async function generateTransactions(count = 25) {
  const { data } = await api.post("/api/transactions/generate", { count });
  return data;
}

export async function uploadTransactions(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/api/transactions/upload", formData);
  return data;
}

export async function downloadTransactionTemplate() {
  const response = await api.get("/api/transactions/template", { responseType: "blob" });
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = "transaction-upload-template.csv";
  link.click();
  URL.revokeObjectURL(url);
}

export async function predictTransaction(transactionId) {
  const { data } = await api.post("/api/predict", { transaction_id: transactionId });
  return data;
}

export async function predictAllTransactions() {
  const { data } = await api.post("/api/predict/all");
  return data;
}

export async function explainTransaction(transactionId) {
  const { data } = await api.post("/api/explain", { transaction_id: transactionId });
  return data;
}

export async function getAnalytics() {
  const { data } = await api.get("/api/analytics");
  return data;
}

export async function getTimeline(transactionId) {
  const { data } = await api.get(`/api/investigations/${transactionId}/timeline`);
  return data;
}

export async function recordInvestigationAction(transactionId, action, note = "") {
  const { data } = await api.post("/api/investigations/action", { transaction_id: transactionId, action, note });
  return data;
}

export async function getModelRuns() {
  const { data } = await api.get("/api/models/runs");
  return data;
}
