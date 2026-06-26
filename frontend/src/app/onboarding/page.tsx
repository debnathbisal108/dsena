"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks";
import api from "@/lib/api";
import { getErrorMessage, cn } from "@/lib/utils";
import { Building2, Globe, Brain, Calendar, Settings, CheckCircle, Loader2, ChevronRight } from "lucide-react";

const STEPS = [
  { label: "Business Info", icon: Building2 },
  { label: "AI Knowledge", icon: Brain },
  { label: "Email", icon: Globe },
  { label: "Calendar", icon: Calendar },
  { label: "AI Policy", icon: Settings },
];

const step1Schema = z.object({
  name: z.string().min(2, "Business name required"),
  slug: z.string().min(2).regex(/^[a-z0-9-]+$/, "Lowercase, numbers, hyphens only"),
  description: z.string().min(20, "Please describe your business (min 20 characters)"),
  services: z.string().min(10, "List your main services"),
  target_customer: z.string().min(5, "Describe your ideal customer"),
  pricing_guidance: z.string().optional(),
  faqs: z.string().optional(),
  business_rules: z.string().optional(),
  website_url: z.string().url("Enter a valid URL").optional().or(z.literal("")),
});
type Step1 = z.infer<typeof step1Schema>;

const policySchema = z.object({
  ai_tone: z.enum(["professional", "friendly", "casual", "premium"]),
  max_followup_attempts: z.coerce.number().min(1).max(10),
  allowed_hours_start: z.coerce.number().min(0).max(23),
  allowed_hours_end: z.coerce.number().min(1).max(24),
  allowed_timezone: z.string(),
});
type PolicyForm = z.infer<typeof policySchema>;

