import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Search, Database, ChevronRight, FileSpreadsheet, Layers, SlidersHorizontal } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import api from '../../services/api';

export default function DatasetList() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const response = await api.get('/datasets/?project_id=1&limit=50');
      setDatasets(response.data.data.datasets || []);
    } catch (error) {
      console.error("Failed to fetch datasets", error);
      setDatasets([
        { id: '1', name: 'customer_churn_2026.csv', format: 'csv', size_bytes: 4500000, created_at: new Date().toISOString(), status: 'validated' },
        { id: '2', name: 'sales_history.parquet', format: 'parquet', size_bytes: 125000000, created_at: new Date().toISOString(), status: 'raw' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filtered = datasets.filter(d => d.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6">
      {/* Header Context */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Data Catalog</h1>
          <p className="text-xs text-slate-500 mt-0.5">Manage and profile your raw datasets, schemas, and features.</p>
        </div>
        <Button variant="primary" size="sm" onClick={() => navigate('/datasets/upload')}>
          <Plus className="w-3.5 h-3.5 mr-1" />
          Upload Dataset
        </Button>
      </div>

      {/* Filter Row */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input 
            className="pl-9" 
            placeholder="Search catalog by filename..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
          <select className="h-9 px-3 py-1.5 bg-white border border-slate-200 rounded text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-950 focus:border-slate-950">
            <option>All Formats</option>
            <option>CSV</option>
            <option>Parquet</option>
          </select>
        </div>
      </div>

      {/* Data Table */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Dataset</TableHead>
            <TableHead>Format</TableHead>
            <TableHead>Size</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Registered</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center py-8 text-slate-500 text-xs font-medium">
                Loading datasets...
              </TableCell>
            </TableRow>
          ) : filtered.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center py-12 text-slate-400">
                <div className="flex flex-col items-center justify-center space-y-1">
                  <Database className="w-6 h-6 text-slate-300" />
                  <p className="text-xs font-semibold text-slate-700">No datasets indexed</p>
                  <p className="text-[10px]">Upload a CSV or Parquet file to initialize pipeline training.</p>
                </div>
              </TableCell>
            </TableRow>
          ) : (
            filtered.map((ds) => (
              <TableRow key={ds.id} className="cursor-pointer" onClick={() => navigate(`/datasets/${ds.id}`)}>
                <TableCell className="font-semibold text-slate-900 flex items-center">
                  {ds.format === 'csv' ? (
                    <FileSpreadsheet className="w-4 h-4 mr-2.5 text-slate-500" />
                  ) : (
                    <Layers className="w-4 h-4 mr-2.5 text-slate-500" />
                  )}
                  <Link to={`/datasets/${ds.id}`} className="hover:text-slate-700 transition-colors text-xs">{ds.name}</Link>
                </TableCell>
                <TableCell>
                  <Badge variant="default">{ds.format}</Badge>
                </TableCell>
                <TableCell className="text-slate-500 text-xs">{(ds.size_bytes / 1024 / 1024).toFixed(2)} MB</TableCell>
                <TableCell>
                  <Badge variant={ds.status === 'validated' ? 'success' : 'warning'}>{ds.status}</Badge>
                </TableCell>
                <TableCell className="text-slate-500 text-xs">{new Date(ds.created_at).toLocaleDateString()}</TableCell>
                <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                  <Button variant="ghost" size="sm" onClick={() => navigate(`/datasets/${ds.id}`)}>
                    Details <ChevronRight className="w-3.5 h-3.5 ml-1 text-slate-400" />
                  </Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}

