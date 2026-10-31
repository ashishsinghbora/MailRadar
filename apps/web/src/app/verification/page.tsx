"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, RefreshCw, AlertCircle, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { getContacts, verifyAllContacts, verifyContact } from "@/lib/api";

export default function VerificationPage() {
  const [contacts, setContacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifyingAll, setVerifyingAll] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await getContacts();
      setContacts(data);
    } catch {
      setContacts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleVerifyAll = async () => {
    setVerifyingAll(true);
    setNotice(null);
    try {
      const res = await verifyAllContacts();
      setNotice(`Verified ${res.verified_count} contact(s) successfully.`);
      loadData();
    } catch (e: any) {
      setNotice("Batch verification encountered an issue.");
    } finally {
      setVerifyingAll(false);
    }
  };

  const validCount = contacts.filter((c) => c.verification_status === "VALID").length;
  const uncheckedCount = contacts.filter((c) => c.verification_status === "UNCHECKED").length;
  const noMxCount = contacts.filter((c) => c.verification_status === "NO_MX").length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Email Verification Engine</h1>
          <p className="text-sm text-slate-400 mt-1">
            Validate RFC syntax, confirm live DNS MX mail exchangers, and guard against temporary disposable domains.
          </p>
        </div>

        <button
          onClick={handleVerifyAll}
          disabled={verifyingAll || uncheckedCount === 0}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs rounded-lg flex items-center space-x-2 shadow-lg shadow-indigo-600/20"
        >
          {verifyingAll ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          <span>Verify All Unchecked ({uncheckedCount})</span>
        </button>
      </div>

      {notice && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm">
          {notice}
        </div>
      )}

      {/* Verification Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 rounded-xl bg-[#0f1626] border border-[#1d2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">MX Confirmed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <span className="text-3xl font-bold text-white mt-2 block">{validCount}</span>
          <span className="text-xs text-slate-500 mt-1 block">Valid mail servers published</span>
        </div>

        <div className="p-5 rounded-xl bg-[#0f1626] border border-[#1d2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Pending Check</span>
            <AlertCircle className="w-4 h-4 text-amber-400" />
          </div>
          <span className="text-3xl font-bold text-amber-300 mt-2 block">{uncheckedCount}</span>
          <span className="text-xs text-slate-500 mt-1 block">Needs DNS inspection</span>
        </div>

        <div className="p-5 rounded-xl bg-[#0f1626] border border-[#1d2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">No Reachable MX</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <span className="text-3xl font-bold text-rose-400 mt-2 block">{noMxCount}</span>
          <span className="text-xs text-slate-500 mt-1 block">Unreachable domain</span>
        </div>
      </div>

      {/* Verification Table */}
      <div className="rounded-xl border border-[#1d2740] bg-[#0f1626] overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-[#1d2740] bg-[#0b101c] text-slate-400 text-xs font-semibold uppercase tracking-wider">
              <th className="py-3 px-4">Address</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Verification Details</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#162035] text-sm">
            {contacts.map((c) => (
              <tr key={c.id} className="hover:bg-[#131c30]">
                <td className="py-3 px-4">
                  <span className="font-semibold text-white block">{c.email}</span>
                  <span className="text-xs text-slate-400">{c.full_name || "Maintainer"}</span>
                </td>
                <td className="py-3 px-4">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-xs font-semibold border ${
                      c.verification_status === "VALID"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : c.verification_status === "UNCHECKED"
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                    }`}
                  >
                    {c.verification_status}
                  </span>
                </td>
                <td className="py-3 px-4 text-xs text-slate-400">
                  {c.verification_status === "VALID"
                    ? "DNS MX records confirmed. Ready for campaign selection."
                    : c.verification_status === "UNCHECKED"
                    ? "Click verify to query DNS resolvers."
                    : "Domain does not possess active MX records."}
                </td>
                <td className="py-3 px-4 text-right">
                  <button
                    onClick={async () => {
                      await verifyContact(c.id);
                      loadData();
                    }}
                    className="px-2.5 py-1 text-xs bg-[#162035] hover:bg-[#1d2a45] text-slate-300 rounded border border-[#233150]"
                  >
                    Re-verify
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
