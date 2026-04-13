import { useState } from 'react';
import { Search, FileText, ExternalLink, BookOpen, TrendingUp, Hammer } from 'lucide-react';
import { searchKnowledge, searchScenarios } from '../services/api';

const categories = [
  { id: 'all', label: 'All', icon: BookOpen },
  { id: 'competitor', label: 'Competitor Intel', icon: TrendingUp },
  { id: 'scenario', label: 'Scenarios', icon: Hammer },
];

interface SearchResult {
  COMPANY_NAME?: string;
  TRANSCRIPT_TEXT?: string;
  FILING_DATE?: string;
  FILING_TYPE?: string;
  CONTENT?: string;
  SCENARIO_ID?: string;
  SOURCE_TYPE?: string;
}

export default function KnowledgeBase() {
  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const doSearch = async () => {
    if (!query.trim()) return;
    setIsSearching(true);
    setHasSearched(true);
    try {
      if (selectedCategory === 'scenario') {
        const data = await searchScenarios(query);
        setResults(data?.results || []);
      } else if (selectedCategory === 'competitor') {
        const data = await searchKnowledge(query);
        setResults(data?.results || []);
      } else {
        const [intel, scenarios] = await Promise.all([
          searchKnowledge(query).catch(() => ({ results: [] })),
          searchScenarios(query).catch(() => ({ results: [] })),
        ]);
        setResults([...(intel?.results || []), ...(scenarios?.results || [])]);
      }
    } catch {
      setResults([]);
    }
    setIsSearching(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Knowledge Base</h1>
        <p className="text-slate-400 mt-1">Search competitor earnings, scenario documentation & market intelligence via Cortex Search</p>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && doSearch()}
              placeholder="Search earnings transcripts, scenarios, market intel..."
              className="w-full bg-slate-700 rounded-lg pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
          <button onClick={doSearch} disabled={isSearching} className="px-5 py-3 bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50 text-sm font-medium">
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>
        <div className="flex gap-2 mt-4">
          {categories.map((cat) => {
            const Icon = cat.icon;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${selectedCategory === cat.id ? 'bg-amber-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}
              >
                <Icon className="w-4 h-4" />
                {cat.label}
              </button>
            );
          })}
        </div>
      </div>

      {hasSearched && (
        <p className="text-sm text-slate-400">{results.length} results found</p>
      )}

      <div className="space-y-4">
        {results.map((result, i) => (
          <div key={i} className="bg-slate-800 rounded-xl border border-slate-700 p-5 hover:border-slate-600 transition-colors cursor-pointer group">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-4 h-4 text-amber-400" />
                  <span className="text-xs text-slate-400">{result.COMPANY_NAME || result.SCENARIO_ID || 'Document'}</span>
                  {result.FILING_DATE && <><span className="text-xs text-slate-500">•</span><span className="text-xs text-slate-400">{result.FILING_DATE}</span></>}
                  {result.FILING_TYPE && <span className="text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-400 ml-2">{result.FILING_TYPE}</span>}
                  {result.SOURCE_TYPE && <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 ml-2">{result.SOURCE_TYPE}</span>}
                </div>
                <p className="text-sm text-slate-300 line-clamp-3">{result.TRANSCRIPT_TEXT || result.CONTENT || ''}</p>
              </div>
              <ExternalLink className="w-5 h-5 text-slate-500 group-hover:text-slate-300 transition-colors ml-4 flex-shrink-0" />
            </div>
          </div>
        ))}
      </div>

      {!hasSearched && (
        <div className="text-center py-12">
          <Search className="w-12 h-12 mx-auto mb-4 text-slate-600" />
          <p className="text-slate-400">Enter a search query to find competitor earnings, scenario documentation, and market intelligence</p>
          <p className="text-xs text-slate-500 mt-2">Powered by Snowflake Cortex Search — semantic retrieval from 40+ documents</p>
        </div>
      )}

      <div className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/30 rounded-xl p-5">
        <div className="flex items-start gap-4">
          <BookOpen className="w-5 h-5 text-amber-400 mt-1" />
          <div>
            <h4 className="font-semibold text-amber-400">Knowledge Base Powered by Cortex Search</h4>
            <p className="text-sm text-slate-400 mt-1">
              This knowledge base uses Snowflake Cortex Search for semantic retrieval of competitor earnings transcripts
              and scenario documentation. 2 search services: COMPETITOR_INTEL_SEARCH (22 docs) + SCENARIO_SEARCH_SERVICE (18 docs).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
