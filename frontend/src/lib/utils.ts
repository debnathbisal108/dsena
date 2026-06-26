import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";

export const cn = (...i: ClassValue[]) => twMerge(clsx(i));
export const formatDate = (d: string) => format(new Date(d), "MMM d, yyyy");
export const formatDateTime = (d: string) => format(new Date(d), "MMM d, yyyy 'at' h:mm a");
export const timeAgo = (d: string) => formatDistanceToNow(new Date(d), { addSuffix: true });

export function scoreColor(score: number): string {
  if (score >= 70) return "text-red-600 bg-red-50";
  if (score >= 40) return "text-amber-600 bg-amber-50";
  return "text-blue-600 bg-blue-50";
}
export function scoreLabel(score: number): string {
  if (score >= 70) return "🔥 Hot";
  if (score >= 40) return "🌤 Warm";
  return "❄️ Cold";
}
export function statusColor(status: string): string {
  const map: Record<string, string> = {
    new: "bg-gray-100 text-gray-700",
    ai_contacted: "bg-blue-100 text-blue-700",
    nurturing: "bg-indigo-100 text-indigo-700",
    meeting_proposed: "bg-purple-100 text-purple-700",
    meeting_booked: "bg-green-100 text-green-700",
    qualified: "bg-emerald-100 text-emerald-700",
    disqualified: "bg-red-100 text-red-700",
    stopped: "bg-gray-200 text-gray-500",
    needs_human: "bg-orange-100 text-orange-700",
    unsubscribed: "bg-gray-200 text-gray-400",
  };
  return map[status] || "bg-gray-100 text-gray-600";
}
export function actionTypeLabel(type: string): string {
  const map: Record<string, string> = {
    initial_response: "Initial response sent",
    followup: "Follow-up sent",
    propose_meeting: "Meeting proposed",
    stop_outreach: "Outreach stopped",
    escalated_human: "Escalated to human",
    wait: "Decided to wait",
    scored: "Lead scored",
  };
  return map[type] || type;
}
export function getErrorMessage(e: unknown): string {
  if (typeof e === "object" && e !== null && "response" in e) {
    const err = e as { response?: { data?: { detail?: string } } };
    return err.response?.data?.detail || "An error occurred";
  }
  return "An unexpected error occurred";
}
