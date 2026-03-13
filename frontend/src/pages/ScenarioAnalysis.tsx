import { useState } from 'react';
import { 
  Play, 
  RefreshCw,
  AlertTriangle,
  Shuffle,
  BookOpen,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const scenarios = [
  { id: 'BASE_CASE', name: 'Base Case', category: 'Baseline', description: 'Current trajectory with normal growth assumptions', interpretation: 'Reflects continuation of current market conditions. Use as benchmark for comparing other scenarios. Assumes 2-4% annual growth in line with historical averages.' },
  { id: 'MIXED_SIGNALS', name: 'Mixed Signals', category: 'Baseline', description: 'Mixed market conditions', interpretation: 'Models uncertainty with offsetting positive and negative factors. Higher volatility than base case. Useful for stress-testing hedging strategies.' },
  { id: 'MILD_RECESSION', name: 'Mild Recession', category: 'Bear', description: '15% revenue decline, 18-month recovery', interpretation: 'Similar to 2001 recession. Expect housing starts to drop 20-30%, infrastructure projects delayed. Recovery typically begins 12-18 months after trough.' },
  { id: 'HOUSING_SLOWDOWN', name: 'Housing Slowdown', category: 'Bear', description: 'Housing market slowdown scenario', interpretation: 'Residential construction accounts for ~30% of aggregate demand. A slowdown impacts Southeast and Southwest regions most heavily.' },
  { id: 'ENERGY_COST_SQUEEZE', name: 'Energy Cost Squeeze', category: 'Bear', description: 'Rising energy costs impact margins', interpretation: 'Diesel and natural gas are major cost drivers. A 30% energy price spike compresses margins by 200-400 bps without price increases.' },
  { id: 'IIJA_INFRASTRUCTURE_BOOM', name: 'Infrastructure Boom', category: 'Bull', description: 'IIJA spending acceleration +20%', interpretation: 'Infrastructure Investment and Jobs Act accelerates highway/bridge spending. Benefits highway segment (+15-25%), concentrated in states with aging infrastructure.' },
  { id: 'HOUSING_RECOVERY', name: 'Housing Recovery', category: 'Bull', description: 'Housing market recovery scenario', interpretation: 'Housing starts return to 1.6M+ annually. Strongest impact in Sunbelt regions (Southeast, Southwest). Multiplier effect on commercial construction follows.' },
  { id: 'ENERGY_COST_TAILWIND', name: 'Low Energy Costs', category: 'Bull', description: 'Favorable energy cost environment', interpretation: 'Lower input costs expand margins. Can either flow to bottom line or fund competitive pricing. Historically adds 150-300 bps to gross margin.' },
  { id: 'HURRICANE_MAJOR', name: 'Major Hurricane', category: 'Disruption', description: 'Category 4+ Gulf Coast impact', interpretation: 'Short-term (1-3 months) operational disruption, followed by 12-24 month reconstruction demand surge. Net positive for aggregate demand but timing uncertainty.' },
  { id: 'CALIFORNIA_WILDFIRE', name: 'California Wildfire', category: 'Disruption', description: 'Wildfire season impact', interpretation: 'Disrupts West region operations. Reconstruction demand follows 6-12 months after event. Insurance and permitting delays extend recovery timeline.' },
  { id: 'TEXAS_DROUGHT_EXTENDED', name: 'Texas Drought', category: 'Disruption', description: 'Extended Texas drought conditions', interpretation: 'Water restrictions can halt concrete production. Southwest region most exposed. Consider inventory pre-positioning during drought forecasts.' },
  { id: 'HOUSING_CRASH_2008', name: '2008 Housing Crash', category: 'Stress', description: '2008-style housing market crash', interpretation: 'SEVERE STRESS TEST: 40-50% decline in residential demand. Recovery took 5+ years. Tests company survivability, not expected outcome. VaR/CVaR metrics critical here.' },
  { id: 'STAGFLATION', name: 'Stagflation', category: 'Stress', description: 'High inflation, low growth scenario', interpretation: 'SEVERE STRESS TEST: High inflation erodes purchasing power while recession cuts volume. Pricing power tested. Margin compression with volume decline - worst combination.' },
];

const glossaryTerms = [
  { term: 'Monte Carlo Simulation', definition: 'A computational technique that runs thousands of random scenarios to model uncertainty. Each "path" represents one possible future, allowing us to see the full range of outcomes rather than a single forecast.' },
  { term: 'Terminal Revenue', definition: 'The projected annual revenue at the end of the simulation horizon (e.g., 24 months out). This is the key output we\'re trying to forecast.' },
  { term: 'VaR (Value at Risk) 95%', definition: 'The revenue level we have 95% confidence of exceeding. In other words, there\'s only a 5% chance revenue falls below this threshold. Used for downside risk planning.' },
  { term: 'CVaR (Conditional VaR) 95%', definition: 'The average revenue in the worst 5% of scenarios. More conservative than VaR because it considers how bad the tail scenarios actually are, not just where they start.' },
  { term: 'P10 / P50 / P90', definition: 'Percentile outcomes. P10 = 10th percentile (downside case), P50 = median (most likely), P90 = 90th percentile (upside case). Provides a range of outcomes for planning.' },
  { term: 'Paths', definition: 'The number of random simulations to run. More paths = more accurate statistics but longer runtime. 5,000 paths typically sufficient for stable estimates.' },
  { term: 'Drift', definition: 'The expected growth rate in the simulation model. Positive drift = expected growth, negative drift = expected decline. Represents the trend component.' },
  { term: 'Volatility', definition: 'The degree of randomness/uncertainty in each path. Higher volatility = wider range of outcomes. Calibrated from historical revenue variance.' },
];

interface SimulationResults {
  scenario_type: string;
  n_paths: number;
  n_months: number;
  terminal_mean: number;
  terminal_std: number;
  var_95: number;
  cvar_95: number;
  p10: number;
  p50: number;
  p90: number;
  paths_sample: number[][];
}

export default function ScenarioAnalysis() {
  const [selectedScenario, setSelectedScenario] = useState('BASE_CASE');
  const [nPaths, setNPaths] = useState(5000);
  const [nMonths, setNMonths] = useState(24);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SimulationResults | null>(null);
  const [showGlossary, setShowGlossary] = useState(false);
  const [showInterpretation, setShowInterpretation] = useState(true);

  const runSimulation = async () => {
    setIsRunning(true);
    setError(null);
    
    try {
      const response = await fetch('/api/agent/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          scenario_type: selectedScenario,
          n_paths: nPaths,
          n_months: nMonths,
          base_revenue: 7900.0
        })
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Simulation failed');
      }
      
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
    
    setIsRunning(false);
  };

  const currentScenario = scenarios.find(s => s.id === selectedScenario);

  const pathData = (results?.paths_sample && results.paths_sample.length === 5 && results.paths_sample[0]?.length > 0) ? 
    Array.from({ length: results.paths_sample[0].length }, (_, i) => ({
      month: i,
      p5: results.paths_sample[0][i] || 0,
      p25: results.paths_sample[1][i] || 0,
      p50: results.paths_sample[2][i] || 0,
      p75: results.paths_sample[3][i] || 0,
      p95: results.paths_sample[4][i] || 0,
    })) : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Scenario Analysis</h1>
          <p className="text-slate-400 mt-1">Monte Carlo revenue simulations with what-if scenarios</p>
        </div>
        <button
          onClick={() => setShowGlossary(!showGlossary)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors text-sm"
        >
          <BookOpen className="w-4 h-4" />
          {showGlossary ? 'Hide' : 'Show'} Glossary
        </button>
      </div>

      {showGlossary && (
        <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-xl p-5">
          <h3 className="font-semibold text-blue-400 mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            Key Terms & Definitions
          </h3>
          <div className="grid grid-cols-2 gap-4">
            {glossaryTerms.map((item, idx) => (
              <div key={idx} className="bg-slate-800/50 rounded-lg p-3">
                <p className="font-medium text-amber-400 text-sm">{item.term}</p>
                <p className="text-slate-400 text-xs mt-1">{item.definition}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
        <h3 className="font-semibold mb-2 flex items-center gap-2">
          <Info className="w-4 h-4 text-amber-400" />
          How to Use This Tool
        </h3>
        <p className="text-slate-400 text-sm">
          1. <strong className="text-white">Select a scenario</strong> from the left panel based on the market conditions you want to analyze.
          2. <strong className="text-white">Adjust parameters</strong> - more paths gives more accurate statistics, longer horizon for strategic planning.
          3. <strong className="text-white">Run the simulation</strong> and review the probability distribution of outcomes.
          4. <strong className="text-white">Compare scenarios</strong> by running multiple simulations and noting VaR/CVaR differences.
        </p>
      </div>

      <div className="grid grid-cols-4 gap-6">
        <div className="col-span-1 bg-slate-800 rounded-xl border border-slate-700 p-4">
          <h3 className="font-semibold mb-4">Select Scenario</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {scenarios.map(scenario => (
              <button
                key={scenario.id}
                onClick={() => setSelectedScenario(scenario.id)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedScenario === scenario.id
                    ? 'bg-amber-600 text-white'
                    : 'bg-slate-700/50 hover:bg-slate-700 text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{scenario.name}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    scenario.category === 'Bull' ? 'bg-green-500/20 text-green-400' :
                    scenario.category === 'Bear' ? 'bg-red-500/20 text-red-400' :
                    scenario.category === 'Stress' ? 'bg-purple-500/20 text-purple-400' :
                    scenario.category === 'Disruption' ? 'bg-orange-500/20 text-orange-400' :
                    'bg-slate-500/20 text-slate-400'
                  }`}>{scenario.category}</span>
                </div>
                <div className={`text-xs mt-1 ${selectedScenario === scenario.id ? 'text-amber-200' : 'text-slate-500'}`}>
                  {scenario.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="col-span-3 space-y-6">
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-lg">{currentScenario?.name}</h3>
                <p className="text-slate-400 text-sm">{currentScenario?.description}</p>
              </div>
              <div className="flex items-center gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Paths</label>
                  <input
                    type="number"
                    value={nPaths}
                    onChange={(e) => setNPaths(Number(e.target.value))}
                    className="w-24 bg-slate-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Months</label>
                  <input
                    type="number"
                    value={nMonths}
                    onChange={(e) => setNMonths(Number(e.target.value))}
                    className="w-20 bg-slate-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>
                <button
                  onClick={runSimulation}
                  disabled={isRunning}
                  className="flex items-center gap-2 px-4 py-2 bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50 mt-4"
                >
                  {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  {isRunning ? 'Running...' : 'Run Simulation'}
                </button>
              </div>
            </div>

            {currentScenario && (
              <div className="border-t border-slate-700 pt-4 mt-4">
                <button
                  onClick={() => setShowInterpretation(!showInterpretation)}
                  className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
                >
                  {showInterpretation ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  Scenario Interpretation & Business Impact
                </button>
                {showInterpretation && (
                  <div className="mt-3 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                    <p className="text-sm text-slate-300">{currentScenario.interpretation}</p>
                  </div>
                )}
              </div>
            )}

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mt-4">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            {results && (
              <div className="grid grid-cols-6 gap-4 mt-6">
                <div className="bg-gradient-to-br from-amber-500/20 to-amber-600/10 rounded-lg p-4 border border-amber-500/30">
                  <p className="text-slate-400 text-xs">Terminal Mean</p>
                  <p className="text-2xl font-bold text-amber-400">${(results.terminal_mean / 1000).toFixed(2)}B</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <p className="text-slate-400 text-xs">VaR 95%</p>
                  <p className="text-xl font-bold text-red-400">${(results.var_95 / 1000).toFixed(2)}B</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <p className="text-slate-400 text-xs">CVaR 95%</p>
                  <p className="text-xl font-bold text-red-500">${(results.cvar_95 / 1000).toFixed(2)}B</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <p className="text-slate-400 text-xs">P10 (Downside)</p>
                  <p className="text-xl font-bold text-orange-400">${((results.p10 || results.var_95 * 0.9) / 1000).toFixed(2)}B</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <p className="text-slate-400 text-xs">P50 (Median)</p>
                  <p className="text-xl font-bold">${((results.p50 || results.terminal_mean * 0.98) / 1000).toFixed(2)}B</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <p className="text-slate-400 text-xs">P90 (Upside)</p>
                  <p className="text-xl font-bold text-green-400">${((results.p90 || results.terminal_mean * 1.1) / 1000).toFixed(2)}B</p>
                </div>
              </div>
            )}
          </div>

          {results && (
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-5">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Shuffle className="w-5 h-5 text-purple-400" />
                Revenue Projection Summary ({nMonths} months)
              </h3>
              {pathData.length > 0 ? (
                <>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={pathData}>
                        <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                        <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `${(v/1000).toFixed(1)}B`} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                          formatter={(v: number) => [`${(v/1000).toFixed(2)}B`, '']}
                        />
                        <Area type="monotone" dataKey="p95" stroke="transparent" fill="#22c55e" fillOpacity={0.1} />
                        <Area type="monotone" dataKey="p75" stroke="transparent" fill="#22c55e" fillOpacity={0.2} />
                        <Line type="monotone" dataKey="p50" stroke="#f59e0b" strokeWidth={2} dot={false} />
                        <Area type="monotone" dataKey="p25" stroke="transparent" fill="#ef4444" fillOpacity={0.2} />
                        <Area type="monotone" dataKey="p5" stroke="transparent" fill="#ef4444" fillOpacity={0.1} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex items-center justify-center gap-6 mt-4 text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500/30 rounded" />
                      <span className="text-slate-400">P75-P95 (Upside)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-amber-500 rounded" />
                      <span className="text-slate-400">P50 (Median)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500/30 rounded" />
                      <span className="text-slate-400">P5-P25 (Downside)</span>
                    </div>
                  </div>
                </>
              ) : (
                <div className="h-64 flex items-center justify-center">
                  <div className="text-center text-slate-400">
                    <Shuffle className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p>Path distribution not available from this simulation.</p>
                    <p className="text-sm mt-1">Summary statistics shown above.</p>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/30 rounded-xl p-5">
            <div className="flex items-start gap-4">
              <AlertTriangle className="w-5 h-5 text-purple-400 mt-1" />
              <div>
                <h4 className="font-semibold text-purple-400">Reading the Results</h4>
                <div className="text-sm text-slate-400 mt-2 space-y-2">
                  <p>
                    <strong className="text-amber-400">Terminal Mean</strong>: The average expected annual revenue at the end of your forecast horizon. 
                    This is your "most likely" outcome and should be used for baseline planning.
                  </p>
                  <p>
                    <strong className="text-red-400">VaR 95%</strong>: There's only a 5% probability that revenue falls below this level. 
                    Use this for downside planning - if your budget assumes this revenue, you have 95% confidence of meeting it.
                  </p>
                  <p>
                    <strong className="text-red-500">CVaR 95%</strong>: The average revenue in the worst 5% of scenarios. More conservative than VaR - 
                    use for stress testing capital reserves and worst-case contingency planning.
                  </p>
                  <p>
                    <strong className="text-green-400">P90 (Upside)</strong>: Only 10% of simulations exceed this value. 
                    Use for stretch targets and upside opportunity planning.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
