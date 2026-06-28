import Link from "next/link";
import { Plus, ArrowRight } from "lucide-react";
import { createServerSupabase } from "@/lib/supabase";

export const metadata = { title: "Portfolios" };

export default async function PortfoliosPage() {
  const supabase = await createServerSupabase();
  const { data: { user }, error: authError } = await supabase.auth.getUser();

  if (authError || !user) {
    return null;
  }

  const { data: portfolios, error } = await supabase
    .from("portfolios")
    .select("id, name, opening_date, starting_cash, is_archived")
    .eq("owner_id", user.id)
    .order("created_at", { ascending: false });

  if (error) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Portfolios</h1>
          <p className="text-sm text-neutral-500 mt-1">Manage your personal portfolios</p>
        </div>
        <Link href="/portfolios/new" className="btn-primary">
          <Plus className="w-4 h-4 mr-1.5" /> New Portfolio
        </Link>
      </div>

      {portfolios.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-neutral-500">No portfolios yet. Create your first one.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {portfolios.map((p) => (
            <Link key={p.id} href={`/portfolios/${p.id}`} className="card hover:bg-neutral-900/50 transition-colors block">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{p.name}</h3>
                  <p className="text-sm text-neutral-500 mt-0.5">
                    Opened {p.opening_date} · ${p.starting_cash.toLocaleString()} initial
                    {p.is_archived && <span className="ml-2 text-yellow-500">Archived</span>}
                  </p>
                </div>
                <ArrowRight className="w-4 h-4 text-neutral-500" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
