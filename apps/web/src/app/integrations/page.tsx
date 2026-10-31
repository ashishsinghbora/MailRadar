"use client";

import { useState } from "react";
import { Layers, Github, Mail, Shield, CheckCircle2, AlertCircle } from "lucide-react";
import { testIntegration } from "@/lib/api";

export default function IntegrationsPage() {
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleTest = async (provider: string) => {
    try {
      const res = await testIntegration(provider);
      setTestResult(`${provider}: ${res.message}`);
    } catch (err: any) {
      setTestResult(`Failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Connected Integrations</h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage API credentials for repository discovery, rate-limiting quotas, and outbound delivery providers.
        </p>
      </div>

      {testResult && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm font-mono flex items-center justify-between">
          <span>{testResult}</span>
          <button onClick={() => setTestResult(null)} className="text-slate-400 hover:text-white text-xs">Dismiss</button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* GitHub Integration Card */}
        <div className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740] space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center">
                <Github className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">GitHub Official API</h3>
                <span className="text-xs text-slate-400">Discovery & Metadata</span>
              </div>
            </div>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Active
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Queries repository metadata, READMEs, and contribution guides with strict rate limit backoff. Tokens are encrypted at rest with Fernet.
          </p>
          <div className="pt-2 border-t border-[#1a2338]">
            <button
              onClick={() => handleTest("GITHUB")}
              className="px-3 py-1.5 bg-[#18223c] hover:bg-[#202d4f] text-slate-300 text-xs font-semibold rounded-lg border border-[#253255]"
            >
              Test API Connection
            </button>
          </div>
        </div>

        {/* Sandbox Delivery Card */}
        <div className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740] space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-indigo-950 flex items-center justify-center">
                <Shield className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">Sandbox Provider</h3>
                <span className="text-xs text-slate-400">Safe Test Mode</span>
              </div>
            </div>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Default Active
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Captures and audits outreach messages locally with zero external network egress. Guaranteed protection against unintentional real sending.
          </p>
          <div className="pt-2 border-t border-[#1a2338]">
            <button
              onClick={() => handleTest("SANDBOX")}
              className="px-3 py-1.5 bg-[#18223c] hover:bg-[#202d4f] text-slate-300 text-xs font-semibold rounded-lg border border-[#253255]"
            >
              Verify Sandbox Status
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
