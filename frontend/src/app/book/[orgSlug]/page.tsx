"use client";
import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "next/navigation";
import axios from "axios";
import { format, addDays, startOfDay } from "date-fns";
import { CheckCircle, ChevronLeft, ChevronRight, Calendar, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function BookingPage() {
  const { orgSlug } = useParams<{ orgSlug: string }>();
  const searchParams = useSearchParams();
  const leadId = searchParams.get("lead_id") || "";
  const [orgName, setOrgName] = useState("");
  const [selectedDate, setSelectedDate] = useState(startOfDay(addDays(new Date(), 1)));
  const [slots, setSlots] = useState<{ starts_at: string; ends_at: string }[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<{ starts_at: string; ends_at: string } | null>(null);
  const [booking, setBooking] = useState(false);
  const [booked, setBooked] = useState<{ meet_link: string; starts_at: string } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    axios.get(`${API_URL}/public/form/${orgSlug}/config`)
      .then((r) => setOrgName(r.data.org_name)).catch(() => {});
  }, [orgSlug]);

  useEffect(() => { fetchSlots(selectedDate); }, [selectedDate]);

  async function fetchSlots(date: Date) {
    setLoadingSlots(true); setSelectedSlot(null);
    try {
      const r = await axios.get(`${API_URL}/public/book/${orgSlug}?date=${format(date, "yyyy-MM-dd")}`);
      setSlots(r.data.slots);
    } catch { setSlots([]); }
    finally { setLoadingSlots(false); }
  }

  async function confirmBooking() {
    if (!selectedSlot || !leadId) return;
    setBooking(true); setError("");
    try {
      const r = await axios.post(`${API_URL}/public/book/${orgSlug}`, {
        lead_id: leadId, starts_at: selectedSlot.starts_at, ends_at: selectedSlot.ends_at,
      });
      setBooked({ meet_link: r.data.meet_link, starts_at: selectedSlot.starts_at });
    } catch (e: any) { setError(e?.response?.data?.detail || "Booking failed. Please try another time."); }
    finally { setBooking(false); }
  }

  if (booked) return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-white px-4">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Meeting confirmed!</h2>
        <p className="text-gray-600 mb-2">Discovery call with <strong>{orgName}</strong>:</p>
        <p className="text-lg font-semibold text-primary-700 mb-6">
          {format(new Date(booked.starts_at), "EEEE, MMMM d 'at' h:mm a")} UTC
        </p>
        {booked.meet_link && (
          <a href={booked.meet_link} target="_blank" rel="noopener noreferrer"
            className="btn-primary inline-flex items-center gap-2">
            <Calendar className="w-4 h-4" /> Join Google Meet
          </a>
        )}
        <p className="text-sm text-gray-400 mt-4">Check your email for a calendar invite.</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white px-4 py-12">
      <div className="max-w-lg mx-auto">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Book a discovery call</h1>
          <p className="text-gray-500 mt-1">with {orgName}</p>
        </div>
        <div className="card p-6">
          {/* Date nav */}
          <div className="flex items-center justify-between mb-6">
            <button onClick={() => setSelectedDate((d) => addDays(d, -1))}
              disabled={selectedDate <= startOfDay(addDays(new Date(), 1))}
              className="btn-secondary p-2 disabled:opacity-40">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <div className="text-center">
              <p className="font-semibold text-gray-900">{format(selectedDate, "EEEE")}</p>
              <p className="text-sm text-gray-500">{format(selectedDate, "MMMM d, yyyy")}</p>
            </div>
            <button onClick={() => setSelectedDate((d) => addDays(d, 1))} className="btn-secondary p-2">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Slots */}
          {loadingSlots ? (
            <div className="grid grid-cols-3 gap-2">
              {[...Array(9)].map((_, i) => <div key={i} className="h-10 bg-gray-100 rounded-lg animate-pulse" />)}
            </div>
          ) : slots.length === 0 ? (
            <p className="text-center text-gray-400 py-8 text-sm">No available slots. Try another date.</p>
          ) : (
            <div className="grid grid-cols-3 gap-2">
              {slots.map((slot) => (
                <button key={slot.starts_at} onClick={() => setSelectedSlot(slot)}
                  className={cn("py-2 px-3 rounded-lg text-sm font-medium transition-colors border",
                    selectedSlot?.starts_at === slot.starts_at
                      ? "bg-primary-600 text-white border-primary-600"
                      : "bg-white text-gray-700 border-gray-200 hover:border-primary-400 hover:text-primary-600")}>
                  {format(new Date(slot.starts_at), "h:mm a")}
                </button>
              ))}
            </div>
          )}

          {selectedSlot && (
            <div className="mt-6 pt-6 border-t border-gray-100">
              {error && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-4">{error}</div>}
              <p className="text-sm text-gray-600 mb-4 text-center">
                Selected: <strong>{format(new Date(selectedSlot.starts_at), "h:mm a")} — {format(new Date(selectedSlot.ends_at), "h:mm a")} UTC</strong>
              </p>
              <button onClick={confirmBooking} className="btn-primary w-full py-3" disabled={booking || !leadId}>
                {booking ? "Confirming…" : leadId ? "Confirm Booking" : "No lead ID — submit the form first"}
              </button>
            </div>
          )}
        </div>
        <p className="text-center text-xs text-gray-400 mt-6">Powered by AI Sales Employee</p>
      </div>
    </div>
  );
}
