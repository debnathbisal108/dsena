"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import axios from "axios";
import { CheckCircle, Zap } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const schema = z.object({
  full_name: z.string().min(2, "Name required"),
  email: z.string().email("Valid email required"),
  phone: z.string().optional(),
  company: z.string().optional(),
  role: z.string().optional(),
  message: z.string().min(10, "Please tell us a bit more (min 10 characters)"),
});
type F = z.infer<typeof schema>;

export default function LeadFormPage() {
  const { orgSlug } = useParams<{ orgSlug: string }>();
  const [orgName, setOrgName] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const isWidget = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("widget") === "1";

  useEffect(() => {
    axios.get(`${API_URL}/public/form/${orgSlug}/config`)
      .then((r) => setOrgName(r.data.org_name))
      .catch(() => setOrgName("us"));
  }, [orgSlug]);

  const { register, handleSubmit, formState: { errors } } = useForm<F>({ resolver: zodResolver(schema) });

  async function onSubmit(data: F) {
    setLoading(true); setError("");
    try {
      const params = new URLSearchParams(window.location.search);
      await axios.post(`${API_URL}/public/form/${orgSlug}`, {
        ...data,
        utm_source: params.get("utm_source") || undefined,
        utm_medium: params.get("utm_medium") || undefined,
        utm_campaign: params.get("utm_campaign") || undefined,
      });
      setSubmitted(true);
    } catch (e: any) { setError(e?.response?.data?.detail || "Something went wrong. Please try again."); }
    finally { setLoading(false); }
  }

  if (submitted) {
    return (
      <div className={`${isWidget ? "p-6" : "min-h-screen bg-gradient-to-br from-primary-50 to-white flex items-center justify-center px-4"}`}>
        <div className="text-center max-w-md mx-auto">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">You're all set!</h2>
          <p className="text-gray-500 text-sm">
            Thanks for reaching out to <strong>{orgName}</strong>. Check your inbox — our AI will be in touch within minutes!
          </p>
        </div>
      </div>
    );
  }

  const formContent = (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {error && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Full Name <span className="text-red-500">*</span></label>
          <input {...register("full_name")} className="input" placeholder="Jane Smith" />
          {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email <span className="text-red-500">*</span></label>
          <input {...register("email")} type="email" className="input" placeholder="jane@company.com" />
          {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
          <input {...register("phone")} type="tel" className="input" placeholder="+1 555 000 0000" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
          <input {...register("company")} className="input" placeholder="Acme Inc." />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Your Role</label>
        <input {...register("role")} className="input" placeholder="Marketing Director, Founder…" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">How can we help? <span className="text-red-500">*</span></label>
        <textarea {...register("message")} rows={4} className="input resize-none"
          placeholder="Tell us about your project, goals, timeline, or budget…" />
        {errors.message && <p className="text-red-500 text-xs mt-1">{errors.message.message}</p>}
      </div>
      <button type="submit" className="btn-primary w-full py-3" disabled={loading}>
        {loading ? "Sending…" : "Send Message →"}
      </button>
    </form>
  );

  if (isWidget) {
    return (
      <div className="p-5 bg-white min-h-full">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-6 h-6 bg-primary-600 rounded flex items-center justify-center">
            <Zap className="w-3 h-3 text-white" />
          </div>
          <h2 className="font-semibold text-gray-900 text-sm">Contact {orgName}</h2>
        </div>
        {formContent}
        <p className="text-center text-xs text-gray-400 mt-4">Powered by AI Sales Employee</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Get in touch with {orgName}</h1>
          <p className="text-gray-500 mt-2 text-sm">Our AI will respond within minutes.</p>
        </div>
        <div className="card p-8">{formContent}</div>
        <p className="text-center text-xs text-gray-400 mt-6">Powered by AI Sales Employee</p>
      </div>
    </div>
  );
}
