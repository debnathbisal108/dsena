"use client";
import { useState } from "react";
import { useAuth, useCalendarStatus } from "@/hooks";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import api from "@/lib/api";
import { getErrorMessage, cn } from "@/lib/utils";
import { CheckCircle, Calendar, Link as LinkIcon, Bot, Loader2 } from "lucide-react";

const orgSchema = z.object({
  name: z.string().min(2),
  description: z.string().min(10),
  services: z.string().min(5),
  target_customer: z.string().min(5),
  pricing_guidance: z.string().optional(),
  faqs: z.string().optional(),
  business_rules: z.string().optional(),
  website_url: z.string().optional(),
});
type OrgForm = z.infer<typeof orgSchema>;

const policySchema = z.object({
  ai_tone: z.enum(["professional", "friendly", "casual", "premium"]),
  max_followup_attempts: z.coerce.number().min(1).max(10),
  allowed_hours_start: z.coerce.number().min(0).max(23),
  allowed_hours_end: z.coerce.number().min(1).max(24),
  allowed_timezone: z.string(),
});
type PolicyForm = z.infer<typeof policySchema>;

export default function SettingsPage() {
  const { user, org, setOrg } = useAuth();
  const { data: calStatus } = useCalendarStatus();
  const [savedOrg, setSavedOrg] = useState(false);
  const [savedPolicy, setSavedPolicy] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const orgForm = useForm<OrgForm>({
    resolver: zodResolver(orgSchema),
    defaultValues: {
      name: org?.name || "",
      description: org?.description || "",
      services: org?.services || "",
      target_customer: org?.target_customer || "",
      pricing_guidance: org?.pricing_guidance || "",
      faqs: org?.faqs || "",
      business_rules: org?.business_rules || "",
      website_url: org?.website_url || "",
    },
  });

  const policyForm = useForm<PolicyForm>({
    resolver: zodResolver(policySchema),
    defaultValues: {
      ai_tone: (org?.ai_tone as any) || "professional",
      max_followup_attempts: org?.max_followup_attempts || 5,
      allowed_hours_start: org?.allowed_hours_start || 8,
      allowed_hours_end: org?.allowed_hours_end || 18,
      allowed_timezone: org?.allowed_timezone || "UTC",
    },
  });

  async function saveOrgInfo(data: OrgForm) {
    setLoading(true); setError("");
    try {
      const res = await api.post("/api/onboarding/business-info", { ...data, slug: org!.slug });
      setOrg(res.data);
      setSavedOrg(true);
      setTimeout(() => setSavedOrg(false), 2500);
    } catch (e) { setError(getErrorMessage(e)); }
    finally { setLoading(false); }
  }

  async function savePolicy(data: PolicyForm) {
    setLoading(true); setError("");
    try {
      const res = await api.post("/api/onboarding/ai-policy", data);
      setOrg(res.data);
      setSavedPolicy(true);
      setTimeout(() => setSavedPolicy(false), 2500);
    } catch (e) { setError(getErrorMessage(e)); }
    finally { setLoading(false); }
  }

  async function connectCalendar() {
    try {
      const res = await api.get("/api/calendar/connect");
      window.location.href = res.data.auth_url;
    } catch (e) { setError(getErrorMessage(e)); }
  }

  return (
    <div className="space-y-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {error && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>}

      {/* Business Info */}
      <div className="card p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Business Information</h2>
        <form onSubmit={orgForm.handleSubmit(saveOrgInfo)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Business Name</label>
            <input {...orgForm.register("name")} className="input" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea {...orgForm.register("description")} rows={3} className="input resize-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Services</label>
            <textarea {...orgForm.register("services")} rows={2} className="input resize-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Target Customer</label>
            <input {...orgForm.register("target_customer")} className="input" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Pricing Guidance</label>
            <textarea {...orgForm.register("pricing_guidance")} rows={2} className="input resize-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Business Rules for AI</label>
            <textarea {...orgForm.register("business_rules")} rows={2} className="input resize-none"
              placeholder="e.g. Never promise specific results. Always suggest a call for pricing questions." />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Website URL</label>
            <input {...orgForm.register("website_url")} className="input" placeholder="https://yoursite.com" />
          </div>
          <button type="submit" className="btn-primary flex items-center gap-2" disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : savedOrg ? <CheckCircle className="w-4 h-4" /> : null}
            {savedOrg ? "Saved!" : "Save Changes"}
          </button>
        </form>

        {/* Form link */}
        <div className="mt-6 pt-6 border-t border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <LinkIcon className="w-4 h-4" /> Your Lead Form URL
          </h3>
          <div className="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-700 font-mono select-all break-all">
            {typeof window !== "undefined" ? window.location.origin : ""}/form/{org?.slug}
          </div>
          <p className="text-xs text-gray-400 mt-2">Share this link or embed it with the widget script.</p>
          <pre className="bg-gray-900 text-green-400 text-xs rounded-lg p-3 mt-2 overflow-x-auto">
{`<script src="${typeof window !== "undefined" ? window.location.origin : ""}/widget.js" data-org="${org?.slug}"></script>`}
          </pre>
        </div>
      </div>

      {/* AI Policy */}
      <div className="card p-6">
        <h2 className="font-semibold text-gray-900 mb-1 flex items-center gap-2">
          <Bot className="w-4 h-4 text-primary-500" /> AI Behaviour Policy
        </h2>
        <p className="text-sm text-gray-500 mb-4">Configure how your AI sales employee behaves.</p>
        <form onSubmit={policyForm.handleSubmit(savePolicy)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Communication Tone</label>
            <div className="grid grid-cols-2 gap-2">
              {["professional", "friendly", "casual", "premium"].map((tone) => (
                <label key={tone} className={cn(
                  "flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors",
                  policyForm.watch("ai_tone") === tone ? "border-primary-500 bg-primary-50" : "border-gray-200 hover:border-gray-300"
                )}>
                  <input {...policyForm.register("ai_tone")} type="radio" value={tone} className="sr-only" />
                  <span className="text-sm font-medium capitalize">{tone}</span>
                </label>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Follow-up Attempts: <strong>{policyForm.watch("max_followup_attempts")}</strong>
            </label>
            <input {...policyForm.register("max_followup_attempts")} type="range" min={1} max={10} className="w-full" />
            <div className="flex justify-between text-xs text-gray-400 mt-1"><span>1 (minimal)</span><span>10 (persistent)</span></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Send from hour</label>
              <select {...policyForm.register("allowed_hours_start")} className="input">
                {Array.from({ length: 24 }, (_, i) => <option key={i} value={i}>{i}:00</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Until hour</label>
              <select {...policyForm.register("allowed_hours_end")} className="input">
                {Array.from({ length: 24 }, (_, i) => <option key={i + 1} value={i + 1}>{i + 1}:00</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
            <select {...policyForm.register("allowed_timezone")} className="input">
              {[["UTC","UTC"],["America/New_York","Eastern US"],["America/Chicago","Central US"],
                ["America/Los_Angeles","Pacific US"],["Europe/London","London"],
                ["Europe/Paris","Paris"],["Asia/Kolkata","India (IST)"],
                ["Asia/Singapore","Singapore"],["Australia/Sydney","Sydney"]].map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>
          <button type="submit" className="btn-primary flex items-center gap-2" disabled={loading}>
            {savedPolicy ? <CheckCircle className="w-4 h-4" /> : null}
            {savedPolicy ? "Saved!" : "Save AI Policy"}
          </button>
        </form>
      </div>

      {/* Calendar */}
      <div className="card p-6">
        <h2 className="font-semibold text-gray-900 mb-1 flex items-center gap-2">
          <Calendar className="w-4 h-4" /> Google Calendar
        </h2>
        <p className="text-sm text-gray-500 mb-4">AI books meetings directly into your calendar when leads are ready.</p>
        {calStatus?.connected ? (
          <div className="flex items-center gap-2 text-green-700 bg-green-50 px-4 py-3 rounded-lg text-sm">
            <CheckCircle className="w-4 h-4" /> Calendar connected — AI can book meetings automatically
          </div>
        ) : (
          <button onClick={connectCalendar} className="btn-primary flex items-center gap-2">
            <Calendar className="w-4 h-4" /> Connect Google Calendar
          </button>
        )}
      </div>

      {/* Account */}
      <div className="card p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Account</h2>
        <div className="space-y-2 text-sm">
          {[["Name", user?.full_name], ["Email", user?.email],
            ["Verified", user?.is_verified ? "✓ Verified" : "⚠ Not verified"]].map(([l, v]) => (
            <div key={l} className="flex gap-2">
              <span className="text-gray-500 w-24">{l}</span>
              <span className="text-gray-900 font-medium">{v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
