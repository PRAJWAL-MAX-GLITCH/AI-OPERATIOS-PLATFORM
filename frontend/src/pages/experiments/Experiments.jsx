import { SimpleLineChart } from '../../components/ui/charts/ChartCards';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';

export default function Experiments() {
  const metricHistory = [
    { name: 'Run 1', f1: 0.72, accuracy: 0.75 },
    { name: 'Run 2', f1: 0.78, accuracy: 0.81 },
    { name: 'Run 3', f1: 0.82, accuracy: 0.84 },
    { name: 'Run 4', f1: 0.85, accuracy: 0.88 },
    { name: 'Run 5', f1: 0.84, accuracy: 0.87 },
  ];

  const runs = [
    { id: 'run-8f72a', params: 'lr=0.01, depth=6', metrics: 'F1: 0.85, Acc: 0.88', date: '2026-07-16' },
    { id: 'run-2c9b1', params: 'lr=0.05, depth=4', metrics: 'F1: 0.82, Acc: 0.84', date: '2026-07-15' },
    { id: 'run-5a3d4', params: 'lr=0.001, depth=8', metrics: 'F1: 0.78, Acc: 0.81', date: '2026-07-14' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">MLflow Experiments</h1>
        <p className="text-gray-500">Track and compare parameters, metrics, and artifacts.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SimpleLineChart 
          title="F1 & Accuracy over Runs" 
          data={metricHistory} 
          lines={['f1', 'accuracy']} 
        />
        
        <Card>
          <CardHeader>
            <CardTitle>Experiment Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between border-b pb-2">
                <span className="text-gray-500">Experiment ID</span>
                <span className="font-medium">exp-customer-churn</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-gray-500">Total Runs</span>
                <span className="font-medium">24</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-gray-500">Best Metric (F1)</span>
                <span className="font-medium text-green-600">0.85</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Runs</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run ID</TableHead>
                <TableHead>Parameters</TableHead>
                <TableHead>Metrics</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.map((run) => (
                <TableRow key={run.id}>
                  <TableCell className="font-medium text-primary-600">{run.id}</TableCell>
                  <TableCell className="font-mono text-xs">{run.params}</TableCell>
                  <TableCell className="font-mono text-xs">{run.metrics}</TableCell>
                  <TableCell>{run.date}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
