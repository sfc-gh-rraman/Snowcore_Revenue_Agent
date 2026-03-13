import { useState, useEffect } from 'react';
import { 
  Mountain, 
  Brain, 
  BarChart3, 
  Shield, 
  ArrowRight,
  Map,
  Sparkles,
  ChevronRight,
  TrendingUp,
  AlertTriangle,
  DollarSign,
  Activity,
  CloudRain,
  Truck
} from 'lucide-react';

const PLATFORM_NAME = "GRANITE";

const features = [
  {
    icon: Brain,
    title: 'Monte Carlo Forecasting',
    description: 'Probabilistic revenue projections across 13 scenario types. Infrastructure demand, weather disruptions, and commodity price shocks.',
    color: 'purple'
  },
  {
    icon: Shield,
    title: 'Risk Analytics',
    description: 'VaR analysis, stress testing across hurricane, recession, and supply chain scenarios. Regional exposure quantification.',
    color: 'red'
  },
  {
    icon: BarChart3,
    title: 'Scenario Comparison',
    description: 'Side-by-side scenario analysis with sensitivity sweeps. Compare base case vs. disaster scenarios instantly.',
    color: 'blue'
  },
  {
    icon: Activity,
    title: 'Real-time Intelligence',
    description: 'AI-powered Q&A over shipments, pricing, and macro indicators. Natural language access to your data.',
    color: 'green'
  }
];

const stats = [
  { value: '$7.9B', label: 'Annual Revenue', suffix: '' },
  { value: '227M', label: 'Tons Shipped', suffix: '' },
  { value: '$21.98', label: 'Avg Price/Ton', suffix: '' },
  { value: '13', label: 'Active Scenarios', suffix: '' },
];

interface LandingProps {
  onNavigate: (page: string) => void;
}

