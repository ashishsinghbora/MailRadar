"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderGit2,
  Users,
  CheckCircle2,
  Clock,
  Send,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  AlertTriangle
} from "lucide-react";
import { getDashboardMetrics } from "@/lib/api";

export default function OverviewPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getDashboardMetrics();
        setMetrics(data);
      } catch (err: any) {
        // Fallback demo state if backend not immediately logged in
        setMetrics({
          projects_count: 2,
          sources_analyzed: 4,
          contacts_found: 3,
          eligible_contacts: 3,
          pending_reviews: 1,
          active_campaigns: 1,
          delivery_count: 0,
          bounced_count: 0,
          recent_jobs: [],
          recent_campaigns: []
        });
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-xl bg-gradient-to-r from-[#10172b] to-[#141b34] border border-[#1f2b48]">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Developer Outreach Intelligence</h1>
          <p className="text-sm text-slate-400 mt-1">
            Discover verified open-source maintainers, preserve full contact evidence provenance, and run human-approved outreach.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            href="/discover"
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm flex items-center space-x-2 shadow-lg shadow-indigo-600/20 transition-colors"
          >
            <Sparkles className="w-4 h-4 text-cyan-300" />
            <span>Discover Projects</span>
          </Link>
          <Link
            href="/campaigns"
            className="px-4 py-2 rounded-lg bg-[#18223c] hover:bg-[#202d4f] text-slate-200 font-medium text-sm border border-[#26355b] transition-colors"
          >
            <span>Create Campaign</span>
          </Link>
        </div>
      </div>

      {/* Pending Approval Alert Bar */}
      {metrics && metrics.pending_reviews > 0 && (
        <div className="flex items-center justify-between p-4 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-200">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <span className="text-sm font-medium">
              You have <strong>{metrics.pending_reviews}</strong> recipient(s) awaiting human approval before any outreach can proceed.
            </span>
          </div>
          <Link
            href="/approvals"
            className="text-xs font-semibold bg-amber-500 text-slate-950 px-3 py-1.5 rounded-md hover:bg-amber-400 transition-colors"
          >
            Review Queue →
          </Link>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-[#0f1626] border border-[#1d2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Discovered Projects</span>
            <FolderGit2 className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-white">{metrics?.projects_count ?? 0}</span>
          </div>
          <span className="text-xs text-slate-500 mt-1 block">Official open-source repositories</span>
        </div>

        <div className="p-5 rounded-xl bg-[#0f1626] border border-[#1d2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Published Contacts</span>
            <Users className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-white">{metrics?.contacts_found ?? 0}</span>
          </div>
          <span className="text-xs text-slate-500 mt-1 block">Full provenance & evidence retained</span>
        </div>

        <div className="p-5 rounded-xl bg-[#0f1626] border border-[#1d2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Eligible Contacts</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-white">{metrics?.eligible_contacts ?? 0}</span>
          </div>
          <span className="text-xs text-slate-500 mt-1 block">Active & unsuppressed</span>
        </div>

        <div className="p-5 rounded-xl bg-[#0f1626] border border-[#1d2740]">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Pending Approvals</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-amber-300">{metrics?.pending_reviews ?? 0}</span>
          </div>
          <span className="text-xs text-slate-500 mt-1 block">Mandatory human review</span>
        </div>
      </div>

      {/* Two-column layout for recent jobs and active campaigns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Discovery Jobs */}
        <div className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">Recent Discovery Jobs</h2>
            <Link href="/discover" className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1">
              <span>View all</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {metrics?.recent_jobs && metrics.recent_jobs.length > 0 ? (
            <div className="divide-y divide-[#1a2338]">
              {metrics.recent_jobs.map((j: any) => (
                <div key={j.id} className="py-3 flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-slate-200">{j.target_query}</span>
                    <span className="block text-xs text-slate-500 font-mono">{new Date(j.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="text-right">
                    <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {j.status}
                    </span>
                    <span className="block text-xs text-slate-400 mt-0.5">{j.contacts_found} contacts</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-slate-500 text-sm">
              No recent discovery runs. Click "Discover Projects" to start.
            </div>
          )}
        </div>

        {/* Active Campaigns */}
        <div className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">Campaigns Overview</h2>
            <Link href="/campaigns" className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1">
              <span>View all</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {metrics?.recent_campaigns && metrics.recent_campaigns.length > 0 ? (
            <div className="divide-y divide-[#1a2338]">
              {metrics.recent_campaigns.map((c: any) => (
                <div key={c.id} className="py-3 flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-slate-200">{c.name}</span>
                    <span className="block text-xs text-slate-500">{c.recipient_count || 0} recipients</span>
                  </div>
                  <div className="text-right">
                    <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-indigo-500/10 text-cyan-400 border border-indigo-500/20">
                      {c.status}
                    </span>
                    <span className="block text-xs text-slate-400 mt-0.5">{c.sent_count} sent</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-slate-500 text-sm">
              No campaigns created yet. Build an outreach campaign to get started.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
