"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  TrendingUp, Briefcase, ArrowLeftRight, FileText, LogOut, ChevronLeft, Settings, BarChart3,
} from "lucide-react";
import { signOut } from "@/lib/auth";
import { useState } from "react";

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { href: "/portfolios", label: "Portfolio", icon: Briefcase },
    { href: "/performance", label: "Performance", icon: BarChart3 },
    { href: "/model", label: "Top 30", icon: TrendingUp },
    { href: "/compare", label: "Compare", icon: ArrowLeftRight },
    { href: "/instructions", label: "Instructions", icon: FileText },
    { href: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <aside className={`${collapsed ? "w-16" : "w-16 md:w-56"} transition-all duration-200 flex flex-col border-r`} style={{ borderColor: "rgba(255,255,255,0.06)", background: "#09090b" }}>
      <div className="flex items-center justify-between px-4 h-14 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        {!collapsed && <span className="text-sm font-semibold tracking-tight text-neutral-200 hidden md:inline">Investment Tracker</span>}
        <button onClick={() => setCollapsed(!collapsed)} className="p-1 rounded hover:bg-white/5 text-neutral-500 hidden md:block">
          <ChevronLeft className={`w-4 h-4 transition-transform ${collapsed ? "rotate-180" : ""}`} />
        </button>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={isActive ? "nav-link-active" : "nav-link"}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!collapsed && <span className="hidden md:inline">{item.label}</span>}
            </Link>
          );
        })}
      </nav>
      <div className="p-2 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <button onClick={() => signOut()} className="nav-link w-full">
          <LogOut className="w-4 h-4 shrink-0" />
          {!collapsed && <span className="hidden md:inline">Sign out</span>}
        </button>
      </div>
    </aside>
  );
}
