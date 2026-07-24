import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  FolderGit2, 
  Plus, 
  MoreVertical, 
  Clock, 
  Users, 
  Activity,
  Search
} from 'lucide-react';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import api from '../../services/api';
import { formatDistanceToNow } from 'date-fns';

export default function Projects() {
  const [searchQuery, setSearchQuery] = useState('');

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      // Mock data for now, would be replaced by actual API call
      // const response = await api.get('/projects');
      // return response.data;
      return [
        { id: 1, name: 'Customer Churn Prediction', description: 'Predicting which customers are likely to churn in the next quarter.', status: 'Active', members: 4, updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), models: 3 },
        { id: 2, name: 'Support Ticket Routing', description: 'NLP model to automatically route support tickets to correct departments.', status: 'Active', members: 2, updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), models: 1 },
        { id: 3, name: 'Fraud Detection Pipeline', description: 'Real-time anomaly detection for financial transactions.', status: 'Archived', members: 5, updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(), models: 5 },
      ];
    }
  });

  const filteredProjects = projects?.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-500 mt-1">Manage your team's AI initiatives and workspaces</p>
        </div>
        <Button className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Project
        </Button>
      </div>

      <div className="flex gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <Input 
            placeholder="Search projects..." 
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <select className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-sm font-medium text-gray-700">
          <option>All Status</option>
          <option>Active</option>
          <option>Archived</option>
        </select>
        <select className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-sm font-medium text-gray-700">
          <option>Sort by: Recent</option>
          <option>Sort by: Name</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          <div className="col-span-full py-12 text-center text-gray-500">Loading projects...</div>
        ) : filteredProjects?.map((project) => (
          <Card key={project.id} className="hover:border-primary-500 transition-colors cursor-pointer group">
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-primary-50 rounded-lg text-primary-600">
                  <FolderGit2 className="w-6 h-6" />
                </div>
                <button className="text-gray-400 hover:text-gray-600">
                  <MoreVertical className="w-5 h-5" />
                </button>
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
                {project.name}
              </h3>
              <p className="text-gray-500 text-sm mb-4 line-clamp-2">
                {project.description}
              </p>

              <div className="flex items-center justify-between text-sm text-gray-500 mt-auto pt-4 border-t border-gray-100">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1.5 tooltip" title="Team Members">
                    <Users className="w-4 h-4" />
                    <span>{project.members}</span>
                  </div>
                  <div className="flex items-center gap-1.5 tooltip" title="Deployed Models">
                    <Activity className="w-4 h-4" />
                    <span>{project.models}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4" />
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
