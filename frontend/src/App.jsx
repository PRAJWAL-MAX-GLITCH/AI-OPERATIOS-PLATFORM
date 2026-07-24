import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './routes/ProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';

import DatasetList from './pages/datasets/DatasetList';
import DatasetUpload from './pages/datasets/DatasetUpload';
import DatasetDetails from './pages/datasets/DatasetDetails';
import FeatureEngineering from './pages/features/FeatureEngineering';
import TrainingJobs from './pages/training/TrainingJobs';
import Experiments from './pages/experiments/Experiments';
import ModelRegistry from './pages/models/ModelRegistry';
import PredictionUI from './pages/predictions/PredictionUI';

import Projects from './pages/projects/Projects';
import KnowledgeBases from './pages/rag/KnowledgeBases';
import Chat from './pages/chat/Chat';
import Agents from './pages/agents/Agents';
import Monitoring from './pages/monitoring/Monitoring';
import Settings from './pages/settings/Settings';

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Routes Wrapper */}
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            
            {/* ML Platform Routes */}
            <Route path="/projects" element={<Projects />} />
            <Route path="/datasets" element={<DatasetList />} />
            <Route path="/datasets/upload" element={<DatasetUpload />} />
            <Route path="/datasets/:id" element={<DatasetDetails />} />
            <Route path="/features" element={<FeatureEngineering />} />
            <Route path="/training" element={<TrainingJobs />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/models" element={<ModelRegistry />} />
            <Route path="/predict" element={<PredictionUI />} />
            <Route path="/rag" element={<KnowledgeBases />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Route>

        {/* Redirect root to dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
