import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { CheckCircle2 } from 'lucide-react';

export default function PredictionUI() {
  const [formData, setFormData] = useState({ age: '', income: '', balance: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Simulate API inference call
    setTimeout(() => {
      setResult({
        prediction: 'Churn',
        confidence: 0.87,
        details: 'High risk based on low balance and tenure.'
      });
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Live Prediction</h1>
        <p className="text-gray-500">Test the currently deployed Production model.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Input Features</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input 
                label="Age" 
                type="number" 
                value={formData.age}
                onChange={(e) => setFormData({...formData, age: e.target.value})}
                required 
              />
              <Input 
                label="Income" 
                type="number" 
                value={formData.income}
                onChange={(e) => setFormData({...formData, income: e.target.value})}
                required 
              />
              <Input 
                label="Account Balance" 
                type="number" 
                value={formData.balance}
                onChange={(e) => setFormData({...formData, balance: e.target.value})}
                required 
              />
              <Button type="submit" className="w-full" isLoading={loading}>
                Run Prediction
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Inference Result</CardTitle>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle2 className="w-6 h-6" />
                  <span className="font-semibold text-lg">Prediction Successful</span>
                </div>
                
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-500 mb-1">Predicted Class</p>
                  <p className="text-3xl font-bold text-gray-900">{result.prediction}</p>
                </div>
                
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-500 mb-1">Confidence Score</p>
                  <p className="text-3xl font-bold text-gray-900">{(result.confidence * 100).toFixed(1)}%</p>
                </div>
                
                <p className="text-sm text-gray-600">{result.details}</p>
              </div>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-400 text-sm py-12">
                Submit the form to see prediction results here.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
