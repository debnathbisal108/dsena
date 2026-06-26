"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks";
import api from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";
import { Zap } from "lucide-react";

const schema = z.object({ email: z.string().email(), password: z.string().min(1) });
type F = z.infer<typeof schema>;

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<F>({ resolver: zodResolver(schema) });

  async function onSubmit(data: F) {
    setLoading(true); setError("");
    try {
      const res = await api.post("/api/auth/login", data);
      await login(res.data.access_token, res.data.refresh_token);
      router.replace("/");
    } catch (e) { setError(getErrorMessage(e)); }
    finally { setLoading(false); }
  }

  async function googleLogin() {
    try { const res = await api.get("/api/auth/google"); window.location.href = res.data.url; }
    catch (e) { setError(getErrorMessage(e)); }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-white px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">AI Sales Employee</h1>
          <p className="text-gray-500 mt-1">Your autonomous AI sales representative</p>
        </div>
        <div className="card p-8">
          <button onClick={googleLogin} className="btn-secondary w-full flex items-center justify-center gap-2 mb-6">
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>
          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-200" /></div>
            <div className="relative flex justify-center text-sm"><span className="bg-white px-2 text-gray-400">or</span></div>
          </div>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input {...register("email")} type="email" className="input" placeholder="you@company.com" />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input {...register("password")} type="password" className="input" placeholder="••••••••" />
            </div>
            <div className="flex justify-end text-sm">
              <Link href="/forgot-password" className="text-primary-600 hover:underline">Forgot password?</Link>
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>
          <p className="text-center text-sm text-gray-500 mt-6">
            No account? <Link href="/register" className="text-primary-600 hover:underline">Register free</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
