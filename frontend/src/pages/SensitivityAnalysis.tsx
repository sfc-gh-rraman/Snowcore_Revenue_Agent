import { useState } from 'react';
import { Play, RefreshCw, BookOpen, Info, TrendingUp, TrendingDown } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const parameters = [
  { 
    id: 'drift', 
    name: 'Drift (Growth Rate)', 
    description: 'Monthly growth rate',
    fullDescription: 'The expected monthly growth rate (trend) in revenue. Positive drift = growth trajectory, negative drift = decline. This is the "mu" parameter in the GBM model. A 2% monthly drift compounds to ~27% annual growth.',
    businessImpact: 'Directly affects terminal revenue projections. Use historical growth rates as baseline, then adjust for expected market conditions.',
    min: -0.05,
    max: 0.10,
    step: 0.01,
    format: 'percent',
    presets: [
      { label: 'Negative to Flat', values: [-0.04, -0.02, 0, 0.01, 0.02] },
      { label: 'Conservative', values: [-0.02, 0, 0.02, 0.04, 0.06] },
      { label: 'Aggressive', values: [0, 0.02, 0.04, 0.06, 0.08] },
    ]
  },
  { 
    id: 'volatility', 
    name: 'Volatility', 
    description: 'Return volatility',
    fullDescription: 'The standard deviation of monthly revenue changes. Higher volatility = wider distribution of outcomes. This is the "sigma" parameter in the GBM model, representing uncertainty.',
    businessImpact: 'Higher volatility increases both upside potential AND downside risk. The VaR-to-Mean spread widens as volatility increases. Construction materials typically have 15-25% annualized volatility.',
    min: 0.05,
    max: 0.35,
    step: 0.02,
    format: 'percent',
    presets: [
      { label: 'Low Vol', values: [0.05, 0.08, 0.10, 0.12, 0.15] },
      { label: 'Normal', values: [0.08, 0.12, 0.16, 0.20, 0.25] },
      { label: 'High Vol', values: [0.15, 0.20, 0.25, 0.30, 0.35] },
    ]
  },
  { 
    id: 'revenue_shock', 
    name: 'Revenue Shock', 
    description: 'Initial shock %',
    fullDescription: 'An immediate one-time adjustment to the starting revenue base. Models sudden market changes like contract wins/losses, facility closures, or acquisition impacts.',
    businessImpact: 'Use to model "what-if" scenarios for known events. A -20% shock models losing a major customer; +15% models a significant contract win. The shock applies immediately, then normal drift/volatility takes over.',
    min: -0.30,
    max: 0.30,
    step: 0.05,
    format: 'percent',
    presets: [
      { label: 'Negative Shocks', values: [-0.25, -0.15, -0.10, -0.05, 0] },
      { label: 'Balanced', values: [-0.20, -0.10, 0, 0.10, 0.20] },
      { label: 'Positive Shocks', values: [0, 0.05, 0.10, 0.15, 0.25] },
    ]
  },
  { 
    id: 'highway_growth', 
    name: 'Highway Growth', 
    description: 'Infrastructure multiplier',
    fullDescription: 'Growth rate modifier for the highway/infrastructure segment (~35% of SnowCore revenue). Reflects DOT budgets, federal infrastructure spending (IIJA), and state highway programs.',
    businessImpact: 'Highway segment is most sensitive to government policy. IIJA provides multi-year visibility. Each 5% change in highway growth impacts total revenue by ~1.75% (35% × 5%).',
    min: -0.10,
    max: 0.20,
    step: 0.025,
    format: 'percent',
    presets: [
      { label: 'Decline', values: [-0.10, -0.05, 0, 0.025, 0.05] },
      { label: 'Baseline', values: [-0.05, 0, 0.05, 0.10, 0.15] },
      { label: 'IIJA Boost', values: [0, 0.05, 0.10, 0.15, 0.20] },
    ]
  },
  { 
    id: 'residential_growth', 
    name: 'Residential Growth', 
    description: 'Housing multiplier',
    fullDescription: 'Growth rate modifier for residential construction segment (~30% of revenue). Tied to housing starts, mortgage rates, and demographic trends. Most volatile segment.',
    businessImpact: 'Residential is most cyclical - first to fall in recession, first to recover. Each 5% change impacts total revenue by ~1.5%. Watch housing starts data (typically leads aggregate demand by 3-6 months).',
    min: -0.15,
    max: 0.15,
    step: 0.025,
    format: 'percent',
    presets: [
      { label: 'Housing Crash', values: [-0.15, -0.10, -0.05, 0, 0.02] },
      { label: 'Balanced', values: [-0.10, -0.05, 0, 0.05, 0.10] },
      { label: 'Recovery', values: [-0.02, 0, 0.05, 0.10, 0.15] },
    ]
  },
];