export default function OnboardingPage() {
  const { setOrg } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [crawlUrl, setCrawlUrl] = useState("");
  const [crawlJobId, setCrawlJobId] = useState("");
  const [crawlStatus, setCrawlStatus] = useState<"idle" | "running" | "done" | "failed">("idle");
  const [crawlProgress, setCrawlProgress] = useState({ pages: 0, chunks: 0 });
  const [org, setLocalOrg] = useState<any>(null);

  const step1Form = useForm<Step1>({ resolver: zodResolver(step1Schema) });
  const policyForm = useForm<PolicyForm>({
    resolver: zodResolver(policySchema),
    defaultValues: { ai_tone: "professional", max_followup_attempts: 5, allowed_hours_start: 8, allowed_hours_end: 18, allowed_timezone: "UTC" },
  });

  async function submitStep1(data: Step1) {
    setLoading(true); setError("");
    try {
      const res = await api.post("/api/onboarding/business-info", data);
      setLocalOrg(res.data);
      setCrawlUrl(data.website_url || "");
      setStep(2);
    } catch (e) { setError(getErrorMessage(e)); }
    finally { setLoading(false); }
  }

  async function startCrawl() {
    if (!crawlUrl) { setStep(3); return; }
    setLoading(true); setError(""); setCrawlStatus("running");
    try {
      const res = await api.post("/api/onboarding/crawl-website", { url: crawlUrl });
      setCrawlJobId(res.data.id);
      pollCrawl(res.data.id);
    } catch (e) { setError(getErrorMessage(e)); setCrawlStatus("failed"); setLoading(false); }
  }

  function pollCrawl(jobId: string) {
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/api/onboarding/crawl-status/${jobId}`);
        const job = res.data;
        setCrawlProgress({ pages: job.pages_found, chunks: job.chunks_created });
        if (job.status === "done") {
          clearInterval(interval);
          setCrawlStatus("done");
          setLoading(false);
        } else if (job.status === "failed") {
          clearInterval(interval);
          setCrawlStatus("failed");
          setError(job.error || "Crawl failed");
          setLoading(false);
        }
      } catch { clearInterval(interval); setLoading(false); }
    }, 2000);
  }

  async function submitPolicy(data: PolicyForm) {
    setLoading(true); setError("");
    try {
      const res = await api.post("/api/onboarding/ai-policy", data);
      setOrg(res.data);
      router.replace("/dashboard");
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
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white">
      <div className="max-w-2xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-2xl font-bold text-gray-900">Set up your AI Sales Employee</h1>
          <p className="text-gray-500 mt-1">Ready in under 10 minutes</p>
        </div>

        {/* Step indicators */}
        <div className="flex items-center justify-center gap-2 mb-10">
          {STEPS.map((s, i) => {
            const n = i + 1;
            const done = step > n;
            const active = step === n;
            return (
              <div key={n} className="flex items-center">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all",
                  done ? "bg-green-500 text-white" : active ? "bg-primary-600 text-white" : "bg-gray-200 text-gray-500"
                )}>
                  {done ? <CheckCircle className="w-4 h-4" /> : n}
                </div>
                <span className={cn("hidden sm:block text-xs ml-1.5 mr-3", active ? "text-gray-900 font-medium" : "text-gray-400")}>
                  {s.label}
                </span>
                {i < STEPS.length - 1 && <div className={cn("h-0.5 w-4 sm:w-6", step > n ? "bg-green-400" : "bg-gray-200")} />}
              </div>
            );
          })}
        </div>

        {error && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-6">{error}</div>}

        {/* Step 1: Business Info */}
        {step === 1 && (
          <div className="card p-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Tell us about your business</h2>
            <form onSubmit={step1Form.handleSubmit(submitStep1)} className="space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Business Name <span className="text-red-500">*</span></label>
                  <input {...step1Form.register("name")} className="input" placeholder="Acme Marketing Agency" />
                  {step1Form.formState.errors.name && <p className="text-red-500 text-xs mt-1">{step1Form.formState.errors.name.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">URL Slug <span className="text-red-500">*</span></label>
                  <input {...step1Form.register("slug")} className="input" placeholder="acme-marketing" />
                  <p className="text-xs text-gray-400 mt-1">Your form: /form/acme-marketing</p>
                  {step1Form.formState.errors.slug && <p className="text-red-500 text-xs mt-1">{step1Form.formState.errors.slug.message}</p>}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Business Description <span className="text-red-500">*</span></label>
                <textarea {...step1Form.register("description")} rows={3} className="input resize-none"
                  placeholder="We help small businesses grow their online presence through SEO, content marketing, and paid ads..." />
                {step1Form.formState.errors.description && <p className="text-red-500 text-xs mt-1">{step1Form.formState.errors.description.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Services Offered <span className="text-red-500">*</span></label>
                <textarea {...step1Form.register("services")} rows={2} className="input resize-none"
                  placeholder="SEO audits, content strategy, Google Ads management, social media marketing..." />
                {step1Form.formState.errors.services && <p className="text-red-500 text-xs mt-1">{step1Form.formState.errors.services.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Target Customer <span className="text-red-500">*</span></label>
                <input {...step1Form.register("target_customer")} className="input"
                  placeholder="Small e-commerce businesses, $500k-$5M revenue, US-based" />
                {step1Form.formState.errors.target_customer && <p className="text-red-500 text-xs mt-1">{step1Form.formState.errors.target_customer.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Pricing Guidance</label>
                <textarea {...step1Form.register("pricing_guidance")} rows={2} className="input resize-none"
                  placeholder="Projects start at $2,000/month. Discovery call required for custom quotes." />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Business Rules for AI</label>
                <textarea {...step1Form.register("business_rules")} rows={2} className="input resize-none"
                  placeholder="Never promise specific results or timelines. Don't discuss competitor pricing. Always suggest a call for questions about pricing." />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Website URL</label>
                <input {...step1Form.register("website_url")} className="input" placeholder="https://yoursite.com" />
                <p className="text-xs text-gray-400 mt-1">AI will crawl your site to build its knowledge base</p>
              </div>
              <button type="submit" className="btn-primary w-full py-3 flex items-center justify-center gap-2" disabled={loading}>
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                {loading ? "Saving…" : "Continue →"}
              </button>
            </form>
          </div>
        )}

        {/* Step 2: Knowledge */}
        {step === 2 && (
          <div className="card p-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Build AI Knowledge Base</h2>
            <p className="text-gray-500 text-sm mb-6">AI will read your website and learn everything about your business automatically.</p>

            {crawlUrl && (
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <p className="text-sm text-gray-600 mb-3">Website to crawl: <strong>{crawlUrl}</strong></p>
                {crawlStatus === "idle" && (
                  <button onClick={startCrawl} className="btn-primary flex items-center gap-2" disabled={loading}>
                    <Brain className="w-4 h-4" /> Start Crawling
                  </button>
                )}
                {crawlStatus === "running" && (
                  <div>
                    <div className="flex items-center gap-2 text-sm text-primary-600 mb-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      AI is reading your website…
                    </div>
                    <div className="text-xs text-gray-500">
                      {crawlProgress.pages} pages found · {crawlProgress.chunks} knowledge chunks created
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full mt-2 overflow-hidden">
                      <div className="h-full bg-primary-500 rounded-full animate-pulse" style={{ width: "60%" }} />
                    </div>
                  </div>
                )}
                {crawlStatus === "done" && (
                  <div className="flex items-center gap-2 text-green-600 text-sm">
                    <CheckCircle className="w-4 h-4" />
                    Done! {crawlProgress.pages} pages read, {crawlProgress.chunks} knowledge chunks created
                  </div>
                )}
                {crawlStatus === "failed" && (
                  <p className="text-red-500 text-sm">Crawl failed. You can skip this and add knowledge manually later.</p>
                )}
              </div>
            )}

            {!crawlUrl && (
              <div className="bg-amber-50 rounded-lg p-4 mb-6 text-sm text-amber-700">
                No website URL provided. You can add knowledge manually from the Knowledge Base page after setup.
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setStep(3)}
                disabled={crawlStatus === "running"}
                className="btn-primary flex items-center gap-2"
              >
                {crawlStatus === "done" ? "Continue →" : "Skip for now →"}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Email */}
        {step === 3 && (
          <div className="card p-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Connect Email</h2>
            <p className="text-gray-500 text-sm mb-6">
              For now, emails are sent via Resend. Set your <code className="bg-gray-100 px-1 rounded">RESEND_FROM_EMAIL</code> in your backend environment variables to customize the sending address.
            </p>
            <div className="bg-blue-50 rounded-lg p-4 text-sm text-blue-700 mb-6">
              <p className="font-medium mb-1">Email sending is already configured</p>
              <p>Your AI will send emails from the address you set in <code>RESEND_FROM_EMAIL</code>. Gmail/Outlook OAuth integration is available in Version 2.</p>
            </div>
            <button onClick={() => setStep(4)} className="btn-primary flex items-center gap-2">
              Continue <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Step 4: Calendar */}
        {step === 4 && (
          <div className="card p-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Connect Google Calendar</h2>
            <p className="text-gray-500 text-sm mb-6">
              AI will push high-intent leads to book discovery calls directly in your calendar.
            </p>
            <button onClick={connectCalendar} className="btn-primary flex items-center gap-2 mb-4">
              <Calendar className="w-4 h-4" /> Connect Google Calendar
            </button>
            <button onClick={() => setStep(5)} className="btn-secondary text-sm">
              Skip for now — I'll connect later
            </button>
          </div>
        )}

        {/* Step 5: AI Policy */}
        {step === 5 && (
          <div className="card p-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Configure AI Behaviour</h2>
            <p className="text-gray-500 text-sm mb-6">Set the rules your AI follows when engaging leads.</p>
            <form onSubmit={policyForm.handleSubmit(submitPolicy)} className="space-y-5">
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
                  Maximum Follow-up Attempts: <strong>{policyForm.watch("max_followup_attempts")}</strong>
                </label>
                <input {...policyForm.register("max_followup_attempts")} type="range" min={1} max={10} className="w-full" />
                <div className="flex justify-between text-xs text-gray-400 mt-1"><span>1 (minimal)</span><span>10 (persistent)</span></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Send emails from hour</label>
                  <select {...policyForm.register("allowed_hours_start")} className="input">
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i} value={i}>{i}:00</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Until hour</label>
                  <select {...policyForm.register("allowed_hours_end")} className="input">
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i + 1} value={i + 1}>{i + 1}:00</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
                <select {...policyForm.register("allowed_timezone")} className="input">
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern US</option>
                  <option value="America/Chicago">Central US</option>
                  <option value="America/Los_Angeles">Pacific US</option>
                  <option value="Europe/London">London</option>
                  <option value="Europe/Paris">Paris</option>
                  <option value="Asia/Kolkata">India (IST)</option>
                  <option value="Asia/Singapore">Singapore</option>
                  <option value="Australia/Sydney">Sydney</option>
                </select>
              </div>
              <button type="submit" className="btn-primary w-full py-3 flex items-center justify-center gap-2" disabled={loading}>
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                {loading ? "Finishing setup…" : "Launch my AI Sales Employee →"}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
