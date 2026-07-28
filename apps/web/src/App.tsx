import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { RoleRoute } from "./auth/RoleRoute";
import { ChallengeListPage } from "./pages/ChallengeListPage";
import { DashboardPage } from "./pages/DashboardPage";
import { AuthoringPage } from "./pages/AuthoringPage";
import { LoginPage } from "./pages/LoginPage";
import { ProfilePage } from "./pages/ProfilePage";
import { PeoplePage } from "./pages/PeoplePage";
import { ReviewPage } from "./pages/ReviewPage";
import { SearchPage } from "./pages/SearchPage";
import { SolutionPage } from "./pages/SolutionPage";
import { WorkflowPage } from "./pages/WorkflowPage";
import { copy } from "./content/uiCopy";

export function App() {
  return <Routes><Route path="/login" element={<LoginPage />} /><Route element={<ProtectedRoute />}><Route element={<AppShell />}><Route path="/" element={<DashboardPage />} /><Route path="/dashboard" element={<Navigate replace to="/" />} /><Route path="/search" element={<SearchPage />} /><Route path="/solutions/new" element={<AuthoringPage />} /><Route path="/drafts" element={<ChallengeListPage status="draft" title={copy.nav.drafts} />} /><Route path="/solutions/:challengeId" element={<SolutionPage />} /><Route path="/solutions/:challengeId/preview" element={<SolutionPage />} /><Route path="/solutions/:challengeId/edit" element={<AuthoringPage />} /><Route path="/people" element={<PeoplePage />} /><Route path="/people/:userId" element={<ProfilePage />} /><Route path="/forbidden" element={<WorkflowPage kind="forbidden" />} /><Route element={<RoleRoute roles={["reviewer", "administrator"]} />}><Route path="/reviews" element={<ReviewPage />} /></Route><Route element={<RoleRoute roles={["administrator"]} />}><Route path="/admin/users" element={<WorkflowPage kind="admin" />} /></Route><Route path="*" element={<WorkflowPage kind="notFound" />} /></Route></Route></Routes>;
}
