import { useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card, CardContent } from '../../components/ui/Card';
import { Brain, ArrowUpRight, Archive } from 'lucide-react';

export default function ModelRegistry() {
  const [models] = useState([
    { id: 'mod-1a2b', name: 'Churn Predictor V3', version: 'v3.2', stage: 'Production', algorithm: 'XGBoost', created: '2026-07-16' },
    { id: 'mod-3c4d', name: 'Churn Predictor V4', version: 'v4.0', stage: 'Staging', algorithm: 'LightGBM', created: '2026-07-17' },
    { id: 'mod-5e6f', name: 'Sales Forecaster', version: 'v1.1', stage: 'Development', algorithm: 'Prophet', created: '2026-07-10' },
    { id: 'mod-7g8h', name: 'Churn Predictor V2', version: 'v2.8', stage: 'Archived', algorithm: 'RandomForest', created: '2026-01-05' },
  ]);

  const getStageBadge = (stage) => {
    switch (stage) {
      case 'Production': return 'success';
      case 'Staging': return 'warning';
      case 'Development': return 'primary';
      default: return 'default';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Model Registry</h1>
          <p className="text-gray-500">Manage model lifecycles across Development, Staging, and Production.</p>
        </div>
        <Button>
          <Brain className="w-4 h-4 mr-2" />
          Register Model
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Model Name</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Stage</TableHead>
                <TableHead>Algorithm</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {models.map((mod) => (
                <TableRow key={mod.id}>
                  <TableCell className="font-medium flex items-center">
                    <Brain className="w-4 h-4 mr-2 text-primary-500" />
                    {mod.name}
                  </TableCell>
                  <TableCell>{mod.version}</TableCell>
                  <TableCell>
                    <Badge variant={getStageBadge(mod.stage)}>{mod.stage}</Badge>
                  </TableCell>
                  <TableCell>{mod.algorithm}</TableCell>
                  <TableCell>{mod.created}</TableCell>
                  <TableCell className="text-right space-x-2">
                    {mod.stage !== 'Archived' && mod.stage !== 'Production' && (
                      <Button variant="ghost" size="sm" className="text-green-600 hover:text-green-700 hover:bg-green-50">
                        <ArrowUpRight className="w-4 h-4 mr-1" /> Promote
                      </Button>
                    )}
                    {mod.stage !== 'Archived' && (
                      <Button variant="ghost" size="sm" className="text-gray-500 hover:text-gray-700">
                        <Archive className="w-4 h-4 mr-1" /> Archive
                      </Button>
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
