import { useState } from 'react';
import { 
  Database, 
  ChevronDown, 
  ChevronRight,
  Layers,
  ArrowRight,
  Table2,
  FileCode,
  Eye,
  Cpu,
  Globe,
  CloudLightning,
  Building2,
  Fuel,
  Newspaper,
  FileText,
  Wrench,
  ClipboardList,
  Search
} from 'lucide-react';

interface DataSource {
  id: string;
  name: string;
  provider: string;
  category: 'marketplace' | 'paid' | 'external' | 'sec' | 'synthetic' | 'curated';
  icon: React.ElementType;
  color: string;
  description: string;
  sourceLocation: string;
  tables: TableInfo[];
}

interface TableInfo {
  name: string;
  schema: string;
  description: string;
  columns: ColumnInfo[];
  usedBy: UsageInfo[];
}

interface ColumnInfo {
  name: string;
  source: string;
  transformation?: string;
  businessMeaning: string;
}

interface UsageInfo {
  type: 'view' | 'procedure' | 'api' | 'frontend';
  name: string;
  purpose: string;
}

const dataSources: DataSource[] = [
  {
    id: 'noaa',
    name: 'NOAA Weather Data',
    provider: 'Snowflake Marketplace (Free)',
    category: 'marketplace',
    icon: CloudLightning,
    color: 'blue',
    description: 'Daily weather metrics from NOAA stations mapped to SnowCore sales regions. Drives construction day calculations and seasonal adjustments.',
    sourceLocation: 'SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.NOAA_WEATHER_METRICS_TIMESERIES',
    tables: [{
      name: 'DAILY_WEATHER',
      schema: 'ATOMIC',
      description: 'Aggregated daily weather by SnowCore sales region with construction feasibility flags',
      columns: [
        { name: 'TEMP_HIGH_F', source: 'NOAA_WEATHER_METRICS.TMAX', transformation: 'VALUE * 9/50 + 32 (°C→°F)', businessMeaning: 'Daily high temperature - affects concrete curing and asphalt laying' },
        { name: 'TEMP_LOW_F', source: 'NOAA_WEATHER_METRICS.TMIN', transformation: 'VALUE * 9/50 + 32 (°C→°F)', businessMeaning: 'Daily low temperature - freeze risk indicator' },
        { name: 'PRECIPITATION_IN', source: 'NOAA_WEATHER_METRICS.PRCP', transformation: 'VALUE / 254 (mm→in)', businessMeaning: 'Daily precipitation - construction delay trigger' },
        { name: 'SNOW_IN', source: 'NOAA_WEATHER_METRICS.SNOW', transformation: 'VALUE / 25.4 (mm→in)', businessMeaning: 'Snowfall - major construction blocker' },
        { name: 'IS_CONSTRUCTION_DAY', source: 'Derived', transformation: 'precip < 0.5" AND snow < 2" AND temp > 28°F', businessMeaning: 'Boolean flag: can construction occur today?' },
        { name: 'WEATHER_DELAY_REASON', source: 'Derived', transformation: 'Rule-based classification', businessMeaning: 'HEAVY_RAIN / SNOW / FREEZE - reason for delay' },
        { name: 'CDD / HDD', source: 'Derived', transformation: 'Cooling/Heating degree days from avg temp', businessMeaning: 'Energy demand correlation indicator' },
      ],
      usedBy: [
        { type: 'frontend', name: 'Weather Risk Page', purpose: 'Display regional weather conditions and construction days lost' },
        { type: 'frontend', name: 'Mission Control', purpose: 'Weather alerts and MTD construction days' },
        { type: 'procedure', name: 'RUN_SIMULATION', purpose: 'Seasonality factors derived from historical patterns' },
      ]
    }]
  },
  {
    id: 'census',
    name: 'Census Construction Spending',
    provider: 'Snowflake Marketplace (Free)',
    category: 'marketplace',
    icon: Building2,
    color: 'green',
    description: 'US construction spending data by category (highway, residential, commercial). Primary macro indicator for demand forecasting.',
    sourceLocation: 'SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_REAL_ESTATE_TIMESERIES',
    tables: [{
      name: 'MONTHLY_MACRO_INDICATORS',
      schema: 'ATOMIC',
      description: 'Monthly US construction spending with year-over-year growth calculations',
      columns: [
        { name: 'HIGHWAY_CONSTRUCTION_USD', source: 'US_REAL_ESTATE.ALL_NONRES_HIGHWAY_A', transformation: 'Direct (annual rate)', businessMeaning: 'Highway spending - primary demand driver for aggregates (35% of revenue)' },
        { name: 'RESIDENTIAL_CONSTRUCTION_USD', source: 'US_REAL_ESTATE.ALL_RES_SA', transformation: 'Direct (seasonally adjusted)', businessMeaning: 'Residential spending - secondary demand driver (~22% of revenue)' },
        { name: 'NONRES_COMMERCIAL_USD', source: 'US_REAL_ESTATE.ALL_NONRES_COMMERCIAL_SA', transformation: 'Direct (seasonally adjusted)', businessMeaning: 'Commercial construction - data center boom driver' },
        { name: 'HIGHWAY_YOY_GROWTH', source: 'Derived', transformation: '(current - lag12) / lag12', businessMeaning: 'Scenario trigger: >15% = Infrastructure Boom, <-10% = Slowdown' },
        { name: 'RESIDENTIAL_YOY_GROWTH', source: 'Derived', transformation: '(current - lag12) / lag12', businessMeaning: 'Scenario trigger: >12% = Housing Recovery, <-15% = Slowdown' },
        { name: 'CONSTRUCTION_MOMENTUM_3M', source: 'Derived', transformation: '3-month rolling average of total spending', businessMeaning: 'Trend indicator for ML feature engineering' },
      ],
      usedBy: [
        { type: 'view', name: 'ANALYTICS.SCENARIO_TRIGGERS', purpose: 'Compare YoY growth to scenario thresholds' },
        { type: 'view', name: 'ANALYTICS.REVENUE_DRIVERS_INTEGRATED', purpose: 'Join with shipments for driver analysis' },
        { type: 'view', name: 'ANALYTICS.ENERGY_MACRO_CORRELATION', purpose: 'Correlate with energy prices' },
        { type: 'frontend', name: 'Scenario Analysis', purpose: 'Determine which scenarios are currently triggered' },
      ]
    }]
  },
  {
    id: 'yes_energy',
    name: 'Yes Energy Fuel Prices',
    provider: 'Yes Energy (Paid Marketplace)',
    category: 'paid',
    icon: Fuel,
    color: 'orange',
    description: 'Daily natural gas and fuel price data. Critical for margin analysis and energy cost scenarios.',
    sourceLocation: 'YES_ENERGY_FOUNDATION_DATA.FOUNDATION.TS_FUEL_PRICES_V',
    tables: [{
      name: 'DAILY_COMMODITY_PRICES',
      schema: 'ATOMIC',
      description: 'Daily commodity prices with natural gas from Yes Energy, other commodities synthetic',
      columns: [
        { name: 'NATURAL_GAS_HENRY_HUB', source: 'TS_FUEL_PRICES_V.VALUE', transformation: 'Direct ($/MMBtu)', businessMeaning: 'Primary energy cost driver - affects production and delivery costs' },
        { name: 'DIESEL_GULF_COAST', source: 'Synthetic (correlated)', transformation: 'Base ~$3.50/gal + seasonal', businessMeaning: 'Delivery cost driver - directly impacts logistics' },
        { name: 'LIQUID_ASPHALT_GULF', source: 'Synthetic', transformation: 'Base ~$620/ton + correlation', businessMeaning: 'Input cost for asphalt segment' },
      ],
      usedBy: [
        { type: 'procedure', name: 'ML.RUN_SIMULATION', purpose: 'Loads current gas price as simulation parameter' },
        { type: 'procedure', name: 'ML.COMPARE_SCENARIOS', purpose: 'Context for scenario comparison' },
        { type: 'view', name: 'ANALYTICS.SCENARIO_TRIGGERS', purpose: '30-day avg gas price determines active scenarios' },
        { type: 'view', name: 'ANALYTICS.ENERGY_MACRO_CORRELATION', purpose: 'Links energy prices with construction spending' },
        { type: 'api', name: '/api/kpis', purpose: 'Current energy prices for dashboard' },
      ]
    }]
  },
  {
    id: 'rto_insider',
    name: 'RTO Insider News',
    provider: 'RTO Insider (Existing Account)',
    category: 'external',
    icon: Newspaper,
    color: 'purple',
    description: 'Energy and infrastructure news articles. Powers the Cortex Search knowledge base for AI-driven insights.',
    sourceLocation: 'RTO_INSIDER_DOCS.DRAFT_WORK.SAMPLE_RTO',
    tables: [{
      name: 'CONSTRUCTION_NEWS_ARTICLES',
      schema: 'DOCS',
      description: 'Curated news articles for Cortex Search with category classification',
      columns: [
        { name: 'TITLE', source: 'SAMPLE_RTO.POSTTITLE', transformation: 'Direct', businessMeaning: 'Article headline for search results' },
        { name: 'CONTENT', source: 'SAMPLE_RTO.POSTCONTENT', transformation: 'Direct', businessMeaning: 'Full article text indexed by Cortex Search' },
        { name: 'CATEGORY', source: 'Derived', transformation: 'Rule-based: ILIKE patterns', businessMeaning: 'INFRASTRUCTURE / CONSTRUCTION / REGULATORY / GRID / MARKET_NEWS' },
        { name: 'TAGS', source: 'Derived', transformation: 'Region extraction from title', businessMeaning: 'TEXAS / CALIFORNIA / SOUTHEAST based on keywords' },
      ],
      usedBy: [
        { type: 'procedure', name: 'CORTEX_SEARCH_SERVICE', purpose: 'CONSTRUCTION_NEWS_SEARCH enables NL queries' },
        { type: 'frontend', name: 'Knowledge Base Page', purpose: 'Search for infrastructure, IIJA, energy news' },
        { type: 'api', name: '/api/agent/chat', purpose: 'Agent can search news for market context' },
      ]
    }]
  },
  {
    id: 'sec_filings',
    name: 'SnowCore SEC Filings',
    provider: 'SEC 10-K/10-Q (Manual)',
    category: 'sec',
    icon: FileText,
    color: 'slate',
    description: 'Quarterly financial data from SnowCore Materials SEC filings. Ground truth for model calibration and backtesting.',
    sourceLocation: 'Manual entry from investor.vulcanmaterials.com',
    tables: [{
      name: 'QUARTERLY_FINANCIALS',
      schema: 'ATOMIC',
      description: 'Actual quarterly results from SEC filings for validation',
      columns: [
        { name: 'TOTAL_REVENUE_USD', source: '10-K/10-Q Revenue line', transformation: 'Direct', businessMeaning: 'Baseline for simulation calibration' },
        { name: 'TOTAL_SHIPMENTS_TONS', source: '10-K Operational highlights', transformation: 'Direct', businessMeaning: 'Volume calibration (226.8M tons/year)' },
        { name: 'AGG_PRICE_PER_TON', source: '10-K Aggregates segment', transformation: 'Direct', businessMeaning: 'Price realization ($21.98/ton)' },
        { name: 'AGG_CASH_GROSS_PROFIT_TON', source: '10-K Unit economics', transformation: 'Direct', businessMeaning: 'Margin calibration ($11.33/ton)' },
        { name: 'EBITDA_MARGIN_PCT', source: '10-K/10-Q Calculated', transformation: 'EBITDA / Revenue', businessMeaning: 'Profitability benchmark (51.5%)' },
      ],
      usedBy: [
        { type: 'view', name: 'ANALYTICS.V_MODEL_PERFORMANCE', purpose: 'Compare forecasts to actuals' },
        { type: 'frontend', name: 'Revenue Deep Dive', purpose: 'Historical trend validation' },
      ]
    }]
  },
  {
    id: 'synthetic_shipments',
    name: 'Synthetic Shipment Data',
    provider: 'Generated (Internal)',
    category: 'synthetic',
    icon: Wrench,
    color: 'cyan',
    description: 'Monte Carlo generated shipment data calibrated to SEC-reported totals. Provides granular monthly/regional detail not available in public filings.',
    sourceLocation: 'Generated via Python script from 10-K parameters',
    tables: [{
      name: 'MONTHLY_SHIPMENTS',
      schema: 'ATOMIC',
      description: 'Synthetic monthly shipments by region, product, and customer segment',
      columns: [
        { name: 'SHIPMENT_TONS', source: 'Monte Carlo generation', transformation: 'Seasonal pattern × regional allocation', businessMeaning: 'Monthly volume for simulation base' },
        { name: 'REVENUE_USD', source: 'Derived', transformation: 'SHIPMENT_TONS × PRICE_PER_TON', businessMeaning: 'Historical series for drift/volatility calibration' },
        { name: 'PRICE_PER_TON', source: 'Monte Carlo generation', transformation: 'Base $21.98 ± noise, 4% annual trend', businessMeaning: 'Price realization by region' },
        { name: 'REGION_CODE', source: '10-K geographic split', transformation: 'TX 22%, SE 30%, FL 15%, CA 18%, VA 10%, IL 5%', businessMeaning: 'Regional allocation matching 10-K' },
        { name: 'CUSTOMER_SEGMENT_CODE', source: '10-K end markets', transformation: 'Highway 35%, Residential 22%, etc.', businessMeaning: 'Demand composition by segment' },
      ],
      usedBy: [
        { type: 'procedure', name: 'ML.RUN_SIMULATION', purpose: 'Calculates μ (drift) and σ (volatility) from pct_change()' },
        { type: 'procedure', name: 'ML.RUN_SENSITIVITY_ANALYSIS', purpose: 'Base revenue trajectory for parameter sweeps' },
        { type: 'view', name: 'ANALYTICS.REVENUE_DRIVERS_INTEGRATED', purpose: 'Join with macro data for driver analysis' },
        { type: 'view', name: 'ANALYTICS.REGIONAL_PERFORMANCE', purpose: 'Regional KPIs and capacity utilization' },
        { type: 'api', name: '/api/kpis', purpose: 'Dashboard revenue and shipment metrics' },
        { type: 'frontend', name: 'Mission Control', purpose: 'Revenue charts, regional performance' },
        { type: 'frontend', name: 'Shipments Page', purpose: 'Shipment history and trends' },
      ]
    }]
  },
  {
    id: 'scenario_definitions',
    name: 'Scenario Definitions',
    provider: 'Curated (Manual)',
    category: 'curated',
    icon: ClipboardList,
    color: 'amber',
    description: '13 predefined scenarios with revenue multipliers, triggers, and phase definitions. Drives the Monte Carlo simulation engine.',
    sourceLocation: 'SNOWCORE_MATERIALS_DB.ML.SCENARIO_DEFINITIONS',
    tables: [{
      name: 'SCENARIO_DEFINITIONS',
      schema: 'ML',
      description: 'Scenario parameters including multipliers, thresholds, and phase definitions',
      columns: [
        { name: 'SCENARIO_ID', source: 'Manual definition', transformation: 'Direct', businessMeaning: 'Unique identifier (e.g., IIJA_INFRASTRUCTURE_BOOM)' },
        { name: 'REVENUE_MULTIPLIER', source: 'Industry analysis', transformation: 'Direct', businessMeaning: 'Impact on revenue (1.25 = +25% growth)' },
        { name: 'GAS_PRICE_THRESHOLD', source: 'Historical analysis', transformation: 'Direct', businessMeaning: '<$3 triggers bull, >$6 triggers bear' },
        { name: 'HIGHWAY_GROWTH_THRESHOLD', source: 'Census correlation', transformation: 'Direct', businessMeaning: '>15% triggers Infrastructure Boom' },
        { name: 'HAS_PHASES', source: 'Scenario design', transformation: 'Boolean', businessMeaning: 'Whether scenario has disruption/recovery phases' },
        { name: 'PHASE1_MULTIPLIER', source: 'Historical events', transformation: 'Direct', businessMeaning: 'Impact during disruption phase (e.g., 0.7 for hurricane)' },
        { name: 'PHASE2_MULTIPLIER', source: 'Recovery analysis', transformation: 'Direct', businessMeaning: 'Impact during recovery phase (e.g., 1.3 for rebuild)' },
      ],
      usedBy: [
        { type: 'procedure', name: 'ML.RUN_SIMULATION', purpose: 'Load scenario params, apply multipliers' },
        { type: 'procedure', name: 'ML.COMPARE_SCENARIOS', purpose: 'Compare multiple scenarios side-by-side' },
        { type: 'view', name: 'ANALYTICS.SCENARIO_TRIGGERS', purpose: 'Match current conditions to triggers' },
        { type: 'view', name: 'ANALYTICS.SCENARIO_SIMULATION_SUMMARY', purpose: 'Join with latest simulation results' },
        { type: 'api', name: '/api/scenarios', purpose: 'List available scenarios for frontend' },
        { type: 'frontend', name: 'Scenario Analysis', purpose: 'Scenario selection and interpretation' },
      ]
    }]
  },
];

