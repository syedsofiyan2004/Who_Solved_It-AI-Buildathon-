import { useNavigate } from "react-router-dom";

import { copy } from "../content/uiCopy";
import { Button } from "../components/ui/Button";
import { PageHeader } from "../components/ui/PageHeader";
import { StatePanel } from "../components/ui/StatePanel";

type WorkflowKind = "admin" | "forbidden" | "notFound";

const configuration = {
  admin: { title: copy.page.adminTitle, description: copy.page.adminBody, state: "denied" },
  forbidden: { title: copy.state.permissionTitle, description: copy.state.permissionBody, state: "denied" },
  notFound: { title: copy.page.notFoundTitle, description: copy.page.notFoundBody, state: "notFound" }
} as const;

export function WorkflowPage({ kind }: { kind: WorkflowKind }) {
  const navigate = useNavigate();
  const page = configuration[kind];
  return <div className="space-y-6"><PageHeader title={page.title} description={page.description} action={kind === "notFound" ? <Button onClick={() => navigate("/")}>{copy.nav.dashboard}</Button> : undefined} /><StatePanel kind={page.state} /></div>;
}
