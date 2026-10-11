import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  Search,
  FileText,
  Bookmark,
  CheckCircle,
  AlertCircle,
  ExternalLink
} from 'lucide-react';
import { api } from '../services/api';
import { PolicyDocument } from '../types';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';

export const KnowledgePage: React.FC = () => {
  const [policies, setPolicies] = useState<PolicyDocument[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any | null>(null);
  const [searching, setSearching] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<any | null>(null);

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    try {
      const res = await api.getPolicies();
      setPolicies(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setSearching(true);
      const res = await api.searchKnowledge(searchQuery.trim());
      setSearchResults(res);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const handleOpenDetails = async (id: string) => {
    try {
      const doc = await api.getPolicyDetails(id);
      setSelectedPolicy(doc);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-teal-400" />
          Policy & Regulatory Knowledge Center (RAG)
        </h1>
        <p className="text-xs text-slate-400">
          Local TF-IDF passage indexing and semantic search over versioned banking SOPs and regulatory guidelines.
        </p>
      </div>

      {/* RAG Query Box */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-md space-y-4">
        <h2 className="text-sm font-bold text-white flex items-center gap-2">
          <Search className="w-4 h-4 text-teal-400" />
          Ask Policy Knowledge Base
        </h2>
        <form onSubmit={handleSearch} className="flex gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Try: 'What is the loan eligibility DTI limit?' or 'Unusual transactions monitoring policy'..."
            className="flex-1 bg-slate-950 border border-slate-800 focus:border-teal-500 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none transition"
          />
          <button
            type="submit"
            disabled={searching || !searchQuery.trim()}
            className="px-5 py-2.5 bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-lg shadow-teal-500/20"
          >
            {searching ? 'Searching...' : 'Search Policy'}
          </button>
        </form>

        {/* Search Results */}
        {searchResults && (
          <div className="pt-3 border-t border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">
                {searchResults.answer_supported ? (
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle className="w-4 h-4" /> Grounded Policy Evidence Found
                  </span>
                ) : (
                  <span className="text-amber-400 font-semibold flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" /> Insufficient Evidence
                  </span>
                )}
              </span>
              {searchResults.primary_source && (
                <span className="text-slate-500 font-mono text-[11px]">Primary Source: {searchResults.primary_source}</span>
              )}
            </div>

            <p className="text-xs text-slate-300 italic">{searchResults.summary}</p>

            {searchResults.matches && searchResults.matches.length > 0 && (
              <div className="space-y-2.5 pt-1">
                {searchResults.matches.map((m: any, idx: number) => (
                  <div key={idx} className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-teal-400 font-mono">[{m.document_id}] {m.title}</span>
                      <Badge label={`Relevance: ${m.relevance_score}`} variant="info" />
                    </div>
                    <blockquote className="border-l-2 border-teal-500/50 pl-3 py-1 text-slate-200 italic leading-relaxed">
                      "{m.supporting_passage}"
                    </blockquote>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Policy Library Cards */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold text-white">Indexed Banking Policy Library</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {policies.map((p) => (
            <div
              key={p.id}
              onClick={() => handleOpenDetails(p.id)}
              className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-xl p-5 space-y-3 shadow-sm hover:shadow-md transition cursor-pointer flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-teal-400 font-bold text-xs">{p.id}</span>
                  <Badge label={p.version} variant="default" />
                </div>
                <h3 className="text-sm font-bold text-white leading-snug">{p.title}</h3>
                <p className="text-xs text-slate-400 mt-1">{p.category}</p>
              </div>
              <div className="pt-3 border-t border-slate-800/80 flex justify-between items-center text-xs text-slate-500">
                <span>Passages: {p.passages_count}</span>
                <span className="text-teal-400 font-medium flex items-center gap-1">Read Document &rarr;</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Policy Details Modal */}
      {selectedPolicy && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedPolicy(null)}
          title={`Policy Document: ${selectedPolicy.id}`}
        >
          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">{selectedPolicy.title}</h3>
                <span className="text-slate-400">{selectedPolicy.category} • Effective: {selectedPolicy.effective_date}</span>
              </div>
              <Badge label={selectedPolicy.version} variant="verified" />
            </div>

            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-slate-200 leading-relaxed font-sans space-y-2">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">Full Regulatory Text</span>
              <p className="whitespace-pre-wrap">{selectedPolicy.content}</p>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
