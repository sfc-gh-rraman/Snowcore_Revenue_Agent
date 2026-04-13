import { useState, useEffect } from 'react';
import { MapPin, TrendingUp, Building2, Truck, DollarSign } from 'lucide-react';
import { fetchRegionsDetail } from '../services/api';

export default function RegionMap() {
  const [regions, setRegions] = useState<any[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);

  useEffect(() => {
    fetchRegionsDetail().then(setRegions).catch(() => {});
  }, []);

  const currentRegion = selectedRegion ? regions.find(r => r.REGION_CODE === selectedRegion) : null;

  const statusColors: Record<string, string> = { strong: 'bg-green-500', normal: 'bg-amber-500', weak: 'bg-red-500' };
  const statusBorders: Record<string, string> = { strong: 'border-green-500/50 bg-green-500/10', normal: 'border-amber-500/50 bg-amber-500/10', weak: 'border-red-500/50 bg-red-500/10' };

  const getStatus = (r: any) => r.REVENUE_M > 200 ? 'strong' : r.REVENUE_M > 100 ? 'normal' : 'weak';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Regional Performance</h1>
        <p className="text-slate-400 mt-1">Geographic breakdown of revenue, operations, and market dynamics</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {regions.map((region) => {
          const status = getStatus(region);
          return (
            <button
              key={region.REGION_CODE}
              onClick={() => setSelectedRegion(selectedRegion === region.REGION_CODE ? null : region.REGION_CODE)}
              className={`p-4 rounded-xl border transition-all text-left ${selectedRegion === region.REGION_CODE ? 'border-amber-500 bg-amber-500/10' : 'border-slate-700 bg-slate-800 hover:border-slate-600'}`}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold">{region.REGION_NAME}</h3>
                <span className={`w-2.5 h-2.5 rounded-full ${statusColors[status]}`} />
              </div>
              <p className="text-2xl font-bold text-amber-400">${region.REVENUE_M}M</p>
              <p className="text-sm text-slate-400 mt-1">{region.TONS_M}M tons @ ${region.AVG_PRICE}/ton</p>
              <p className="text-xs text-slate-500 mt-2">{region.PLANT_COUNT} plants</p>
            </button>
          );
        })}
      </div>

      {currentRegion && (
        <div className={`rounded-xl border p-6 ${statusBorders[getStatus(currentRegion)]}`}>
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold">{currentRegion.REGION_NAME} Region</h2>
              <p className="text-slate-400">{currentRegion.REGION_CODE}</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-700">
              <span className={`w-2 h-2 rounded-full ${statusColors[getStatus(currentRegion)]}`} />
              <span className="text-sm capitalize">{getStatus(currentRegion)}</span>
            </div>
          </div>
          <div className="grid grid-cols-5 gap-4 mb-6">
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1"><DollarSign className="w-4 h-4" />Revenue</div>
              <p className="text-xl font-bold">${currentRegion.REVENUE_M}M</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1"><Truck className="w-4 h-4" />Volume</div>
              <p className="text-xl font-bold">{currentRegion.TONS_M}M<span className="text-sm text-slate-400"> tons</span></p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1"><TrendingUp className="w-4 h-4" />Price/Ton</div>
              <p className="text-xl font-bold">${currentRegion.AVG_PRICE}</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1"><Building2 className="w-4 h-4" />Plants</div>
              <p className="text-xl font-bold">{currentRegion.PLANT_COUNT}</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-slate-400 text-sm mb-1"><TrendingUp className="w-4 h-4" />Products</div>
              <p className="text-xl font-bold">{currentRegion.N_PRODUCTS}</p>
            </div>
          </div>
        </div>
      )}

      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-xl p-5">
        <div className="flex items-start gap-4">
          <MapPin className="w-5 h-5 text-blue-400 mt-1" />
          <div>
            <h4 className="font-semibold text-blue-400">Geographic Concentration</h4>
            <p className="text-sm text-slate-400 mt-1">
              SnowCore's Sunbelt strategy positions the company in high-growth markets.
              <strong className="text-white"> 6 operating regions</strong> covering the Southeast, Texas, Florida, California, Virginia, and Illinois —
              all benefiting from population migration, infrastructure investment, and data center construction.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
