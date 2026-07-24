import { useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card, CardContent } from '../../components/ui/Card';
import { Play, Square } from 'lucide-react';

export default function TrainingJobs() {
  const [jobs] = useState([
    { id: 'job-001', algorithm: 'XGBoost', dataset: 'customer_churn_2026.csv', status: 'running', progress: 45, duration: '12m 30s' },
    { id: 'job-002', algorithm: 'RandomForest', dataset: 'sales_history.parquet', status: 'completed', progress: 100, duration: '45m 12s' },
    { id: 'job-003', algorithm: 'NeuralNet (PyTorch)', dataset: 'image_corpus_v2', status: 'failed', progress: 12, duration: '2m 10s' },
  ]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Training Jobs</h1>
          <p className="text-gray-500">Monitor active distributed training tasks.</p>
        </div>
        <Button>
          <Play className="w-4 h-4 mr-2" />
          New Training Job
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job ID</TableHead>
                <TableHead>Algorithm</TableHead>
                <TableHead>Dataset</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map((job) => (
                <TableRow key={job.id}>
                  <TableCell className="font-medium text-primary-600">{job.id}</TableCell>
                  <TableCell>{job.algorithm}</TableCell>
                  <TableCell>{job.dataset}</TableCell>
                  <TableCell>
                    <Badge variant={job.status === 'completed' ? 'success' : job.status === 'running' ? 'primary' : 'danger'}>
                      {job.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <div className="w-full bg-gray-200 rounded-full h-2 max-w-[100px]">
                        <div 
                          className={`h-2 rounded-full ${job.status === 'failed' ? 'bg-red-500' : 'bg-primary-600'}`} 
                          style={{ width: `${job.progress}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-500">{job.progress}%</span>
                    </div>
                  </TableCell>
                  <TableCell>{job.duration}</TableCell>
                  <TableCell className="text-right">
                    {job.status === 'running' ? (
                      <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700 hover:bg-red-50">
                        <Square className="w-4 h-4 mr-2" /> Stop
                      </Button>
                    ) : (
                      <Button variant="ghost" size="sm">View Logs</Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
