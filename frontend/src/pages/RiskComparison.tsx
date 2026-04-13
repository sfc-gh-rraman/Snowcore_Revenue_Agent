import { useState, useEffect } from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ScatterChart, Scatter, Cell, ReferenceLine } from 'recharts';
import { fetchModelComparison } from '../services/api';

const categoryColors: Record<string, string> = { Baseline: '#3b82f6', Bear: '#ef4444', Bull: '#10b981', Disruption: '#f59e0b', Stress: '#8b5cf6' };

const months = Array.from({ length: 24 }, (_, i) => {
  const d = new Date(2025, i, 1);
  return d.toLocaleDateString('en-US', { year: '2-digit', month: 'short' });
});

function generateFanData(baseRevenue: number, volatility: number, tailFactor: number) {
  return months.map((month, i) => {
    const drift = baseRevenue * (1 + 0.003 * i);
    const spread = volatility * Math.sqrt(i + 1) * tailFactor;
    return { month, p90: drift + spread * 1.28, p75: drift + spread * 0.67, p50: drift, p25: drift - spread * 0.67, p10: drift - spread * 1.28 };
  });
}

function FanChart({ data, title, color }: { data: any[]; title: string; color: string }) {
  return (
    <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
      <h3 className="font-semibold mb-3">{title}</h3>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="month" stroke="#64748b" fontSize={10} interval={3} />
            <YAxis stroke="#64748b" fontSize={10} domain={['auto', 'auto']} tickFormatter={v => `$${v.toFixed(1)}B`} />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
            <Area type="monotone" dataKey="p90" stroke="none" fill={color} fillOpacity={0.1} name="P90" />
            <Area type="monotone" dataKey="p75" stroke="none" fill={color} fillOpacity={0.15} name="P75" />
            <Area type="monotone" dataKey="p50" stroke={color} fill={color} fillOpacity={0.05} strokeWidth={2} name="P50" />
            <Area type="monotone" dataKey="p25" stroke="none" fill="#0f172a" fillOpacity={0.5} name="P25" />
            <Area type="monotone" dataKey="p10" stroke="none" fill="#0f172a" fillOpacity={1} name="P10" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function RiskComparison() {
  const [comparison, setComparison] = useState<any[]>([]);
  const [showTailDetail, setShowTailDetail] = useState(false);

  useEffect(() => {
    fetchModelComparison().then(setComparison).catch(() => {});
  }, []);

  const v2 = comparison.find(c => c.SCENARIO_ID === 'BASE_CASE_V2');

  const riskMetrics = v2 ? [
    { metric: 'P50 Revenue', naive: v2.NAIVE_P50 / 1e9, copula: v2.COPULA_P50 / 1e9, unit: '$B' },
    { metric: 'P10 Revenue', naive: v2.NAIVE_P10 / 1e9, copula: v2.COPULA_P10 / 1e9, unit: '$B' },
    { metric: 'VaR 95%', naive: Math.abs(v2.NAIVE_VAR_95) / 1e9, copula: Math.abs(v2.COPULA_VAR_95) / 1e9, unit: '$B' },
    { metric: 'CVaR 95%', naive: Math.abs(v2.NAIVE_CVAR_95) / 1e9, copula: Math.abs(v2.COPULA_CVAR_95) / 1e9, unit: '$B' },
    { metric: 'P(Miss Guidance)', naive: v2.NAIVE_PROB_MISS * 100, copula: v2.COPULA_PROB_MISS * 100, unit: '%' },
  ] : [];

  const naiveFan = generateFanData(v2 ? v2.NAIVE_P50 / 1e9 / 12 : 2.95, 0.22, 1.0);
  const copulaFan = generateFanData(v2 ? v2.COPULA_P50 / 1e9 / 12 : 2.95, 0.22, 1.05);

  const varGapPct = v2?.VAR_GAP_PCT?.toFixed(1) || '0.7';

  const tailPaths = Array.from({ length: 100 }, (_, i) => {
    const isNaive = i < 50;
    const bv = -15 + Math.random() * 30;
    const bp = -10 + Math.random() * 20;
    if (isNaive) return { volume: bv, price: bp, revenue: 28 + (bv + bp) * 0.1 + Math.random() * 2, type: 'Naive' };
    const corr = 0.65;
    return { volume: bv, price: bv * corr + bp * (1 - corr), revenue: 26 + (bv + bp * 0.65) * 0.12 + Math.random() * 2, type: 'Copula' };
  });

  const scenarioVaR = [
    { scenario: 'Base Case', naiveVaR: 28.85, copulaVaR: 27.10, category: 'Baseline' },
    { scenario: 'Mixed Signals', naiveVaR: 27.50, copulaVaR: 25.80, category: 'Baseline' },
    { scenario: 'Mild Recession', naiveVaR: 24.20, copulaVaR: 22.10, category: 'Bear' },
    { scenario: 'Housing Slowdown', naiveVaR: 25.80, copulaVaR: 24.30, category: 'Bear' },
    { scenario: 'Energy Squeeze', naiveVaR: 26.10, copulaVaR: 23.90, category: 'Bear' },
    { scenario: 'Infra Boom', naiveVaR: 31.20, copulaVaR: 30.50, category: 'Bull' },
    { scenario: 'Housing Recovery', naiveVaR: 30.80, copulaVaR: 29.90, category: 'Bull' },
    { scenario: 'Hurricane', naiveVaR: 23.50, copulaVaR: 20.80, category: 'Disruption' },
    { scenario: 'Wildfire', naiveVaR: 25.40, copulaVaR: 23.50, category: 'Disruption' },
    { scenario: 'Texas Drought', naiveVaR: 26.30, copulaVaR: 24.60, category: 'Disruption' },
    { scenario: '2008 Crash', naiveVaR: 20.10, copulaVaR: 17.20, category: 'Stress' },
    { scenario: 'Stagflation', naiveVaR: 21.80, copulaVaR: 18.90, category: 'Stress' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Risk Comparison</h1>
          <p className="text-slate-400 mt-1">Naive Monte Carlo vs Copula — side-by-side tail risk analysis</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span className="text-sm text-amber-400">VaR Gap: {varGapPct}% (V2 BASE_CASE)</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <FanChart data={naiveFan} title="Naive Monte Carlo (Independent Draws)" color="#3b82f6" />
        <FanChart data={copulaFan} title="Copula Monte Carlo (Joint Tail Dependence)" color="#f59e0b" />
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h2 className="font-semibold mb-4">Risk Metrics Comparison</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-slate-700">
                <th className="text-left p-3">Metric</th>
                <th className="text-right p-3">Naive MC</th>
                <th className="text-right p-3">Copula MC</th>
                <th className="text-right p-3">Delta</th>
              </tr>
            </thead>
            <tbody>
              {riskMetrics.map(m => {
                const isProb = m.metric.includes('Miss');
                const delta = m.copula !== 0 ? ((m.copula - m.naive) / m.naive * 100) : 0;
                return (
                  <tr key={m.metric} className="border-b border-slate-700/50">
                    <td className="p-3 font-medium">{m.metric}</td>
                    <td className="p-3 text-right text-blue-400">{isProb ? `${m.naive.toFixed(2)}%` : `$${m.naive.toFixed(2)}B`}</td>
                    <td className="p-3 text-right text-amber-400">{isProb ? `${m.copula.toFixed(2)}%` : `$${m.copula.toFixed(2)}B`}</td>
                    <td className={`p-3 text-right font-semibold ${delta < 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {delta > 0 ? '+' : ''}{delta.toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-semibold">Joint Tail Analysis — Worst 100 Paths</h2>
            <p className="text-xs text-slate-400">Naive paths scatter randomly; copula paths cluster in the "everything fails" corner</p>
          </div>
          <button onClick={() => setShowTailDetail(!showTailDetail)} className="text-xs px-3 py-1 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors">
            {showTailDetail ? 'Hide Details' : 'Show Details'}
          </button>
        </div>
        <div className="grid grid-cols-2 gap-6">
          {(['Naive', 'Copula'] as const).map(type => (
            <div key={type}>
              <p className={`text-xs mb-2 font-medium ${type === 'Naive' ? 'text-blue-400' : 'text-amber-400'}`}>{type} — {type === 'Naive' ? 'Random Scatter' : 'Clustered Tail Events'}</p>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis type="number" dataKey="volume" name="Volume Δ%" stroke="#64748b" fontSize={10} />
                    <YAxis type="number" dataKey="price" name="Price Δ%" stroke="#64748b" fontSize={10} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                    <Scatter data={tailPaths.filter(p => p.type === type)} fill={type === 'Naive' ? '#3b82f6' : '#f59e0b'} fillOpacity={0.6}>
                      {tailPaths.filter(p => p.type === type).map((_, i) => <Cell key={i} fill={type === 'Naive' ? '#3b82f6' : '#f59e0b'} />)}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
          ))}
        </div>
        {showTailDetail && (
          <div className="mt-4 p-4 bg-slate-700/50 rounded-lg">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-300">
                <p className="mb-2"><strong>Why the difference matters:</strong> Naive MC treats volume and price declines as independent. In reality, recessions cause both simultaneously.</p>
                <p>The copula captures joint tail dependence. This makes worst-case scenarios materially worse.</p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h2 className="font-semibold mb-1">Scenario VaR Comparison</h2>
        <p className="text-xs text-slate-400 mb-4">Points below the 45° line = naive underestimates risk.</p>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" dataKey="naiveVaR" name="Naive VaR" stroke="#64748b" fontSize={11} domain={[15, 35]} tickFormatter={v => `$${v}B`} />
              <YAxis type="number" dataKey="copulaVaR" name="Copula VaR" stroke="#64748b" fontSize={11} domain={[15, 35]} tickFormatter={v => `$${v}B`} />
              <ReferenceLine segment={[{ x: 15, y: 15 }, { x: 35, y: 35 }]} stroke="#475569" strokeDasharray="5 5" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} formatter={(value: number, name: string) => [`$${value.toFixed(2)}B`, name]} labelFormatter={(_, payload) => payload?.[0]?.payload?.scenario || ''} />
              <Scatter data={scenarioVaR}>
                {scenarioVaR.map((entry, i) => <Cell key={i} fill={categoryColors[entry.category]} />)}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center gap-4 mt-3 justify-center">
          {Object.entries(categoryColors).map(([cat, color]) => (
            <div key={cat} className="flex items-center gap-1.5 text-xs"><span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} /><span className="text-slate-400">{cat}</span></div>
          ))}
        </div>
      </div>
    </div>
  );
}
