import { createServerSupabase } from "@/lib/supabase";
import { NextResponse } from "next/server";

export async function GET() {
  const supabase = await createServerSupabase();
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  const { count: portfolioCount } = await supabase
    .from("portfolios")
    .select("*", { count: "exact", head: true })
    .eq("owner_id", user.id);

  const { count: modelCount } = await supabase
    .from("model_snapshots")
    .select("*", { count: "exact", head: true })
    .eq("status", "PUBLISHED");

  return NextResponse.json({
    portfolioCount: portfolioCount ?? 0,
    modelPublished: (modelCount ?? 0) > 0,
    totalValue: null,
    cash: null,
  });
}
