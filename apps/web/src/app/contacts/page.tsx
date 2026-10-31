"use client";

import { useEffect, useState } from "react";
import { Users, Search, Download, ShieldCheck, Eye, X, ExternalLink, Loader2 } from "lucide-react";
import { getContacts, verifyContact } from "@/lib/api";

export default function ContactsPage() {
  const [contacts, setContacts] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedContact, setSelectedContact] = useState<any | null>(null);

  const fetchContacts = async () => {
    setLoading(true);
    try {
      const data = await getContacts(search || undefined, statusFilter || undefined);
      setContacts(data);
    } catch {
      setContacts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContacts();
  }, [statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchContacts();
  };

  const handleVerify = async (contactId: string) => {
    try {
      const updated = await verifyContact(contactId);
      setContacts((prev) =>
        prev.map((c) => (c.id === contactId ? { ...c, verification_status: updated.status } : c))
      );
    } catch (err) {
      alert("Verification check failed.");
    }
  };

  const exportUrl = (format: string) => {
    return `http://localhost:8000/api/v1/contacts/export?format=${format}`;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Contact Database</h1>
          <p className="text-sm text-slate-400 mt-1">
            Explicitly published developer contacts with permanent provenance and verification records.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <a
            href={exportUrl("csv")}
            download
            className="px-3 py-1.5 bg-[#18223c] text-xs font-semibold text-slate-200 border border-[#26355b] rounded-lg hover:bg-[#202d4f] flex items-center space-x-1.5"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span>Export CSV</span>
          </a>
          <a
            href={exportUrl("json")}
            download
            className="px-3 py-1.5 bg-[#18223c] text-xs font-semibold text-slate-200 border border-[#26355b] rounded-lg hover:bg-[#202d4f] flex items-center space-x-1.5"
          >
            <Download className="w-3.5 h-3.5 text-indigo-400" />
            <span>Export JSON</span>
          </a>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-[#0f1626] border border-[#1d2740] flex flex-wrap gap-4 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex-1 max-w-md relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search email, name or role..."
            className="w-full pl-9 pr-4 py-1.5 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </form>

        <div className="flex items-center space-x-3">
          <label className="text-xs text-slate-400">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-[#141d33] border border-[#222e4d] rounded-lg text-xs text-white focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="VALID">Valid (MX Confirmed)</option>
            <option value="UNCHECKED">Unchecked</option>
            <option value="NO_MX">No MX</option>
            <option value="INVALID_SYNTAX">Invalid Syntax</option>
            <option value="DISPOSABLE">Disposable</option>
          </select>
        </div>
      </div>

      {/* Contacts Table */}
      {loading ? (
        <div className="p-12 text-center text-slate-500 flex justify-center items-center space-x-2">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Loading contacts...</span>
        </div>
      ) : contacts.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-[#0f1626] border border-[#1d2740] text-slate-400">
          <Users className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="font-medium text-slate-300">No contacts found</p>
          <p className="text-xs text-slate-500 mt-1">Run discovery or refine search filters.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-[#1d2740] bg-[#0f1626] overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#1d2740] bg-[#0b101c] text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Contact</th>
                <th className="py-3 px-4">Role / Title</th>
                <th className="py-3 px-4">Relevance</th>
                <th className="py-3 px-4">Verification</th>
                <th className="py-3 px-4">Suppression</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#162035] text-sm">
              {contacts.map((c) => (
                <tr key={c.id} className="hover:bg-[#131c30] transition-colors">
                  <td className="py-3 px-4">
                    <span className="font-semibold text-white block">{c.email}</span>
                    <span className="text-xs text-slate-400">{c.full_name || "Name not published"}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-block px-2 py-0.5 rounded text-xs bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
                      {c.role_title || "Maintainer"}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400"
                          style={{ width: `${Math.round(c.relevance_score * 100)}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-mono text-slate-400">
                        {Math.round(c.relevance_score * 100)}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium border ${
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
                  <td className="py-3 px-4">
                    {c.is_suppressed ? (
                      <span className="text-xs text-rose-400 font-semibold">Suppressed</span>
                    ) : (
                      <span className="text-xs text-emerald-400">Active</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right space-x-2">
                    <button
                      onClick={() => handleVerify(c.id)}
                      className="px-2.5 py-1 text-xs bg-[#162035] hover:bg-[#1d2a45] text-slate-300 rounded border border-[#233150]"
                    >
                      Verify DNS
                    </button>
                    <button
                      onClick={() => setSelectedContact(c)}
                      className="p-1 text-slate-400 hover:text-cyan-400 inline-block"
                      title="View Evidence Provenance"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Provenance Evidence Modal */}
      {selectedContact && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-[#0f1626] border border-[#222e4d] rounded-xl max-w-2xl w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#1f2b45]">
              <div>
                <h3 className="text-lg font-semibold text-white">Contact Evidence & Provenance</h3>
                <span className="text-xs text-slate-400 font-mono">{selectedContact.email}</span>
              </div>
              <button
                onClick={() => setSelectedContact(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Preserved Source Documentation
              </h4>
              {selectedContact.sources && selectedContact.sources.length > 0 ? (
                selectedContact.sources.map((s: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-lg bg-[#141d33] border border-[#222e4d] space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                        {s.source_category}
                      </span>
                      <a
                        href={s.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-indigo-400 hover:underline flex items-center space-x-1"
                      >
                        <span className="truncate max-w-xs">{s.source_url}</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                    <div className="p-3 bg-[#0a0f1d] rounded border border-[#1a2338] text-xs font-mono text-slate-300 whitespace-pre-wrap">
                      "{s.evidence_text}"
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 italic">No provenance source attached.</p>
              )}
            </div>

            <div className="pt-3 border-t border-[#1f2b45] flex justify-end">
              <button
                onClick={() => setSelectedContact(null)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
