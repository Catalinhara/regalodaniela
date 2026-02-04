import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import './ColleagueList.css';

interface Colleague {
    id: string;
    name: string;
    relationship_type: string; // Stored as "Hierarchy (Characteristics)" or just "Hierarchy"
}

interface Props {
    onCheckIn: (type: string, id: string, name: string) => void;
    onAnalyze: (type: string, id: string, name: string) => void;
    onBack: () => void;
}

export const ColleagueList: React.FC<Props> = ({ onCheckIn, onAnalyze, onBack }) => {
    const { t } = useTranslation();
    const [colleagues, setColleagues] = useState<Colleague[]>([]);
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedColleague, setSelectedColleague] = useState<Colleague | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [history, setHistory] = useState<any[]>([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [expandedHistoryId, setExpandedHistoryId] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        name: '',
        hierarchy: 'Peer' as 'Peer' | 'Mentor' | 'Supervisee' | 'Boss',
        characteristics: '' // Free text field
    });

    // Manage background scroll lock
    useEffect(() => {
        if (modalOpen || selectedColleague) {
            document.body.classList.add('modal-open');
        } else {
            document.body.classList.remove('modal-open');
        }
        return () => document.body.classList.remove('modal-open');
    }, [modalOpen, selectedColleague]);

    const fetchColleagues = async () => {
        setIsLoading(true);
        try {
            setColleagues(await api.getColleagues());
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => { fetchColleagues(); }, []);

    useEffect(() => {
        if (selectedColleague) {
            loadHistory(selectedColleague.id);
        } else {
            setHistory([]);
        }
    }, [selectedColleague]);

    const loadHistory = async (colleagueId: string) => {
        setLoadingHistory(true);
        try {
            const data = await api.getColleagueHistory(colleagueId);
            setHistory(data);
        } catch (e) {
            console.error("Failed to load history", e);
        } finally {
            setLoadingHistory(false);
        }
    };

    const handleAdd = async () => {
        if (!formData.name?.trim()) return;

        try {
            // Construct relationship_type from hierarchy + characteristics
            const relationshipType = formData.characteristics.trim()
                ? `${formData.hierarchy} (${formData.characteristics.trim()})`
                : formData.hierarchy;

            const payload = {
                name: formData.name.trim(),
                relationship_type: relationshipType
            };

            await api.createColleague(payload);
            setModalOpen(false);
            resetForm();
            fetchColleagues();
        } catch (e) {
            console.error('Failed to add colleague', e);
        }
    };

    const resetForm = () => {
        setFormData({
            name: '',
            hierarchy: 'Peer',
            characteristics: ''
        });
    };

    const getInitials = (name: string) => {
        if (!name) return '??';
        const parts = name.trim().split(' ');
        if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
        return name.substring(0, 2).toUpperCase();
    };

    // Parse relationship_type into hierarchy and characteristics
    const parseRelationship = (relationshipType: string): { hierarchy: string; characteristics: string } => {
        const match = relationshipType.match(/^([^(]+)(?:\s*\(([^)]+)\))?$/);
        if (match) {
            return {
                hierarchy: match[1].trim(),
                characteristics: match[2]?.trim() || ''
            };
        }
        return { hierarchy: relationshipType, characteristics: '' };
    };

    const getRelationshipLabel = (relationshipType: string): string => {
        const { hierarchy, characteristics } = parseRelationship(relationshipType);

        // Translate hierarchy
        let translatedHierarchy = hierarchy;
        switch (hierarchy) {
            case 'Peer':
                translatedHierarchy = t('colleagues_module.relationships.Peer');
                break;
            case 'Mentor':
                translatedHierarchy = t('colleagues_module.relationships.Mentor');
                break;
            case 'Supervisee':
                translatedHierarchy = t('colleagues_module.relationships.Supervisee');
                break;
            case 'Boss':
                translatedHierarchy = t('colleagues_module.relationships.Boss');
                break;
        }

        // Combine with characteristics (not translated)
        return characteristics
            ? `${translatedHierarchy} (${characteristics})`
            : translatedHierarchy;
    };

    const getAuraClass = (relationshipType: string) => {
        const { hierarchy, characteristics } = parseRelationship(relationshipType);

        // Use characteristics to determine aura if it contains certain keywords
        const lowerChars = characteristics.toLowerCase();
        if (lowerChars.includes('narcisista') || lowerChars.includes('narcissistic') ||
            lowerChars.includes('tóxico') || lowerChars.includes('toxic') ||
            lowerChars.includes('hostil') || lowerChars.includes('hostile')) {
            return 'aura-narcissistic';
        }

        // Otherwise use hierarchy
        if (hierarchy === 'Mentor') return 'aura-mentor';
        if (hierarchy === 'Supervisee') return 'aura-supervisee';
        if (hierarchy === 'Boss') return 'aura-boss';
        return 'aura-peer';
    };

    return (
        <div className="colleagues-container">
            {/* ATMOSPHERIC BACKGROUND BLOBS */}
            <div className="bg-blob blob-1"></div>
            <div className="bg-blob blob-2"></div>
            <div className="bg-blob blob-3"></div>

            {/* STICKY GLASS HEADER */}
            <header className="colleagues-header">
                <button className="btn-back-clean" onClick={onBack} aria-label="Back">
                    ‹
                </button>
                <div className="header-title-container">
                    <h1>{t('colleagues_module.title')}</h1>
                    <span>{t('colleagues_module.subtitle')}</span>
                </div>
                <button className="btn-add-action" onClick={() => setModalOpen(true)} aria-label={t('colleagues_module.add_action')}>
                    +
                </button>
            </header>

            <main className="colleagues-viewport">
                {isLoading && <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{t('colleagues_module.loading')}</div>}

                {!isLoading && colleagues.length === 0 ? (
                    <div className="colleagues-empty">
                        <div className="colleagues-empty-icon">🤝</div>
                        <h3>{t('colleagues_module.empty_title')}</h3>
                        <p>{t('colleagues_module.empty_text')}</p>
                        <button className="btn-premium-submit" onClick={() => setModalOpen(true)} style={{ maxWidth: '200px', margin: '20px auto' }}>
                            {t('colleagues_module.add_first')}
                        </button>
                    </div>
                ) : (
                    <div className="colleagues-grid-v2">
                        {colleagues.map((colleague, index) => {
                            const auraClass = getAuraClass(colleague.relationship_type);

                            return (
                                <div
                                    key={colleague.id}
                                    className={`colleague-card-v2 card-float-${(index % 3) + 1}`}
                                    onClick={() => setSelectedColleague(colleague)}
                                >
                                    <div className={`avatar-sphere ${auraClass}`}>
                                        <div className="getInitials">{getInitials(colleague.name)}</div>
                                    </div>
                                    <div className="colleague-info-v2">
                                        <h3>{colleague.name}</h3>
                                        <p>{getRelationshipLabel(colleague.relationship_type)}</p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>

            {/* PREMIUM MODAL - ADD COLLEAGUE */}
            {modalOpen && (
                <div className="premium-modal-overlay" onClick={() => setModalOpen(false)}>
                    <div className="premium-modal-card" onClick={e => e.stopPropagation()}>
                        <div className="sheet-handle"></div>
                        <div className="modal-header-v2">
                            <h2>{t('colleagues_module.new_title')}</h2>
                            <button className="btn-close-v2" onClick={() => setModalOpen(false)}>×</button>
                        </div>

                        <div className="avatar-stage">
                            <div className="avatar-preview-v2">
                                <div className="getInitials">{getInitials(formData.name || 'CO')}</div>
                            </div>
                        </div>

                        <div className="premium-form-grid">
                            <div>
                                <label className="field-label">{t('colleagues_module.name_label')}</label>
                                <input
                                    className="input-soft"
                                    placeholder={t('colleagues_module.name_placeholder')}
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="field-label">{t('colleagues_module.hierarchy_label')}</label>
                                <select
                                    className="input-soft"
                                    value={formData.hierarchy}
                                    onChange={e => setFormData({ ...formData, hierarchy: e.target.value as any })}
                                >
                                    <option value="Peer">{t('colleagues_module.relationships.Peer')}</option>
                                    <option value="Mentor">{t('colleagues_module.relationships.Mentor')}</option>
                                    <option value="Supervisee">{t('colleagues_module.relationships.Supervisee')}</option>
                                    <option value="Boss">{t('colleagues_module.relationships.Boss')}</option>
                                </select>
                            </div>

                            <div>
                                <label className="field-label">{t('colleagues_module.characteristics_label')}</label>
                                <input
                                    className="input-soft"
                                    placeholder={t('colleagues_module.characteristics_placeholder')}
                                    value={formData.characteristics}
                                    onChange={e => setFormData({ ...formData, characteristics: e.target.value })}
                                />
                            </div>

                            <button className="btn-premium-submit" onClick={handleAdd}>
                                {t('colleagues_module.add_button')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* DETAIL VIEW */}
            {selectedColleague && (
                <div className="premium-modal-overlay" onClick={() => setSelectedColleague(null)}>
                    <div className="detail-stage" onClick={e => e.stopPropagation()}>
                        <div className="sheet-handle"></div>
                        <span className="detail-header-pill" style={{ background: '#F3F3FA', color: '#4A148C' }}>{getRelationshipLabel(selectedColleague.relationship_type)}</span>

                        <div
                            className={`avatar-sphere ${getAuraClass(selectedColleague.relationship_type)}`}
                            style={{ margin: '15px auto 20px', width: '120px', height: '120px', fontSize: '3.5rem' }}
                        >
                            <div className="getInitials">{getInitials(selectedColleague.name)}</div>
                        </div>

                        <h2 style={{ color: 'var(--text-main)', margin: '0 0 5px' }}>{selectedColleague.name}</h2>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{t('colleagues_module.contact_type')}</p>

                        <hr style={{ margin: '25px 0', opacity: 0.1, width: '100%' }} />

                        <div className="detail-content-scroll">
                            <div style={{ textAlign: 'left', display: 'grid', gap: '15px' }}>
                                {/* History Section */}
                                <div className="history-section">
                                    <label className="field-label">{t('colleagues_module.history_title')}</label>
                                    {loadingHistory ? (
                                        <p className="loading-text">{t('colleagues_module.loading_history')}</p>
                                    ) : history.length > 0 ? (
                                        <div className="history-scroll">
                                            {history.map((h, i) => (
                                                <div key={h.id || i} className="history-item">
                                                    <div className="history-dot"></div>
                                                    <div className="history-main">
                                                        <div
                                                            className="history-meta clickable"
                                                            onClick={() => setExpandedHistoryId(expandedHistoryId === h.id ? null : h.id)}
                                                        >
                                                            <span className="h-mood">{h.mood_state}</span>
                                                            <span className="h-date">{new Date(h.timestamp).toLocaleDateString()}</span>
                                                        </div>
                                                        <p className="h-intent">{h.intent?.replace('_', ' ')}</p>
                                                        {expandedHistoryId === h.id && (
                                                            <div className="history-details">
                                                                {h.energy_level && (
                                                                    <p className="h-detail"><strong>{t('patients.history_energy')}:</strong> {h.energy_level}/10</p>
                                                                )}
                                                                {h.text_content && (
                                                                    <p className="h-detail h-note"><strong>{t('patients.history_note')}:</strong> {h.text_content}</p>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="history-empty">{t('colleagues_module.no_history')}</p>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="detail-actions" style={{ gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                            <button className="btn-pill btn-pill-secondary" onClick={() => setSelectedColleague(null)} style={{ gridColumn: 'span 2' }}>
                                {t('colleagues_module.close')}
                            </button>
                            <button className="btn-pill btn-pill-primary" onClick={() => {
                                onAnalyze('COLLEAGUE', selectedColleague.id, selectedColleague.name);
                                setSelectedColleague(null);
                            }}>
                                {t('colleagues_module.deep_analysis')}
                            </button>
                            <button className="btn-pill btn-pill-primary" onClick={() => {
                                onCheckIn('COLLEAGUE', selectedColleague.id, selectedColleague.name);
                                setSelectedColleague(null);
                            }}>
                                {t('colleagues_module.check_in')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
