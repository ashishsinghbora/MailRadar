"use client";

import { useEffect, useState } from "react";
import { History, Shield, Filter, Loader2 } from "lucide-react";
import { getAuditLogs } from "@/lib/api";

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await getAuditLogs();
        setLogs(data);
      } catch {
        setLogs([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Security Audit Logs</h1>
        <p className="text-sm text-slate-400 mt-1">
          Immutable event ledger recording operator actions, authentication attempts, discovery executions, and campaign decisions.
        </p>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 flex justify-center items-center space-x-2">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Loading audit ledger...</span>
        </div>
      ) : logs.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-[#0f1626] border border-[#1d2740] text-slate-400">
          <History className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="font-semibold text-white">No audit logs recorded yet</p>
          <p className="text-xs text-slate-500 mt-1">System actions will appear here automatically.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-[#1d2740] bg-[#0f1626] overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#1d2740] bg-[#0b101c] text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Target Type</th>
                <th className="py-3 px-4">IP Address</th>
                <th className="py-3 px-4 text-right">Target ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#162035] text-sm font-mono">
              {logs.map((l) => (
                <tr key={l.id} className="hover:bg-[#131c30]">
                  <td className="py-3 px-4 text-xs text-slate-400">
                    {new Date(l.created_at).toISOString().replace("T", " ").slice(0, 19)}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs font-semibold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                      {l.action}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-300">
                    {l.target_type}
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-400">
                    {l.ip_address || "127.0.0.1"}
                  </td>
                  <td className="py-3 px-4 text-right text-xs text-slate-500">
                    {l.target_id ? l.target_id.slice(0, 8) : "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
