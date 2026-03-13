import { useState } from 'react';
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
import { Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const mockRegionStatus = [
  { regionCode: 'SOUTHEAST', regionName: 'Southeast', currentRevenue: 185.2, forecastRevenue: 182.0, variancePct: 1.8, pricePerTon: 22.50, status: 'STRONG', shipmentTons: 8.2 },
  { regionCode: 'SOUTHWEST', regionName: 'Southwest', currentRevenue: 142.5, forecastRevenue: 145.0, variancePct: -1.7, pricePerTon: 21.20, status: 'NORMAL', shipmentTons: 6.7 },
  { regionCode: 'WEST', regionName: 'West', currentRevenue: 98.3, forecastRevenue: 96.0, variancePct: 2.4, pricePerTon: 24.80, status: 'STRONG', shipmentTons: 4.0 },
  { regionCode: 'MIDAMERICA', regionName: 'Mid-America', currentRevenue: 62.1, forecastRevenue: 65.0, variancePct: -4.5, pricePerTon: 19.40, status: 'WEAK', shipmentTons: 3.2 },
];

const mockRevenueTrend = Array.from({ length: 12 }, (_, i) => ({
  month: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i],
  actual: 580 + Math.sin(i / 2) * 80 + Math.random() * 40,
  forecast: 580 + Math.sin(i / 2) * 80,
}));

const mockAlerts = [
  { id: 1, severity: 'HIGH', message: 'Hurricane watch in Gulf Coast - potential 15% shipment disruption', time: '14:32' },
  { id: 2, severity: 'MEDIUM', message: 'Natural gas prices up 12% - asphalt cost pressure expected', time: '14:15' },
  { id: 3, severity: 'LOW', message: 'Housing starts exceed forecast in Texas +8%', time: '13:45' },
];

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

function RegionStatusCard({ region }: { region: typeof mockRegionStatus[0] }) {
  const statusColors: Record<string, string> = {
    STRONG: 'bg-green-500',
    NORMAL: 'bg-amber-500',
    WEAK: 'bg-red-500',
  };

  return (
    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 hover:border-slate-600 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">{region.regionName}</h3>
        <span className={`w-2.5 h-2.5 rounded-full ${statusColors[region.status]}`} />
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-slate-400">Revenue</p>
          <p className="font-medium">${region.currentRevenue.toFixed(1)}M</p>
        </div>
        <div>
          <p className="text-slate-400">Price/Ton</p>
          <p className="font-medium">${region.pricePerTon.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-slate-400">Variance</p>
          <p className={`font-medium ${region.variancePct > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {region.variancePct > 0 ? '+' : ''}{region.variancePct}%
          </p>
        </div>
        <div>
          <p className="text-slate-400">Shipments</p>
          <p className="font-medium">{region.shipmentTons}M tons</p>
        </div>
      </div>
    </div>
  );
}

function AlertItem({ alert }: { alert: typeof mockAlerts[0] }) {
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
    { role: 'assistant', content: 'Hello! I\'m your Vulcan revenue analyst. Ask me about shipments, pricing, scenarios, or run simulations.' }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const [conversationId, setConversationId] = useState<string | null>(null);

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
        body: JSON.stringify({ 
          message: userMessage,
          conversation_id: conversationId
        })
      });
      
      if (!response.ok) throw new Error('Chat failed');
      
      const data = await response.json();
      setConversationId(data.conversation_id);
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error connecting to agent. Please check backend is running.`
      }]);
    }
    setIsLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Mission Control</h1>
          <p className="text-slate-400 mt-1">Vulcan Materials Revenue Intelligence</p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-slate-400">Live</span>
          <span className="text-slate-500">|</span>
          <span className="text-slate-300">{new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <KpiCard 
          title="YTD Revenue" 
          value="$5.82" 
          unit="B" 
          icon={DollarSign}
          trend="up"
          trendValue="+7.2%"
          color="amber"
        />
        <KpiCard 
          title="Shipments" 
          value="168.2" 
          unit="M tons" 
          icon={Truck}
          trend="up"
          trendValue="+3.1%"
          color="blue"
        />
        <KpiCard 
          title="Avg Price/Ton" 
          value="$21.98" 
          unit="" 
          icon={Activity}
          trend="up"
          trendValue="+6.2%"
          color="green"
        />
        <KpiCard 
          title="Active Alerts" 
          value="3" 
          unit="" 
          icon={AlertTriangle}
          color="red"
        />
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h2 className="font-semibold mb-4">Monthly Revenue - Last 12 Months ($M)</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={mockRevenueTrend}>
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
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(v: number) => [`$${v.toFixed(1)}M`, '']}
                />
                <Area type="monotone" dataKey="actual" stroke="#f59e0b" fill="url(#revenueGradient)" strokeWidth={2} name="Actual" />
                <Line type="monotone" dataKey="forecast" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" name="Forecast" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h2 className="font-semibold mb-4">Risk Alerts</h2>
          <div className="space-y-3">
            {mockAlerts.map(alert => (
              <AlertItem key={alert.id} alert={alert} />
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          <h2 className="font-semibold mb-4">Regional Performance</h2>
          <div className="grid grid-cols-2 gap-4">
            {mockRegionStatus.map(region => (
              <RegionStatusCard key={region.regionCode} region={region} />
            ))}
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
              <div key={i} className={`p-3 rounded-lg text-sm ${
                msg.role === 'user' 
                  ? 'bg-amber-600 ml-8' 
                  : 'bg-slate-700 mr-8'
              }`}>
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
              <button 
                onClick={handleChat}
                className="p-2 bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
