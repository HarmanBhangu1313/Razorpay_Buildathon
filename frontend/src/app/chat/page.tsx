'use client'
import { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import CartConfirmation from '@/components/CartConfirmation';

import ReactMarkdown from 'react-markdown';

export default function ChatPage() {
    const [messages, setMessages] = useState([{ role: 'agent', content: 'Hi! How can I help you shop today?' }]);
    const [input, setInput] = useState('');
    const [sessionId, setSessionId] = useState<string>('');
    const [loading, setLoading] = useState(false);
    
    // state for checkout flow
    const [checkoutState, setCheckoutState] = useState<any>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }

    useEffect(() => {
        setSessionId(uuidv4());
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, checkoutState]);

    const sendMessage = async (e: any) => {
        e.preventDefault();
        if (!input.trim() || loading) return;
        
        const text = input;
        setInput('');
        setMessages(m => [...m, { role: 'user', content: text }]);
        setLoading(true);
        setCheckoutState(null);
        
        try {
            const res = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, message: text })
            });
            const data = await res.json();
            
            if (data.response) {
                setMessages(m => [...m, { role: 'agent', content: data.response }]);
            }
            
            if (data.ready_for_checkout) {
                setCheckoutState({
                    cart: data.cart,
                    guardrails: data.guardrails
                });
            }
        } catch (err) {
            console.error(err);
            setMessages(m => [...m, { role: 'agent', content: '⚠️ API Rate Limit Exceeded. Please wait 10 seconds and try again.' }]);
        } finally {
            setLoading(false);
        }
    };
    
    const handleConfirm = async () => {
        const res = await fetch('http://localhost:8000/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, email: "buyer@example.com" })
        });
        const data = await res.json();
        
        if (data.success && data.payment_link) {
            window.open(data.payment_link, '_blank');
            setMessages(m => [...m, { role: 'agent', content: '✅ I have generated your payment link! Complete your payment in the new tab.' }]);
            setCheckoutState(null);
        } else {
            alert("Checkout failed: " + data.error);
        }
    };

    return (
        <div className="flex h-screen bg-gray-100 p-8 justify-center">
            <div className="w-full max-w-2xl bg-white shadow-xl rounded-xl flex flex-col overflow-hidden">
                <div className="p-4 bg-black text-white font-bold text-lg flex justify-between items-center">
                    <span>AgentShop AI Assistant</span>
                    <span className="text-xs font-normal text-gray-400">Session: {sessionId ? sessionId.substring(0,8) : '...'}</span>
                </div>
                
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((m, i) => (
                        <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-black whitespace-pre-wrap'}`}>
                                {m.role === 'user' ? (
                                    m.content
                                ) : (
                                    <div className="prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0">
                                        <ReactMarkdown>
                                            {m.content}
                                        </ReactMarkdown>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    
                    {checkoutState && (
                        <div className="flex justify-start mt-4">
                            <div className="max-w-[80%]">
                                <CartConfirmation 
                                    cart={checkoutState.cart} 
                                    guardrails={checkoutState.guardrails}
                                    onConfirm={handleConfirm}
                                />
                            </div>
                        </div>
                    )}
                    
                    {loading && <div className="text-gray-500 animate-pulse text-sm ml-2">AgentShop is typing...</div>}
                    <div ref={messagesEndRef} />
                </div>
                
                <form onSubmit={sendMessage} className="p-4 border-t flex gap-2">
                    <input 
                        type="text" 
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        placeholder="I need a laptop under ₹70,000 for college..." 
                        className="flex-1 border rounded-full px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500 bg-white text-black placeholder-gray-400"
                        disabled={loading || checkoutState !== null}
                    />
                    <button type="submit" disabled={loading || checkoutState !== null || !input.trim()} className="bg-black text-white px-6 rounded-full disabled:opacity-50 hover:bg-gray-800 font-medium">
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
}
