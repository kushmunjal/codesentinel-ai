import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { SidebarLayout } from "./components/layout/SidebarLayout";
import Overview from "./pages/Overview";
import PullRequests from "./pages/PullRequests";
import Issues from "./pages/Issues";
import Evaluation from "./pages/Evaluation";
import Settings from "./pages/Settings";
import Activity from "./pages/Activity";

function App() {
  return (
    <Router>
      <SidebarLayout>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/prs" element={<PullRequests />} />
          <Route path="/issues" element={<Issues />} />
          <Route path="/eval" element={<Evaluation />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/activity" element={<Activity />} />
        </Routes>
      </SidebarLayout>
    </Router>
  );
}

export default App;
