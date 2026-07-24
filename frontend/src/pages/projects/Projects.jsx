import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  FolderGit2, 
  Plus, 
  MoreVertical, 
  Clock, 
  Users, 
  Activity,
  Search,
  SlidersHorizontal,
  ChevronRight
} from 'lucide-react';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';
import { formatDistanceToNow } from 'date-fns';

export default function Projects() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      return [
        { id: 1, name: 'Customer Churn Prediction', description: 'Predicting which customers are likely to churn in the next quarter.', status: 'Active', members: 4, updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), models: 3 },
        { id: 2, name: 'Support Ticket Routing', description: 'NLP model to automatically route support tickets to correct departments.', status: 'Active', members: 2, updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), models: 1 },
        { id: 3, name: 'Fraud Detection Pipeline', description: 'Real-time anomaly detection for financial transactions.', status: 'Archived', members: 5, updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(), models: 5 },
      ];
    }
  });

  const filteredProjects = projects?.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'All' || p.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">Projects</h1>
          <p className="text-xs text-slate-500 mt-0.5">Manage workspaces, models, datasets, and pipelines.</p>
        </div>
        <Button variant="primary" size="sm" className="flex items-center gap-1.5">
          <Plus className="w-3.5 h-3.5" />
          Create Project
        </Button>
      </div>

      {/* Filters contextual row */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
          <Input 
            placeholder="Search projects..." 
            className="pl-9"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
          <select 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 px-3 py-1.5 bg-white border border-slate-200 rounded text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-950 focus:border-slate-950 transition-colors"
          >
            <option value="All">All Statuses</option>
            <option value="Active">Active</option>
            <option value="Archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Projects listing grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {isLoading ? (
          <div className="col-span-full py-12 text-center text-slate-500 text-xs font-medium">Loading projects...</div>
        ) : filteredProjects?.length === 0 ? (
          <div className="col-span-full py-16 text-center border border-dashed border-slate-200 rounded-lg bg-white">
            <FolderGit2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="text-xs font-semibold text-slate-700">No projects found</p>
            <p className="text-[10px] text-slate-400 mt-0.5">Create your first project to start tracking ML models.</p>
          </div>
        ) : filteredProjects?.map((project) => (
          <Card key={project.id} className="hover:border-slate-400 transition-colors cursor-pointer group flex flex-col justify-between">
            <CardContent className="p-5 flex flex-col flex-1">
              <div className="flex justify-between items-start mb-3">
                <div className="p-2 bg-slate-100 rounded text-slate-700">
                  <FolderGit2 className="w-4 h-4" />
                </div>
                <Badge variant={project.status === 'Active' ? 'success' : 'default'}>
                  {project.status}
                </Badge>
              </div>
              
              <div className="space-y-1 mb-4 flex-1">
                <h3 className="text-sm font-bold text-slate-900 group-hover:text-slate-700 transition-colors flex items-center gap-1">
                  {project.name}
                  <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 transition-colors" />
                </h3>
                <p className="text-slate-500 text-xs line-clamp-2 leading-relaxed">
                  {project.description}
                </p>
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-3 border-t border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1" title="Team Members">
                    <Users className="w-3 h-3 text-slate-400" />
                    <span className="font-semibold text-slate-600">{project.members}</span>
                  </div>
                  <div className="flex items-center gap-1" title="Deployed Models">
                    <Activity className="w-3 h-3 text-slate-400" />
                    <span className="font-semibold text-slate-600">{project.models} models</span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>{formatDistanceToNow(new Date(project.updatedAt), { addSuffix: true })}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

