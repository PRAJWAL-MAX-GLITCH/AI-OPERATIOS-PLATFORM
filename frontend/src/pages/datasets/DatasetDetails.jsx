import { useParams } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { SimpleBarChart } from '../../components/ui/charts/ChartCards';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { CheckCircle2, AlertTriangle, Info, ArrowLeft, Database, Activity, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';

export default function DatasetDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const profile = {
    name: 'customer_churn_2026.csv',
    rows: 15420,
    columns: 24,
    sizeMB: 4.5,
    qualityScore: 92,
    missingValues: 1.2,
    duplicateRows: 0,
    status: 'Validated'
  };

  const schema = [
    { name: 'customer_id', type: 'string', missing: '0%', unique: '100%' },
    { name: 'age', type: 'numeric', missing: '0.5%', unique: '2.1%' },
    { name: 'monthly_charges', type: 'numeric', missing: '0%', unique: '85%' },
    { name: 'churn', type: 'boolean', missing: '0%', unique: '0.01%' },
    { name: 'plan_type', type: 'categorical', missing: '2.1%', unique: '0.05%' },
  ];

  const qualityData = [
    { name: 'Completeness', score: 98 },
    { name: 'Consistency', score: 95 },
    { name: 'Validity', score: 100 },
    { name: 'Uniqueness', score: 100 },
  ];

  return (
    <div className="space-y-6">
      {/* Header Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => navigate('/datasets')} className="p-1">
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-slate-500" />
              <h1 className="text-lg font-bold text-slate-900">{profile.name}</h1>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">Dataset profiling, schema registry, and anomaly checks.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={profile.qualityScore > 90 ? 'success' : 'warning'} className="px-3 py-1 text-xs">
            Score: {profile.qualityScore}/100
          </Badge>
        </div>
      </div>

      {/* Grid of profiling stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 border-slate-200/80">
          <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Rows</span>
          <span className="block text-lg font-extrabold text-slate-900 mt-1">{profile.rows.toLocaleString()}</span>
        </Card>
        <Card className="p-4 border-slate-200/80">
          <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Columns</span>
          <span className="block text-lg font-extrabold text-slate-900 mt-1">{profile.columns}</span>
        </Card>
        <Card className="p-4 border-slate-200/80">
          <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Missing Values</span>
          <span className="block text-lg font-extrabold text-slate-900 mt-1">{profile.missingValues}%</span>
        </Card>
        <Card className="p-4 border-slate-200/80">
          <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Duplicates</span>
          <span className="block text-lg font-extrabold text-slate-900 mt-1">{profile.duplicateRows}</span>
        </Card>
      </div>

      {/* Visualization Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Data Quality Dimensions</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <SimpleBarChart 
              data={qualityData} 
              dataKey="score" 
              xAxisKey="name"
              color="#09090b"
            />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-slate-500" />
              <CardTitle>Validation Summary</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="px-5">
            <ul className="space-y-3.5 text-xs">
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-slate-800">Schema Matched</p>
                  <p className="text-[10px] text-slate-500">All 24 columns match the expected data types.</p>
                </div>
              </li>
              <li className="flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-slate-800">Missing Values Detected</p>
                  <p className="text-[10px] text-slate-500">Column 'plan_type' has 2.1% missing values. Imputation suggested.</p>
                </div>
              </li>
              <li className="flex items-start gap-2.5">
                <Info className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-slate-800">Imbalance Detected</p>
                  <p className="text-[10px] text-slate-500">Target 'churn' has a unbalanced 15/85 distribution.</p>
                </div>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Schema Registry Table */}
      <Card>
        <CardHeader>
          <CardTitle>Schema & Profiling</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Column Name</TableHead>
                <TableHead>Data Type</TableHead>
                <TableHead>Missing %</TableHead>
                <TableHead>Unique %</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {schema.map(col => (
                <TableRow key={col.name}>
                  <TableCell className="font-semibold text-slate-900">{col.name}</TableCell>
                  <TableCell>
                    <Badge variant="default">{col.type}</Badge>
                  </TableCell>
                  <TableCell className="text-slate-500">{col.missing}</TableCell>
                  <TableCell className="text-slate-500">{col.unique}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

