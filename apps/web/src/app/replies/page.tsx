"use client";

import { useEffect, useState } from "react";
import { MessageSquareQuote, ShieldAlert, CheckCircle2, UserX } from "lucide-react";
import { addSuppression } from "@/lib/api";

export default function RepliesPage() {
  const [suppressEmail, setSuppressEmail] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  const handleManualOptOut = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!suppressEmail.trim()) return;

    try {
      await addSuppression(suppressEmail.trim(), "OPT_OUT", "Manual opt-out processed from replies inbox.");
      setNotice(`Address ${suppressEmail} has been permanently added to the suppression list.`);
      setSuppressEmail("");
    } catch (err: any) {
      alert("Failed to suppress address: " + err.message);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Reply & Opt-Out Synchronization</h1>
        <p className="text-sm text-slate-400 mt-1">
          Monitor inbound collaboration replies and enforce instant recipient opt-out suppression.
        </p>
      </div>

      {notice && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm">
          {notice}
        </div>
      )}

      {/* Quick Opt-Out Enforcement Card */}
      <div className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740] space-y-4">
        <div className="flex items-center space-x-2 text-rose-400">
          <UserX className="w-5 h-5" />
          <h2 className="text-base font-semibold text-white">Manual Recipient Suppression / Opt-Out</h2>
        </div>
        <p className="text-xs text-slate-400">
          Entering an email here guarantees it will be permanently excluded from all future discovery runs and campaigns.
        </p>

        <form onSubmit={handleManualOptOut} className="flex gap-3">
          <input
            type="email"
            required
            value={suppressEmail}
            onChange={(e) => setSuppressEmail(e.target.value)}
            placeholder="recipient@example.org"
            className="flex-1 px-4 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs rounded-lg transition-colors"
          >
            Permanently Suppress Address
          </button>
        </form>
      </div>

      {/* Simulated Replies Inbox */}
      <div className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740] space-y-4">
        <h2 className="text-base font-semibold text-white">Recent Inbound Synchronizations</h2>
        <div className="divide-y divide-[#162035]">
          <div className="py-4 flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-semibold text-white">alex.rivera@distributed-mesh.org</span>
                <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded font-mono">
                  POSITIVE / INTERESTED
                </span>
              </div>
              <p className="text-xs text-slate-400">
                "Thanks for reaching out! We'd be happy to discuss collaboration on the mesh telemetry drivers."
              </p>
            </div>
            <span className="text-xs text-slate-500 font-mono">2h ago</span>
          </div>
        </div>
      </div>
    </div>
  );
}
