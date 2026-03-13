import { useState } from 'react';
import { Search, FileText, ExternalLink, BookOpen, TrendingUp, Hammer, Calendar } from 'lucide-react';

const categories = [
  { id: 'all', label: 'All', icon: BookOpen },
  { id: 'scenario', label: 'Scenarios', icon: TrendingUp },
  { id: 'methodology', label: 'Methodology', icon: Hammer },
  { id: 'market', label: 'Market Intel', icon: Calendar },
];

const articles = [
  { 
    id: 1, 
    title: 'Base Case Scenario Parameters', 
    excerpt: 'Current trajectory assuming normal infrastructure spending growth of 4-6% annually, stable pricing power, and typical weather patterns. Uses historical volatility of 12-15% for Monte Carlo paths.', 
    date: '2024-03-01', 
    source: 'Scenario Library',
    category: 'scenario',
    tags: ['base case', 'normal growth', 'IIJA']
  },
  { 
    id: 2, 
    title: 'Hurricane Impact Modeling', 
    excerpt: 'Major hurricane scenarios model 20-30% initial revenue shock in affected Gulf Coast regions, followed by construction boom during recovery. Historical data from Harvey, Irma, and Ian inform parameters.', 
    date: '2024-03-01', 
    source: 'Scenario Library',
    category: 'scenario',
    tags: ['hurricane', 'gulf coast', 'recovery']
  },
  { 
    id: 3, 
    title: 'Monte Carlo Simulation Methodology', 
    excerpt: 'Revenue paths simulated using Geometric Brownian Motion with seasonal adjustments. Drift calibrated from historical growth rates, volatility from monthly returns. 5000+ paths ensure stable percentile estimates.', 
    date: '2024-03-01', 
    source: 'Methodology Guide',
    category: 'methodology',
    tags: ['monte carlo', 'GBM', 'simulation']
  },
  { 
    id: 4, 
    title: 'Recession Scenario Framework', 
    excerpt: 'Mild recession assumes 15% revenue decline over 6 months, 18-month recovery. Severe recession models 25% decline with 36-month recovery. Based on 2008-2009 and 2020 patterns.', 
    date: '2024-03-01', 
    source: 'Scenario Library',
    category: 'scenario',
    tags: ['recession', 'economic', 'recovery']
  },
  { 
    id: 5, 
    title: 'IIJA Spending Impact Analysis', 
    excerpt: 'Infrastructure Investment and Jobs Act provides $550B+ in new spending through 2026. Vulcan positioned to capture highway, bridge, and data center demand in key Sunbelt markets.', 
    date: '2024-03-01', 
    source: 'Market Intelligence',
    category: 'market',
    tags: ['IIJA', 'infrastructure', 'spending']
  },
  { 
    id: 6, 
    title: 'VaR and CVaR Calculations', 
    excerpt: 'Value at Risk (VaR) computed at 95% confidence from simulation percentiles. Conditional VaR (CVaR) averages outcomes in the worst 5% tail, providing expected shortfall metric.', 
    date: '2024-03-01', 
    source: 'Methodology Guide',
    category: 'methodology',
    tags: ['VaR', 'CVaR', 'risk metrics']
  },
  { 
    id: 7, 
    title: 'Data Center Construction Boom', 
    excerpt: 'AI-driven demand creating unprecedented data center construction. Vulcan aggregates used in foundations, access roads, and site preparation. 30-50% growth in this segment projected.', 
    date: '2024-03-01', 
    source: 'Market Intelligence',
    category: 'market',
    tags: ['data center', 'AI', 'growth']
  },
  { 
    id: 8, 
    title: 'Commodity Price Sensitivity', 
    excerpt: 'Diesel and natural gas prices impact transportation and asphalt production costs. Sensitivity analysis shows 10% diesel increase compresses margins by 0.8-1.2%.', 
    date: '2024-03-01', 
    source: 'Methodology Guide',
    category: 'methodology',
    tags: ['diesel', 'costs', 'sensitivity']
  },
];

export default function KnowledgeBase() {
  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const filteredArticles = articles.filter(article => {
    const matchesQuery = query === '' || 
      article.title.toLowerCase().includes(query.toLowerCase()) ||
      article.excerpt.toLowerCase().includes(query.toLowerCase()) ||
      article.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()));
    
    const matchesCategory = selectedCategory === 'all' || article.category === selectedCategory;
    
    return matchesQuery && matchesCategory;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Knowledge Base</h1>
        <p className="text-slate-400 mt-1">Search scenario documentation, methodology guides, and market intelligence</p>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search scenarios, methodology, VaR, Monte Carlo..."
              className="w-full bg-slate-700 rounded-lg pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
        </div>
        
        <div className="flex gap-2 mt-4">
          {categories.map((cat) => {
            const Icon = cat.icon;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  selectedCategory === cat.id
                    ? 'bg-amber-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <Icon className="w-4 h-4" />
                {cat.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">{filteredArticles.length} documents found</p>
        <select className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500">
          <option>Most Relevant</option>
          <option>Most Recent</option>
          <option>Alphabetical</option>
        </select>
      </div>

      <div className="space-y-4">
        {filteredArticles.map((article) => (
          <div 
            key={article.id} 
            className="bg-slate-800 rounded-xl border border-slate-700 p-5 hover:border-slate-600 transition-colors cursor-pointer group"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-4 h-4 text-amber-400" />
                  <span className="text-xs text-slate-400">{article.source}</span>
                  <span className="text-xs text-slate-500">•</span>
                  <span className="text-xs text-slate-400">{article.date}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ml-2 ${
                    article.category === 'scenario' ? 'bg-purple-500/20 text-purple-400' :
                    article.category === 'methodology' ? 'bg-blue-500/20 text-blue-400' :
                    'bg-green-500/20 text-green-400'
                  }`}>
                    {article.category}
                  </span>
                </div>
                <h3 className="font-semibold mb-2 group-hover:text-amber-400 transition-colors">{article.title}</h3>
                <p className="text-sm text-slate-400 mb-3">{article.excerpt}</p>
                <div className="flex flex-wrap gap-2">
                  {article.tags.map((tag, i) => (
                    <span key={i} className="text-xs bg-slate-700 px-2 py-1 rounded text-slate-300">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
              <ExternalLink className="w-5 h-5 text-slate-500 group-hover:text-slate-300 transition-colors ml-4" />
            </div>
          </div>
        ))}
      </div>

      <div className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/30 rounded-xl p-5">
        <div className="flex items-start gap-4">
          <BookOpen className="w-5 h-5 text-amber-400 mt-1" />
          <div>
            <h4 className="font-semibold text-amber-400">Knowledge Base Powered by Cortex Search</h4>
            <p className="text-sm text-slate-400 mt-1">
              This knowledge base uses Snowflake Cortex Search for semantic retrieval of scenario documentation,
              simulation methodology, and market intelligence. Content is maintained alongside the simulation models.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
