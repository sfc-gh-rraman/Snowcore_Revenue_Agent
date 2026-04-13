import { useState, useEffect } from 'react';
import { ArrowUpRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { fetchMonthlyRevenue, fetchRevenueBySegment, fetchRevenueByRegion, fetchPriceHistory, fetchKpis } from '../services/api';

const SEGMENT_COLORS: Record<string, string> = {
  AGGREGATES: '#f59e0b',
  ASPHALT: '#3b82f6',
  CONCRETE: '#10b981',
  SERVICE: '#8b5cf6',
};

export default function RevenueDeepDive() {
  const [timeframe, setTimeframe] = useState('ytd');
  const [monthly, setMonthly] = useState<any[]>([]);
  const [segments, setSegments] = useState<any[]>([]);
  const [regions, setRegions] = useState<any[]>([]);
  const [prices, setPrices] = useState<any[]>([]);
  const [kpis, setKpis] = useState<any>(null);

  useEffect(() => {
    fetchMonthlyRevenue().then(setMonthly).catch(() => {});
    fetchRevenueBySegment().then(setSegments).catch(() => {});
    fetchRevenueByRegion().then(setRegions).catch(() => {});
    fetchPriceHistory().then(setPrices).catch(() => {});
    fetchKpis().then(setKpis).catch(() => {});
  }, []);

  const monthlyChart = monthly.map(m => ({
    month: new Date(m.YEAR_MONTH).toLocaleDateString('en-US', { month: 'short' }),
    revenue: m.REVENUE_M,
  }));

  const segChart = segments.map((s, i) => ({
    name: s.SEGMENT_NAME,
    value: s.REVENUE_M,
    pct: s.PCT,
    color: Object.values(SEGMENT_COLORS)[i % 4],
  }));

  const stoneHistory = prices
    .filter(p => p.PRODUCT_SEGMENT_CODE === 'AGG_STONE')
    .map(p => ({
      month: new Date(p.YEAR_MONTH).toLocaleDateString('en-US', { month: 'short' }),
      aggregates: p.AVG_PRICE,
    }));

  const totalRevB = kpis ? `$${(kpis.total_revenue / 1e9).toFixed(1)}B` : '—';
  const avgPrice = kpis ? `$${kpis.avg_price.toFixed(2)}` : '—';
  const totalTonsM = kpis ? `${(kpis.total_tons / 1e6).toFixed(0)}M` : '—';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Revenue Deep Dive</h1>
          <p className="text-slate-400 mt-1">Comprehensive revenue analysis by segment, region, and end market</p>
        </div>
        <div className="flex items-center gap-2">
          {['ytd', 'q4', 'q3', '12m'].map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                timeframe === tf ? 'bg-amber-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {tf.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-amber-500/20 to-amber-600/10 rounded-xl p-5 border border-amber-500/30">
          <p className="text-slate-400 text-sm">Total Revenue</p>
          <p className="text-3xl font-bold text-amber-400 mt-1">{totalRevB}</p>
          <div className="flex items-center mt-2 text-sm text-green-400">
            <ArrowUpRight className="w-4 h-4 mr-1" />
            All-time
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <p className="text-slate-400 text-sm">Avg Price/Ton</p>
          <p className="text-3xl font-bold mt-1">{avgPrice}</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <p className="text-slate-400 text-sm">Volume Shipped</p>
          <p className="text-3xl font-bold mt-1">{totalTonsM}<span className="text-lg text-slate-400"> tons</span></p>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <p className="text-slate-400 text-sm">Segments</p>
          <p className="text-3xl font-bold mt-1">{segments.length}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">Monthly Revenue ($M)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyChart}>
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `$${v}`} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} formatter={(v: number) => [`$${v}M`, 'Revenue']} />
                <Bar dataKey="revenue" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">Revenue by Segment</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={segChart} cx="50%" cy="50%" innerRadius={50} outerRadius={70} dataKey="value" label={({ name, pct }) => `${name}: ${pct}%`} labelLine={false}>
                  {segChart.map((entry, index) => (<Cell key={index} fill={entry.color} />))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} formatter={(v: number) => [`$${v}M`, '']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {segChart.map((seg) => (
              <div key={seg.name} className="flex items-center gap-2 text-sm">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: seg.color }} />
                <span className="text-slate-400">{seg.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">Revenue by Region</h3>
          <div className="space-y-3">
            {regions.map((region) => (
              <div key={region.REGION_CODE} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                <div>
                  <p className="font-medium">{region.REGION_NAME}</p>
                  <p className="text-sm text-slate-400">{region.TONS_M}M tons @ ${region.AVG_PRICE}/ton</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-amber-400">${region.REVENUE_M}M</p>
                  <p className="text-sm text-slate-400">{region.PCT}% share</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">Price Trends — Crushed Stone ($/ton)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stoneHistory}>
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `$${v.toFixed(0)}`} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} formatter={(v: number) => [`$${v.toFixed(2)}`, '']} />
                <Line type="monotone" dataKey="aggregates" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b', r: 4 }} name="Crushed Stone $/ton" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
