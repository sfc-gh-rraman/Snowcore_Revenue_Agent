import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

export const fetchKpis = () => api.get('/kpis').then(r => r.data);
export const fetchDashboardRegions = () => api.get('/dashboard/regions').then(r => r.data.regions);
export const fetchRevenueTrend = () => api.get('/dashboard/revenue-trend').then(r => r.data.trend);

export const fetchMonthlyRevenue = () => api.get('/revenue/monthly').then(r => r.data.monthly);
export const fetchRevenueBySegment = () => api.get('/revenue/by-segment').then(r => r.data.segments);
export const fetchRevenueByRegion = () => api.get('/revenue/by-region').then(r => r.data.regions);
export const fetchPriceHistory = () => api.get('/revenue/price-history').then(r => r.data.prices);

export const fetchElasticity = () => api.get('/demand/elasticity').then(r => r.data.elasticity);
export const fetchCrossElasticity = () => api.get('/demand/cross-elasticity').then(r => r.data.matrix);
export const fetchDemandDrivers = () => api.get('/demand/drivers').then(r => r.data.drivers);
export const fetchVolumeHistory = () => api.get('/demand/volume-history').then(r => r.data.volume);

export const fetchOptimalPricing = () => api.get('/pricing/optimal').then(r => r.data.pricing);
export const runOptimizer = (region: string, version: string) =>
  api.post('/pricing/optimize', { region_filter: region, model_version: version }).then(r => r.data.result);

export const fetchCompetitiveLandscape = () => api.get('/competitive/landscape').then(r => r.data.landscape);
export const fetchQuarriesByRegion = () => api.get('/competitive/quarries-by-region').then(r => r.data.quarries);
export const fetchCompetitorRevenueTrend = () => api.get('/competitive/revenue-trend').then(r => r.data.trend);
export const fetchPricePremium = () => api.get('/competitive/price-premium').then(r => r.data.premium);

export const fetchModelComparison = () => api.get('/risk/model-comparison').then(r => r.data.comparison);
export const fetchSimulationPaths = () => api.get('/risk/simulation-paths').then(r => r.data.paths);

export const fetchRegionsDetail = () => api.get('/regions/detail').then(r => r.data.regions);

export const fetchWeatherImpact = () => api.get('/weather/monthly-impact').then(r => r.data.weather);
export const fetchRegionalExposure = () => api.get('/weather/regional-exposure').then(r => r.data.exposure);

export const searchKnowledge = (query: string, limit = 10) =>
  api.post('/knowledge/search', { query, limit }).then(r => r.data.results);
export const searchScenarios = (query: string, limit = 10) =>
  api.post('/knowledge/scenario-search', { query, limit }).then(r => r.data.results);

export const fetchScenarios = () => api.get('/scenarios').then(r => r.data.scenarios);

export const fetchMacroIndicators = () => api.get('/macro/indicators').then(r => r.data.indicators);
export const fetchEnergyPrices = () => api.get('/macro/energy').then(r => r.data.energy);

export default api;
