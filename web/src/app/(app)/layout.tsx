import { createServerSupabase } from "@/lib/supabase";
import Sidebar from "@/components/layout/Sidebar";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  let isOwner = false;

  try {
    const supabase = await createServerSupabase();
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      const { data: profile } = await supabase
        .from("profiles")
        .select("is_owner")
        .eq("id", user.id)
        .single();
      isOwner = profile?.is_owner === true;
    }
  } catch {
    // Non-critical – owner gate falls back to false
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar isOwner={isOwner} />
      <main className="flex-1 overflow-y-auto bg-neutral-950">
        <div className="max-w-7xl mx-auto px-6 py-6">
          {children}
        </div>
      </main>
    </div>
  );
}
