// src/lib/api.ts
import axios from "axios";
// const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const API_URL = "https://dsena.onrender.com";

export const api = axios.create({ baseURL: API_URL, headers: { "Content-Type": "application/json" } });
api.interceptors.request.use((c) => {
  if (typeof window !== "undefined") { const t = localStorage.getItem("access_token"); if (t) c.headers.Authorization = `Bearer ${t}`; }
  return c;
});
api.interceptors.response.use((r) => r, async (err) => {
  const orig = err.config;
  if (err.response?.status === 401 && !orig._retry) {
    orig._retry = true;
    const refresh = localStorage.getItem("refresh_token");
    if (refresh) {
      try {
        const { data } = await axios.post(`${API_URL}/api/auth/refresh`, { refresh_token: refresh });
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        orig.headers.Authorization = `Bearer ${data.access_token}`;
        return api(orig);
      } catch { localStorage.removeItem("access_token"); localStorage.removeItem("refresh_token"); window.location.href = "/login"; }
    }
  }
  return Promise.reject(err);
});
export default api;
