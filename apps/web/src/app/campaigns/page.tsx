"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Send, Plus, CheckCircle, Clock, Play, AlertCircle, Loader2 } from "lucide-react";
import { getCampaigns, createCampaign, sendCampaign, getTemplates, getContacts } from "@/lib/api";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [contacts, setContacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [dispatchStatus, setDispatchStatus] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cData, tData, cntData] = await Promise.all([
        getCampaigns(),
        getTemplates(),
        getContacts(),
      ]);
      setCampaigns(cData);
      setTemplates(tData);
      setContacts(cntData.filter((c: any) => !c.is_suppressed));
    } catch {
      setCampaigns([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    try {
      await createCampaign(newName, newDesc, selectedTemplate || undefined, selectedContacts);
      setShowCreateModal(false);
      setNewName("");
      setNewDesc("");
      setSelectedContacts([]);
      loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create campaign.");
    }
  };

  const handleSend = async (campaignId: string) => {
    try {
      setDispatchStatus("Dispatching approved messages via sandbox provider...");
      const res = await sendCampaign(campaignId, true);
      setDispatchStatus(`Sent ${res.delivered} message(s) successfully in sandbox mode.`);
      loadData();
    } catch (err: any) {
      setDispatchStatus(`Error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Campaign Manager</h1>
          <p className="text-sm text-slate-400 mt-1">
            Build personalized collaboration campaigns. Every recipient requires explicit human approval before dispatch.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs rounded-lg flex items-center space-x-2 shadow-lg shadow-indigo-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Outreach Campaign</span>
        </button>
      </div>

      {dispatchStatus && (
        <div className="p-4 rounded-lg bg-[#141d33] border border-[#222e4d] text-cyan-300 text-sm font-mono flex items-center justify-between">
          <span>{dispatchStatus}</span>
          <button onClick={() => setDispatchStatus(null)} className="text-slate-400 hover:text-white text-xs">Dismiss</button>
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-slate-500 flex justify-center items-center space-x-2">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Loading campaigns...</span>
        </div>
      ) : campaigns.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-[#0f1626] border border-[#1d2740] text-slate-400">
          <Send className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="font-medium text-slate-300">No campaigns created yet</p>
          <p className="text-xs text-slate-500 mt-1">Create a campaign, attach a template, and review candidate recipients.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {campaigns.map((c) => (
            <div key={c.id} className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740] flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${
                      c.status === "APPROVED"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : c.status === "RECIPIENT_REVIEW"
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : c.status === "COMPLETED"
                        ? "bg-indigo-500/10 text-indigo-300 border-indigo-500/20"
                        : "bg-slate-800 text-slate-300 border-slate-700"
                    }`}
                  >
                    {c.status}
                  </span>
                  <span className="text-xs font-mono text-slate-500">Limit: {c.daily_limit}/day</span>
                </div>

                <h3 className="text-lg font-semibold text-white mt-2">{c.name}</h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">{c.description || "No description provided."}</p>
              </div>

              {/* Progress metrics */}
              <div className="space-y-2 pt-2 border-t border-[#1a2338]">
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Recipients: {c.recipient_count || 0}</span>
                  <span>Approved: {c.approved_count || 0}</span>
                  <span>Sent: {c.sent_count || 0}</span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400"
                    style={{
                      width: `${c.recipient_count ? Math.round((c.sent_count / c.recipient_count) * 100) : 0}%`,
                    }}
                  ></div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-2 pt-2">
                {c.status === "RECIPIENT_REVIEW" && (
                  <Link
                    href={`/approvals?campaign_id=${c.id}`}
                    className="flex-1 py-2 text-center bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 rounded-lg text-xs font-semibold transition-colors"
                  >
                    Review Recipients →
                  </Link>
                )}

                {c.status === "APPROVED" && (
                  <button
                    onClick={() => handleSend(c.id)}
                    className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 shadow-md shadow-emerald-600/20 transition-colors"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Send Approved Messages</span>
                  </button>
                )}

                {c.status === "DRAFT" && (
                  <Link
                    href={`/approvals?campaign_id=${c.id}`}
                    className="flex-1 py-2 text-center bg-[#18223c] text-slate-300 border border-[#253255] rounded-lg text-xs font-semibold hover:bg-[#202d4f]"
                  >
                    Add / Review Recipients
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Campaign Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center p-4 z-50">
          <form onSubmit={handleCreateCampaign} className="bg-[#0f1626] border border-[#222e4d] rounded-xl max-w-xl w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Create New Outreach Campaign</h3>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Campaign Name</label>
              <input
                type="text"
                required
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. Distributed Mesh Maintainer Outreach"
                className="w-full px-3 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Description / Goal</label>
              <textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Purpose of outreach..."
                className="w-full px-3 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500 h-20"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Select Email Template</label>
              <select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="w-full px-3 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">No template (assign later)</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>{t.name} — ({t.subject})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Select Eligible Contacts ({selectedContacts.length} selected)
              </label>
              <div className="max-h-40 overflow-y-auto p-2 bg-[#141d33] border border-[#222e4d] rounded-lg space-y-1">
                {contacts.map((c) => (
                  <label key={c.id} className="flex items-center space-x-2 text-xs text-slate-300 hover:bg-[#1a243e] p-1.5 rounded cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedContacts.includes(c.id)}
                      onChange={(e) => {
                        if (e.target.checked) setSelectedContacts([...selectedContacts, c.id]);
                        else setSelectedContacts(selectedContacts.filter((id) => id !== c.id));
                      }}
                      className="rounded border-[#222e4d] bg-[#0f1626]"
                    />
                    <span>{c.email}</span>
                    <span className="text-slate-500 font-mono">({c.role_title || "Maintainer"})</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-[#1f2b45] flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 bg-[#18223c] text-slate-300 rounded-lg text-xs font-semibold hover:bg-[#202d4f]"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-indigo-600/20"
              >
                Create Campaign
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
