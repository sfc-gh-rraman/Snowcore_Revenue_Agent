import { useState, useEffect } from 'react';
import { AlertTriangle, MapPin, Building2, Shield } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell, Legend, LineChart, Line } from 'recharts';
import { fetchCompetitiveLandscape, fetchQuarriesByRegion, fetchCompetitorRevenueTrend, fetchPricePremium } from '../services/api';

export default function CompetitiveIntel() {
  const [landscape, setLandscape] = useState<any[]>([]);
  const [quarries, setQuarries] = useState<any[]>([]);
  const [revTrend, setRevTrend] = useState<any[]>([]);
  const [premium, setPremium] = useState<any[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string>('all');

  useEffect(() => {
    fetchCompetitiveLandscape().then(setLandscape).catch(() => {});
    fetchQuarriesByRegion().then(setQuarries).catch(() => {});
    fetchCompetitorRevenueTrend().then(setRevTrend).catch(() => {});
    fetchPricePremium().then(setPremium).catch(() => {});
  }, []);

  const marketShare = landscape.map(l => ({
    name: l.COMPANY_NAME?.replace(' CO', '').replace(' INC', '').replace(' LLC', '').replace(' PUBLIC LTD', ''),
    value: l.MSHA_QUARRY_SITES || 0,
    color: l.COMPANY_NAME?.includes('VULCAN') ? '#f59e0b' : l.COMPANY_NAME?.includes('MARTIN') ? '#3b82f6' : l.COMPANY_NAME?.includes('CRH') ? '#10b981' : '#64748b',
  }));

  const regions = [...new Set(quarries.map(q => q.REGION_CODE))];
  const operatorMap: Record<string, string> = { VMC: 'snowcore', MLM: 'mlm', CRH: 'crh', HEIDELBERG: 'heidelberg', OTHER: 'other' };
  const quarryByRegion = regions.map(rc => {
    const regionQuarries = quarries.filter(q => q.REGION_CODE === rc);
    const row: any = { region: rc };
    regionQuarries.forEach(q => {
      const key = operatorMap[q.OPERATOR_GROUP] || 'other';
      row[key] = (row[key] || 0) + q.QUARRY_COUNT;
    });
    row.total = regionQuarries.reduce((s: number, q: any) => s + q.QUARRY_COUNT, 0);
    return row;
  });

  const filteredQuarries = selectedRegion === 'all' ? quarryByRegion : quarryByRegion.filter(q => q.region === selectedRegion);

  const totalQuarries = quarryByRegion.reduce((s, q) => s + (q.total || 0), 0);
  const snowcoreTotal = quarryByRegion.reduce((s, q) => s + (q.snowcore || 0), 0);

  const trendByQtr: Record<string, any> = {};
  revTrend.forEach(r => {
    const key = r.PERIOD_END_DATE?.slice(0, 7);
    if (!trendByQtr[key]) trendByQtr[key] = { quarter: `${r.FISCAL_PERIOD} ${r.PERIOD_END_DATE?.slice(2, 4)}` };
    const short = r.COMPANY_NAME?.includes('VULCAN') ? 'VMC' : r.COMPANY_NAME?.includes('MARTIN') ? 'MLM' : r.COMPANY_NAME?.includes('EAGLE') ? 'EXP' : null;
    if (short) trendByQtr[key][short] = r.REVENUE_B;
  });
  const trendChart = Object.values(trendByQtr).slice(-8);

  const avgPremium = premium.length > 0 ? (premium.reduce((s, p) => s + p.AVG_PRICE, 0) / premium.length) : 0;

  const competitiveAlerts = [
    { id: 1, severity: 'HIGH', company: 'Martin Marietta', event: 'Acquired 3 quarries in Georgia — expanding Southeast presence', date: '2026-03-28', type: 'M&A' },
    { id: 2, severity: 'MEDIUM', company: 'CRH', event: 'Announced $400M infrastructure investment in Texas operations', date: '2026-03-22', type: 'Expansion' },
    { id: 3, severity: 'LOW', company: 'Heidelberg', event: 'Q4 earnings beat: revenue +8% YoY, margins expanding', date: '2026-03-15', type: 'Earnings' },
    { id: 4, severity: 'MEDIUM', company: 'Eagle Materials', event: 'New ready-mix concrete plant approved near Dallas', date: '2026-03-10', type: 'Permit' },
    { id: 5, severity: 'HIGH', company: 'Martin Marietta', event: 'Aggressive pricing in Virginia — undercutting by ~4%', date: '2026-03-05', type: 'Pricing' },
    { id: 6, severity: 'LOW', company: 'Summit Materials', event: 'CEO transition announced — strategic review underway', date: '2026-02-28', type: 'Corporate' },
  ];

  const typeColors: Record<string, string> = { 'M&A': 'bg-red-500/20 text-red-400', Expansion: 'bg-amber-500/20 text-amber-400', Earnings: 'bg-green-500/20 text-green-400', Permit: 'bg-blue-500/20 text-blue-400', Pricing: 'bg-purple-500/20 text-purple-400', Corporate: 'bg-slate-500/20 text-slate-400' };
  const sevColors: Record<string, string> = { HIGH: 'border-red-500 bg-red-500/10', MEDIUM: 'border-amber-500 bg-amber-500/10', LOW: 'border-blue-500 bg-blue-500/10' };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Competitive Intelligence</h1>
        <p className="text-slate-400 mt-1">Quarry landscape, market position & competitor monitoring</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center gap-2 mb-2"><MapPin className="w-4 h-4 text-amber-400" /><span className="text-sm text-slate-400">Total Quarries Tracked</span></div>
          <p className="text-2xl font-bold">{totalQuarries.toLocaleString()}</p>
          <p className="text-xs text-slate-500 mt-1">MSHA active/intermittent</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center gap-2 mb-2"><Building2 className="w-4 h-4 text-amber-400" /><span className="text-sm text-slate-400">SnowCore Sites</span></div>
          <p className="text-2xl font-bold">{snowcoreTotal}</p>
          <p className="text-xs text-slate-500 mt-1">{totalQuarries > 0 ? ((snowcoreTotal / totalQuarries) * 100).toFixed(1) : 0}% market coverage</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center gap-2 mb-2"><Shield className="w-4 h-4 text-green-400" /><span className="text-sm text-slate-400">Avg Price (latest)</span></div>
          <p className="text-2xl font-bold text-green-400">${avgPremium.toFixed(2)}</p>
          <p className="text-xs text-slate-500 mt-1">across all regions</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center gap-2 mb-2"><AlertTriangle className="w-4 h-4 text-red-400" /><span className="text-sm text-slate-400">Active Alerts</span></div>
          <p className="text-2xl font-bold text-red-400">{competitiveAlerts.filter(a => a.severity === 'HIGH').length}</p>
          <p className="text-xs text-slate-500 mt-1">high severity events</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-slate-800 rounded-xl p-5 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Quarry Count by Region & Operator</h2>
            <select value={selectedRegion} onChange={e => setSelectedRegion(e.target.value)} className="bg-slate-700 text-sm rounded-lg px-3 py-1.5 border border-slate-600 focus:outline-none">
              <option value="all">All Regions</option>
              {regions.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={filteredQuarries}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="region" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="snowcore" name="SnowCore" fill="#f59e0b" stackId="a" />
                <Bar dataKey="mlm" name="MLM" fill="#3b82f6" stackId="a" />
                <Bar dataKey="heidelberg" name="Heidelberg" fill="#8b5cf6" stackId="a" />
                <Bar dataKey="crh" name="CRH" fill="#10b981" stackId="a" />
                <Bar dataKey="other" name="Other" fill="#64748b" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h2 className="font-semibold mb-4">National Market Share (by Sites)</h2>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={marketShare} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" paddingAngle={2}>
                  {marketShare.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-1 mt-2">
            {marketShare.map(m => (
              <div key={m.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: m.color }} /><span className="text-slate-300">{m.name}</span></div>
                <span className="text-slate-400">{m.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h2 className="font-semibold mb-1">Competitor Revenue Trend ($B quarterly)</h2>
          <p className="text-xs text-slate-400 mb-3">CRH is a $37B global company — US aggregates share is ~15%.</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="quarter" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} tickFormatter={v => `$${v}B`} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="VMC" stroke="#f59e0b" strokeWidth={2} name="SnowCore (VMC)" />
                <Line type="monotone" dataKey="MLM" stroke="#3b82f6" strokeWidth={2} name="Martin Marietta" />
                <Line type="monotone" dataKey="EXP" stroke="#10b981" strokeWidth={1.5} name="Eagle Materials" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h2 className="font-semibold mb-4">Regional Pricing</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="text-left p-2">Region</th>
                  <th className="text-right p-2">Avg Price</th>
                </tr>
              </thead>
              <tbody>
                {premium.map(r => (
                  <tr key={r.REGION_CODE} className="border-b border-slate-700/50">
                    <td className="p-2 font-medium">{r.REGION_NAME}</td>
                    <td className="p-2 text-right text-amber-400">${r.AVG_PRICE}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h2 className="font-semibold mb-4">Competitive Alerts</h2>
        <div className="space-y-3">
          {competitiveAlerts.map(alert => (
            <div key={alert.id} className={`p-3 rounded-lg border-l-4 ${sevColors[alert.severity]}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium">{alert.company}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${typeColors[alert.type]}`}>{alert.type}</span>
                  </div>
                  <p className="text-sm text-slate-300">{alert.event}</p>
                </div>
                <span className="text-xs text-slate-500 ml-2 whitespace-nowrap">{alert.date}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
