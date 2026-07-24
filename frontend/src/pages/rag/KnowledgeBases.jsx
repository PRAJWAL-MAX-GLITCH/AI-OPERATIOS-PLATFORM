import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Database, FileText, Search, Trash2, ArrowRight, Layers, CheckCircle2, Clock, SlidersHorizontal } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import api from '../../services/api';

export default function KnowledgeBases() {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    embedding_model: 'all-MiniLM-L6-v2',
    chunk_size: 512,
    chunk_overlap: 64,
  });

  const navigate = useNavigate();

  useEffect(() => {
    fetchKnowledgeBases();
  }, []);

  const fetchKnowledgeBases = async () => {
    try {
      const response = await api.get('/rag/knowledge-bases');
      setKnowledgeBases(response.data.data || []);
    } catch (error) {
      console.error('Failed to fetch knowledge bases', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post('/rag/knowledge-bases', formData);
      setIsModalOpen(false);
      setFormData({
        name: '',
        description: '',
        embedding_model: 'all-MiniLM-L6-v2',
        chunk_size: 512,
        chunk_overlap: 64,
      });
      fetchKnowledgeBases();
    } catch (error) {
      console.error('Failed to create knowledge base', error);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this knowledge base?')) return;
    try {
      await api.delete(`/rag/knowledge-bases/${id}`);
      fetchKnowledgeBases();
    } catch (error) {
      console.error('Failed to delete knowledge base', error);
    }
  };

  const filtered = knowledgeBases.filter((kb) =>
    kb.name.toLowerCase().includes(search.toLowerCase()) ||
    (kb.description && kb.description.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Knowledge Bases</h1>
          <p className="text-xs text-slate-500 mt-0.5">Manage vector embeddings, document registries, and cognitive retrieval contexts.</p>
        </div>
        <Button variant="primary" size="sm" onClick={() => setIsModalOpen(true)}>
          <Plus className="w-3.5 h-3.5 mr-1" />
          Create Collection
        </Button>
      </div>

      {/* Filter Row */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            className="pl-9"
            placeholder="Search vector collections..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
          <select className="h-9 px-3 py-1.5 bg-white border border-slate-200 rounded text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-950 focus:border-slate-950">
            <option>All Indexes</option>
            <option>Indexed</option>
            <option>Pending</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500 text-xs font-medium">Loading knowledge bases...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-slate-200 rounded-lg bg-white">
          <Database className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <h3 className="text-xs font-semibold text-slate-700">No Knowledge Bases Found</h3>
          <p className="text-[10px] text-slate-400 mt-0.5">Get started by creating a new vector knowledge base.</p>
          <Button variant="secondary" size="sm" className="mt-4" onClick={() => setIsModalOpen(true)}>
            <Plus className="w-3.5 h-3.5 mr-1" /> Create collection
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((kb) => (
            <Card
              key={kb.id}
              className="hover:border-slate-400 transition-colors cursor-pointer border border-slate-200/80 flex flex-col justify-between"
              onClick={() => navigate(`/rag/documents?kb_id=${kb.id}`)}
            >
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start mb-2">
                  <div className="p-2 bg-slate-100 rounded text-slate-700">
                    <Database className="w-4 h-4" />
                  </div>
                  <Badge variant={kb.is_indexed ? 'success' : 'warning'}>
                    {kb.is_indexed ? 'Indexed' : 'Pending'}
                  </Badge>
                </div>
                <CardTitle className="text-xs font-bold text-slate-900 truncate">{kb.name}</CardTitle>
                <p className="text-[10px] text-slate-500 line-clamp-2 mt-0.5 leading-relaxed">{kb.description || 'No description provided.'}</p>
              </CardHeader>
              <CardContent className="pt-2">
                <div className="grid grid-cols-2 gap-2 text-[10px] font-medium text-slate-500 border-t border-slate-100 pt-3">
                  <div className="flex items-center space-x-1">
                    <FileText className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-slate-700 font-semibold">{kb.total_documents} documents</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Layers className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-slate-700 font-semibold">{kb.total_chunks} chunks</span>
                  </div>
                  <div className="flex items-center space-x-1 col-span-2 text-slate-400">
                    <span>Embeddings: {kb.embedding_model}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-slate-100 mt-4 pt-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-slate-900 hover:bg-slate-50 p-0 text-[10px] font-bold"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/chat?kb_id=${kb.id}`);
                    }}
                  >
                    Open Assistant <ArrowRight className="w-3 h-3 ml-1" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-rose-600 hover:text-rose-700 hover:bg-rose-50 p-1"
                    onClick={(e) => handleDelete(kb.id, e)}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create Knowledge Base">
        <form onSubmit={handleCreate} className="space-y-4">
          <Input
            label="Collection Name"
            placeholder="e.g. Financial Reports 2026"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Input
            label="Description"
            placeholder="Brief overview of collection contents..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
          <Input
            label="Embedding Model"
            value={formData.embedding_model}
            onChange={(e) => setFormData({ ...formData, embedding_model: e.target.value })}
            disabled
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Chunk Size"
              type="number"
              value={formData.chunk_size}
              onChange={(e) => setFormData({ ...formData, chunk_size: parseInt(e.target.value) })}
            />
            <Input
              label="Chunk Overlap"
              type="number"
              value={formData.chunk_overlap}
              onChange={(e) => setFormData({ ...formData, chunk_overlap: parseInt(e.target.value) })}
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4 border-t border-slate-100">
            <Button type="button" variant="ghost" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={creating}>
              Create Collection
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

