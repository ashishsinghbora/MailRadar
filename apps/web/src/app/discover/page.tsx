"use client";

import { useState } from "react";
import { Search, Sparkles, Loader2, Star, GitFork, ExternalLink, CheckCircle } from "lucide-react";
import { triggerDiscovery } from "@/lib/api";

export default function DiscoverPage() {
  const [query, setQuery] = useState("distributed mesh");
  const [language, setLanguage] = useState("Python");
  const [minStars, setMinStars] = useState(50);
  const [limit, setLimit] = useState(10);
  const [loading, setLoading] = useState(false);
  const [jobResult, setJobResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setJobResult(null);

    try {
      const res = await triggerDiscovery(query, language || undefined, minStars, limit);
      setJobResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to execute discovery job.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">GitHub Discovery Engine</h1>
        <p className="text-sm text-slate-400 mt-1">
          Scan official repositories, parse maintainer signals from README/CONTRIBUTING documentation, and verify published contact channels.
        </p>
      </div>

      {/* Discovery Form */}
      <form onSubmit={handleSearch} className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740] space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">
              Target Topic or Repository Name
            </label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. distributed consensus, eBPF, kubernetes"
                className="w-full pl-9 pr-4 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">
              Language Filter
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="">Any Language</option>
              <option value="Python">Python</option>
              <option value="TypeScript">TypeScript</option>
              <option value="Go">Go</option>
              <option value="Rust">Rust</option>
              <option value="Java">Java</option>
              <option value="C++">C++</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">
              Minimum Stars
            </label>
            <input
              type="number"
              value={minStars}
              onChange={(e) => setMinStars(Number(e.target.value))}
              min={0}
              className="w-full px-3 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-[#1a2338]">
          <span className="text-xs text-slate-500">
            Strict SSRF protection and official documentation crawl policies enforced.
          </span>
          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm flex items-center space-x-2 shadow-lg shadow-indigo-600/20 transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Scanning Official Sources...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-cyan-300" />
                <span>Run Discovery Pipeline</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Error display */}
      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Results Card */}
      {jobResult && (
        <div className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740] space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-emerald-400">
              <CheckCircle className="w-5 h-5" />
              <h2 className="text-base font-semibold text-white">Discovery Execution Completed</h2>
            </div>
            <span className="text-xs font-mono text-slate-400">Job: {jobResult.id.slice(0, 8)}</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-lg bg-[#141d33] border border-[#222e4d]">
            <div>
              <span className="text-xs text-slate-400">Query Target</span>
              <p className="text-sm font-semibold text-white mt-0.5">{jobResult.target_query}</p>
            </div>
            <div>
              <span className="text-xs text-slate-400">Status</span>
              <p className="text-sm font-semibold text-emerald-400 mt-0.5">{jobResult.status}</p>
            </div>
            <div>
              <span className="text-xs text-slate-400">Projects Discovered</span>
              <p className="text-sm font-semibold text-white mt-0.5">{jobResult.projects_found}</p>
            </div>
            <div>
              <span className="text-xs text-slate-400">Contacts Extracted</span>
              <p className="text-sm font-semibold text-cyan-400 mt-0.5">{jobResult.contacts_found}</p>
            </div>
          </div>

          <div className="flex space-x-3 pt-2">
            <a
              href="/projects"
              className="text-xs font-semibold px-4 py-2 bg-indigo-600/20 text-cyan-300 border border-indigo-500/30 rounded-lg hover:bg-indigo-600/30 transition-colors"
            >
              Inspect Discovered Projects →
            </a>
            <a
              href="/contacts"
              className="text-xs font-semibold px-4 py-2 bg-[#1a243e] text-slate-300 border border-[#253255] rounded-lg hover:bg-[#202c4c] transition-colors"
            >
              View Extracted Contacts →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
