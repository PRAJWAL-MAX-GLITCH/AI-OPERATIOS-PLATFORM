import { useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card, CardContent } from '../../components/ui/Card';
import { Brain, ArrowUpRight, Archive, SlidersHorizontal, ChevronRight } from 'lucide-react';

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
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Model Registry</h1>
          <p className="text-xs text-slate-500 mt-0.5">Control lifecycle stages, parameters, and evaluations for production-grade models.</p>
        </div>
        <Button variant="primary" size="sm">
          <Brain className="w-3.5 h-3.5 mr-1" />
          Register Model
        </Button>
      </div>

      {/* Filter Row */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <input
            className="flex h-9 w-full rounded border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-950 focus:border-slate-950"
            placeholder="Search registered models by name..."
          />
        </div>
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
          <select className="h-9 px-3 py-1.5 bg-white border border-slate-200 rounded text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-950 focus:border-slate-950">
            <option>All Stages</option>
            <option>Production</option>
            <option>Staging</option>
            <option>Development</option>
          </select>
        </div>
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
                  <TableCell className="font-semibold text-slate-900 flex items-center">
                    <Brain className="w-4 h-4 mr-2.5 text-slate-500" />
                    {mod.name}
                  </TableCell>
                  <TableCell className="text-slate-500 font-mono text-[10px]">{mod.version}</TableCell>
                  <TableCell>
                    <Badge variant={getStageBadge(mod.stage)}>{mod.stage}</Badge>
                  </TableCell>
                  <TableCell className="font-mono text-slate-500 text-xs">{mod.algorithm}</TableCell>
                  <TableCell className="text-slate-500 text-xs">{mod.created}</TableCell>
                  <TableCell className="text-right space-x-1" onClick={(e) => e.stopPropagation()}>
                    {mod.stage !== 'Archived' && mod.stage !== 'Production' && (
                      <Button variant="ghost" size="sm" className="text-emerald-700 hover:bg-emerald-50">
                        <ArrowUpRight className="w-3 h-3 mr-1" /> Promote
                      </Button>
                    )}
                    {mod.stage !== 'Archived' && (
                      <Button variant="ghost" size="sm" className="text-slate-500 hover:bg-slate-50">
                        <Archive className="w-3 h-3 mr-1" /> Archive
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" className="text-slate-700">
                      View <ChevronRight className="w-3 h-3 ml-0.5 text-slate-400" />
                    </Button>
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

