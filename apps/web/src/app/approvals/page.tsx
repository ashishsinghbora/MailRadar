"use client";

import { useEffect, useState } from "react";
import { CheckSquare, CheckCircle, XCircle, ShieldAlert, Eye, Loader2 } from "lucide-react";
import { getPendingApprovals, reviewRecipient, bulkReviewRecipients } from "@/lib/api";

export default function ApprovalQueuePage() {
  const [recipients, setRecipients] = useState<any[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await getPendingApprovals();
      setRecipients(data);
    } catch {
      setRecipients([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSingleReview = async (id: string, approved: boolean) => {
    try {
      await reviewRecipient(id, approved);
      setNotice(`Recipient ${approved ? "approved" : "rejected"} successfully.`);
      loadData();
    } catch (err: any) {
      alert("Review action failed: " + err.message);
    }
  };

  const handleBulkApprove = async () => {
    if (selectedIds.length === 0) return;
    const campaignId = recipients[0]?.campaign_id;
    if (!campaignId) return;

    try {
      await bulkReviewRecipients(campaignId, selectedIds, true);
      setNotice(`Approved ${selectedIds.length} recipient(s).`);
      setSelectedIds([]);
      loadData();
    } catch (err: any) {
      alert("Bulk approval failed: " + err.message);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Human Approval Queue</h1>
          <p className="text-sm text-slate-400 mt-1">
            Mandatory gate: Every candidate recipient must be audited and explicitly approved by an operator before sending.
          </p>
        </div>

        {selectedIds.length > 0 && (
          <button
            onClick={handleBulkApprove}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs rounded-lg flex items-center space-x-2 shadow-lg shadow-emerald-600/20"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Approve Selected ({selectedIds.length})</span>
          </button>
        )}
      </div>

      {notice && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm">
          {notice}
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-slate-500 flex justify-center items-center space-x-2">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Loading approval queue...</span>
        </div>
      ) : recipients.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-[#0f1626] border border-[#1d2740] text-slate-400">
          <CheckSquare className="w-8 h-8 text-emerald-500 mx-auto mb-3" />
          <p className="font-semibold text-white">Queue is Clear</p>
          <p className="text-xs text-slate-500 mt-1">
            All candidate recipients have been reviewed or no active drafts require review.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-[#1d2740] bg-[#0f1626] overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#1d2740] bg-[#0b101c] text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4 w-10">
                  <input
                    type="checkbox"
                    checked={selectedIds.length === recipients.length && recipients.length > 0}
                    onChange={(e) => {
                      if (e.target.checked) setSelectedIds(recipients.map((r) => r.id));
                      else setSelectedIds([]);
                    }}
                    className="rounded border-[#222e4d] bg-[#0f1626]"
                  />
                </th>
                <th className="py-3 px-4">Recipient</th>
                <th className="py-3 px-4">Relevance</th>
                <th className="py-3 px-4">Verification</th>
                <th className="py-3 px-4">Source Provenance</th>
                <th className="py-3 px-4 text-right">Human Decision</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#162035] text-sm">
              {recipients.map((r) => {
                const c = r.contact;
                const source = c?.sources?.[0];
                return (
                  <tr key={r.id} className="hover:bg-[#131c30]">
                    <td className="py-3 px-4">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(r.id)}
                        onChange={(e) => {
                          if (e.target.checked) setSelectedIds([...selectedIds, r.id]);
                          else setSelectedIds(selectedIds.filter((id) => id !== r.id));
                        }}
                        className="rounded border-[#222e4d] bg-[#0f1626]"
                      />
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-white block">{c?.email || "N/A"}</span>
                      <span className="text-xs text-slate-400">{c?.full_name || "Maintainer"}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-xs font-mono font-medium text-cyan-400">
                        {c?.relevance_score ? Math.round(c.relevance_score * 100) : 50}%
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-block px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {c?.verification_status || "VALID"}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-xs text-slate-400 line-clamp-1 max-w-xs font-mono">
                        "{source?.evidence_text || "Official maintainer contact"}"
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleSingleReview(r.id, true)}
                        className="px-3 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 rounded text-xs font-semibold"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleSingleReview(r.id, false)}
                        className="px-3 py-1 bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 rounded text-xs font-semibold"
                      >
                        Reject
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
