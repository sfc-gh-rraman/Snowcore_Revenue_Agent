import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  AreaChart, Area, CartesianGrid, Legend 
} from 'recharts';
import { fetchElasticity, fetchCrossElasticity, fetchDemandDrivers, fetchVolumeHistory } from '../services/api';

function ElasticityCard({ product, elasticity, rSquared, classification, color }: {
  product: string; elasticity: number; rSquared: number; classification: string; color: string;
}) {
  const isElastic = Math.abs(elasticity) > 1;
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-400">{product}</span>
        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold">{elasticity.toFixed(2)}</span>
        {elasticity > 0 ? <TrendingUp className="w-4 h-4 text-green-400" /> : <TrendingDown className="w-4 h-4 text-red-400" />}
      </div>
      <div className="flex items-center justify-between mt-2">
        <span className={`text-xs px-2 py-0.5 rounded-full ${isElastic ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
          {classification}
        </span>
        <span className={`text-xs ${rSquared > 0.5 ? 'text-slate-400' : 'text-amber-400'}`}>R² = {rSquared.toFixed(2)}</span>
      </div>
    </div>
  );
}

const PRODUCT_COLORS: Record<string, string> = {
  AGG_STONE: '#f59e0b', AGG_SAND: '#3b82f6', ASPHALT_MIX: '#10b981',
  CONCRETE_RMX: '#8b5cf6', AGG_SPECIALTY: '#ec4899', SERVICE_LOGISTICS: '#06b6d4',
};

export default function DemandSensing() {
  const [elasticity, setElasticity] = useState<any[]>([]);
  const [crossMatrix, setCrossMatrix] = useState<any[]>([]);
  const [drivers, setDrivers] = useState<any[]>([]);
  const [volumeHistory, setVolumeHistory] = useState<any[]>([]);

  useEffect(() => {
    fetchElasticity().then(setElasticity).catch(() => {});
    fetchCrossElasticity().then(setCrossMatrix).catch(() => {});
    fetchDemandDrivers().then(setDrivers).catch(() => {});
    fetchVolumeHistory().then(setVolumeHistory).catch(() => {});
  }, []);

  const products = ['AGG_STONE', 'AGG_SAND', 'AGG_SPECIALTY', 'ASPHALT_MIX', 'CONCRETE_RMX', 'SERVICE_LOGISTICS'];
  const shortNames: Record<string, string> = {
    AGG_STONE: 'Stone', AGG_SAND: 'Sand', AGG_SPECIALTY: 'Specialty',
    ASPHALT_MIX: 'Asphalt', CONCRETE_RMX: 'Concrete', SERVICE_LOGISTICS: 'Service',
  };

  const getCellColor = (val: number, isDiag: boolean) => {
    if (isDiag) return 'bg-slate-600 text-white';
    if (Math.abs(val) < 0.5) return 'bg-slate-700/50 text-slate-500';
    if (val > 2) return 'bg-green-600/60 text-green-200';
    if (val > 0) return 'bg-green-600/30 text-green-300';
    if (val < -2) return 'bg-red-600/40 text-red-300';
    return 'bg-red-600/20 text-red-400';
  };

  const driverChart = drivers.map(d => ({
    month: new Date(d.YEAR_MONTH).toLocaleDateString('en-US', { year: '2-digit', month: 'short' }),
    volume: d.VOLUME_M,
    highway: d.HIGHWAY_SPEND_B,
    construction: d.CONSTRUCTION_SPEND_B,
  }));

  const volChart = volumeHistory.map(v => {
    const dt = new Date(v.YEAR_MONTH);
    const isHistory = dt < new Date('2026-01-01');
    return {
      month: dt.toLocaleDateString('en-US', { year: '2-digit', month: 'short' }),
      actual: isHistory ? v.VOLUME_M : undefined,
      p50: !isHistory ? v.VOLUME_M : undefined,
    };
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Demand Sensing</h1>
        <p className="text-slate-400 mt-1">Price elasticity, demand drivers & volume forecasts</p>
      </div>

      <div>
        <h2 className="font-semibold mb-3 flex items-center gap-2">
          Own-Price Elasticity by Product
          <span className="text-xs text-slate-500 font-normal">|e| {'<'} 1 = pricing power · |e| {'>'} 1 = volume risk</span>
        </h2>
        <div className="grid grid-cols-3 gap-4">
          {elasticity.map(e => (
            <ElasticityCard
              key={e.PRODUCT_SEGMENT_CODE}
              product={e.SEGMENT_NAME}
              elasticity={e.OWN_ELASTICITY}
              rSquared={e.R_SQUARED}
              classification={e.CLASSIFICATION}
              color={PRODUCT_COLORS[e.PRODUCT_SEGMENT_CODE] || '#64748b'}
            />
          ))}
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h2 className="font-semibold mb-1">Cross-Elasticity Matrix</h2>
        <p className="text-xs text-slate-400 mb-4">
          <span className="text-green-400">Green = substitutes</span> · <span className="text-red-400">Red = complements</span> · Diagonal = own-price
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr>
                <th className="text-left p-1.5 text-slate-400">↓ Price of / Volume of →</th>
                {products.map(p => <th key={p} className="p-1.5 text-slate-400 text-center">{shortNames[p]}</th>)}
              </tr>
            </thead>
            <tbody>
              {products.map((pi, ri) => (
                <tr key={pi}>
                  <td className="p-1.5 text-slate-300 font-medium">{shortNames[pi]}</td>
                  {products.map((pj, ci) => {
                    const cell = crossMatrix.find(c => c.PRODUCT_I === pi && c.PRODUCT_J === pj);
                    const val = cell?.CROSS_ELASTICITY ?? 0;
                    return (
                      <td key={pj} className={`p-1.5 text-center rounded ${getCellColor(val, ri === ci)}`}>
                        {val > 0 ? '+' : ''}{val.toFixed(2)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h2 className="font-semibold">Demand Drivers — Trend</h2>
        <p className="text-xs text-slate-400 mb-4">Volume vs macro indicators</p>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={driverChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
              <YAxis yAxisId="vol" stroke="#f59e0b" fontSize={11} />
              <YAxis yAxisId="spend" orientation="right" stroke="#3b82f6" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line yAxisId="vol" type="monotone" dataKey="volume" stroke="#f59e0b" strokeWidth={2} name="Volume (M tons)" dot={false} />
              <Line yAxisId="spend" type="monotone" dataKey="highway" stroke="#3b82f6" strokeWidth={1.5} name="Highway Spend ($B)" dot={false} />
              <Line yAxisId="spend" type="monotone" dataKey="construction" stroke="#10b981" strokeWidth={1.5} name="Construction ($B)" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-semibold">Monthly Volume (M tons)</h2>
            <p className="text-xs text-slate-400">Full shipment history from Snowflake</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-3 h-0.5 bg-amber-400 inline-block" /> Historical
            <ArrowRight className="w-3 h-3" />
            <span className="w-3 h-0.5 bg-blue-400 inline-block" /> 2026
          </div>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={volChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
              <Area type="monotone" dataKey="p50" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.1} strokeWidth={2} name="2026" />
              <Line type="monotone" dataKey="actual" stroke="#f59e0b" strokeWidth={2} dot={false} name="Historical" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
