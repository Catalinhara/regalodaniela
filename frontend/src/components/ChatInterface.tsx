import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import './ChatInterface.css';
import ReactMarkdown from 'react-markdown';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

interface Props {
    onBack: () => void;
}

export const ChatInterface: React.FC<Props> = ({ onBack }) => {
    const { i18n } = useTranslation();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    // Load History on Mount
    useEffect(() => {
        const loadHistory = async () => {
            setLoading(true);
            try {
                // For MVP, we send a "ping" to get a warm greeting from the new personality
                // But we append it to avoid flickering if we had a local greeting
                const response = await api.sendChat("START_SESSION", i18n.language);
                setMessages([{ role: 'assistant', content: response.content }]);
            } catch (e) {
                console.error(e);
                setMessages([{
                    role: 'assistant',
                    content: i18n.language.startsWith('es')
                        ? "¡Hola! He tenido un pequeño traspié con mi memoria, pero aquí estoy. ¿Qué tal va todo?"
                        : "Hi there! I had a little hiccup, but I'm here now. How's it going?"
                }]);
            } finally {
                setLoading(false);
            }
        };
        loadHistory();
    }, []);

    useEffect(() => {
        // Debounced scroll to bottom for stability
        const timeoutId = setTimeout(() => {
            bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 100);
        return () => clearTimeout(timeoutId);
    }, [messages, loading]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMsg: Message = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const response = await api.sendChat(userMsg.content, i18n.language);
            setMessages(prev => [...prev, { role: 'assistant', content: response.content }]);
        } catch (e) {
            console.error(e);
            setMessages(prev => [...prev, { role: 'assistant', content: "I'm having trouble connecting right now." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="chat-overlay-fixed">
            <div className="chat-sheet">
                {/* 1. HEADER (Fixed) */}
                <div className="cc-header">
                    <button className="cc-btn-back" onClick={onBack}>✕</button>
                    <div className="cc-title-group">
                        <div className="cc-title">Companion Chat</div>
                        <span className="cc-subtitle">
                            <span className="cc-status-dot"></span>
                            Online
                        </span>
                    </div>
                    <div style={{ width: 36 }}></div>
                </div>

                {/* 2. MESSAGES (Scrollable) */}
                <div className="cc-messages">
                    {messages.map((m, i) => (
                        <div key={i} className={`cc-msg ${m.role === 'user' ? 'cc-msg-user' : 'cc-msg-assistant'}`}>
                            {m.role === 'user' ? (
                                m.content
                            ) : (
                                <ReactMarkdown>{m.content}</ReactMarkdown>
                            )}
                        </div>
                    ))}
                    {loading && (
                        <div className="cc-msg cc-msg-assistant" style={{ fontStyle: 'italic', color: '#90A4AE' }}>
                            {i18n.language.startsWith('es') ? "Compy está pensando..." : "Compy is thinking..."}
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                {/* 3. INPUT (Fixed Bottom) */}
                <div className="cc-input-area">
                    <div className="cc-input-wrapper">
                        <input
                            className="cc-input"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleSend()}
                            placeholder="Type your message..."
                            disabled={loading}
                        />
                        <button className="cc-send-btn" onClick={handleSend} disabled={loading}>
                            ↑
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
