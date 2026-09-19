import { Route, Routes } from "react-router-dom";

import DashboardLayout from "./layouts/DashboardLayout";
import ComingSoon from "./pages/ComingSoon";
import Dashboard from "./pages/Dashboard";
import DatasetExplorer from "./pages/DatasetExplorer";
import Experiments from "./pages/Experiments";
import Explainability from "./pages/Explainability";
import FlowInvestigation from "./pages/FlowInvestigation";
import LivePrediction from "./pages/LivePrediction";
import ModelComparison from "./pages/ModelComparison";
import ModelTraining from "./pages/ModelTraining";
import PcapAnalyzer from "./pages/PcapAnalyzer";
import Preprocessing from "./pages/Preprocessing";
import Reports from "./pages/Reports";
import SecurityAlerts from "./pages/SecurityAlerts";
import TrafficExplorer from "./pages/TrafficExplorer";
import { ToastProvider } from "./hooks/useToast";

export default function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="datasets" element={<DatasetExplorer />} />
          <Route path="preprocessing" element={<Preprocessing />} />
          <Route path="training" element={<ModelTraining />} />
          <Route path="comparison" element={<ModelComparison />} />
          <Route path="experiments" element={<Experiments />} />
          <Route path="predict" element={<LivePrediction />} />
          <Route path="explainability" element={<Explainability />} />
          <Route path="pcap" element={<PcapAnalyzer />} />
          <Route path="traffic" element={<TrafficExplorer />} />
          <Route path="traffic/:id" element={<FlowInvestigation />} />
          <Route path="alerts" element={<SecurityAlerts />} />
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<ComingSoon title="Settings" phase="a later phase" />} />
        </Route>
      </Routes>
    </ToastProvider>
  );
}
