import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { RoleRoute } from "./auth/RoleRoute";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { SearchPage } from "./pages/SearchPage";
import { SolutionPage } from "./pages/SolutionPage";
import { WorkflowPage } from "./pages/WorkflowPage";

export function App() {
  return <Routes><Route path="/login" element={<LoginPage />} /><Route element={<ProtectedRoute />}><Route element={<AppShell />}><Route path="/" element={<DashboardPage />} /><Route path="/dashboard" element={<Navigate replace to="/" />} /><Route path="/search" element={<SearchPage />} /><Route path="/solutions/new" element={<WorkflowPage kind="authoring" />} /><Route path="/solutions/:challengeId" element={<SolutionPage />} /><Route path="/solutions/:challengeId/preview" element={<SolutionPage />} /><Route path="/solutions/:challengeId/edit" element={<WorkflowPage kind="authoring" />} /><Route path="/people/:userId" element={<WorkflowPage kind="profile" />} /><Route path="/forbidden" element={<WorkflowPage kind="forbidden" />} /><Route element={<RoleRoute roles={["reviewer", "administrator"]} />}><Route path="/reviews" element={<WorkflowPage kind="reviews" />} /></Route><Route element={<RoleRoute roles={["administrator"]} />}><Route path="/admin/users" element={<WorkflowPage kind="admin" />} /></Route><Route path="*" element={<WorkflowPage kind="notFound" />} /></Route></Route></Routes>;
}
