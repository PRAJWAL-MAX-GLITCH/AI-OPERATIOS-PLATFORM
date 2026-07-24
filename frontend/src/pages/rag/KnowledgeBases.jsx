import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Database, FileText, Search, Trash2, ArrowRight, Layers, CheckCircle2, Clock } from 'lucide-react';
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Knowledge Bases</h1>
          <p className="text-gray-500">Manage vector embeddings, document collections, and retrieval configurations.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Create Knowledge Base
        </Button>
      </div>

      <div className="flex items-center space-x-4 bg-white p-4 border border-gray-200 rounded-lg shadow-sm">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            className="pl-9"
            placeholder="Search knowledge bases..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading knowledge bases...</div>
      ) : filtered.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <Database className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-gray-900">No Knowledge Bases Found</h3>
            <p className="text-sm text-gray-500 mt-1">Get started by creating a new knowledge base collection.</p>
            <Button className="mt-4" onClick={() => setIsModalOpen(true)}>
              <Plus className="w-4 h-4 mr-2" /> Create Knowledge Base
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((kb) => (
            <Card
              key={kb.id}
              className="hover:shadow-md transition-shadow cursor-pointer border border-gray-200"
              onClick={() => navigate(`/rag/documents?kb_id=${kb.id}`)}
            >
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <div className="space-y-1">
                  <CardTitle className="text-base font-bold text-gray-900">{kb.name}</CardTitle>
                  <p className="text-xs text-gray-500 line-clamp-2">{kb.description || 'No description provided.'}</p>
                </div>
                <Badge variant={kb.is_indexed ? 'success' : 'warning'}>
                  {kb.is_indexed ? 'Indexed' : 'Pending Index'}
                </Badge>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="grid grid-cols-2 gap-2 text-xs border-t border-gray-100 pt-3 text-gray-600">
                  <div className="flex items-center space-x-1">
                    <FileText className="w-3.5 h-3.5 text-gray-400" />
                    <span>{kb.total_documents} Documents</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Layers className="w-3.5 h-3.5 text-gray-400" />
                    <span>{kb.total_chunks} Chunks</span>
                  </div>
                  <div className="flex items-center space-x-1 col-span-2">
                    <Database className="w-3.5 h-3.5 text-gray-400" />
                    <span>Model: {kb.embedding_model}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-gray-100 pt-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-primary-600 hover:text-primary-700 hover:bg-primary-50 p-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/chat?kb_id=${kb.id}`);
                    }}
                  >
                    Open Chat <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    onClick={(e) => handleDelete(kb.id, e)}
                  >
                    <Trash2 className="w-4 h-4" />
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
            label="Knowledge Base Name"
            placeholder="e.g. Financial Reports 2026"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Input
            label="Description"
            placeholder="Brief overview of the documents in this collection"
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

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={creating}>
              Create Knowledge Base
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
