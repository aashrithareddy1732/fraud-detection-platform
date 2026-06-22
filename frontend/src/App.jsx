import { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import Analytics from "./pages/Analytics.jsx";
import Investigation from "./pages/Investigation.jsx";
import ModelEvaluation from "./pages/ModelEvaluation.jsx";
import Transactions from "./pages/Transactions.jsx";

const tabs = [
  { id: "dashboard", label: "Risk Overview" },
  { id: "transactions", label: "Transaction Monitor" },
  { id: "investigation", label: "Case Investigation" },
  { id: "analytics", label: "Fraud Analytics" },
  { id: "models", label: "Model Performance" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedTransactionId, setSelectedTransactionId] = useState("");
  const [dataVersion, setDataVersion] = useState(0);
  const [darkMode, setDarkMode] = useState(false);

  function refreshData() {
    setDataVersion((version) => version + 1);
  }

  useEffect(() => {
    if (selectedTransactionId) {
      setActiveTab("investigation");
    }
  }, [selectedTransactionId]);

  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? "dark" : "light";
  }, [darkMode]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Fraud Risk Operations</p>
          <h1>Transaction Risk Command Center</h1>
        </div>
        <nav>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={activeTab === tab.id ? "active" : ""}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
        <button className="theme-toggle" onClick={() => setDarkMode((enabled) => !enabled)}>
          {darkMode ? "Light mode" : "Dark mode"}
        </button>
      </aside>

      <main>
        {activeTab === "dashboard" && (
          <Dashboard refreshVersion={dataVersion} onDataChanged={refreshData} />
        )}
        {activeTab === "transactions" && (
          <Transactions
            refreshVersion={dataVersion}
            onDataChanged={refreshData}
            onInvestigate={setSelectedTransactionId}
          />
        )}
        {activeTab === "investigation" && (
          <Investigation
            refreshVersion={dataVersion}
            onDataChanged={refreshData}
            selectedTransactionId={selectedTransactionId}
            onSelectTransaction={setSelectedTransactionId}
          />
        )}
        {activeTab === "analytics" && <Analytics refreshVersion={dataVersion} />}
        {activeTab === "models" && <ModelEvaluation refreshVersion={dataVersion} />}
      </main>
    </div>
  );
}
