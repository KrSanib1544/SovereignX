// frontend/src/components/knowledge/SearchTester.tsx
import React, { useState } from 'react';
import { Search, Loader2, BookOpen, Hash } from 'lucide-react';
import { queryKnowledgeVault } from '../../api/workspaces';
import { QueryResultItem } from '../../types/workspace';
import { Badge } from '../common/Badge';

interface SearchTesterProps {
  workspaceId: string;
}

export const SearchTester: React.FC<SearchTesterProps> = ({ workspaceId }) => {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(4);
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<QueryResultItem[]>([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    setSearched(true);
    try {
      const hits = await queryKnowledgeVault(workspaceId, query, topK);
      setResults(hits);
    } catch (err: any) {
      alert(`Search failed: ${err.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="bg-[#111827] border border-gray-800 rounded-xl p-5 space-y-4 font-mono text-xs shadow-lg">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-gray-200 text-sm tracking-wide">VECTOR SIMILARITY SEARCH TESTER</h3>
        <span className="text-[10px] text-gray-500">FASTEMBED BGE-SMALL-EN-V1.5 (384-D)</span>
      </div>

      <form onSubmit={handleSearch} className="flex space-x-2">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Pump 3B ultrasonic wall thickness measurements"
            className="w-full bg-[#0B0F17] border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-gray-100 focus:outline-none focus:border-cyan-500 text-xs"
          />
        </div>

        <div className="flex items-center space-x-1.5 bg-[#0B0F17] border border-gray-700 rounded-lg px-2 text-xs">
          <span className="text-gray-500">Top-K:</span>
          <select
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="bg-transparent text-gray-200 focus:outline-none cursor-pointer"
          >
            <option value={2}>2</option>
            <option value={4}>4</option>
            <option value={6}>6</option>
            <option value={8}>8</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={isSearching || !query.trim()}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-lg transition-colors disabled:opacity-50 flex items-center space-x-1.5"
        >
          {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          <span>Query</span>
        </button>
      </form>

      {/* Results List */}
      {results.length > 0 && (
        <div className="space-y-2.5 pt-2 border-t border-gray-800">
          <span className="text-gray-400 text-[10px] block">RETRIEVED VECTOR CHUNKS ({results.length}):</span>
          {results.map((hit, i) => (
            <div key={i} className="bg-[#0B0F17] border border-gray-800/80 rounded-lg p-3 space-y-1.5">
              <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center space-x-2">
                  <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="font-semibold text-gray-200">{hit.filename}</span>
                  {hit.page_number && (
                    <span className="text-gray-400">Page {hit.page_number}</span>
                  )}
                  {hit.section_title && (
                    <span className="text-gray-500">• {hit.section_title}</span>
                  )}
                </div>
                <Badge variant="accent" size="sm">
                  SCORE: {(hit.score * 100).toFixed(1)}%
                </Badge>
              </div>

              <p className="text-gray-300 text-[11px] leading-relaxed bg-[#111827]/50 p-2 rounded border border-gray-800/50">
                {hit.content}
              </p>
            </div>
          ))}
        </div>
      )}

      {searched && results.length === 0 && !isSearching && (
        <p className="text-gray-500 text-center py-4">No matching vector chunks found for this query.</p>
      )}
    </div>
  );
};
