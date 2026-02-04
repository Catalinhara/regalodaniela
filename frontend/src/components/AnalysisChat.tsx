import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import './AnalysisChat.css';
import ReactMarkdown from 'react-markdown';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

interface AnalysisChatProps {
    context: { type: string; id: string; name: string };
    onBack: () => void;
}

export const AnalysisChat: React.FC<AnalysisChatProps> = ({ context, onBack }) => {
    const { i18n } = useTranslation();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    // Initial greeting / trigger analysis automatically
    useEffect(() => {
        const initAnalysis = async () => {
            setLoading(true);
            try {
                const response = await api.sendAnalysisChat(
                    { type: context.type, id: context.id },
                    "Please provide a deep analysis of this case.",
                    [],
                    i18n.language
                );
                setMessages([{ role: 'assistant', content: response.content }]);
            } catch (e) {
                console.error(e);
                setMessages([{ role: 'assistant', content: "I'm unable to perform the analysis right now." }]);
            } finally {
                setLoading(false);
            }
        };
        initAnalysis();
    }, [context.id, context.type, i18n.language]);

    useEffect(() => {
        // Use a small timeout to ensure DOM has updated before scrolling
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
            const history = messages.map(m => ({ role: m.role, content: m.content }));
            const response = await api.sendAnalysisChat(
                { type: context.type, id: context.id },
                userMsg.content,
                history,
                i18n.language
            );
            setMessages(prev => [...prev, { role: 'assistant', content: response.content }]);
        } catch (e) {
            console.error(e);
            setMessages(prev => [...prev, { role: 'assistant', content: "An error occurred during consultation." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="analysis-modal-overlay">
            <div className="analysis-sheet">
                {/* 1. Header (Fixed) */}
                <div className="ac-header">
                    <button className="ac-btn-close" onClick={onBack}>✕</button>
                    <div>
                        <div className="ac-title">Deep Analysis</div>
                        <span className="ac-subtitle">Consulting on {context.name}</span>
                    </div>
                    <div style={{ width: 36 }}></div> {/* Spacer for balance */}
                </div>

                {/* 2. Messages (Scrollable) */}
                <div className="ac-messages">
                    {messages.map((m, i) => (
                        <div key={i} className={`ac-msg ${m.role === 'user' ? 'ac-msg-user' : 'ac-msg-assistant'}`}>
                            {m.role === 'user' ? (
                                m.content
                            ) : (
                                <ReactMarkdown>{m.content}</ReactMarkdown>
                            )}
                        </div>
                    ))}
                    {loading && (
                        <div className="ac-msg ac-msg-assistant" style={{ fontStyle: 'italic', color: '#90A4AE' }}>
                            {i18n.language.startsWith('es')
                                ? "Generando análisis profundo, puede tardar varios segundos..."
                                : "Generating deep analysis, this may take a few seconds..."}
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                {/* 3. Input (Fixed Bottom) */}
                <div className="ac-input-area">
                    <div className="ac-input-wrapper">
                        <textarea
                            className="ac-input"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={e => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend();
                                }
                            }}
                            placeholder="Consult Specialist..."
                            disabled={loading}
                            rows={1}
                        />
                        <button className="ac-send-btn" onClick={handleSend} disabled={loading}>
                            ↑
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
