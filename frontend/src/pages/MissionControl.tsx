import { useState, useEffect } from 'react';
import { 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle,
  DollarSign,
  MessageSquare,
  Send,
  Truck
} from 'lucide-react';
import { XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { fetchDashboardRegions, fetchRevenueTrend, fetchKpis } from '../services/api';

interface RegionData {
  REGION_CODE: string;
  REGION_NAME: string;
  CURRENT_REVENUE_M: number;
  PREV_REVENUE_M: number;
  VARIANCE_PCT: number;
  PRICE_PER_TON: number;
  SHIPMENT_TONS_M: number;
  STATUS: string;
}

interface TrendData {
  YEAR_MONTH: string;
  REVENUE_M: number;
  TONS_M: number;
  AVG_PRICE: number;
}

function KpiCard({ title, value, unit, icon: Icon, trend, trendValue, color = 'blue' }: {
  title: string;
  value: string;
  unit: string;
  icon: React.ElementType;
  trend?: 'up' | 'down';
  trendValue?: string;
  color?: string;
}) {
  const colors: Record<string, string> = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    amber: 'from-amber-500 to-amber-600',
    red: 'from-red-500 to-red-600',
  };

  return (
    <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-400 text-sm">{title}</p>
          <p className="text-2xl font-bold mt-1">
            {value}
            <span className="text-sm text-slate-400 ml-1">{unit}</span>
          </p>
        </div>
        <div className={`p-2.5 rounded-lg bg-gradient-to-br ${colors[color]}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      {trend && (
        <div className="flex items-center mt-3 text-sm">
          {trend === 'up' ? (
            <TrendingUp className="w-4 h-4 text-green-400 mr-1" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-400 mr-1" />
          )}
          <span className={trend === 'up' ? 'text-green-400' : 'text-red-400'}>
            {trendValue}
          </span>
          <span className="text-slate-500 ml-1">vs last month</span>
        </div>
      )}
    </div>
  );
}

function RegionStatusCard({ region }: { region: RegionData }) {
  const statusColors: Record<string, string> = {
    STRONG: 'bg-green-500',
    NORMAL: 'bg-amber-500',
    WEAK: 'bg-red-500',
  };

  return (
    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 hover:border-slate-600 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">{region.REGION_NAME}</h3>
        <span className={`w-2.5 h-2.5 rounded-full ${statusColors[region.STATUS] || 'bg-slate-500'}`} />
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-slate-400">Revenue</p>
          <p className="font-medium">${region.CURRENT_REVENUE_M}M</p>
        </div>
        <div>
          <p className="text-slate-400">Price/Ton</p>
          <p className="font-medium">${region.PRICE_PER_TON}</p>
        </div>
        <div>
          <p className="text-slate-400">Variance</p>
          <p className={`font-medium ${region.VARIANCE_PCT > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {region.VARIANCE_PCT > 0 ? '+' : ''}{region.VARIANCE_PCT}%
          </p>
        </div>
        <div>
          <p className="text-slate-400">Shipments</p>
          <p className="font-medium">{region.SHIPMENT_TONS_M}M tons</p>
        </div>
      </div>
    </div>
  );
}

function AlertItem({ alert }: { alert: { id: number; severity: string; message: string; time: string } }) {
  const severityColors: Record<string, string> = {
    HIGH: 'border-red-500 bg-red-500/10',
    MEDIUM: 'border-amber-500 bg-amber-500/10',
    LOW: 'border-blue-500 bg-blue-500/10',
  };

  return (
    <div className={`p-3 rounded-lg border-l-4 ${severityColors[alert.severity]}`}>
      <div className="flex items-start justify-between">
        <p className="text-sm">{alert.message}</p>
        <span className="text-xs text-slate-500 ml-2">{alert.time}</span>
      </div>
    </div>
  );
}

export default function MissionControl() {
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<{ role: string; content: string }[]>([
    { role: 'assistant', content: 'Hello! I\'m your SnowCore revenue analyst. Ask me about shipments, pricing, scenarios, or run simulations.' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const [regions, setRegions] = useState<RegionData[]>([]);
  const [trend, setTrend] = useState<TrendData[]>([]);
  const [kpis, setKpis] = useState<{ total_revenue: number; total_tons: number; avg_price: number; n_scenarios: number } | null>(null);
  const [alerts] = useState([
    { id: 1, severity: 'HIGH', message: 'Hurricane watch in Gulf Coast - potential 15% shipment disruption', time: '14:32' },
    { id: 2, severity: 'MEDIUM', message: 'Natural gas prices up 12% - asphalt cost pressure expected', time: '14:15' },
    { id: 3, severity: 'LOW', message: 'Housing starts exceed forecast in Texas +8%', time: '13:45' },
  ]);

  useEffect(() => {
    fetchDashboardRegions().then(setRegions).catch(() => {});
    fetchRevenueTrend().then(setTrend).catch(() => {});
    fetchKpis().then(setKpis).catch(() => {});
  }, []);

  const handleChat = async () => {
    if (!chatInput.trim()) return;
    const userMessage = chatInput;
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatInput('');
    setIsLoading(true);
    try {
      const response = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, conversation_id: conversationId })
      });
      if (!response.ok) throw new Error('Chat failed');
      const data = await response.json();
      setConversationId(data.conversation_id);
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error connecting to agent. Please check backend is running.' }]);
    }
    setIsLoading(false);
  };

  const trendChart = trend.map(t => ({
    month: new Date(t.YEAR_MONTH).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
    actual: t.REVENUE_M,
  }));

  const totalRevB = kpis ? (kpis.total_revenue / 1e9).toFixed(2) : '—';
  const totalTonsM = kpis ? (kpis.total_tons / 1e6).toFixed(1) : '—';
  const avgPrice = kpis ? `$${kpis.avg_price.toFixed(2)}` : '—';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Mission Control</h1>
          <p className="text-slate-400 mt-1">SnowCore Materials Revenue Intelligence</p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-slate-400">Live</span>
          <span className="text-slate-500">|</span>
          <span className="text-slate-300">{new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <KpiCard title="Total Revenue" value={`$${totalRevB}`} unit="B" icon={DollarSign} color="amber" />
        <KpiCard title="Total Shipments" value={totalTonsM} unit="M tons" icon={Truck} color="blue" />
        <KpiCard title="Avg Price/Ton" value={avgPrice} unit="" icon={Activity} color="green" />
        <KpiCard title="Active Alerts" value={String(alerts.length)} unit="" icon={AlertTriangle} color="red" />
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h2 className="font-semibold mb-4">Monthly Revenue Trend ($M)</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendChart}>
                <defs>
                  <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `$${v}`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  formatter={(v: number) => [`$${v.toFixed(1)}M`, 'Revenue']}
                />
                <Area type="monotone" dataKey="actual" stroke="#f59e0b" fill="url(#revenueGradient)" strokeWidth={2} name="Actual" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h2 className="font-semibold mb-4">Risk Alerts</h2>
          <div className="space-y-3">
            {alerts.map(alert => (
              <AlertItem key={alert.id} alert={alert} />
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          <h2 className="font-semibold mb-4">Regional Performance</h2>
          <div className="grid grid-cols-2 gap-4">
            {regions.length > 0 ? regions.map(region => (
              <RegionStatusCard key={region.REGION_CODE} region={region} />
            )) : (
              <div className="col-span-2 text-center text-slate-500 py-8">Loading regions...</div>
            )}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl border border-slate-700 flex flex-col">
          <div className="p-4 border-b border-slate-700">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-amber-400" />
              <h2 className="font-semibold">AI Revenue Analyst</h2>
            </div>
          </div>
          <div className="flex-1 p-4 space-y-3 overflow-y-auto max-h-64">
            {chatMessages.map((msg, i) => (
              <div key={i} className={`p-3 rounded-lg text-sm ${msg.role === 'user' ? 'bg-amber-600 ml-8' : 'bg-slate-700 mr-8'}`}>
                {msg.content}
              </div>
            ))}
            {isLoading && (
              <div className="bg-slate-700 mr-8 p-3 rounded-lg text-sm">
                <span className="animate-pulse">Thinking...</span>
              </div>
            )}
          </div>
          <div className="p-4 border-t border-slate-700">
            <div className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleChat()}
                placeholder="Ask about revenue, scenarios..."
                className="flex-1 bg-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
              <button onClick={handleChat} className="p-2 bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors">
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
