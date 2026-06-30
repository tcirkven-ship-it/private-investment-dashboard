import { redirect } from "next/navigation";
import { createServerSupabase } from "@/lib/supabase";

export default async function Home() {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (user) {
    redirect("/portfolios");
  } else {
    redirect("/login");
  }
}
