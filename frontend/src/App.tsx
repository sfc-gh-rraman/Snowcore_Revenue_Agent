import { BrowserRouter, Routes, Route, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { 
  LayoutDashboard, 
  Map, 
  Mountain,
  BarChart3,
  Activity,
  DollarSign,
  Truck,
  CloudRain,
  Brain,
  Database
} from 'lucide-react';

import Landing from './pages/Landing';
import MissionControl from './pages/MissionControl';
import ScenarioAnalysis from './pages/ScenarioAnalysis';
import SensitivityAnalysis from './pages/SensitivityAnalysis';
import KnowledgeBase from './pages/KnowledgeBase';
import RevenueDeepDive from './pages/RevenueDeepDive';
import RegionMap from './pages/RegionMap';
import Shipments from './pages/Shipments';
import WeatherRisk from './pages/WeatherRisk';
import DataExplorer from './pages/DataExplorer';

const queryClient = new QueryClient();

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Mission Control' },
  { path: '/scenarios', icon: BarChart3, label: 'Scenarios' },
  { path: '/sensitivity', icon: Activity, label: 'Sensitivity' },
  { path: '/revenue', icon: DollarSign, label: 'Revenue Deep Dive' },
  { path: '/regions', icon: Map, label: 'Region Map' },
  { path: '/shipments', icon: Truck, label: 'Shipments' },
  { path: '/weather', icon: CloudRain, label: 'Weather Risk' },
  { path: '/knowledge', icon: Brain, label: 'Knowledge Base' },
  { path: '/data', icon: Database, label: 'Data Explorer' },
];

function AppLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <nav className="fixed top-0 left-0 h-screen w-64 bg-slate-800 border-r border-slate-700 p-4">
        <button 
          onClick={() => navigate('/')}
          className="flex items-center gap-3 mb-8 px-2 hover:opacity-80 transition-opacity cursor-pointer w-full text-left"
        >
          <Mountain className="w-8 h-8 text-amber-400" />
          <div>
            <h1 className="text-lg font-bold">GRANITE</h1>
            <p className="text-xs text-slate-400">Vulcan Revenue Intelligence</p>
          </div>
        </button>
        
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-amber-600 text-white'
                    : 'text-slate-300 hover:bg-slate-700'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="text-sm font-medium">{item.label}</span>
            </NavLink>
          ))}
        </div>
        
        <div className="absolute bottom-4 left-4 right-4 p-3 bg-slate-700/50 rounded-lg">
          <p className="text-xs text-slate-400">Cortex Agent</p>
          <p className="text-sm font-medium text-green-400">● Connected</p>
        </div>
      </nav>

      <main className="ml-64 p-6 min-h-screen bg-slate-900">
        {children}
      </main>
    </div>
  );
}

function LandingWrapper() {
  const navigate = useNavigate();
  return <Landing onNavigate={(page) => navigate(page === '/' ? '/dashboard' : page)} />;
}

function AppRoutes() {
  const location = useLocation();
  const isLanding = location.pathname === '/';

  if (isLanding) {
    return <LandingWrapper />;
  }

  return (
    <AppLayout>
      <Routes>
        <Route path="/dashboard" element={<MissionControl />} />
        <Route path="/scenarios" element={<ScenarioAnalysis />} />
        <Route path="/sensitivity" element={<SensitivityAnalysis />} />
        <Route path="/revenue" element={<RevenueDeepDive />} />
        <Route path="/regions" element={<RegionMap />} />
        <Route path="/shipments" element={<Shipments />} />
        <Route path="/weather" element={<WeatherRisk />} />
        <Route path="/knowledge" element={<KnowledgeBase />} />
        <Route path="/data" element={<DataExplorer />} />
      </Routes>
    </AppLayout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/*" element={<AppRoutes />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
