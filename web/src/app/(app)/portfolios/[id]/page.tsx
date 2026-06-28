import { notFound } from "next/navigation";
import Link from "next/link";
import { createServerSupabase } from "@/lib/supabase";
import { ArrowLeft, Trash2 } from "lucide-react";
import { deletePortfolio } from "@/lib/actions";
import DeletePortfolioButton from "./DeletePortfolioButton";

export default async function PortfolioDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  const { data: portfolio } = await supabase
    .from("portfolios")
    .select("*")
    .eq("id", id)
    .single();

  if (!portfolio) notFound();
  const isOwner = portfolio.owner_id === user?.id;

  const tabs = [
    { label: "Overview", href: "" },
    { label: "Holdings", href: `/portfolios/${id}/holdings` },
    { label: "Transactions", href: `/portfolios/${id}/transactions` },
    { label: "Performance", href: `/portfolios/${id}/performance` },
    { label: "Quarterly Review", href: `/portfolios/${id}/rebalance` },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/portfolios" className="btn-ghost p-1"><ArrowLeft className="w-4 h-4" /></Link>
          <div>
            <h1 className="text-2xl font-semibold">{portfolio.name}</h1>
            <p className="text-sm text-neutral-500 mt-0.5">Opened {portfolio.opening_date}</p>
          </div>
        </div>
        {isOwner && <DeletePortfolioButton portfolioId={id} />}
      </div>

      <div className="flex gap-1 border-b border-neutral-800 pb-0.5 overflow-x-auto">
        {tabs.map((tab) => (
          tab.href ? (
            <Link key={tab.label} href={tab.href}
              className="whitespace-nowrap px-4 py-2 text-sm font-medium text-neutral-400 hover:text-neutral-100 border-b-2 border-transparent hover:border-neutral-500 transition-colors">
              {tab.label}
            </Link>
          ) : (
            <span key={tab.label} className="whitespace-nowrap px-4 py-2 text-sm font-medium text-blue-400 border-b-2 border-blue-500">
              {tab.label}
            </span>
          )
        ))}
      </div>

      <div className="card">
        <p className="text-sm text-neutral-500">Select a tab above to view details.</p>
      </div>
    </div>
  );
}
