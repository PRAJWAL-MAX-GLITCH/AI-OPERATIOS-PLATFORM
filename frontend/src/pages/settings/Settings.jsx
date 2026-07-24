import React from 'react';
import { User, Shield, Bell, Key, Database } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuth } from '../../context/AuthContext';

export default function Settings() {
  const { user } = useAuth();

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Manage your account and workspace preferences</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="md:col-span-1 space-y-1">
          <button className="w-full text-left px-4 py-2 bg-primary-50 text-primary-700 font-medium rounded-lg flex items-center gap-3">
            <User className="w-5 h-5" />
            Profile
          </button>
          <button className="w-full text-left px-4 py-2 text-gray-600 hover:bg-gray-50 font-medium rounded-lg flex items-center gap-3">
            <Shield className="w-5 h-5" />
            Security
          </button>
          <button className="w-full text-left px-4 py-2 text-gray-600 hover:bg-gray-50 font-medium rounded-lg flex items-center gap-3">
            <Bell className="w-5 h-5" />
            Notifications
          </button>
          <button className="w-full text-left px-4 py-2 text-gray-600 hover:bg-gray-50 font-medium rounded-lg flex items-center gap-3">
            <Key className="w-5 h-5" />
            API Keys
          </button>
          <button className="w-full text-left px-4 py-2 text-gray-600 hover:bg-gray-50 font-medium rounded-lg flex items-center gap-3">
            <Database className="w-5 h-5" />
            Integrations
          </button>
        </div>

        <div className="md:col-span-3 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-6 mb-6">
                <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 text-2xl font-bold">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div>
                  <Button variant="outline">Change Avatar</Button>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input label="First Name" defaultValue="Admin" />
                <Input label="Last Name" defaultValue="User" />
                <Input label="Email Address" type="email" defaultValue={user?.username || 'admin@example.com'} className="col-span-2" />
                <Input label="Role" defaultValue={user?.role || 'Administrator'} disabled className="col-span-2" />
              </div>
              <div className="pt-4 flex justify-end">
                <Button>Save Changes</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
