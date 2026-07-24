import { useParams } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { SimpleBarChart, SimpleLineChart } from '../../components/ui/charts/ChartCards';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { CheckCircle2, AlertTriangle, Info } from 'lucide-react';

export default function DatasetDetails() {
  const { id } = useParams();

  // Mocked profiling data
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">{profile.name}</h1>
          <p className="text-gray-500">Dataset profiling and quality analysis.</p>
        </div>
        <Badge variant={profile.qualityScore > 90 ? 'success' : 'warning'} className="text-sm px-4 py-1">
          Quality Score: {profile.qualityScore}/100
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-gray-500 font-medium">Total Rows</p>
            <p className="text-2xl font-bold">{profile.rows.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-gray-500 font-medium">Columns</p>
            <p className="text-2xl font-bold">{profile.columns}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-gray-500 font-medium">Missing Values</p>
            <p className="text-2xl font-bold">{profile.missingValues}%</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-gray-500 font-medium">Duplicates</p>
            <p className="text-2xl font-bold">{profile.duplicateRows}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SimpleBarChart 
          title="Data Quality Dimensions" 
          data={qualityData} 
          dataKey="score" 
          xAxisKey="name"
          color="#10b981"
        />
        
        <Card>
          <CardHeader>
            <CardTitle>Validation Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-4">
              <li className="flex items-start">
                <CheckCircle2 className="w-5 h-5 text-green-500 mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-medium">Schema Matched</p>
                  <p className="text-xs text-gray-500">All 24 columns match the expected data types.</p>
                </div>
              </li>
              <li className="flex items-start">
                <AlertTriangle className="w-5 h-5 text-yellow-500 mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-medium">Missing Values Detected</p>
                  <p className="text-xs text-gray-500">Column 'plan_type' has 2.1% missing values. Consider imputation.</p>
                </div>
              </li>
              <li className="flex items-start">
                <Info className="w-5 h-5 text-blue-500 mr-2 mt-0.5" />
                <div>
                  <p className="text-sm font-medium">Imbalance Detected</p>
                  <p className="text-xs text-gray-500">Target 'churn' has a 15/85 distribution.</p>
                </div>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Schema & Profiling</CardTitle>
        </CardHeader>
        <CardContent>
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
                  <TableCell className="font-medium">{col.name}</TableCell>
                  <TableCell><Badge>{col.type}</Badge></TableCell>
                  <TableCell>{col.missing}</TableCell>
                  <TableCell>{col.unique}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
