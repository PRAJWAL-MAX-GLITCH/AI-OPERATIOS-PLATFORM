import React from 'react';
import { Activity, Cpu, Database, Server, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';

export default function Monitoring() {
  const metrics = [
    { label: 'CPU Usage', value: '45%', icon: Cpu, color: 'text-blue-600', bg: 'bg-blue-100' },
    { label: 'Memory Usage', value: '12.4 GB', icon: Server, color: 'text-purple-600', bg: 'bg-purple-100' },
    { label: 'Active DB Connections', value: '142', icon: Database, color: 'text-green-600', bg: 'bg-green-100' },
    { label: 'Error Rate', value: '0.02%', icon: AlertTriangle, color: 'text-orange-600', bg: 'bg-orange-100' },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
        <p className="text-gray-500 mt-1">Real-time infrastructure and model serving health</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {metrics.map((metric, idx) => (
          <Card key={idx}>
            <CardContent className="p-6 flex items-center gap-4">
              <div className={`p-3 rounded-lg ${metric.bg} ${metric.color}`}>
                <metric.icon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">{metric.label}</p>
                <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>API Latency (ms)</CardTitle>
          </CardHeader>
          <CardContent className="h-64 flex items-center justify-center text-gray-400 bg-gray-50 rounded-b-lg border-t border-gray-100">
            Chart Placeholder
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Model Requests / min</CardTitle>
          </CardHeader>
          <CardContent className="h-64 flex items-center justify-center text-gray-400 bg-gray-50 rounded-b-lg border-t border-gray-100">
            Chart Placeholder
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
