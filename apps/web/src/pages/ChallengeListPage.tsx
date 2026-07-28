import { useQuery } from "@tanstack/react-query";
import { FileText } from "lucide-react";
import { Link } from "react-router-dom";

import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { PageHeader } from "../components/ui/PageHeader";
import { StatePanel } from "../components/ui/StatePanel";
import { copy } from "../content/uiCopy";
import { listChallenges } from "../services/api";

export function ChallengeListPage({ status, title }: { status: string; title: string }) {
  const query = useQuery({ queryKey: ["challenge-list", status], queryFn: () => listChallenges(status) });
  if (query.isLoading) return <LoadingSkeleton rows={6} />;
  if (query.isError) return <StatePanel kind="error" onRetry={() => void query.refetch()} />;
  return (
    <div className="space-y-6">
      <PageHeader title={title} />
      {query.data?.data.length ? (
        <div className="divide-y divide-border rounded-app border border-border bg-surface">
          {query.data.data.map((item) => (
            <Link className="flex items-center justify-between gap-3 px-4 py-3 text-sm hover:bg-surface-muted" key={item.id} to={`/solutions/${item.id}/edit`}>
              <span className="inline-flex min-w-0 items-center gap-3">
                <FileText className="h-4 w-4 shrink-0 text-text-muted" aria-hidden="true" />
                <span className="truncate font-medium">{item.title}</span>
              </span>
              <span className="shrink-0 rounded-control border border-border px-2 py-1 text-xs text-text-muted">{item.status}</span>
            </Link>
          ))}
        </div>
      ) : <StatePanel kind="empty" />}
    </div>
  );
}
