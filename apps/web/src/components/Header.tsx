"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Terminal, Shield, User as UserIcon, LogOut } from "lucide-react";
import { clearToken } from "@/lib/api";

export function Header() {
  const [userName, setUserName] = useState<string>("Operator");
  const [orgName, setOrgName] = useState<string>("MailRadar Org");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("mailradar_user");
      if (stored) {
        const u = JSON.parse(stored);
        if (u.email) setUserName(u.email.split("@")[0]);
      }
    } catch {}
  }, []);

  const handleLogout = () => {
    clearToken();
    window.location.href = "/login";
  };

  return (
    <header className="h-16 border-b border-[#1a2338] bg-[#0a0f1d]/80 backdrop-blur px-8 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center space-x-4">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400 bg-[#141d33] border border-[#222e4d] px-2.5 py-1 rounded">
          {orgName}
        </span>
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>API v1 Connected (Port 8000)</span>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        <Link
          href="/approvals"
          className="text-xs font-medium text-amber-300 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-md hover:bg-amber-500/20 transition-colors"
        >
          Approval Queue
        </Link>

        <div className="flex items-center space-x-2 bg-[#141d33] border border-[#222e4d] px-3 py-1.5 rounded-lg text-sm text-slate-200">
          <UserIcon className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-xs font-medium">{userName}</span>
        </div>

        <button
          onClick={handleLogout}
          title="Sign out"
          className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-[#161f36] rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
