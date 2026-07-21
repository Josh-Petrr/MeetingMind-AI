"use client";

import { useState } from "react";
import { Search, BrainCircuit, Loader2, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/memory/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
          org_id: "org_demo_123",
          top_k: 5,
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to search memories");
      }

      const data = await res.json();
      setResults(data.results || []);
      setHasSearched(true);
    } catch (err) {
      console.error(err);
      setError("An error occurred while searching. Is the backend running?");
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto h-full flex flex-col">
      <header className="mb-12 text-center mt-12">
        <h2 className="text-4xl font-bold text-white mb-4 tracking-tight">Organizational Memory</h2>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto">
          Query the collective intelligence of all past meetings. Ask questions about decisions, action items, or discussions.
        </p>
      </header>

      <form onSubmit={handleSearch} className="relative w-full max-w-3xl mx-auto mb-12 group">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <Search className="h-6 w-6 text-slate-500 group-focus-within:text-blue-400 transition-colors" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="block w-full pl-14 pr-32 py-5 bg-slate-900/60 border border-white/10 rounded-2xl text-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all shadow-xl backdrop-blur-sm"
          placeholder="e.g. What did we decide about the AWS migration?"
        />
        <div className="absolute inset-y-2 right-2 flex items-center">
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-all flex items-center gap-2"
          >
            {isSearching ? <Loader2 className="w-5 h-5 animate-spin" /> : "Search"}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-4 mb-8 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-center max-w-3xl mx-auto w-full">
          {error}
        </div>
      )}

      <div className="flex-1 max-w-3xl mx-auto w-full space-y-4 pb-12">
        {isSearching && !results.length && (
          <div className="flex justify-center py-12">
            <BrainCircuit className="w-12 h-12 text-blue-500/50 animate-pulse" />
          </div>
        )}

        {hasSearched && !isSearching && results.length === 0 && (
          <div className="text-center py-12 text-slate-500">
            No memories found matching your query.
          </div>
        )}

        {!isSearching && results.map((result, i) => (
          <div key={i} className="glass-panel p-6 rounded-2xl hover:border-blue-500/30 transition-colors group">
            <div className="flex items-start justify-between mb-3">
              <span className="px-3 py-1 bg-white/5 rounded-full text-xs font-medium text-slate-300 uppercase tracking-wider border border-white/10">
                {result.memory_type}
              </span>
              <span className="text-xs font-mono text-slate-500">
                Match: {((result.score || result.relevance_score || 0) * 100).toFixed(1)}%
              </span>
            </div>
            <p className="text-slate-200 text-lg leading-relaxed mb-4 group-hover:text-white transition-colors">
              "{result.text}"
            </p>
            <div className="flex items-center justify-between text-sm text-slate-500 border-t border-white/5 pt-4">
              <div className="flex items-center gap-2">
                <span className="font-medium text-slate-400">Meeting ID:</span>
                <span className="font-mono">{result.meeting_id}</span>
              </div>
              <Link 
                href={`/review/${result.meeting_id}`}
                className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors font-medium cursor-pointer"
              >
                View Full Context <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
