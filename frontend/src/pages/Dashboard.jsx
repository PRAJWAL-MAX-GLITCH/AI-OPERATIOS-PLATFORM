import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { 
  FolderGit2, 
  Database, 
  Brain, 
  FlaskConical,
  Activity
} from 'lucide-react';

const METRICS = [
  { label: 'Active Projects', value: '12', icon: FolderGit2, color: 'text-blue-600', bg: 'bg-blue-100' },
  { label: 'Total Datasets', value: '48', icon: Database, color: 'text-emerald-600', bg: 'bg-emerald-100' },
  { label: 'Deployed Models', value: '7', icon: Brain, color: 'text-purple-600', bg: 'bg-purple-100' },
  { label: 'Running Experiments', value: '3', icon: FlaskConical, color: 'text-amber-600', bg: 'bg-amber-100' },
];

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Dashboard Overview</h1>
        <p className="text-gray-500">Welcome to the Enterprise AI Operations Platform.</p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {METRICS.map((metric) => {
          const Icon = metric.icon;
          return (
            <Card key={metric.label}>
              <CardContent className="p-6 flex items-center">
                <div className={`p-3 rounded-lg ${metric.bg} ${metric.color} mr-4`}>
                  <Icon className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">{metric.label}</p>
                  <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-gray-500" />
              <CardTitle>System Health</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b pb-2">
                <span className="text-sm text-gray-600">Database</span>
                <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">Operational</span>
              </div>
              <div className="flex justify-between items-center border-b pb-2">
                <span className="text-sm text-gray-600">Celery Workers</span>
                <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">Operational</span>
              </div>
              <div className="flex justify-between items-center border-b pb-2">
                <span className="text-sm text-gray-600">MLflow Tracking</span>
                <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">Operational</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center h-40 text-gray-500 text-sm">
              <p>No recent activity detected.</p>
              <p>Start an experiment or create a new agent to see logs.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
