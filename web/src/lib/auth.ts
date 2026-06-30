"use server";

import { createServerSupabase } from "./supabase";
import { redirect } from "next/navigation";

export async function signIn(email: string, password: string) {
  const supabase = await createServerSupabase();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) return { error: error.message };
  redirect("/portfolios");
}

export async function signOut() {
  const supabase = await createServerSupabase();
  await supabase.auth.signOut();
  redirect("/login");
}

export async function getSession() {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}
