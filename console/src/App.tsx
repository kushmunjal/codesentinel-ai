import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { SidebarLayout } from "./components/layout/SidebarLayout";
import Overview from "./pages/Overview";
import PullRequests from "./pages/PullRequests";
import Issues from "./pages/Issues";
import Evaluation from "./pages/Evaluation";
import Settings from "./pages/Settings";
import Activity from "./pages/Activity";
import Login from "./pages/Login";

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Authentication Route */}
          <Route path="/login" element={<Login />} />

          {/* Console Application Routes wrapped in SidebarLayout */}
          <Route
            path="/*"
            element={
              <SidebarLayout>
                <Routes>
                  <Route path="/" element={<Overview />} />
                  <Route path="/prs" element={<PullRequests />} />
                  <Route path="/issues" element={<Issues />} />
                  <Route path="/eval" element={<Evaluation />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/activity" element={<Activity />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </SidebarLayout>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
