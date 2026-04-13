import { useState, useEffect } from 'react';
import { Thermometer, AlertTriangle, TrendingDown, MapPin, Calendar, Droplets, Sun, CloudLightning } from 'lucide-react';
import { XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { fetchWeatherImpact, fetchRegionalExposure } from '../services/api';

export default function WeatherRisk() {
  const [weatherData, setWeatherData] = useState<any[]>([]);
  const [exposure, setExposure] = useState<any[]>([]);

  useEffect(() => {
    fetchWeatherImpact().then(setWeatherData).catch(() => {});
    fetchRegionalExposure().then(setExposure).catch(() => {});
  }, []);

  const monthlyAgg: Record<string, { precip: number; revenue: number; count: number }> = {};
  weatherData.forEach(w => {
    const m = new Date(w.YEAR_MONTH).toLocaleDateString('en-US', { month: 'short' });
    if (!monthlyAgg[m]) monthlyAgg[m] = { precip: 0, revenue: 0, count: 0 };
    monthlyAgg[m].precip += w.PRECIP_DAYS || 0;
    monthlyAgg[m].revenue += w.REVENUE_M || 0;
    monthlyAgg[m].count += 1;
  });
  const monthlyChart = Object.entries(monthlyAgg).map(([month, d]) => ({
    month,
    precipDays: Math.round(d.precip / Math.max(d.count, 1)),
    revenueM: Math.round(d.revenue / Math.max(d.count, 1)),
  }));

  const totalRevExposed = exposure.reduce((s, e) => s + (e.ANNUAL_REVENUE_M || 0), 0);

  const hurricaneScenarios = [
    { name: 'Category 1-2', probability: 45, revenueImpact: -5, recoveryMonths: 2, color: '#fbbf24' },
    { name: 'Category 3', probability: 25, revenueImpact: -12, recoveryMonths: 4, color: '#f97316' },
    { name: 'Category 4+', probability: 10, revenueImpact: -25, recoveryMonths: 8, color: '#ef4444' },
  ];

  const activeAlerts = [
    { type: 'Hurricane Watch', location: 'Gulf of Mexico', severity: 'high', message: 'Tropical system developing, potential Cat 2-3 landfall in 5-7 days', icon: CloudLightning },
    { type: 'Heat Advisory', location: 'Phoenix, AZ', severity: 'medium', message: 'Extreme heat (115°F+) expected, reduced operating hours likely', icon: Thermometer },
    { type: 'Flood Warning', location: 'Houston, TX', severity: 'medium', message: 'Heavy rainfall forecast, 4-6 inches over 48 hours', icon: Droplets },
    { type: 'Drought Monitor', location: 'Central Texas', severity: 'low', message: 'Water restrictions may impact concrete operations', icon: Sun },
  ];

  const historicalEvents = [
    { year: 2024, event: 'Hurricane Helene', region: 'FL/GA', lostRevenue: 45, recoveryDays: 21 },
    { year: 2023, event: 'Hurricane Idalia', region: 'FL', lostRevenue: 28, recoveryDays: 14 },
    { year: 2022, event: 'Hurricane Ian', region: 'FL', lostRevenue: 125, recoveryDays: 45 },
    { year: 2021, event: 'Winter Storm Uri', region: 'TX', lostRevenue: 85, recoveryDays: 18 },
  ];

  const sevColors: Record<string, string> = { high: 'border-red-500 bg-red-500/10', medium: 'border-amber-500 bg-amber-500/10', low: 'border-blue-500 bg-blue-500/10' };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Weather Risk Analysis</h1>
        <p className="text-slate-400 mt-1">Climate exposure, hurricane scenarios, and operational disruption modeling</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-red-500/20 to-red-600/10 rounded-xl p-5 border border-red-500/30">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-1"><CloudLightning className="w-4 h-4" />Hurricane Season Risk</div>
          <p className="text-3xl font-bold text-red-400">Elevated</p>
          <p className="text-sm text-slate-400 mt-1">Aug-Oct peak exposure</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-1"><Calendar className="w-4 h-4" />Regions Tracked</div>
          <p className="text-3xl font-bold">{exposure.length}</p>
          <p className="text-sm text-slate-400 mt-1">with weather data</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-1"><TrendingDown className="w-4 h-4" />Total Revenue Exposed</div>
          <p className="text-3xl font-bold text-amber-400">${Math.round(totalRevExposed)}M</p>
          <p className="text-sm text-slate-400 mt-1">annual (weather regions)</p>
        </div>
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-1"><MapPin className="w-4 h-4" />Active Alerts</div>
          <p className="text-3xl font-bold">{activeAlerts.length}</p>
          <p className="text-sm text-slate-400 mt-1">across all regions</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {activeAlerts.map((alert, i) => {
          const Icon = alert.icon;
          return (
            <div key={i} className={`p-4 rounded-xl border-l-4 ${sevColors[alert.severity]}`}>
              <div className="flex items-start gap-3">
                <Icon className={`w-5 h-5 mt-0.5 ${alert.severity === 'high' ? 'text-red-400' : alert.severity === 'medium' ? 'text-amber-400' : 'text-blue-400'}`} />
                <div>
                  <div className="flex items-center gap-2"><span className="font-semibold">{alert.type}</span><span className="text-xs text-slate-500">• {alert.location}</span></div>
                  <p className="text-sm text-slate-400 mt-1">{alert.message}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">Monthly Weather Impact (Avg Precip Days & Revenue $M)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyChart}>
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} />
                <YAxis yAxisId="left" stroke="#64748b" fontSize={12} />
                <YAxis yAxisId="right" orientation="right" stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Bar yAxisId="left" dataKey="precipDays" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Avg Precip Days" />
                <Bar yAxisId="right" dataKey="revenueM" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Revenue ($M)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold mb-4">Hurricane Scenario Analysis</h3>
          <div className="space-y-4">
            {hurricaneScenarios.map((scenario) => (
              <div key={scenario.name} className="p-3 bg-slate-700/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{scenario.name}</span>
                  <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: `${scenario.color}20`, color: scenario.color }}>{scenario.probability}% prob</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><p className="text-slate-400">Revenue Impact</p><p className="font-medium text-red-400">{scenario.revenueImpact}%</p></div>
                  <div><p className="text-slate-400">Recovery</p><p className="font-medium">{scenario.recoveryMonths} months</p></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h3 className="font-semibold mb-4">Regional Weather Exposure</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 text-slate-400 font-medium">Region</th>
                <th className="text-right py-3 text-slate-400 font-medium">Revenue</th>
                <th className="text-center py-3 text-slate-400 font-medium">Avg Temp (°F)</th>
                <th className="text-center py-3 text-slate-400 font-medium">Avg Precip Days</th>
                <th className="text-center py-3 text-slate-400 font-medium">Risk Score</th>
              </tr>
            </thead>
            <tbody>
              {exposure.map((r) => (
                <tr key={r.REGION_CODE} className="border-b border-slate-700/50">
                  <td className="py-3 font-medium">{r.REGION_NAME}</td>
                  <td className="py-3 text-right text-amber-400">${r.ANNUAL_REVENUE_M}M</td>
                  <td className="py-3 text-center">{r.AVG_TEMP}°F</td>
                  <td className="py-3 text-center">{r.AVG_PRECIP_DAYS}</td>
                  <td className="py-3 text-center">
                    <span className={`px-2 py-0.5 rounded text-xs ${r.WEATHER_RISK_SCORE > 80 ? 'bg-red-500/20 text-red-400' : r.WEATHER_RISK_SCORE > 50 ? 'bg-amber-500/20 text-amber-400' : 'bg-green-500/20 text-green-400'}`}>
                      {r.WEATHER_RISK_SCORE}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h3 className="font-semibold mb-4">Historical Weather Events</h3>
        <div className="grid grid-cols-4 gap-4">
          {historicalEvents.map((event) => (
            <div key={event.event} className="bg-slate-700/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2"><span className="text-xs text-slate-500">{event.year}</span><span className="text-xs text-slate-400">{event.region}</span></div>
              <p className="font-semibold text-sm">{event.event}</p>
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                <div><p className="text-slate-400">Lost Revenue</p><p className="font-medium text-red-400">-${event.lostRevenue}M</p></div>
                <div><p className="text-slate-400">Recovery</p><p className="font-medium">{event.recoveryDays} days</p></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gradient-to-r from-amber-500/10 to-red-500/10 border border-amber-500/30 rounded-xl p-5">
        <div className="flex items-start gap-4">
          <AlertTriangle className="w-5 h-5 text-amber-400 mt-1" />
          <div>
            <h4 className="font-semibold text-amber-400">Weather Risk Mitigation</h4>
            <p className="text-sm text-slate-400 mt-1">
              SnowCore's geographic diversification provides natural hedging. While Gulf Coast operations face hurricane risk,
              construction typically <strong className="text-white">rebounds strongly post-storm</strong> due to rebuilding demand.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
