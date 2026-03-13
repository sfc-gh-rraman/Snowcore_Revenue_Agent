import { useState } from 'react';
import { 
  MapPin, 
  TrendingUp, 
  Building2,
  Truck,
  DollarSign,
  AlertTriangle
} from 'lucide-react';

const regions = [
  { 
    id: 'southeast', 
    name: 'Southeast', 
    states: ['FL', 'GA', 'AL', 'SC', 'NC', 'TN', 'VA'],
    revenue: 2850,
    volume: 126.7,
    pricePerTon: 22.50,
    growth: 8.2,
    plants: 145,
    status: 'strong',
    highlights: ['IIJA highway projects accelerating', 'Florida data center boom', 'Strong residential in GA/NC'],
    risks: ['Hurricane exposure', 'Labor shortages in FL']
  },
  { 
    id: 'southwest', 
    name: 'Southwest', 
    states: ['TX', 'AZ', 'NM', 'OK'],
    revenue: 2120,
    volume: 100.0,
    pricePerTon: 21.20,
    growth: 6.5,
    plants: 98,
    status: 'normal',
    highlights: ['Texas infrastructure spending up 15%', 'Phoenix metro expansion', 'Data center growth in Dallas'],
    risks: ['Extreme heat disruptions', 'Water availability concerns']
  },
  { 
    id: 'west', 
    name: 'West', 
    states: ['CA', 'NV', 'CO', 'UT'],
    revenue: 1580,
    volume: 63.7,
    pricePerTon: 24.80,
    growth: 9.1,
    plants: 72,
    status: 'strong',
    highlights: ['California HSR project phases', 'Nevada data center corridor', 'Premium pricing power'],
    risks: ['Permitting delays in CA', 'Wildfire season disruptions']
  },
  { 
    id: 'midamerica', 
    name: 'Mid-America', 
    states: ['IL', 'MO', 'KS', 'AR', 'LA'],
    revenue: 1350,
    volume: 69.6,
    pricePerTon: 19.40,
    growth: 4.2,
    plants: 65,
    status: 'weak',
    highlights: ['Mississippi River infrastructure', 'Stable municipal demand'],
    risks: ['Slower economic growth', 'Flooding risk along rivers', 'Competitive pressure']
  },
];

const stateDetails = [
  { state: 'TX', revenue: 1250, volume: 58.5, growth: 7.8 },
  { state: 'FL', revenue: 980, volume: 42.3, growth: 9.2 },
  { state: 'CA', revenue: 920, volume: 35.2, growth: 8.5 },
  { state: 'GA', revenue: 680, volume: 31.5, growth: 7.1 },
  { state: 'AZ', revenue: 520, volume: 25.8, growth: 11.2 },
  { state: 'NC', revenue: 480, volume: 22.4, growth: 6.8 },
  { state: 'TN', revenue: 420, volume: 19.8, growth: 5.9 },
  { state: 'VA', revenue: 380, volume: 17.2, growth: 4.5 },
];

export default function RegionMap() {
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);

  const currentRegion = selectedRegion ? regions.find(r => r.id === selectedRegion) : null;

  const statusColors: Record<string, string> = {
    strong: 'bg-green-500',
    normal: 'bg-amber-500',
    weak: 'bg-red-500',
  };

  const statusBorders: Record<string, string> = {
    strong: 'border-green-500/50 bg-green-500/10',
    normal: 'border-amber-500/50 bg-amber-500/10',
    weak: 'border-red-500/50 bg-red-500/10',
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Regional Performance</h1>
        <p className="text-slate-400 mt-1">Geographic breakdown of revenue, operations, and market dynamics</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {regions.map((region) => (
          <button
            key={region.id}
            onClick={() => setSelectedRegion(selectedRegion === region.id ? null : region.id)}
            className={`p-4 rounded-xl border transition-all text-left ${
              selectedRegion === region.id 
                ? 'border-amber-500 bg-amber-500/10' 
                : 'border-slate-700 bg-slate-800 hover:border-slate-600'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">{region.name}</h3>
              <span className={`w-2.5 h-2.5 rounded-full ${statusColors[region.status]}`} />
            </div>
            <p className="text-2xl font-bold text-amber-400">${(region.revenue / 1000).toFixed(2)}B</p>
            <p className={`text-sm mt-1 ${region.growth > 6 ? 'text-green-400' : 'text-slate-400'}`}>
              {region.growth > 0 ? '+' : ''}{region.growth}% YoY
            </p>
            <p className="text-xs text-slate-500 mt-2">{region.states.join(', ')}</p>
          </button>
        ))}
      </div>

      {currentRegion && (
        <div className={`rounded-xl border p-6 ${statusBorders[currentRegion.status]}`}>
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold">{currentRegion.name} Region</h2>
              <p className="text-slate-400">{currentRegion.states.join(', ')}</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-700">
              <span className={`w-2 h-2 rounded-full ${statusColors[currentRegion.status]}`} />
              <span className="text-sm capitalize">{currentRegion.status}</span>
            </div>
          </div>

          <div className="grid grid-cols-5 gap-4 mb-6">
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                <DollarSign className="w-4 h-4" />
                Revenue
              </div>
              <p className="text-xl font-bold">${(currentRegion.revenue / 1000).toFixed(2)}B</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                <Truck className="w-4 h-4" />
                Volume
              </div>
              <p className="text-xl font-bold">{currentRegion.volume}M<span className="text-sm text-slate-400"> tons</span></p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                <TrendingUp className="w-4 h-4" />
                Price/Ton
              </div>
              <p className="text-xl font-bold">${currentRegion.pricePerTon}</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                <Building2 className="w-4 h-4" />
                Plants
              </div>
              <p className="text-xl font-bold">{currentRegion.plants}</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                <TrendingUp className="w-4 h-4" />
                Growth
              </div>
              <p className={`text-xl font-bold ${currentRegion.growth > 6 ? 'text-green-400' : ''}`}>
                +{currentRegion.growth}%
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-400" />
                Key Highlights
              </h4>
              <ul className="space-y-2">
                {currentRegion.highlights.map((h, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400 mt-2" />
                    <span className="text-slate-300">{h}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Risk Factors
              </h4>
              <ul className="space-y-2">
                {currentRegion.risks.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-2" />
                    <span className="text-slate-300">{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h3 className="font-semibold mb-4">Top States by Revenue</h3>
        <div className="grid grid-cols-4 gap-4">
          {stateDetails.map((state) => (
            <div key={state.state} className="bg-slate-700/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-lg font-bold">{state.state}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  state.growth > 8 ? 'bg-green-500/20 text-green-400' : 'bg-slate-600 text-slate-400'
                }`}>
                  +{state.growth}%
                </span>
              </div>
              <p className="text-xl font-bold text-amber-400">${state.revenue}M</p>
              <p className="text-sm text-slate-400">{state.volume}M tons</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-xl p-5">
        <div className="flex items-start gap-4">
          <MapPin className="w-5 h-5 text-blue-400 mt-1" />
          <div>
            <h4 className="font-semibold text-blue-400">Geographic Concentration</h4>
            <p className="text-sm text-slate-400 mt-1">
              Vulcan's Sunbelt strategy positions the company in high-growth markets. 
              <strong className="text-white"> 75% of revenue</strong> comes from Texas, Florida, California, and Georgia - 
              all benefiting from population migration, infrastructure investment, and data center construction.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
