import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { 
  FolderGit2, 
  Database, 
  Brain, 
  FlaskConical,
  Activity,
  ArrowUpRight,
  ShieldCheck,
  Cpu,
  Layers,
  Terminal,
  FileCheck2,
  RefreshCw,
  Plus
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const METRICS = [
  { label: 'Active Projects', value: '12', icon: FolderGit2, detail: '+2 this week' },
  { label: 'Total Datasets', value: '48', icon: Database, detail: '2.4 GB indexed' },
  { label: 'Deployed Models', value: '7', icon: Brain, detail: '99.8% uptime' },
  { label: 'Running Experiments', value: '3', icon: FlaskConical, detail: 'Active training' },
];

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      {/* Upper context Header with micro-actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">AI Operations Overview</h1>
          <p className="text-xs text-slate-500 mt-0.5">Control center for training runs, datasets, and cognitive agents.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => navigate('/datasets/upload')}>
            <Plus className="w-3.5 h-3.5 mr-1" /> Upload Dataset
          </Button>
          <Button variant="primary" size="sm" onClick={() => navigate('/agents')}>
            Run Agent Task
          </Button>
        </div>
      </div>

      {/* Metrics Row (not oversized cards) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {METRICS.map((metric) => {
          const Icon = metric.icon;
          return (
            <Card key={metric.label} className="border-slate-200/80">
              <CardContent className="p-4 flex items-center justify-between">
                <div className="space-y-1">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">{metric.label}</span>
                  <span className="block text-xl font-extrabold text-slate-900 leading-none">{metric.value}</span>
                  <span className="block text-[10px] text-slate-500 font-medium">{metric.detail}</span>
                </div>
                <div className="p-2 bg-slate-50 border border-slate-100 rounded text-slate-600">
                  <Icon className="w-4 h-4" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      
      {/* Primary operational widgets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Real Enterprise System Health list */}
        <Card className="lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-slate-500" />
              <CardTitle>Infrastructure Status</CardTitle>
            </div>
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100 px-5 text-xs">
              <div className="flex justify-between items-center py-3">
                <span className="font-semibold text-slate-600">PostgreSQL DB</span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold uppercase tracking-wider">Operational</span>
              </div>
              <div className="flex justify-between items-center py-3">
                <span className="font-semibold text-slate-600">Celery Queue</span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold uppercase tracking-wider">Operational</span>
              </div>
              <div className="flex justify-between items-center py-3">
                <span className="font-semibold text-slate-600">MLflow Tracking</span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold uppercase tracking-wider">Operational</span>
              </div>
              <div className="flex justify-between items-center py-3">
                <span className="font-semibold text-slate-600">Redis Cache</span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold uppercase tracking-wider">Operational</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Real activity list with technical icons */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div className="flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-slate-500" />
              <CardTitle>System Activity Logs</CardTitle>
            </div>
            <button className="text-[10px] font-bold text-slate-500 hover:text-slate-900 flex items-center gap-1 uppercase tracking-wider">
              <RefreshCw className="w-3 h-3" /> Refresh
            </button>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100 px-5 text-xs">
              <div className="py-3 flex items-start gap-3">
                <div className="mt-0.5 p-1 bg-slate-100 rounded text-slate-600">
                  <FileCheck2 className="w-3 h-3" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-800">Dataset `customer_churn_q3.csv` uploaded</p>
                  <p className="text-[10px] text-slate-400">12,500 rows • validation checks passed</p>
                </div>
                <span className="text-[10px] text-slate-400 whitespace-nowrap">2m ago</span>
              </div>
              <div className="py-3 flex items-start gap-3">
                <div className="mt-0.5 p-1 bg-slate-100 rounded text-slate-600">
                  <Cpu className="w-3 h-3" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-800">Model registry sync completed</p>
                  <p className="text-[10px] text-slate-400">MLflow run updated</p>
                </div>
                <span className="text-[10px] text-slate-400 whitespace-nowrap">15m ago</span>
              </div>
              <div className="py-3 flex items-start gap-3">
                <div className="mt-0.5 p-1 bg-slate-100 rounded text-slate-600">
                  <Layers className="w-3 h-3" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-800">Knowledge base chunking verified</p>
                  <p className="text-[10px] text-slate-400">Vector embeddings generated</p>
                </div>
                <span className="text-[10px] text-slate-400 whitespace-nowrap">1h ago</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

