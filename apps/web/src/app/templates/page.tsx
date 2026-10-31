"use client";

import { useEffect, useState } from "react";
import { FileText, Plus, Eye, Code, Loader2 } from "lucide-react";
import { getTemplates, createTemplate, previewTemplate } from "@/lib/api";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [name, setName] = useState("");
  const [subject, setSubject] = useState("");
  const [bodyMarkdown, setBodyMarkdown] = useState("");
  const [previewData, setPreviewData] = useState<any | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await getTemplates();
      setTemplates(data);
    } catch {
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !subject.trim()) return;

    try {
      await createTemplate(name, subject, bodyMarkdown);
      setShowCreateModal(false);
      setName("");
      setSubject("");
      setBodyMarkdown("");
      loadData();
    } catch (err: any) {
      alert("Failed to save template: " + err.message);
    }
  };

  const handlePreview = async (templateId: string) => {
    try {
      const p = await previewTemplate(templateId);
      setPreviewData(p);
    } catch (err: any) {
      alert("Preview generation failed.");
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Outreach Templates</h1>
          <p className="text-sm text-slate-400 mt-1">
            Standardized message formats with automatic variable interpolation.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs rounded-lg flex items-center space-x-2 shadow-lg shadow-indigo-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Template</span>
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 flex justify-center items-center space-x-2">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Loading templates...</span>
        </div>
      ) : templates.length === 0 ? (
        <div className="p-12 text-center rounded-xl bg-[#0f1626] border border-[#1d2740] text-slate-400">
          <FileText className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="font-semibold text-white">No templates found</p>
          <p className="text-xs text-slate-500 mt-1">Create an outreach template to personalize recipient emails.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((t) => (
            <div key={t.id} className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740] flex flex-col justify-between space-y-4">
              <div>
                <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                  {t.variables?.length || 0} Variables
                </span>
                <h3 className="text-base font-semibold text-white mt-2">{t.name}</h3>
                <p className="text-xs text-slate-300 font-medium mt-1">Subject: {t.subject}</p>
                <div className="mt-3 p-3 bg-[#141d33] rounded border border-[#222e4d] text-xs font-mono text-slate-400 line-clamp-3">
                  {t.body_markdown}
                </div>
              </div>

              <div className="pt-2 border-t border-[#1a2338] flex items-center justify-between">
                <div className="flex flex-wrap gap-1">
                  {(t.variables || []).slice(0, 2).map((v: string) => (
                    <span key={v} className="text-[10px] text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">
                      {`{{${v}}}`}
                    </span>
                  ))}
                </div>
                <button
                  onClick={() => handlePreview(t.id)}
                  className="px-3 py-1 bg-indigo-600/20 hover:bg-indigo-600/30 text-cyan-300 rounded text-xs font-semibold flex items-center space-x-1 border border-indigo-500/30"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Preview</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Template Preview Modal */}
      {previewData && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center p-4 z-50">
          <div className="bg-[#0f1626] border border-[#222e4d] rounded-xl max-w-2xl w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Interpolated Email Preview</h3>
            <div className="p-3 bg-[#141d33] rounded border border-[#222e4d]">
              <span className="text-xs font-semibold text-slate-400">Subject:</span>
              <p className="text-sm font-semibold text-white mt-0.5">{previewData.subject}</p>
            </div>
            <div className="p-4 bg-white rounded text-slate-900 min-h-48 text-sm" dangerouslySetInnerHTML={{ __html: previewData.body_html }} />
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setPreviewData(null)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/75 flex items-center justify-center p-4 z-50">
          <form onSubmit={handleCreate} className="bg-[#0f1626] border border-[#222e4d] rounded-xl max-w-xl w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Create Email Template</h3>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Template Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Open Source Collaboration Inquiry"
                className="w-full px-3 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Subject Line</label>
              <input
                type="text"
                required
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Collaboration inquiry regarding {{project_name}}"
                className="w-full px-3 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Body (Markdown)</label>
              <textarea
                required
                value={bodyMarkdown}
                onChange={(e) => setBodyMarkdown(e.target.value)}
                placeholder="Hi {{first_name}},\n\nI noticed your work on {{project_name}}..."
                className="w-full px-3 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500 h-40 font-mono text-xs"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                Available tags: `{"{{first_name}}"}`, `{"{{full_name}}"}`, `{"{{project_name}}"}`, `{"{{organization_name}}"}`
              </span>
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
                Save Template
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
