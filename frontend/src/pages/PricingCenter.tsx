import { useState, useEffect } from 'react';
import { Play, AlertTriangle, CheckCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { fetchOptimalPricing, runOptimizer as apiRunOptimizer } from '../services/api';

export default function PricingCenter() {
  const [pricingData, setPricingData] = useState<any[]>([]);
  const [isOptimizing, setIsOptimizing] = useState(false);

  useEffect(() => {
    fetchOptimalPricing().then(setPricingData).catch(() => {});
  }, []);

  const topPricing = pricingData.slice(0, 6);

  const runOptimizer = async () => {
    setIsOptimizing(true);
    try {
      await apiRunOptimizer('ALL', 'v2');
      const fresh = await fetchOptimalPricing();
      setPricingData(fresh);
    } catch { /* noop */ }
    setIsOptimizing(false);
  };

  const constraints = [
    { name: 'Margin Floor', value: 15, unit: '%', min: 5, max: 30 },
    { name: 'Max Price Change', value: 10, unit: '%', min: 1, max: 25 },
    { name: 'Competitor Parity', value: 5, unit: '%', min: 1, max: 15 },
    { name: 'Capacity Cap', value: 95, unit: '%', min: 70, max: 100 },
  ];

  const convergedCount = pricingData.filter(p => p.OPTIMIZER_STATUS?.includes('successfully')).length;
  const totalCount = pricingData.length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Pricing Center</h1>
          <p className="text-slate-400 mt-1">Constrained pricing optimization with SLSQP</p>
        </div>
        <button onClick={runOptimizer} disabled={isOptimizing} className="flex items-center gap-2 px-4 py-2 bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50">
          <Play className="w-4 h-4" />
          {isOptimizing ? 'Running...' : 'Run Optimizer'}
        </button>
      </div>

      <div>
        <h2 className="font-semibold mb-3">Current vs Optimal Pricing (v2)</h2>
        <div className="grid grid-cols-3 gap-4">
          {topPricing.map((item, i) => {
            const isConverged = item.OPTIMIZER_STATUS?.includes('successfully');
            return (
              <div key={i} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="text-sm font-medium">{item.PRODUCT_NAME}</span>
                    <span className="text-xs text-slate-500 ml-2">{item.REGION_CODE}</span>
                  </div>
                  {isConverged ? <CheckCircle className="w-4 h-4 text-green-400" /> : <AlertTriangle className="w-4 h-4 text-amber-400" />}
                </div>
                <div className="grid grid-cols-2 gap-3 mt-3">
                  <div>
                    <p className="text-xs text-slate-400">Current</p>
                    <p className="text-lg font-semibold">${item.CURRENT_PRICE}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">Optimal</p>
                    <p className="text-lg font-semibold text-green-400">${item.OPTIMAL_PRICE}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-700">
                  <span className={`text-sm font-medium ${item.PRICE_DELTA_PCT > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {item.PRICE_DELTA_PCT > 0 ? '+' : ''}{item.PRICE_DELTA_PCT}%
                  </span>
                  <span className="text-sm text-amber-400">{item.PROFIT_DELTA_M > 0 ? '+' : ''}${item.PROFIT_DELTA_M}M</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${item.ELASTICITY_CLASSIFICATION?.includes('INELASTIC') ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'}`}>
                    {item.ELASTICITY_CLASSIFICATION || ''}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h2 className="font-semibold mb-4">Optimization Constraints</h2>
          <div className="space-y-4">
            {constraints.map(c => (
              <div key={c.name}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-slate-300">{c.name}</span>
                  <span className="text-sm font-medium text-amber-400">{c.value}{c.unit}</span>
                </div>
                <div className="relative h-2 bg-slate-700 rounded-full">
                  <div className="absolute h-full bg-amber-500 rounded-full" style={{ width: `${((c.value - c.min) / (c.max - c.min)) * 100}%` }} />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
                  <span>{c.min}{c.unit}</span>
                  <span>{c.max}{c.unit}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-slate-700/50 rounded-lg">
            <p className="text-xs text-slate-400">
              {convergedCount} of {totalCount} product-region combinations converged.
              Boundary-hit results shown with ⚠ indicator.
            </p>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h2 className="font-semibold mb-4">Profit Impact by Region</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topPricing} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" stroke="#64748b" fontSize={11} tickFormatter={v => `$${v}M`} />
                <YAxis type="category" dataKey="REGION_CODE" stroke="#64748b" fontSize={11} width={100} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} formatter={(v: number) => [`$${v}M`, 'Profit Impact']} />
                <Bar dataKey="PROFIT_DELTA_M" radius={[0, 4, 4, 0]}>
                  {topPricing.map((_, i) => (<Cell key={i} fill={i % 2 === 0 ? '#f59e0b' : '#d97706'} />))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h2 className="font-semibold mb-4">Full Pricing Table</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-slate-700">
                <th className="text-left p-3">Region</th>
                <th className="text-left p-3">Product</th>
                <th className="text-right p-3">Current</th>
                <th className="text-right p-3">Optimal</th>
                <th className="text-right p-3">Δ%</th>
                <th className="text-right p-3">Profit Δ</th>
                <th className="text-left p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {pricingData.map((p, i) => (
                <tr key={i} className="border-b border-slate-700/50">
                  <td className="p-3">{p.REGION_CODE}</td>
                  <td className="p-3 font-medium">{p.PRODUCT_NAME}</td>
                  <td className="p-3 text-right">${p.CURRENT_PRICE}</td>
                  <td className="p-3 text-right text-green-400">${p.OPTIMAL_PRICE}</td>
                  <td className={`p-3 text-right ${p.PRICE_DELTA_PCT > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {p.PRICE_DELTA_PCT > 0 ? '+' : ''}{p.PRICE_DELTA_PCT}%
                  </td>
                  <td className="p-3 text-right text-amber-400">${p.PROFIT_DELTA_M}M</td>
                  <td className="p-3 text-xs">{p.OPTIMIZER_STATUS?.includes('successfully') ? '✅' : '⚠️'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