const categoryInfo: Record<string, { label: string; bgColor: string; textColor: string }> = {
  marketplace: { label: 'Snowflake Marketplace', bgColor: 'bg-blue-500/20', textColor: 'text-blue-400' },
  paid: { label: 'Paid Data', bgColor: 'bg-orange-500/20', textColor: 'text-orange-400' },
  external: { label: 'External Source', bgColor: 'bg-purple-500/20', textColor: 'text-purple-400' },
  sec: { label: 'SEC Filings', bgColor: 'bg-slate-500/20', textColor: 'text-slate-400' },
  synthetic: { label: 'Generated', bgColor: 'bg-cyan-500/20', textColor: 'text-cyan-400' },
  curated: { label: 'Curated', bgColor: 'bg-amber-500/20', textColor: 'text-amber-400' },
};

const usageTypeInfo: Record<string, { icon: React.ElementType; color: string }> = {
  view: { icon: Eye, color: 'text-green-400' },
  procedure: { icon: Cpu, color: 'text-purple-400' },
  api: { icon: Globe, color: 'text-blue-400' },
  frontend: { icon: Layers, color: 'text-amber-400' },
};

export default function DataExplorer() {
  const [expandedSource, setExpandedSource] = useState<string | null>('noaa');
  const [expandedTable, setExpandedTable] = useState<string | null>('DAILY_WEATHER');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const filteredSources = dataSources.filter(source => {
    const matchesSearch = searchTerm === '' || 
      source.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      source.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      source.tables.some(t => t.name.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === null || source.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Database className="w-7 h-7 text-amber-400" />
            Data Explorer
          </h1>
          <p className="text-slate-400 mt-1">Complete data lineage from source to application</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search sources, tables..."
              className="pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 w-64"
            />
          </div>
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
            selectedCategory === null ? 'bg-amber-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          All Sources
        </button>
        {Object.entries(categoryInfo).map(([key, info]) => (
          <button
            key={key}
            onClick={() => setSelectedCategory(selectedCategory === key ? null : key)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              selectedCategory === key ? `${info.bgColor} ${info.textColor} ring-1 ring-current` : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {info.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-8 space-y-4">
          <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Layers className="w-5 h-5 text-amber-400" />
              Data Flow Architecture
            </h3>
            <div className="flex items-center justify-between gap-4 text-xs">
              <div className="flex-1 bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-center">
                <p className="font-semibold text-blue-400">External Sources</p>
                <p className="text-slate-500 mt-1">Marketplace, Yes Energy, RTO Insider, SEC</p>
              </div>
              <ArrowRight className="w-5 h-5 text-slate-500" />
              <div className="flex-1 bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-3 text-center">
                <p className="font-semibold text-cyan-400">ATOMIC Schema</p>
                <p className="text-slate-500 mt-1">Raw/ingested tables</p>
              </div>
              <ArrowRight className="w-5 h-5 text-slate-500" />
              <div className="flex-1 bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 text-center">
                <p className="font-semibold text-purple-400">ML Schema</p>
                <p className="text-slate-500 mt-1">Simulations, procedures</p>
              </div>
              <ArrowRight className="w-5 h-5 text-slate-500" />
              <div className="flex-1 bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-center">
                <p className="font-semibold text-green-400">ANALYTICS Schema</p>
                <p className="text-slate-500 mt-1">Integrated views</p>
              </div>
              <ArrowRight className="w-5 h-5 text-slate-500" />
              <div className="flex-1 bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-center">
                <p className="font-semibold text-amber-400">Frontend</p>
                <p className="text-slate-500 mt-1">API → React app</p>
              </div>
            </div>
          </div>

          {filteredSources.map((source) => {
            const isExpanded = expandedSource === source.id;
            const Icon = source.icon;
            const catInfo = categoryInfo[source.category];
            
            return (
              <div key={source.id} className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                <button
                  onClick={() => setExpandedSource(isExpanded ? null : source.id)}
                  className="w-full p-4 flex items-center justify-between hover:bg-slate-700/50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-2.5 rounded-lg bg-${source.color}-500/20`}>
                      <Icon className={`w-5 h-5 text-${source.color}-400`} />
                    </div>
                    <div className="text-left">
                      <div className="flex items-center gap-3">
                        <h3 className="font-semibold">{source.name}</h3>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${catInfo.bgColor} ${catInfo.textColor}`}>
                          {catInfo.label}
                        </span>
                      </div>
                      <p className="text-sm text-slate-400 mt-0.5">{source.provider}</p>
                    </div>
                  </div>
                  {isExpanded ? <ChevronDown className="w-5 h-5 text-slate-400" /> : <ChevronRight className="w-5 h-5 text-slate-400" />}
                </button>

                {isExpanded && (
                  <div className="border-t border-slate-700 p-4 space-y-4">
                    <div className="bg-slate-700/30 rounded-lg p-3">
                      <p className="text-sm text-slate-300">{source.description}</p>
                      <p className="text-xs text-slate-500 mt-2 font-mono">📍 {source.sourceLocation}</p>
                    </div>

                    {source.tables.map((table) => {
                      const isTableExpanded = expandedTable === table.name;
                      
                      return (
                        <div key={table.name} className="border border-slate-600 rounded-lg overflow-hidden">
                          <button
                            onClick={() => setExpandedTable(isTableExpanded ? null : table.name)}
                            className="w-full p-3 flex items-center justify-between bg-slate-700/50 hover:bg-slate-700 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <Table2 className="w-4 h-4 text-green-400" />
                              <span className="font-mono text-sm">{table.schema}.{table.name}</span>
                            </div>
                            {isTableExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                          </button>

                          {isTableExpanded && (
                            <div className="p-4 space-y-4">
                              <p className="text-sm text-slate-400">{table.description}</p>

                              <div>
                                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Column Mappings</h4>
                                <div className="space-y-2">
                                  {table.columns.map((col, idx) => (
                                    <div key={idx} className="bg-slate-700/30 rounded-lg p-3">
                                      <div className="flex items-start justify-between gap-4">
                                        <div className="flex-1">
                                          <p className="font-mono text-sm text-amber-400">{col.name}</p>
                                          <p className="text-xs text-slate-500 mt-1">
                                            <span className="text-slate-400">Source:</span> {col.source}
                                          </p>
                                          {col.transformation && (
                                            <p className="text-xs text-slate-500">
                                              <span className="text-slate-400">Transform:</span> <code className="text-cyan-400">{col.transformation}</code>
                                            </p>
                                          )}
                                        </div>
                                        <div className="flex-1">
                                          <p className="text-xs text-slate-400">{col.businessMeaning}</p>
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>

                              <div>
                                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Used By</h4>
                                <div className="grid grid-cols-2 gap-2">
                                  {table.usedBy.map((usage, idx) => {
                                    const typeInfo = usageTypeInfo[usage.type];
                                    const UsageIcon = typeInfo.icon;
                                    return (
                                      <div key={idx} className="bg-slate-700/30 rounded-lg p-2 flex items-start gap-2">
                                        <UsageIcon className={`w-4 h-4 ${typeInfo.color} mt-0.5`} />
                                        <div>
                                          <p className="text-xs font-medium">{usage.name}</p>
                                          <p className="text-xs text-slate-500">{usage.purpose}</p>
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="col-span-4 space-y-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-5 sticky top-6">
            <h3 className="font-semibold mb-4">Data Source Summary</h3>
            <div className="space-y-3">
              {Object.entries(categoryInfo).map(([key, info]) => {
                const count = dataSources.filter(s => s.category === key).length;
                return (
                  <div key={key} className="flex items-center justify-between">
                    <span className={`text-sm ${info.textColor}`}>{info.label}</span>
                    <span className={`text-sm px-2 py-0.5 rounded ${info.bgColor} ${info.textColor}`}>{count}</span>
                  </div>
                );
              })}
            </div>
            <div className="border-t border-slate-700 mt-4 pt-4">
              <p className="text-2xl font-bold text-amber-400">{dataSources.length}</p>
              <p className="text-sm text-slate-400">Total Data Sources</p>
            </div>
          </div>

          <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 border border-amber-500/30 rounded-xl p-5">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <FileCode className="w-5 h-5 text-amber-400" />
              Key Procedures
            </h3>
            <div className="space-y-2 text-sm">
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="font-mono text-purple-400">ML.RUN_SIMULATION</p>
                <p className="text-xs text-slate-400 mt-1">Monte Carlo engine consuming MONTHLY_SHIPMENTS + DAILY_COMMODITY_PRICES + SCENARIO_DEFINITIONS</p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="font-mono text-purple-400">ML.RUN_SENSITIVITY_ANALYSIS</p>
                <p className="text-xs text-slate-400 mt-1">Parameter sweep varying drift, volatility, growth rates</p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="font-mono text-purple-400">ML.COMPARE_SCENARIOS</p>
                <p className="text-xs text-slate-400 mt-1">Side-by-side scenario comparison</p>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500/10 to-cyan-500/10 border border-green-500/30 rounded-xl p-5">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Eye className="w-5 h-5 text-green-400" />
              Key Views
            </h3>
            <div className="space-y-2 text-sm">
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="font-mono text-green-400">ANALYTICS.REVENUE_DRIVERS_INTEGRATED</p>
                <p className="text-xs text-slate-400 mt-1">Joins Shipments + Census Macro + Yes Energy</p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="font-mono text-green-400">ANALYTICS.SCENARIO_TRIGGERS</p>
                <p className="text-xs text-slate-400 mt-1">Compares current conditions to scenario thresholds</p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3">
                <p className="font-mono text-green-400">ANALYTICS.ENERGY_MACRO_CORRELATION</p>
                <p className="text-xs text-slate-400 mt-1">Links gas prices to construction spending</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl border border-slate-700 p-5">
            <h3 className="font-semibold mb-3">Simulation Calibration</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">μ (drift)</span>
                <span className="font-mono">MONTHLY_SHIPMENTS.pct_change().mean()</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">σ (volatility)</span>
                <span className="font-mono">MONTHLY_SHIPMENTS.pct_change().std()</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Current revenue</span>
                <span className="font-mono">MONTHLY_SHIPMENTS[-1]</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Gas price</span>
                <span className="font-mono">DAILY_COMMODITY_PRICES[-1]</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Seasonality</span>
                <span className="font-mono">monthly_avg / overall_avg</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
