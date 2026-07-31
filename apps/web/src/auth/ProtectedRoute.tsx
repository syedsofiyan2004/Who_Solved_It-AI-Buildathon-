import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthProvider";

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) {
    return (
      <div className="grid min-h-screen place-items-center bg-canvas text-text">
        <div className="rounded-[12px] border border-border bg-surface px-5 py-4 text-sm text-text-muted shadow-soft">
          Restoring your workspace session
        </div>
      </div>
    );
  }
  return isAuthenticated ? <Outlet /> : <Navigate replace to="/login" state={{ from: location }} />;
}
