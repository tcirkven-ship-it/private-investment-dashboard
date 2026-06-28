import { createServerSupabase } from "@/lib/supabase";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import ModelReviewActions from "./ModelReviewActions";

export const metadata = { title: "Model Review" };

export default async function ModelReviewPage() {
  const supabase = await createServerSupabase();
  const { data: snapshots, error } = await supabase
    .from("model_snapshots")
    .select("id, snapshot_id, status, effective_date")
    .in("status", ["DRAFT", "VALIDATED", "APPROVED"])
    .order("effective_date", { ascending: false });

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
        <h1 className="text-xl font-semibold">Model Review</h1>
      </div>

      {error && <div className="text-sm text-red-400">{error.message}</div>}

      {!snapshots || snapshots.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No snapshots to review.</p>
        </div>
      ) : (
        <ModelReviewActions snapshots={snapshots as Array<{ id: string; snapshot_id: string; status: string; effective_date: string }>} />
      )}
    </div>
  );
}
