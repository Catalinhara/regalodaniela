import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import './PatientList.css';

interface Patient {
    id: string;
    alias: string;
    emotional_load: number;
    age?: number;
    avatar_url?: string;
    avatar_type?: 'photo' | 'emoji' | 'initials';
    description?: string;
    therapy_start_date?: string;
    notes?: string;
    trend?: 'improving' | 'stable' | 'declining';
}

interface Props {
    onCheckIn: (type: string, id: string, name: string) => void;
    onAnalyze: (type: string, id: string, name: string) => void;
    onBack: () => void;
}

const EMOJI_OPTIONS = ['😊', '😌', '🌱', '🌸', '🦋', '☀️', '✨', '🧘', '🕊️', '🌿', '☁️', '🌙'];

export const PatientList: React.FC<Props> = ({ onCheckIn, onAnalyze, onBack }) => {
    const { t } = useTranslation();
    const [patients, setPatients] = useState<Patient[]>([]);
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [history, setHistory] = useState<any[]>([]);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [expandedHistoryId, setExpandedHistoryId] = useState<string | null>(null);

    // Manage background scroll lock
    useEffect(() => {
        if (modalOpen || selectedPatient) {
            document.body.classList.add('modal-open');
        } else {
            document.body.classList.remove('modal-open');
        }
        return () => document.body.classList.remove('modal-open');
    }, [modalOpen, selectedPatient]);

    // Unified Avatar Selection State
    const [avatarSelection, setAvatarSelection] = useState<'emoji' | 'photo' | 'initials'>('emoji');

    // Form state
    const [formData, setFormData] = useState({
        alias: '',
        age: '',
        avatar_url: '😊',
        avatar_type: 'emoji' as 'photo' | 'emoji' | 'initials',
        description: '',
        therapy_start_date: '',
        emotional_load: '5'
    });

    const fetchPatients = async () => {
        setIsLoading(true);
        try {
            setPatients(await api.getPatients());
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => { fetchPatients(); }, []);

    useEffect(() => {
        if (selectedPatient) {
            loadHistory(selectedPatient.id);
        } else {
            setHistory([]);
        }
    }, [selectedPatient]);

    const loadHistory = async (patientId: string) => {
        setLoadingHistory(true);
        try {
            const data = await api.getPatientHistory(patientId);
            setHistory(data);
        } catch (e) {
            console.error("Failed to load history", e);
        } finally {
            setLoadingHistory(false);
        }
    };

    const handleAdd = async () => {
        if (!formData.alias?.trim()) return;

        try {
            const payload: any = {
                alias: formData.alias.trim(),
                emotional_load: parseInt(formData.emotional_load) || 5,
                avatar_type: avatarSelection,
                avatar_url: avatarSelection === 'emoji' ? formData.avatar_url : (avatarSelection === 'photo' ? formData.avatar_url : '')
            };

            if (formData.age) payload.age = parseInt(formData.age);
            if (formData.description) payload.description = formData.description;
            if (formData.therapy_start_date) payload.therapy_start_date = formData.therapy_start_date;

            await api.createPatient(payload);
            setModalOpen(false);
            resetForm();
            fetchPatients();
        } catch (e) {
            console.error('Failed to add patient', e);
        }
    };

    const resetForm = () => {
        setFormData({
            alias: '',
            age: '',
            avatar_url: '😊',
            avatar_type: 'emoji',
            description: '',
            therapy_start_date: '',
            emotional_load: '5'
        });
        setAvatarSelection('emoji');
    };

    const getInitials = (name: string) => {
        if (!name) return '??';
        const parts = name.trim().split(' ');
        if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
        return name.substring(0, 2).toUpperCase();
    };

    const renderAvatarPreview = () => {
        if (avatarSelection === 'photo' && formData.avatar_url) {
            return <img src={formData.avatar_url} alt="Preview" />;
        }
        if (avatarSelection === 'emoji') {
            return formData.avatar_url || '😊';
        }
        return getInitials(formData.alias || 'PT');
    };

    return (
        <div className="patients-container">
            {/* ATMOSPHERIC BACKGROUND BLOBS */}
            <div className="bg-blob blob-1"></div>
            <div className="bg-blob blob-2"></div>
            <div className="bg-blob blob-3"></div>

            {/* STICKY GLASS HEADER */}
            <header className="patients-header">
                <button className="btn-back-clean" onClick={onBack} aria-label="Back">
                    ‹
                </button>
                <div className="header-title-container">
                    <h1>{t('patients.title')}</h1>
                    <span>{t('patients.subtitle')}</span>
                </div>
                <button className="btn-add-action" onClick={() => setModalOpen(true)} aria-label={t('patients.add_action')}>
                    +
                </button>
            </header>

            <main className="patients-viewport">
                {isLoading && <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{t('patients.updating')}</div>}

                {!isLoading && patients.length === 0 ? (
                    <div className="patients-empty">
                        <div className="patients-empty-icon">🕊️</div>
                        <h3>{t('patients.empty_title')}</h3>
                        <p>{t('patients.empty_text')}</p>
                        <button className="btn-premium-submit" onClick={() => setModalOpen(true)} style={{ maxWidth: '200px', margin: '20px auto' }}>
                            {t('patients.add_first')}
                        </button>
                    </div>
                ) : (
                    <div className="patients-grid-v2">
                        {patients.map((patient, index) => {
                            const load = patient.emotional_load;
                            const auraClass = load >= 9 ? 'aura-critical' :
                                load >= 7 ? 'aura-active' :
                                    load >= 4 ? 'aura-stable' : 'aura-safe';

                            const trendIcon = patient.trend === 'improving' ? '↑' :
                                patient.trend === 'declining' ? '↓' : '→';
                            const trendClass = `trend-${patient.trend || 'stable'}`;

                            return (
                                <div
                                    key={patient.id}
                                    className={`patient-card-v2 card-float-${(index % 3) + 1}`}
                                    onClick={() => setSelectedPatient(patient)}
                                >
                                    <div className={`avatar-sphere ${auraClass}`}>
                                        {patient.avatar_type === 'photo' && patient.avatar_url ? (
                                            <img src={patient.avatar_url} alt={patient.alias} />
                                        ) : (
                                            patient.avatar_type === 'emoji' ? (patient.avatar_url || '👤') : getInitials(patient.alias)
                                        )}
                                    </div>
                                    <div className="patient-info-v2">
                                        <div className="patient-name-row">
                                            <h3>{patient.alias}</h3>
                                            <div className={`trend-badge ${trendClass}`} title={t('patients.trend_label', { trend: t(`patients.trends.${patient.trend || 'stable'}`) })}>
                                                {trendIcon}
                                            </div>
                                        </div>
                                        <p>{patient.age ? t('patients.age_short', { age: patient.age }) : t('patients.new_entry')}</p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>

            {/* UNIFIED PREMIUM MODAL - ADD PATIENT */}
            {modalOpen && (
                <div className="premium-modal-overlay" onClick={() => setModalOpen(false)}>
                    <div className="premium-modal-card" onClick={e => e.stopPropagation()}>
                        <div className="sheet-handle"></div>
                        <div className="modal-header-v2">
                            <h2>{t('patients.new_patient_title')}</h2>
                            <button className="btn-close-v2" onClick={() => setModalOpen(false)}>×</button>
                        </div>

                        <div className="avatar-stage">
                            <div className="avatar-preview-v2">
                                {renderAvatarPreview()}
                            </div>
                            <div className="selector-controls">
                                <button
                                    className={`control-pill ${avatarSelection === 'emoji' ? 'active' : ''}`}
                                    onClick={() => setAvatarSelection('emoji')}
                                >{t('patients.avatar_emoji')}</button>
                                <button
                                    className={`control-pill ${avatarSelection === 'photo' ? 'active' : ''}`}
                                    onClick={() => setAvatarSelection('photo')}
                                >{t('patients.avatar_photo')}</button>
                                <button
                                    className={`control-pill ${avatarSelection === 'initials' ? 'active' : ''}`}
                                    onClick={() => setAvatarSelection('initials')}
                                >{t('patients.avatar_initials')}</button>
                            </div>

                            <div className="choice-container">
                                {avatarSelection === 'emoji' && (
                                    <div className="emoji-grid-v2">
                                        {EMOJI_OPTIONS.map(emoji => (
                                            <span
                                                key={emoji}
                                                className={`emoji-item-v2 ${formData.avatar_url === emoji ? 'active' : ''}`}
                                                onClick={() => setFormData({ ...formData, avatar_url: emoji })}
                                            >
                                                {emoji}
                                            </span>
                                        ))}
                                    </div>
                                )}
                                {avatarSelection === 'photo' && (
                                    <input
                                        className="input-soft"
                                        placeholder={t('patients.paste_url')}
                                        value={formData.avatar_type === 'photo' ? formData.avatar_url : ''}
                                        onChange={e => setFormData({ ...formData, avatar_url: e.target.value, avatar_type: 'photo' })}
                                    />
                                )}
                            </div>
                        </div>

                        <div className="premium-form-grid">
                            <div>
                                <label className="field-label">{t('patients.alias_label')}</label>
                                <input
                                    className="input-soft"
                                    placeholder={t('patients.alias_placeholder')}
                                    value={formData.alias}
                                    onChange={e => setFormData({ ...formData, alias: e.target.value })}
                                />
                            </div>

                            <div className="dual-columns">
                                <div>
                                    <label className="field-label">{t('patients.age_label')}</label>
                                    <input
                                        type="number"
                                        className="input-soft"
                                        placeholder={t('patients.optional_placeholder')}
                                        value={formData.age}
                                        onChange={e => setFormData({ ...formData, age: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="field-label">{t('patients.start_date_label')}</label>
                                    <input
                                        type="date"
                                        className="input-soft"
                                        value={formData.therapy_start_date}
                                        onChange={e => setFormData({ ...formData, therapy_start_date: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="field-label">{t('patients.description_label')}</label>
                                <textarea
                                    className="input-soft"
                                    placeholder={t('patients.description_placeholder')}
                                    style={{ minHeight: '80px' }}
                                    value={formData.description}
                                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                                />
                            </div>

                            <button className="btn-premium-submit" onClick={handleAdd}>
                                {t('patients.add_button')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* REFINED DETAIL VIEW */}
            {selectedPatient && (
                <div className="premium-modal-overlay" onClick={() => setSelectedPatient(null)}>
                    <div className="detail-stage" onClick={e => e.stopPropagation()}>
                        <div className="sheet-handle"></div>
                        <span className="detail-header-pill" style={{ background: '#FAF3EF', color: '#B28D6F' }}>{t('patients.emotional_load')}: {selectedPatient.emotional_load}</span>

                        <div
                            className={`avatar-sphere ${selectedPatient.emotional_load > 7 ? 'aura-high' : (selectedPatient.emotional_load > 4 ? 'aura-med' : 'aura-low')}`}
                            style={{ margin: '15px auto 20px', width: '120px', height: '120px', fontSize: '3.5rem' }}
                        >
                            {selectedPatient.avatar_type === 'photo' && selectedPatient.avatar_url ? (
                                <img src={selectedPatient.avatar_url} alt={selectedPatient.alias} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 'inherit' }} />
                            ) : (
                                selectedPatient.avatar_type === 'emoji' ? (selectedPatient.avatar_url || '👤') : getInitials(selectedPatient.alias)
                            )}
                        </div>

                        <h2 style={{ color: 'var(--text-main)', margin: '0 0 5px' }}>{selectedPatient.alias}</h2>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{t('patients.record')}</p>

                        <hr style={{ margin: '25px 0', opacity: 0.1, width: '100%' }} />

                        <div className="detail-content-scroll">
                            <div style={{ textAlign: 'left', display: 'grid', gap: '15px' }}>
                                {selectedPatient.description && (
                                    <div>
                                        <label className="field-label">{t('patients.notes')}</label>
                                        <p style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-soft)' }}>{selectedPatient.description}</p>
                                    </div>
                                )}
                                <div className="dual-columns">
                                    <div>
                                        <label className="field-label">{t('patients.age_label')}</label>
                                        <p style={{ margin: 0 }}>{selectedPatient.age || t('patients.not_set')}</p>
                                    </div>
                                    <div>
                                        <label className="field-label">{t('patients.member_since')}</label>
                                        <p style={{ margin: 0 }}>{selectedPatient.therapy_start_date ? new Date(selectedPatient.therapy_start_date).toLocaleDateString() : t('patients.unknown')}</p>
                                    </div>
                                </div>

                                {/* History Section */}
                                <div className="history-section">
                                    <label className="field-label">{t('patients.clinical_history')}</label>
                                    {loadingHistory ? (
                                        <p className="loading-text">{t('patients.loading_history')}</p>
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
                                        <p className="history-empty">{t('patients.no_history')}</p>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="detail-actions" style={{ gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                            <button className="btn-pill btn-pill-secondary" onClick={() => setSelectedPatient(null)} style={{ gridColumn: 'span 2' }}>
                                {t('patients.close')}
                            </button>
                            <button className="btn-pill btn-pill-primary" onClick={() => {
                                onAnalyze('PATIENT', selectedPatient.id, selectedPatient.alias);
                                setSelectedPatient(null);
                            }}>
                                {t('patients.deep_analysis')}
                            </button>
                            <button className="btn-pill btn-pill-primary" onClick={() => {
                                onCheckIn('PATIENT', selectedPatient.id, selectedPatient.alias);
                                setSelectedPatient(null);
                            }}>
                                {t('patients.check_in')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
