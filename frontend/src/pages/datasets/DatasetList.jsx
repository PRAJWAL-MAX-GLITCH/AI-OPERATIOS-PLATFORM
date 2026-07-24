import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Search, Database } from 'lucide-react';
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
      // Assuming projectId is 1 or managed globally
      // For this UI, we mock the API call if backend doesn't have data yet
      const response = await api.get('/datasets/?project_id=1&limit=50');
      setDatasets(response.data.data.datasets || []);
    } catch (error) {
      console.error("Failed to fetch datasets", error);
      // Fallback dummy data for UI demonstration
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Datasets</h1>
          <p className="text-gray-500">Manage and profile your raw and processed data.</p>
        </div>
        <Button onClick={() => navigate('/datasets/upload')}>
          <Plus className="w-4 h-4 mr-2" />
          Upload Dataset
        </Button>
      </div>

      <div className="flex items-center space-x-4 bg-white p-4 border border-gray-200 rounded-lg">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input 
            className="pl-9" 
            placeholder="Search datasets..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Format</TableHead>
            <TableHead>Size</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Uploaded</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading ? (
            <TableRow><TableCell colSpan={6} className="text-center py-8 text-gray-500">Loading datasets...</TableCell></TableRow>
          ) : filtered.length === 0 ? (
            <TableRow><TableCell colSpan={6} className="text-center py-8 text-gray-500">No datasets found.</TableCell></TableRow>
          ) : (
            filtered.map((ds) => (
              <TableRow key={ds.id}>
                <TableCell className="font-medium flex items-center">
                  <Database className="w-4 h-4 mr-2 text-primary-500" />
                  <Link to={`/datasets/${ds.id}`} className="hover:underline text-primary-700">{ds.name}</Link>
                </TableCell>
                <TableCell><Badge variant="default">{ds.format}</Badge></TableCell>
                <TableCell>{(ds.size_bytes / 1024 / 1024).toFixed(2)} MB</TableCell>
                <TableCell>
                  <Badge variant={ds.status === 'validated' ? 'success' : 'warning'}>{ds.status}</Badge>
                </TableCell>
                <TableCell>{new Date(ds.created_at).toLocaleDateString()}</TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm" onClick={() => navigate(`/datasets/${ds.id}`)}>View</Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
