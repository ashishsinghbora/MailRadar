"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Compass,
  FolderGit2,
  Users,
  ShieldCheck,
  Send,
  CheckSquare,
  FileText,
  MessageSquareQuote,
  BarChart3,
  Layers,
  Sliders,
  History,
  Radar
} from "lucide-react";

const navigationItems = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Discover", href: "/discover", icon: Compass },
  { name: "Projects", href: "/projects", icon: FolderGit2 },
  { name: "Contacts", href: "/contacts", icon: Users },
  { name: "Verification", href: "/verification", icon: ShieldCheck },
  { name: "Campaigns", href: "/campaigns", icon: Send },
  { name: "Approval Queue", href: "/approvals", icon: CheckSquare },
  { name: "Templates", href: "/templates", icon: FileText },
  { name: "Replies", href: "/replies", icon: MessageSquareQuote },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Integrations", href: "/integrations", icon: Layers },
  { name: "Settings", href: "/settings", icon: Sliders },
  { name: "Audit Logs", href: "/audit", icon: History },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 flex-shrink-0 bg-[#0a0f1d] border-r border-[#1a2338] flex flex-col min-h-screen">
      {/* Brand Logo */}
      <div className="h-16 flex items-center px-6 border-b border-[#1a2338]">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Radar className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight text-white">MailRadar</span>
            <span className="block text-[10px] text-slate-400 font-mono uppercase tracking-wider">Intelligence</span>
          </div>
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-indigo-600/15 text-cyan-400 border border-indigo-500/30 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-[#121a2f]"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-cyan-400" : "text-slate-400"}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Ethics & Status badge */}
      <div className="p-4 border-t border-[#1a2338] bg-[#0c1222]/50">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="font-mono text-emerald-400">SSRF Guard Active</span>
        </div>
        <p className="text-[11px] text-slate-500 mt-1">Human approval mandatory before any message delivery.</p>
      </div>
    </aside>
  );
}
