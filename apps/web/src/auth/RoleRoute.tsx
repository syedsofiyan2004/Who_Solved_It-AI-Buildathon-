import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "./AuthProvider";

export function RoleRoute({ roles }: { roles: Array<"employee" | "reviewer" | "administrator"> }) {
  const { user } = useAuth();
  return user && roles.includes(user.role) ? <Outlet /> : <Navigate replace to="/forbidden" />;
}
