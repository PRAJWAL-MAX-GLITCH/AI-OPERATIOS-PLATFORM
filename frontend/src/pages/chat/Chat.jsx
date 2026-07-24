import React, { useState } from 'react';
import { Bot, Send, User, Sparkles, Plus, Clock, MessageSquare, Terminal, RefreshCw, ChevronRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';

export default function Chat() {
  const [conversations, setConversations] = useState([
    { id: 1, title: 'Summarize Churn Model', active: true },
    { id: 2, title: 'RAG transformer details', active: false },
    { id: 3, title: 'Data anomalies check', active: false }
  ]);

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
    
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: 'assistant', 
        content: 'I understand. I am analyzing the latest metrics to provide you with more details.' 
      }]);
    }, 1000);
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-5 select-none">
      {/* Conversation History Sidebar */}
      <div className="w-56 flex flex-col bg-white border border-slate-200/80 rounded-lg p-3 space-y-4">
        <Button variant="secondary" size="sm" className="w-full flex items-center justify-center gap-1">
          <Plus className="w-3.5 h-3.5" /> New Chat
        </Button>
        <div className="flex-1 space-y-1 overflow-y-auto">
          <span className="block px-2 text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">Recent Conversations</span>
          {conversations.map((c) => (
            <button
              key={c.id}
              className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-left text-xs transition-colors ${
                c.active ? 'bg-slate-100 text-slate-900 font-semibold' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="truncate">{c.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main chat box workspace */}
      <div className="flex-grow flex flex-col min-h-0 bg-white border border-slate-200/80 rounded-lg overflow-hidden">
        {/* Chat window Header */}
        <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-slate-950" />
            <span className="text-xs font-bold text-slate-900">Conversational AI Assistant</span>
          </div>
          <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-bold uppercase tracking-wider">Default Model</span>
        </div>

        {/* Message space */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {messages.map((msg) => (
            <div key={msg.id} className="flex gap-4 items-start max-w-3xl">
              <div className={`w-7 h-7 rounded flex items-center justify-center flex-shrink-0 text-xs font-bold ${msg.role === 'user' ? 'bg-slate-100 text-slate-800' : 'bg-slate-950 text-white shadow-sm'}`}>
                {msg.role === 'user' ? 'U' : 'AI'}
              </div>
              <div className="space-y-1">
                <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  {msg.role === 'user' ? 'Operator' : 'Assistant'}
                </span>
                <p className="text-xs text-slate-800 leading-relaxed font-sans">{msg.content}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Chat input composer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <form onSubmit={handleSend} className="flex gap-2">
            <Input 
              className="flex-1"
              placeholder="Ask anything about your models, datasets, or experiments..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <Button type="submit" size="sm" className="px-3">
              <Send className="w-3.5 h-3.5" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}

