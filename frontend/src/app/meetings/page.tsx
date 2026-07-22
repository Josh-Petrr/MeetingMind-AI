"use client";

import { useEffect, useState } from "react";
import { FileText, ArrowRight, CheckCircle2, TrendingUp, Loader2 } from "lucide-react";
import Link from "next/link";

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const baseUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

  useEffect(() => {
    fetch(`${baseUrl}/meetings`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load meetings");
        return res.json();
      })
      .then((data) => {
        setMeetings(data.meetings || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Could not connect to backend server.");
        setLoading(false);
      });
  }, [apiUrl]);

  return (
    <div className="p-8 max-w-6xl mx-auto h-full flex flex-col">
      <header className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Past Meetings Archive</h2>
        <p className="text-slate-400">
          Browse and review all intelligence reports generated for past organization meetings.
        </p>
      </header>

      {loading && (
        <div className="flex justify-center py-20">
          <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-center">
          {error}
        </div>
      )}

      {!loading && !error && meetings.length === 0 && (
        <div className="glass-panel p-12 rounded-2xl text-center text-slate-400">
          <FileText className="w-12 h-12 mx-auto mb-4 text-slate-600" />
          <p className="text-lg mb-4">No processed meetings found yet.</p>
          <Link href="/" className="px-4 py-2 bg-blue-600 text-white rounded-lg inline-block font-medium">
            Process Your First Meeting
          </Link>
        </div>
      )}

      {!loading && meetings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {meetings.map((m) => (
            <div
              key={m.meeting_id}
              className="glass-panel p-6 rounded-2xl border border-white/10 hover:border-blue-500/40 transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs text-blue-400 font-semibold px-2.5 py-1 rounded-md bg-blue-500/10 border border-blue-500/20">
                    {m.meeting_id}
                  </span>
                  <span className="text-xs text-slate-400 capitalize bg-white/5 px-2.5 py-1 rounded-md border border-white/5">
                    Status: {m.status}
                  </span>
                </div>
                <p className="text-slate-300 text-sm mb-6 leading-relaxed">
                  {m.summary_snippet}
                </p>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-white/5">
                <div className="flex gap-4 text-xs text-slate-400">
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" />
                    {m.action_items_count} Actions
                  </span>
                  <span className="flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                    {m.decisions_count} Decisions
                  </span>
                </div>
                <Link
                  href={`/review/${m.meeting_id}`}
                  className="flex items-center gap-1 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors group-hover:translate-x-1 duration-200"
                >
                  View Report <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

