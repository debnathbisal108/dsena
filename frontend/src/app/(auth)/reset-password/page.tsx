"use client";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import api from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";

const schema = z.object({
  password: z.string().min(8, "At least 8 characters"),
  confirm: z.string(),
}).refine((d) => d.password === d.confirm, { message: "Passwords don't match", path: ["confirm"] });
type F = z.infer<typeof schema>;

export default function ResetPasswordPage() {
  const params = useSearchParams();
  const router = useRouter();
  const token = params.get("token") || "";
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<F>({ resolver: zodResolver(schema) });

  async function onSubmit(data: F) {
    setLoading(true); setError("");
    try {
      await api.post("/api/auth/reset-password", { token, password: data.password });
      router.push("/login?reset=success");
    } catch (e) { setError(getErrorMessage(e)); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-white px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Set new password</h1>
        </div>
        <div className="card p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
              <input {...register("password")} type="password" className="input" />
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
              <input {...register("confirm")} type="password" className="input" />
              {errors.confirm && <p className="text-red-500 text-xs mt-1">{errors.confirm.message}</p>}
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? "Saving…" : "Reset Password"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
