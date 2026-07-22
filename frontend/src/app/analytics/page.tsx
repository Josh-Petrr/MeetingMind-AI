"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { TrendingUp, CheckCircle2, ShieldCheck, Loader2, ChevronLeft, ChevronRight } from "lucide-react";

export default function AnalyticsPage() {
  const [meetings, setMeetings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const pageSize = 10;
  const baseUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

  useEffect(() => {
    fetch(`${baseUrl}/meetings`)
      .then(res => res.json())
      .then(data => {
        setMeetings(data.meetings || []);
        setLoading(false);
      });
  }, [baseUrl]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
      </div>
    );
  }

  // Calculate metrics
  const totalMeetings = meetings.length;
  const totalActions = meetings.reduce((acc, m) => acc + m.action_items_count, 0);
  const totalDecisions = meetings.reduce((acc, m) => acc + m.decisions_count, 0);

  // Prepare chart data (slice based on page, reverse to show chronological order)
  const startIndex = page * pageSize;
  const endIndex = startIndex + pageSize;
  const chartData = [...meetings].slice(startIndex, endIndex).reverse().map(m => ({
    name: m.meeting_id.substring(0, 8) + "...",
    Actions: m.action_items_count,
    Decisions: m.decisions_count
  }));

  const hasNewer = page > 0;
  const hasOlder = endIndex < meetings.length;

  return (
    <div className="p-8 max-w-6xl mx-auto h-full flex flex-col">
      <header className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Executive Analytics</h2>
        <p className="text-slate-400">High-level insights across all organizational meetings.</p>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="glass-panel p-6 rounded-2xl flex items-center justify-between group hover:border-blue-500/30 transition-colors">
          <div>
            <p className="text-sm font-medium text-slate-400 mb-1">Total Meetings Processed</p>
            <h3 className="text-4xl font-bold text-white group-hover:text-blue-400 transition-colors">{totalMeetings}</h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
            <ShieldCheck className="w-6 h-6 text-blue-400" />
          </div>
        </div>
        
        <div className="glass-panel p-6 rounded-2xl flex items-center justify-between group hover:border-amber-500/30 transition-colors">
          <div>
            <p className="text-sm font-medium text-slate-400 mb-1">Total Action Items</p>
            <h3 className="text-4xl font-bold text-white group-hover:text-amber-400 transition-colors">{totalActions}</h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center border border-amber-500/30">
            <CheckCircle2 className="w-6 h-6 text-amber-400" />
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl flex items-center justify-between group hover:border-emerald-500/30 transition-colors">
          <div>
            <p className="text-sm font-medium text-slate-400 mb-1">Key Decisions Logged</p>
            <h3 className="text-4xl font-bold text-white group-hover:text-emerald-400 transition-colors">{totalDecisions}</h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30">
            <TrendingUp className="w-6 h-6 text-emerald-400" />
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="glass-panel p-6 rounded-2xl flex-1 min-h-[400px]">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-white">Productivity Over Time</h3>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={!hasNewer}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-white"
            >
              <ChevronLeft className="w-4 h-4" /> Newer
            </button>
            <span className="text-sm text-slate-400 font-medium">Page {page + 1}</span>
            <button 
              onClick={() => setPage(p => p + 1)}
              disabled={!hasOlder}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-white"
            >
              Older <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
        <ResponsiveContainer width="100%" height="85%">
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip 
              cursor={{ fill: 'rgba(255,255,255,0.05)' }} 
              contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '12px' }}
              itemStyle={{ fontSize: '14px', fontWeight: 'bold' }}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            <Bar dataKey="Actions" fill="#f59e0b" radius={[4, 4, 0, 0]} maxBarSize={60} />
            <Bar dataKey="Decisions" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={60} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

