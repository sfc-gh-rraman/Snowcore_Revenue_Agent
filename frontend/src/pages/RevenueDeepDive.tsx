import { useState } from 'react';
import { ArrowUpRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

const monthlyRevenue = [
  { month: 'Jan', revenue: 520, yoy: 5.2 },
  { month: 'Feb', revenue: 485, yoy: 4.8 },
  { month: 'Mar', revenue: 610, yoy: 7.1 },
  { month: 'Apr', revenue: 680, yoy: 8.2 },
  { month: 'May', revenue: 720, yoy: 6.5 },
  { month: 'Jun', revenue: 695, yoy: 5.9 },
  { month: 'Jul', revenue: 710, yoy: 7.3 },
  { month: 'Aug', revenue: 685, yoy: 6.1 },
  { month: 'Sep', revenue: 640, yoy: 5.4 },
  { month: 'Oct', revenue: 590, yoy: 4.2 },
  { month: 'Nov', revenue: 545, yoy: 3.8 },
  { month: 'Dec', revenue: 480, yoy: 2.9 },
];

const segmentData = [
  { name: 'Aggregates', value: 4200, pct: 53, color: '#f59e0b' },
  { name: 'Asphalt', value: 1850, pct: 23, color: '#3b82f6' },
  { name: 'Concrete', value: 1420, pct: 18, color: '#10b981' },
  { name: 'Other', value: 430, pct: 6, color: '#8b5cf6' },
];

const regionRevenue = [
  { region: 'Southeast', revenue: 2850, growth: 8.2, pricePerTon: 22.50, volume: 126.7 },
  { region: 'Southwest', revenue: 2120, growth: 6.5, pricePerTon: 21.20, volume: 100.0 },
  { region: 'West', revenue: 1580, growth: 9.1, pricePerTon: 24.80, volume: 63.7 },
  { region: 'Mid-America', revenue: 1350, growth: 4.2, pricePerTon: 19.40, volume: 69.6 },
];

const endMarkets = [
  { market: 'Highway & Infrastructure', revenue: 3200, pct: 40, trend: 'up', change: 12.5 },
  { market: 'Residential Construction', revenue: 1840, pct: 23, trend: 'down', change: -3.2 },
  { market: 'Non-residential', revenue: 1520, pct: 19, trend: 'up', change: 5.8 },
  { market: 'Data Centers', revenue: 720, pct: 9, trend: 'up', change: 45.2 },
  { market: 'Other Private', revenue: 620, pct: 8, trend: 'flat', change: 1.1 },
];

const priceHistory = Array.from({ length: 12 }, (_, i) => ({
  month: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i],
  aggregates: 20.50 + i * 0.15 + Math.random() * 0.3,
  asphalt: 85 + i * 0.8 + Math.random() * 2,
  concrete: 125 + i * 0.5 + Math.random() * 3,
}));

export default function RevenueDeepDive() {
  const [timeframe, setTimeframe] = useState('ytd');

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
                timeframe === tf
                  ? 'bg-amber-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
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
          <p className="text-3xl font-bold text-amber-400 mt-1">$7.9B</p>
          <div className="flex items-center mt-2 text-sm text-green-400">
            <ArrowUpRight className="w-4 h-4 mr-1" />
            +7.2% YoY
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <p className="text-slate-400 text-sm">Avg Price/Ton</p>
          <p className="text-3xl font-bold mt-1">$21.98</p>
          <div className="flex items-center mt-2 text-sm text-green-400">
            <ArrowUpRight className="w-4 h-4 mr-1" />
            +6.2% YoY
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <p className="text-slate-400 text-sm">Volume Shipped</p>
          <p className="text-3xl font-bold mt-1">227M<span className="text-lg text-slate-400"> tons</span></p>
          <div className="flex items-center mt-2 text-sm text-green-400">
            <ArrowUpRight className="w-4 h-4 mr-1" />
            +3.1% YoY
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <p className="text-slate-400 text-sm">Gross Margin</p>
          <p className="text-3xl font-bold mt-1">28.4%</p>
          <div className="flex items-center mt-2 text-sm text-green-400">
            <ArrowUpRight className="w-4 h-4 mr-1" />
            +180 bps
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">Monthly Revenue ($M)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyRevenue}>
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `$${v}`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  formatter={(v: number) => [`$${v}M`, 'Revenue']}
                />
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
                <Pie
                  data={segmentData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  dataKey="value"
                  label={({ name, pct }) => `${name}: ${pct}%`}
                  labelLine={false}
                >
                  {segmentData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  formatter={(v: number) => [`$${v}M`, '']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {segmentData.map((seg) => (
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
            {regionRevenue.map((region) => (
              <div key={region.region} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                <div>
                  <p className="font-medium">{region.region}</p>
                  <p className="text-sm text-slate-400">{region.volume}M tons @ ${region.pricePerTon}/ton</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-amber-400">${(region.revenue / 1000).toFixed(2)}B</p>
                  <p className={`text-sm ${region.growth > 5 ? 'text-green-400' : 'text-slate-400'}`}>
                    +{region.growth}% YoY
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">End Market Mix</h3>
          <div className="space-y-3">
            {endMarkets.map((market) => (
              <div key={market.market} className="p-3 bg-slate-700/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-medium text-sm">{market.market}</p>
                  <div className="flex items-center gap-2">
                    <span className="font-bold">${(market.revenue / 1000).toFixed(1)}B</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      market.trend === 'up' ? 'bg-green-500/20 text-green-400' :
                      market.trend === 'down' ? 'bg-red-500/20 text-red-400' :
                      'bg-slate-600 text-slate-400'
                    }`}>
                      {market.change > 0 ? '+' : ''}{market.change}%
                    </span>
                  </div>
                </div>
                <div className="w-full bg-slate-600 rounded-full h-2">
                  <div 
                    className="bg-amber-500 h-2 rounded-full" 
                    style={{ width: `${market.pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h3 className="font-semibold mb-4">Price Trends ($/ton for Aggregates)</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={priceHistory}>
              <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `$${v.toFixed(0)}`} domain={[19, 23]} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                formatter={(v: number) => [`$${v.toFixed(2)}`, '']}
              />
              <Line type="monotone" dataKey="aggregates" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b', r: 4 }} name="Aggregates $/ton" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
