import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";
import App from "./App";
import Dashboard from "./pages/Dashboard";
import Transactions from "./pages/Transactions";
import AgentActivity from "./pages/AgentActivity";
import DemoSimulator from "./pages/DemoSimulator";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Dashboard />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="agent" element={<AgentActivity />} />
          <Route path="demo" element={<DemoSimulator />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
