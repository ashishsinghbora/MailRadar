"use client";

import { useState } from "react";
import { Sliders, KeyRound, Trash2, Shield } from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function SettingsPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordNotice, setPasswordNotice] = useState<string | null>(null);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      setPasswordNotice("Password changed successfully.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err: any) {
      alert("Error: " + err.message);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Organization & User Settings</h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage authentication credentials, encryption preferences, and security policies.
        </p>
      </div>

      {/* Password Change Form */}
      <div className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740] space-y-4">
        <div className="flex items-center space-x-2 text-indigo-400">
          <KeyRound className="w-5 h-5" />
          <h2 className="text-base font-semibold text-white">Change Security Password</h2>
        </div>

        {passwordNotice && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">
            {passwordNotice}
          </div>
        )}

        <form onSubmit={handlePasswordChange} className="space-y-3 max-w-md">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Current Password</label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-3 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">New Password (min 8 chars)</label>
            <input
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3 py-2 bg-[#141d33] border border-[#222e4d] rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs rounded-lg shadow-md transition-colors"
          >
            Update Password
          </button>
        </form>
      </div>

      {/* Security Policies */}
      <div className="p-6 rounded-xl bg-[#0f1626] border border-[#1d2740] space-y-3">
        <div className="flex items-center space-x-2 text-cyan-400">
          <Shield className="w-5 h-5" />
          <h2 className="text-base font-semibold text-white">Security & Ethics Enforcements</h2>
        </div>
        <ul className="text-xs text-slate-400 space-y-2 list-disc list-inside">
          <li>SSRF private network boundary enforcement is active across all crawl adapters.</li>
          <li>Fernet symmetric credential encryption is active for third-party tokens at rest.</li>
          <li>Human approval is strictly mandatory before any campaign sending event is queued.</li>
          <li>Automatic suppression list checks cannot be disabled or bypassed.</li>
        </ul>
      </div>
    </div>
  );
}