const sensitivityGlossary = [
  { term: 'Sensitivity Analysis', definition: 'Tests how changes in ONE input parameter affect simulation outcomes, holding all other parameters constant. Reveals which assumptions most impact results.' },
  { term: 'Terminal Mean', definition: 'Average ending revenue across all simulation paths at a specific parameter value. Shows the central expected outcome.' },
  { term: 'VaR 95% Line', definition: 'The 5th percentile of outcomes at each parameter value. Traces how downside risk changes as you adjust the parameter.' },
  { term: 'Spread', definition: 'The difference between Terminal Mean and VaR 95%. Wider spread = more uncertainty/risk at that parameter value.' },
  { term: 'Steepness', definition: 'How steeply the lines slope. Steep slope = parameter has large impact (high sensitivity). Flat slope = parameter has minimal impact.' },
];

interface SensitivityResult {
  parameter_value: number;
  terminal_mean_m: number;
  terminal_var_95_m: number;
  terminal_cvar_95_m?: number;
  cumulative_mean_m?: number;
}

export default function SensitivityAnalysis() {
  const [selectedParam, setSelectedParam] = useState('drift');
  const [scenario, setScenario] = useState('BASE_CASE');
  const [selectedValues, setSelectedValues] = useState<number[]>([-0.02, 0, 0.02, 0.04, 0.06]);
  const [nPaths, setNPaths] = useState(1000);
  const [nMonths, setNMonths] = useState(24);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SensitivityResult[]>([]);
  const [showGlossary, setShowGlossary] = useState(false);

  const currentParam = parameters.find(p => p.id === selectedParam);

  const runSensitivity = async () => {
    setIsRunning(true);
    setError(null);
    
    try {
      const sortedValues = [...selectedValues].sort((a, b) => a - b);
      
      const response = await fetch('/api/agent/sensitivity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          scenario_type: scenario,
          parameter: selectedParam,
          values: sortedValues,
          n_paths: nPaths,
          n_months: nMonths
        })
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Sensitivity analysis failed');
      }
      
      const data = await response.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
    
    setIsRunning(false);
  };

  const toggleValue = (val: number) => {
    if (selectedValues.includes(val)) {
      if (selectedValues.length > 2) {
        setSelectedValues(selectedValues.filter(v => v !== val));
      }
    } else {
      setSelectedValues([...selectedValues, val]);
    }
  };

  const applyPreset = (presetValues: number[]) => {
    setSelectedValues([...presetValues]);
  };

  const generateRangeValues = () => {
    if (!currentParam) return [];
    const values: number[] = [];
    for (let v = currentParam.min; v <= currentParam.max + 0.0001; v += currentParam.step) {
      values.push(Math.round(v * 1000) / 1000);
    }
    return values;
  };

  const formatValue = (val: number) => {
    return `${(val * 100).toFixed(val % 0.01 === 0 ? 0 : 1)}%`;
  };

  const chartData = results.map(r => ({
    value: r.parameter_value,
    terminalMean: r.terminal_mean_m / 1000,
    var95: r.terminal_var_95_m / 1000
  }));

  const getResultInterpretation = () => {
    if (results.length < 2) return null;
    const firstResult = results[0];
    const lastResult = results[results.length - 1];
    const meanChange = ((lastResult.terminal_mean_m - firstResult.terminal_mean_m) / firstResult.terminal_mean_m) * 100;
    const varChange = ((lastResult.terminal_var_95_m - firstResult.terminal_var_95_m) / firstResult.terminal_var_95_m) * 100;
    const paramRange = `${(firstResult.parameter_value * 100).toFixed(0)}% to ${(lastResult.parameter_value * 100).toFixed(0)}%`;
    
    return {
      meanChange,
      varChange,
      paramRange,
      sensitivity: Math.abs(meanChange) > 20 ? 'HIGH' : Math.abs(meanChange) > 10 ? 'MEDIUM' : 'LOW'
    };
  };

  const interpretation = getResultInterpretation();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Sensitivity Analysis</h1>
          <p className="text-slate-400 mt-1">Explore how individual parameters affect simulation outcomes</p>
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
            Understanding Sensitivity Analysis
          </h3>
          <div className="grid grid-cols-2 gap-4">
            {sensitivityGlossary.map((item, idx) => (
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
          1. <strong className="text-white">Select a parameter</strong> to test (left panel) - this is the variable you want to stress-test.
          2. <strong className="text-white">Choose test values</strong> using presets or manual selection - these are the different values you'll compare.
          3. <strong className="text-white">Run the analysis</strong> to see how the parameter affects Terminal Mean and VaR across the range.
          4. <strong className="text-white">Interpret the chart</strong>: Steep lines = high sensitivity (parameter matters a lot); Flat lines = low sensitivity.
        </p>
      </div>

      <div className="grid grid-cols-4 gap-6">
        <div className="col-span-1 space-y-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
            <h3 className="font-semibold mb-4">Select Parameter to Test</h3>
            <div className="space-y-2">
              {parameters.map(param => (
                <button
                  key={param.id}
                  onClick={() => {
                    setSelectedParam(param.id);
                    setSelectedValues(param.presets[1].values);
                  }}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    selectedParam === param.id
                      ? 'bg-amber-600 text-white'
                      : 'bg-slate-700/50 hover:bg-slate-700 text-slate-300'
                  }`}
                >
                  <div className="font-medium text-sm">{param.name}</div>
                  <div className={`text-xs mt-1 ${selectedParam === param.id ? 'text-amber-200' : 'text-slate-500'}`}>
                    {param.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {currentParam && (
            <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 border border-amber-500/30 rounded-xl p-4">
              <h4 className="font-semibold text-amber-400 text-sm mb-2">About This Parameter</h4>
              <p className="text-xs text-slate-300 mb-3">{currentParam.fullDescription}</p>
              <h4 className="font-semibold text-amber-400 text-sm mb-2">Business Impact</h4>
              <p className="text-xs text-slate-300">{currentParam.businessImpact}</p>
            </div>
          )}
        </div>

        <div className="col-span-3 space-y-6">
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-lg">{currentParam?.name}</h3>
                <p className="text-slate-400 text-sm">{currentParam?.description}</p>
              </div>
              <div className="flex items-center gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Base Scenario</label>
                  <select
                    value={scenario}
                    onChange={(e) => setScenario(e.target.value)}
                    className="bg-slate-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  >
                    <option value="BASE_CASE">Base Case</option>
                    <option value="MILD_RECESSION">Mild Recession</option>
                    <option value="HURRICANE_MAJOR">Major Hurricane</option>
                    <option value="IIJA_INFRASTRUCTURE_BOOM">Infrastructure Boom</option>
                    <option value="HOUSING_CRASH_2008">2008 Housing Crash</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Paths</label>
                  <input
                    type="number"
                    value={nPaths}
                    onChange={(e) => setNPaths(Number(e.target.value))}
                    className="w-20 bg-slate-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
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
                  onClick={runSensitivity}
                  disabled={isRunning || selectedValues.length < 2}
                  className="flex items-center gap-2 px-4 py-2 bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50 mt-4"
                >
                  {isRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  {isRunning ? 'Running...' : 'Run Analysis'}
                </button>
              </div>
            </div>

            <div className="border-t border-slate-700 pt-4 mt-2">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-slate-300">Quick Presets</span>
                <span className="text-xs text-slate-500">{selectedValues.length} values selected</span>
              </div>
              <div className="flex gap-2 mb-4">
                {currentParam?.presets.map((preset, idx) => (
                  <button
                    key={idx}
                    onClick={() => applyPreset(preset.values)}
                    className="px-3 py-1.5 text-xs rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
                  >
                    {preset.label}
                  </button>
                ))}
              </div>

              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-300">Select Values</span>
                <span className="text-xs text-slate-500">Click to toggle • Min 2 required</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {generateRangeValues().map((val) => (
                  <button
                    key={val}
                    onClick={() => toggleValue(val)}
                    className={`px-3 py-1.5 text-xs rounded-lg transition-all ${
                      selectedValues.includes(val)
                        ? 'bg-amber-600 text-white ring-2 ring-amber-400'
                        : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700 hover:text-slate-300'
                    }`}
                  >
                    {formatValue(val)}
                  </button>
                ))}
              </div>

              <div className="mt-4 p-3 bg-slate-900/50 rounded-lg">
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-slate-400">Selected:</span>
                  <div className="flex flex-wrap gap-1">
                    {[...selectedValues].sort((a, b) => a - b).map((val, i) => (
                      <span key={i} className="px-2 py-0.5 bg-amber-600/20 text-amber-400 rounded text-xs font-mono">
                        {formatValue(val)}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mt-4">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            {chartData.length > 0 && (
              <div className="h-72 mt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <XAxis 
                      dataKey="value" 
                      stroke="#64748b" 
                      fontSize={12} 
                      tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                    />
                    <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `$${v.toFixed(1)}B`} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                      formatter={(v: number) => [`$${v.toFixed(2)}B`, '']}
                      labelFormatter={(v) => `${currentParam?.name}: ${(Number(v) * 100).toFixed(0)}%`}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="terminalMean" stroke="#f59e0b" strokeWidth={3} dot={{ fill: '#f59e0b', r: 6 }} name="Terminal Mean" />
                    <Line type="monotone" dataKey="var95" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={{ fill: '#ef4444', r: 4 }} name="VaR 95%" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {results.length > 0 && (
            <>
              {interpretation && (
                <div className={`rounded-xl border p-5 ${
                  interpretation.sensitivity === 'HIGH' 
                    ? 'bg-red-500/10 border-red-500/30' 
                    : interpretation.sensitivity === 'MEDIUM'
                    ? 'bg-amber-500/10 border-amber-500/30'
                    : 'bg-green-500/10 border-green-500/30'
                }`}>
                  <div className="flex items-start gap-4">
                    {interpretation.meanChange > 0 
                      ? <TrendingUp className="w-6 h-6 text-green-400 mt-1" />
                      : <TrendingDown className="w-6 h-6 text-red-400 mt-1" />
                    }
                    <div>
                      <h4 className="font-semibold flex items-center gap-2">
                        Interpretation
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          interpretation.sensitivity === 'HIGH' ? 'bg-red-500/30 text-red-400' :
                          interpretation.sensitivity === 'MEDIUM' ? 'bg-amber-500/30 text-amber-400' :
                          'bg-green-500/30 text-green-400'
                        }`}>
                          {interpretation.sensitivity} SENSITIVITY
                        </span>
                      </h4>
                      <div className="text-sm text-slate-300 mt-2 space-y-1">
                        <p>
                          Changing <strong className="text-white">{currentParam?.name}</strong> from <strong>{interpretation.paramRange}</strong>:
                        </p>
                        <p>
                          • Terminal Mean changes by <strong className={interpretation.meanChange > 0 ? 'text-green-400' : 'text-red-400'}>
                            {interpretation.meanChange > 0 ? '+' : ''}{interpretation.meanChange.toFixed(1)}%
                          </strong>
                        </p>
                        <p>
                          • VaR 95% (downside risk) changes by <strong className={interpretation.varChange > 0 ? 'text-green-400' : 'text-red-400'}>
                            {interpretation.varChange > 0 ? '+' : ''}{interpretation.varChange.toFixed(1)}%
                          </strong>
                        </p>
                        <p className="text-slate-400 mt-2">
                          {interpretation.sensitivity === 'HIGH' 
                            ? `⚠️ This parameter has a large impact on outcomes. Small changes in ${currentParam?.name} significantly affect revenue projections. Monitor this closely.`
                            : interpretation.sensitivity === 'MEDIUM'
                            ? `This parameter has moderate impact. Changes in ${currentParam?.name} noticeably affect outcomes but are not the primary driver.`
                            : `This parameter has limited impact on outcomes. ${currentParam?.name} changes have minimal effect on the overall projection.`
                          }
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="bg-slate-800 rounded-xl border border-slate-700 p-5">
                <h3 className="font-semibold mb-4">Detailed Results</h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-2 text-slate-400 font-medium">{currentParam?.name}</th>
                      <th className="text-right py-2 text-slate-400 font-medium">Terminal Mean</th>
                      <th className="text-right py-2 text-slate-400 font-medium">VaR 95%</th>
                      <th className="text-right py-2 text-slate-400 font-medium">Spread (Risk)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((row, i) => (
                      <tr key={i} className="border-b border-slate-700/50">
                        <td className="py-3">{(row.parameter_value * 100).toFixed(0)}%</td>
                        <td className="py-3 text-right font-medium text-amber-400">${(row.terminal_mean_m / 1000).toFixed(2)}B</td>
                        <td className="py-3 text-right font-medium text-red-400">${(row.terminal_var_95_m / 1000).toFixed(2)}B</td>
                        <td className="py-3 text-right text-slate-400">${((row.terminal_mean_m - row.terminal_var_95_m) / 1000).toFixed(2)}B</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="text-xs text-slate-500 mt-3">
                  💡 <strong>Tip:</strong> The "Spread" column shows the gap between expected outcome and downside risk. 
                  Wider spread = more uncertainty. Compare spreads across parameter values to understand risk profiles.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
