'use client'
import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Dashboard() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/audit')
      .then(res => res.json())
      .then(data => {
        setLogs(data);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8 text-black">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <header className="flex justify-between items-center bg-white p-6 rounded-xl shadow-sm border">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">AgentShop Control Center</h1>
            <p className="text-gray-500 mt-1">AI-Native Merchant Dashboard</p>
          </div>
          <Link href="/chat" className="bg-black text-white px-6 py-2 rounded-lg font-medium hover:bg-gray-800">
            Open Chat Agent
          </Link>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <h3 className="text-gray-500 text-sm font-medium uppercase tracking-wider">Revenue</h3>
            <div className="text-3xl font-bold mt-2">₹1,24,580</div>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <h3 className="text-gray-500 text-sm font-medium uppercase tracking-wider">AI-Assisted Orders</h3>
            <div className="text-3xl font-bold mt-2">18</div>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <h3 className="text-gray-500 text-sm font-medium uppercase tracking-wider">Upsell Conversion</h3>
            <div className="text-3xl font-bold mt-2">31%</div>
          </div>
        </div>

        <section className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="p-6 border-b bg-gray-50 flex justify-between items-center">
            <h2 className="text-xl font-bold">Audit Trail Timeline</h2>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded font-medium">Deterministic Logging Enabled</span>
          </div>
          
          <div className="p-6">
            {loading ? (
              <div className="text-gray-500">Loading audit logs...</div>
            ) : (
              <div className="space-y-6">
                {logs.map((log: any, idx: number) => (
                  <div key={log.id} className="flex gap-4 relative">
                    {/* Timeline line */}
                    {idx !== logs.length - 1 && (
                      <div className="absolute left-4 top-8 bottom-[-24px] w-0.5 bg-gray-200"></div>
                    )}
                    
                    {/* Icon */}
                    <div className={`relative z-10 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center border-2 
                      ${log.decision === 'APPROVED' ? 'bg-green-50 border-green-200 text-green-600' : 
                        log.decision === 'REJECTED' ? 'bg-red-50 border-red-200 text-red-600' : 
                        'bg-blue-50 border-blue-200 text-blue-600'}`}>
                      {log.decision === 'APPROVED' ? '✓' : log.decision === 'REJECTED' ? '✗' : 'i'}
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1 bg-gray-50 border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <span className="font-bold text-lg mr-2 uppercase tracking-tight">{log.action.replace(/_/g, ' ')}</span>
                          <span className={`text-xs px-2 py-1 rounded font-bold ${log.decision === 'APPROVED' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {log.decision}
                          </span>
                        </div>
                        <span className="text-gray-400 text-sm">{new Date(log.timestamp).toLocaleTimeString()}</span>
                      </div>
                      
                      <p className="text-gray-700 mb-3">{log.reason}</p>
                      
                      {log.checks && log.checks.length > 0 && (
                        <div className="mt-3 bg-white p-3 rounded border text-sm">
                          <h4 className="font-semibold text-xs text-gray-500 uppercase tracking-wider mb-2">Evaluated Rules</h4>
                          <div className="space-y-1">
                            {log.checks.map((check: any, i: number) => (
                              <div key={i} className="flex gap-2 items-start">
                                {check.status === 'PASS' ? <span className="text-green-600">✓</span> : 
                                 check.status === 'FAIL' ? <span className="text-red-600">✗</span> : 
                                 <span className="text-yellow-600">⧖</span>}
                                <span><span className="font-medium">{check.name}:</span> {check.reason}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {log.api_calls && log.api_calls.length > 0 && (
                        <div className="mt-3 bg-gray-900 text-green-400 p-3 rounded font-mono text-xs overflow-x-auto">
                          {log.api_calls.map((api: any, i: number) => (
                            <div key={i}>
                              <div>$ POST {api.endpoint} (Amount: {api.amount_inr} INR -> {api.amount_paise} paise)</div>
                              <div className="text-gray-400 mt-1">{JSON.stringify(api.result)}</div>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      <div className="mt-2 text-xs text-gray-400 font-mono">Session: {log.session_id}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

      </div>
    </div>
  );
}
