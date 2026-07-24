import React, { useState } from 'react';
import { Bot, Send, User, Sparkles } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';

export default function Chat() {
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: 'Hello! I am your Enterprise AI assistant. How can I help you today?' },
    { id: 2, role: 'user', content: 'Can you summarize the performance of the Customer Churn model?' },
    { id: 3, role: 'assistant', content: 'Based on the latest evaluation metrics, the Customer Churn model has an accuracy of 92.4% and an F1 score of 0.89 on the test dataset. The most important feature contributing to churn is `customer_support_calls`.' },
  ]);
  const [input, setInput] = useState('');

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setMessages([...messages, { id: Date.now(), role: 'user', content: input }]);
    setInput('');
    
    // Mock response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: 'assistant', 
        content: 'I understand. I am analyzing the latest metrics to provide you with more details.' 
      }]);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] p-4 max-w-5xl mx-auto w-full">
      <div className="flex items-center gap-2 mb-4">
        <Bot className="w-6 h-6 text-primary-600" />
        <h1 className="text-xl font-bold text-gray-900">Conversational AI</h1>
      </div>

      <Card className="flex-1 flex flex-col min-h-0 bg-white">
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-primary-100 text-primary-600' : 'bg-gray-100 text-gray-600'}`}>
                {msg.role === 'user' ? <User className="w-5 h-5" /> : <Sparkles className="w-5 h-5" />}
              </div>
              <div className={`max-w-[70%] p-4 rounded-lg ${msg.role === 'user' ? 'bg-primary-600 text-white rounded-tr-none' : 'bg-gray-50 text-gray-800 rounded-tl-none border border-gray-200'}`}>
                {msg.content}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-gray-200">
          <form onSubmit={handleSend} className="flex gap-2">
            <Input 
              className="flex-1"
              placeholder="Ask anything about your models, datasets, or experiments..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <Button type="submit" className="flex items-center justify-center">
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
