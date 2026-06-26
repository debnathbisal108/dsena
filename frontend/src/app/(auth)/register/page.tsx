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

const schema = z.object({
  full_name: z.string().min(2, "Name required"),
  email: z.string().email(),
  password: z.string().min(8, "At least 8 characters"),
});
type F = z.infer<typeof schema>;

export default function RegisterPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<F>({ resolver: zodResolver(schema) });

  async function onSubmit(data: F) {
    setLoading(true); setError("");
    try {
      const res = await api.post("/api/auth/register", data);
      await login(res.data.access_token, res.data.refresh_token);
      router.replace("/onboarding");
    } catch (e) { setError(getErrorMessage(e)); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-white px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Start your free trial</h1>
          <p className="text-gray-500 mt-1">Your AI sales employee is ready in 8 minutes</p>
        </div>
        <div className="card p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input {...register("full_name")} className="input" placeholder="Jane Smith" />
              {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Work Email</label>
              <input {...register("email")} type="email" className="input" placeholder="jane@company.com" />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input {...register("password")} type="password" className="input" placeholder="Min. 8 characters" />
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>
            <button type="submit" className="btn-primary w-full py-3" disabled={loading}>
              {loading ? "Creating account…" : "Create Free Account →"}
            </button>
          </form>
          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-primary-600 hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