export default function Landing({ onNavigate }: LandingProps) {
  const [mounted, setMounted] = useState(false);
  const [typedText, setTypedText] = useState('');
  const fullText = `Hello, I'm ${PLATFORM_NAME}. Your intelligent revenue forecasting and scenario analysis platform.`;

  useEffect(() => {
    setMounted(true);
    
    let index = 0;
    const interval = setInterval(() => {
      if (index <= fullText.length) {
        setTypedText(fullText.slice(0, index));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 35);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 overflow-y-auto">
      <div className="relative">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>
        <div className="absolute inset-0 bg-gradient-to-b from-slate-900/50 via-transparent to-slate-900" />
        
        <div className="relative max-w-7xl mx-auto px-6 pt-16 pb-24">
          <div className={`text-center transition-all duration-1000 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <div className="relative inline-block mb-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center shadow-2xl shadow-amber-500/30">
                <Mountain size={40} className="text-slate-900" />
              </div>
              <div className="absolute inset-0 w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-600 blur-xl opacity-50" />
            </div>

            <h1 className="text-5xl font-bold mb-3">
              <span className="bg-gradient-to-r from-amber-400 via-orange-400 to-red-500 bg-clip-text text-transparent">
                {PLATFORM_NAME}
              </span>
            </h1>
            <p className="text-lg text-slate-400 mb-1">Vulcan Materials Revenue Intelligence</p>
            <p className="text-sm text-slate-500 mb-6">Monte Carlo Forecasting • Scenario Analysis • Powered by Snowflake Cortex</p>

            <div className="max-w-2xl mx-auto mb-10">
              <div className="bg-slate-800/80 backdrop-blur-sm border border-slate-700 rounded-xl p-5 text-left">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center flex-shrink-0">
                    <Sparkles size={20} className="text-slate-900" />
                  </div>
                  <div>
                    <p className="text-lg text-slate-200">
                      {typedText}
                      <span className="inline-block w-0.5 h-5 bg-amber-400 ml-1 animate-pulse" />
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-center gap-4">
              <button
                onClick={() => onNavigate('/')}
                className="group flex items-center gap-3 px-7 py-3.5 bg-gradient-to-r from-amber-500 to-orange-500 rounded-xl text-slate-900 font-semibold text-lg shadow-xl shadow-amber-500/25 hover:shadow-amber-500/40 hover:scale-105 transition-all"
              >
                Launch Mission Control
                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
              </button>
              <button
                onClick={() => onNavigate('/scenarios')}
                className="flex items-center gap-2 px-5 py-3.5 bg-slate-700/50 border border-slate-600 rounded-xl text-slate-300 font-medium hover:bg-slate-600/50 hover:border-slate-500 transition-all"
              >
                Run Scenarios
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className={`bg-slate-800/50 border-y border-slate-700/50 py-6 transition-all duration-1000 delay-300 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-4 gap-8">
            {stats.map((stat, i) => (
              <div key={i} className="text-center">
                <p className="text-3xl font-bold text-amber-400">
                  {stat.value}<span className="text-lg text-slate-400">{stat.suffix}</span>
                </p>
                <p className="text-sm text-slate-400 mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className={`text-center mb-10 transition-all duration-1000 delay-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          <h2 className="text-2xl font-bold text-slate-200 mb-3">Intelligent Revenue Analytics</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Unifying shipment data, commodity prices, and macro indicators with AI-powered scenario simulation.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-5">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            const colorClasses: Record<string, string> = {
              purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30 text-purple-400',
              green: 'from-green-500/20 to-green-600/10 border-green-500/30 text-green-400',
              blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30 text-blue-400',
              red: 'from-red-500/20 to-red-600/10 border-red-500/30 text-red-400',
            };
            const colorClass = colorClasses[feature.color];
            
            return (
              <div 
                key={i}
                className={`bg-gradient-to-br ${colorClass} border rounded-xl p-6 transition-all duration-500 hover:scale-[1.02] ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
                style={{ transitionDelay: `${600 + i * 100}ms` }}
              >
                <div className="w-11 h-11 rounded-xl bg-slate-800/80 flex items-center justify-center mb-4">
                  <Icon size={22} />
                </div>
                <h3 className="text-lg font-semibold text-slate-200 mb-2">{feature.title}</h3>
                <p className="text-slate-400 text-sm">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-4 gap-3">
          {([
            { icon: TrendingUp, label: 'Mission Control', page: '/', desc: 'Real-time KPIs & AI chat' },
            { icon: BarChart3, label: 'Scenarios', page: '/scenarios', desc: 'Monte Carlo simulation' },
            { icon: Activity, label: 'Sensitivity', page: '/sensitivity', desc: 'Parameter sweeps' },
            { icon: DollarSign, label: 'Revenue Deep Dive', page: '/revenue', desc: 'Regional breakdown' },
          ]).map((link, i) => {
            const Icon = link.icon;
            return (
              <button
                key={i}
                onClick={() => onNavigate(link.page)}
                className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 text-left group hover:border-amber-500/30 hover:bg-slate-800/80 transition-all"
              >
                <div className="flex items-center gap-3 mb-2">
                  <Icon size={18} className="text-amber-400" />
                  <span className="font-medium text-slate-200 group-hover:text-amber-400 transition-colors text-sm">
                    {link.label}
                  </span>
                  <ChevronRight size={14} className="text-slate-500 ml-auto group-hover:translate-x-1 transition-transform" />
                </div>
                <p className="text-xs text-slate-500">{link.desc}</p>
              </button>
            );
          })}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 pb-16">
        <div className={`bg-gradient-to-r from-amber-500/10 to-red-500/10 border border-amber-500/30 rounded-xl p-6 transition-all duration-1000 delay-700 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center flex-shrink-0">
              <AlertTriangle size={24} className="text-amber-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-amber-400 mb-2">Infrastructure Investment: IIJA Tailwinds</h3>
              <p className="text-slate-300 text-sm mb-3">
                The Infrastructure Investment & Jobs Act drives <strong className="text-white">$550B+ in new infrastructure spending</strong> through 2026.
                Vulcan's Sunbelt positioning captures highway, bridge, and data center construction demand.
              </p>
              <p className="text-slate-400 text-sm">
                Key markets: <strong className="text-amber-400">TX, FL, CA, GA, NC</strong> • 
                Revenue upside: <strong className="text-white">8-12% CAGR</strong> • 
                Pricing power: <strong className="text-green-400">+6-8% YoY</strong>
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 pb-16">
        <h3 className="text-lg font-semibold text-slate-300 mb-4">More Analytics</h3>
        <div className="grid grid-cols-6 gap-3">
          {([
            { icon: Map, label: 'Region Map', page: '/regions' },
            { icon: Truck, label: 'Shipments', page: '/shipments' },
            { icon: DollarSign, label: 'Pricing', page: '/pricing' },
            { icon: CloudRain, label: 'Weather Risk', page: '/weather' },
            { icon: Activity, label: 'Commodities', page: '/commodities' },
            { icon: Brain, label: 'Knowledge Base', page: '/knowledge' },
          ]).map((link, i) => {
            const Icon = link.icon;
            return (
              <button
                key={i}
                onClick={() => onNavigate(link.page)}
                className="bg-slate-800/30 border border-slate-700/30 rounded-lg p-3 text-center group hover:border-slate-600 hover:bg-slate-800/50 transition-all"
              >
                <Icon size={18} className="mx-auto mb-2 text-slate-400 group-hover:text-amber-400 transition-colors" />
                <span className="text-xs text-slate-400 group-hover:text-slate-300">{link.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="border-t border-slate-700/50 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-sm text-slate-500">
            Built on <span className="text-amber-400">Snowflake Cortex</span> • Cortex Agent • Cortex Analyst • Cortex Search
          </p>
        </div>
      </div>
    </div>
  );
}
