"use client";
import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import api from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { CheckCircle } from "lucide-react";

const schema = z.object({ email: z.string().email() });
type F = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<F>({ resolver: zodResolver(schema) });

  async function onSubmit(data: F) {
    setLoading(true); setError("");
    try { await api.post("/api/auth/forgot-password", data); setSent(true); }
    catch (e) { setError(getErrorMessage(e)); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-white px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Reset your password</h1>
          <p className="text-gray-500 mt-1">We'll send you a reset link</p>
        </div>
        <div className="card p-8">
          {sent ? (
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <p className="text-gray-700 font-medium">Check your inbox</p>
              <p className="text-gray-500 text-sm mt-1">If that email exists, a reset link has been sent.</p>
              <Link href="/login" className="btn-primary inline-block mt-6">Back to Login</Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {error && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input {...register("email")} type="email" className="input" placeholder="you@company.com" />
                {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
              </div>
              <button type="submit" className="btn-primary w-full" disabled={loading}>
                {loading ? "Sending…" : "Send Reset Link"}
              </button>
              <p className="text-center text-sm text-gray-500">
                <Link href="/login" className="text-primary-600 hover:underline">Back to login</Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
