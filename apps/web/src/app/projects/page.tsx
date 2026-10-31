"use client";

import { useEffect, useState } from "react";
import { FolderGit2, Star, GitFork, ExternalLink, Search, Loader2 } from "lucide-react";
import { getProjects } from "@/lib/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchProjects = async (q?: string) => {
    setLoading(true);
    try {
      const data = await getProjects(q);
      setProjects(data);
    } catch {
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchProjects(search);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Tracked Projects</h1>
          <p className="text-sm text-slate-400 mt-1">
            Repositories identified across discovery scans with official maintainer attribution.
          </p>
        </div>

        <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search repositories..."
              className="pl-9 pr-4 py-1.5 bg-[#0f1626] border border-[#1d2740] rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 bg-[#18223c] text-xs font-semibold text-slate-200 border border-[#26355b] rounded-lg hover:bg-[#202d4f]"
          >
            Search
          </button>
        </form>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 flex justify-center items-center space-x-2">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Loading projects...</span>
        </div>
      ) : projects.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-[#0f1626] border border-[#1d2740] text-slate-400">
          <FolderGit2 className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="font-medium text-slate-300">No tracked projects found</p>
          <p className="text-xs text-slate-500 mt-1">Run a discovery job to scan GitHub for matching projects.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-[#1d2740] bg-[#0f1626] overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#1d2740] bg-[#0b101c] text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Repository</th>
                <th className="py-3 px-4">Language</th>
                <th className="py-3 px-4">Metrics</th>
                <th className="py-3 px-4">Topics</th>
                <th className="py-3 px-4 text-right">Links</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#162035] text-sm">
              {projects.map((p) => (
                <tr key={p.id} className="hover:bg-[#131c30] transition-colors">
                  <td className="py-3 px-4">
                    <span className="font-semibold text-white block">{p.full_name}</span>
                    <span className="text-xs text-slate-400 line-clamp-1 max-w-md">{p.description}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-block px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                      {p.language || "N/A"}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-3 text-xs text-slate-400">
                      <span className="flex items-center space-x-1 text-amber-400">
                        <Star className="w-3.5 h-3.5" />
                        <span>{p.stars_count}</span>
                      </span>
                      <span className="flex items-center space-x-1 text-slate-400">
                        <GitFork className="w-3.5 h-3.5" />
                        <span>{p.forks_count}</span>
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1 max-w-xs">
                      {(p.topics || []).slice(0, 3).map((t: string) => (
                        <span key={t} className="text-[10px] bg-indigo-500/10 text-cyan-400 px-1.5 py-0.5 rounded border border-indigo-500/20">
                          {t}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <a
                      href={p.repository_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 text-slate-400 hover:text-cyan-400 inline-block"
                      title="Open on GitHub"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
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
