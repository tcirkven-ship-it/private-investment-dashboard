"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, TrendingUp, Briefcase, Settings, LogOut, ChevronLeft,
} from "lucide-react";
import { signOut } from "@/lib/auth";
import { useState } from "react";

const mainNavItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/model", label: "Quarterly Top 30", icon: TrendingUp },
  { href: "/portfolios", label: "My Portfolio", icon: Briefcase },
];

const adminNavItems = [
  { href: "/admin/model-review", label: "Admin / Model Review", icon: Settings },
];

export default function Sidebar({ isOwner }: { isOwner?: boolean }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`${collapsed ? "w-16" : "w-56"} transition-all duration-200 flex flex-col border-r border-neutral-800 bg-neutral-950/50 backdrop-blur-sm`}>
      <div className="flex items-center justify-between px-4 h-14 border-b border-neutral-800">
        {!collapsed && <span className="text-sm font-semibold tracking-tight">Dashboard</span>}
        <button onClick={() => setCollapsed(!collapsed)} className="p-1 rounded hover:bg-neutral-800 text-neutral-500">
          <ChevronLeft className={`w-4 h-4 transition-transform ${collapsed ? "rotate-180" : ""}`} />
        </button>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {mainNavItems.map((item) => {
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
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
        {isOwner && (
          <div className="pt-2 mt-2 border-t border-neutral-800">
            {adminNavItems.map((item) => {
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
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </div>
        )}
      </nav>
      <div className="p-2 border-t border-neutral-800">
        <button onClick={() => signOut()} className="nav-link w-full">
          <LogOut className="w-4 h-4 shrink-0" />
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </aside>
  );
}
