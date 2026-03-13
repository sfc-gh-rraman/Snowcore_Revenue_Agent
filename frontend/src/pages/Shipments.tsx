import { useState } from 'react';
import { 
  Truck, 
  MapPin,
  Package,
  Clock
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Line } from 'recharts';

const monthlyShipments = [
  { month: 'Jan', tons: 16.2, trucks: 142000 },
  { month: 'Feb', tons: 15.8, trucks: 138000 },
  { month: 'Mar', tons: 19.5, trucks: 171000 },
  { month: 'Apr', tons: 21.2, trucks: 186000 },
  { month: 'May', tons: 22.8, trucks: 200000 },
  { month: 'Jun', tons: 21.5, trucks: 189000 },
  { month: 'Jul', tons: 20.8, trucks: 182000 },
  { month: 'Aug', tons: 19.2, trucks: 168000 },
  { month: 'Sep', tons: 18.5, trucks: 162000 },
  { month: 'Oct', tons: 17.8, trucks: 156000 },
  { month: 'Nov', tons: 16.5, trucks: 145000 },
  { month: 'Dec', tons: 14.2, trucks: 124000 },
];

const productMix = [
  { product: 'Crushed Stone', tons: 145.2, pct: 64, avgHaul: 32 },
  { product: 'Sand & Gravel', tons: 52.8, pct: 23, avgHaul: 28 },
  { product: 'Asphalt Mix', tons: 18.5, pct: 8, avgHaul: 45 },
  { product: 'Ready-Mix Concrete', tons: 10.5, pct: 5, avgHaul: 15 },
];

const regionalShipments = [
  { region: 'Southeast', tons: 91.2, growth: 5.2, onTime: 94.2 },
  { region: 'Southwest', tons: 68.5, growth: 3.8, onTime: 92.8 },
  { region: 'West', tons: 42.3, growth: 7.1, onTime: 91.5 },
  { region: 'Mid-America', tons: 25.0, growth: 1.2, onTime: 95.1 },
];

const recentShipments = [
  { id: 'SH-284521', customer: 'TX DOT Highway 45', product: 'Crushed Stone', tons: 2450, status: 'delivered', time: '2h ago' },
  { id: 'SH-284520', customer: 'Turner Construction', product: 'Ready-Mix', tons: 180, status: 'in-transit', time: '3h ago' },
  { id: 'SH-284519', customer: 'FL Turnpike Auth', product: 'Asphalt Mix', tons: 890, status: 'delivered', time: '4h ago' },
  { id: 'SH-284518', customer: 'Meta Data Center', product: 'Crushed Stone', tons: 3200, status: 'delivered', time: '5h ago' },
  { id: 'SH-284517', customer: 'Lennar Homes', product: 'Sand & Gravel', tons: 420, status: 'loading', time: '6h ago' },
];

const weeklyTrend = Array.from({ length: 8 }, (_, i) => ({
  week: `W${i + 1}`,
  actual: 4.2 + Math.random() * 0.8,
  forecast: 4.5,
}));

export default function Shipments() {
  const [view, setView] = useState<'volume' | 'logistics'>('volume');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Shipments Analysis</h1>
          <p className="text-slate-400 mt-1">Volume tracking, logistics performance, and delivery metrics</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setView('volume')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              view === 'volume' ? 'bg-amber-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Volume
          </button>
          <button
            onClick={() => setView('logistics')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              view === 'logistics' ? 'bg-amber-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Logistics
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 rounded-xl p-5 border border-blue-500/30">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
            <Package className="w-4 h-4" />
            YTD Volume
          </div>
          <p className="text-3xl font-bold text-blue-400">227M<span className="text-lg text-slate-400"> tons</span></p>
          <p className="text-sm text-green-400 mt-1">+3.1% vs LY</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
            <Truck className="w-4 h-4" />
            Truck Loads
          </div>
          <p className="text-3xl font-bold">1.98M</p>
          <p className="text-sm text-slate-400 mt-1">~115 tons/load avg</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
            <Clock className="w-4 h-4" />
            On-Time Delivery
          </div>
          <p className="text-3xl font-bold text-green-400">93.4%</p>
          <p className="text-sm text-slate-400 mt-1">Target: 95%</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
            <MapPin className="w-4 h-4" />
            Avg Haul Distance
          </div>
          <p className="text-3xl font-bold">31<span className="text-lg text-slate-400"> mi</span></p>
          <p className="text-sm text-slate-400 mt-1">+2.3 mi vs LY</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">Monthly Shipment Volume (M tons)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlyShipments}>
                <defs>
                  <linearGradient id="shipmentGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  formatter={(v: number, name: string) => [
                    name === 'tons' ? `${v}M tons` : `${(v/1000).toFixed(0)}K loads`,
                    name === 'tons' ? 'Volume' : 'Truck Loads'
                  ]}
                />
                <Area type="monotone" dataKey="tons" stroke="#3b82f6" fill="url(#shipmentGradient)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">Product Mix</h3>
          <div className="space-y-4">
            {productMix.map((product) => (
              <div key={product.product}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">{product.product}</span>
                  <span className="text-sm font-medium">{product.tons}M tons</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full" 
                    style={{ width: `${product.pct}%` }}
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">{product.pct}% • Avg haul: {product.avgHaul} mi</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">Regional Volume</h3>
          <div className="space-y-3">
            {regionalShipments.map((region) => (
              <div key={region.region} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                <div>
                  <p className="font-medium">{region.region}</p>
                  <p className="text-sm text-slate-400">On-time: {region.onTime}%</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-blue-400">{region.tons}M tons</p>
                  <p className={`text-sm ${region.growth > 3 ? 'text-green-400' : 'text-slate-400'}`}>
                    +{region.growth}% YoY
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">Recent Shipments</h3>
          <div className="space-y-3">
            {recentShipments.map((shipment) => (
              <div key={shipment.id} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">{shipment.id}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      shipment.status === 'delivered' ? 'bg-green-500/20 text-green-400' :
                      shipment.status === 'in-transit' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-amber-500/20 text-amber-400'
                    }`}>
                      {shipment.status}
                    </span>
                  </div>
                  <p className="text-sm font-medium mt-1">{shipment.customer}</p>
                  <p className="text-xs text-slate-400">{shipment.product}</p>
                </div>
                <div className="text-right">
                  <p className="font-medium">{shipment.tons.toLocaleString()} tons</p>
                  <p className="text-xs text-slate-500">{shipment.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h3 className="font-semibold mb-4">Weekly Volume vs Forecast (M tons)</h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weeklyTrend}>
              <XAxis dataKey="week" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} domain={[3.5, 5.5]} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                formatter={(v: number) => [`${v.toFixed(2)}M tons`, '']}
              />
              <Bar dataKey="actual" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Actual" />
              <Line type="monotone" dataKey="forecast" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" name="Forecast" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
