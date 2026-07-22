"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Brain, FileText, BarChart3 } from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    {
      name: "Command Center",
      href: "/",
      icon: LayoutDashboard,
    },
    {
      name: "Past Meetings",
      href: "/meetings",
      icon: FileText,
    },
    {
      name: "Org Memory",
      href: "/search",
      icon: Brain,
    },
    {
      name: "Analytics",
      href: "/analytics",
      icon: BarChart3,
    },
  ];

  return (
    <aside className="w-64 glass-panel border-y-0 border-l-0 flex flex-col hidden md:flex shrink-0">
      <div className="p-6 border-b border-white/10">
        <h1 className="text-xl font-bold gradient-text tracking-tight flex items-center gap-2">
          <Brain className="w-6 h-6 text-blue-400" />
          MeetingMind AI
        </h1>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all border ${
                isActive
                  ? "bg-blue-500/10 text-blue-400 border-blue-500/30 font-semibold shadow-sm"
                  : "text-slate-400 border-transparent hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
