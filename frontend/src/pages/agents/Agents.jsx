import React from 'react';
import { Bot, Play, Settings2, Plus, Terminal } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

export default function Agents() {
  const agents = [
    { id: 1, name: 'Data Preprocessing Agent', role: 'Data Engineer', status: 'Idle', lastRun: '2 hours ago' },
    { id: 2, name: 'Model Evaluation Agent', role: 'ML Engineer', status: 'Running', lastRun: 'Just now' },
    { id: 3, name: 'Report Generator Agent', role: 'Analyst', status: 'Idle', lastRun: '1 day ago' },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Agents</h1>
          <p className="text-gray-500 mt-1">Manage and orchestrate autonomous AI agents</p>
        </div>
        <Button className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Create Agent
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {agents.map((agent) => (
          <Card key={agent.id} className="hover:border-primary-500 transition-colors">
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-lg ${agent.status === 'Running' ? 'bg-green-100 text-green-600' : 'bg-primary-50 text-primary-600'}`}>
                  <Bot className="w-6 h-6" />
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  agent.status === 'Running' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                }`}>
                  {agent.status}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">{agent.name}</h3>
              <p className="text-sm text-gray-500 mb-4">Role: {agent.role}</p>
              
              <div className="flex gap-2 mt-auto pt-4 border-t border-gray-100">
                <Button variant="outline" size="sm" className="flex-1">
                  <Settings2 className="w-4 h-4 mr-2" />
                  Configure
                </Button>
                <Button variant={agent.status === 'Running' ? 'outline' : 'primary'} size="sm" className="flex-1">
                  <Play className="w-4 h-4 mr-2" />
                  {agent.status === 'Running' ? 'Stop' : 'Run'}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Terminal className="w-5 h-5 text-gray-500" />
            Agent Activity Logs
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-gray-200">
            {[1, 2, 3].map((log) => (
              <div key={log} className="p-4 hover:bg-gray-50 flex items-center justify-between text-sm">
                <div className="flex items-center gap-3">
                  <span className="text-gray-400 font-mono">10:42 AM</span>
                  <span className="font-medium text-gray-900">Model Evaluation Agent</span>
                  <span className="text-gray-500">started evaluating Random Forest on test_set_v2...</span>
                </div>
                <span className="text-blue-600 font-medium">In Progress</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
