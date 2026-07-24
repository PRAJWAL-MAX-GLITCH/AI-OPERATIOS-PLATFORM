import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { ArrowRight, Database, Settings, ArrowDownToLine, Binary } from 'lucide-react';

export default function FeatureEngineering() {
  const steps = [
    { name: 'Raw Dataset', icon: Database, details: '15,420 rows, 24 cols' },
    { name: 'Missing Value Imputation', icon: ArrowDownToLine, details: 'Median strategy for numerical, Mode for categorical' },
    { name: 'Categorical Encoding', icon: Binary, details: 'One-hot encoding for "plan_type", Ordinal for "satisfaction"' },
    { name: 'Feature Scaling', icon: Settings, details: 'StandardScaler applied to continuous variables' },
    { name: 'Processed Dataset', icon: Database, details: '15,420 rows, 38 cols ready for training' }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Feature Engineering Pipeline</h1>
        <p className="text-gray-500">Visualize preprocessing steps applied to datasets before model training.</p>
      </div>

      <div className="flex flex-col space-y-4">
        {steps.map((step, index) => {
          const Icon = step.icon;
          return (
            <div key={step.name} className="flex flex-col">
              <Card className="w-full">
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="p-3 bg-primary-50 rounded-full text-primary-600">
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{step.name}</h3>
                      <p className="text-sm text-gray-500">{step.details}</p>
                    </div>
                  </div>
                  <Badge variant={index === 0 || index === steps.length - 1 ? 'success' : 'primary'}>
                    {index === 0 ? 'Input' : index === steps.length - 1 ? 'Output' : 'Transformation'}
                  </Badge>
                </CardContent>
              </Card>
              {index < steps.length - 1 && (
                <div className="flex justify-center my-2">
                  <ArrowRight className="w-6 h-6 text-gray-300 transform rotate-90" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
