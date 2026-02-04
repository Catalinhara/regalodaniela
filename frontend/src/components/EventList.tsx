import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import './EventList.css';

interface Event {
    id: string;
    title: string;
    event_date: string;
    impact_level: number;
}

interface Props {
    onCheckIn: (type: string, id: string, name: string) => void;
    onAnalyze: (type: string, id: string, name: string) => void;
    onBack: () => void;
}

export const EventList: React.FC<Props> = ({ onCheckIn, onAnalyze, onBack }) => {
    const { t, i18n } = useTranslation();
    const [events, setEvents] = useState<Event[]>([]);
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const [formData, setFormData] = useState({
        title: '',
        impact_level: '5'
    });

    // Manage background scroll lock
    useEffect(() => {
        if (modalOpen || selectedEvent) {
            document.body.classList.add('modal-open');
        } else {
            document.body.classList.remove('modal-open');
        }
        return () => document.body.classList.remove('modal-open');
    }, [modalOpen, selectedEvent]);

    const fetchEvents = async () => {
        setIsLoading(true);
        try {
            setEvents(await api.getEvents());
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => { fetchEvents(); }, []);

    const handleAdd = async () => {
        if (!formData.title?.trim()) return;

        try {
            const payload = {
                title: formData.title.trim(),
                event_date: new Date().toISOString(),
                impact_level: parseInt(formData.impact_level) || 5
            };

            await api.createEvent(payload);
            setModalOpen(false);
            resetForm();
            fetchEvents();
        } catch (e) {
            console.error('Failed to add event', e);
        }
    };

    const resetForm = () => {
        setFormData({
            title: '',
            impact_level: '5'
        });
    };

    const getImpactClass = (level: number) => {
        if (level <= 3) return 'low';
        if (level <= 7) return 'medium';
        return 'high';
    };

    return (
        <div className="events-container">
            {/* ATMOSPHERIC BACKGROUND BLOBS */}
            <div className="bg-blob blob-1"></div>
            <div className="bg-blob blob-2"></div>
            <div className="bg-blob blob-3"></div>

            {/* STICKY GLASS HEADER */}
            <header className="events-header">
                <button className="btn-back-clean" onClick={onBack} aria-label="Back">
                    ‹
                </button>
                <div className="header-title-container">
                    <h1>{t('events_module.title')}</h1>
                    <span>{t('events_module.subtitle')}</span>
                </div>
                <button className="btn-add-action" onClick={() => setModalOpen(true)} aria-label={t('events_module.add_action')}>
                    +
                </button>
            </header>

            <main className="events-viewport">
                {isLoading && <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{t('events_module.loading')}</div>}

                {!isLoading && events.length === 0 ? (
                    <div className="events-empty">
                        <div className="events-empty-icon">📅</div>
                        <h3>{t('events_module.empty_title')}</h3>
                        <p>{t('events_module.empty_text')}</p>
                        <button className="btn-premium-submit" onClick={() => setModalOpen(true)} style={{ maxWidth: '200px', margin: '20px auto' }}>
                            {t('events_module.add_first')}
                        </button>
                    </div>
                ) : (
                    <div className="events-grid-v2">
                        {events.map((event) => {
                            const impactClass = getImpactClass(event.impact_level);

                            return (
                                <div
                                    key={event.id}
                                    className="event-card-v2"
                                    onClick={() => setSelectedEvent(event)}
                                >
                                    <div className={`impact-indicator impact-${impactClass}`}></div>
                                    <div className="event-info-v2">
                                        <h3>{event.title}</h3>
                                        <div className="event-date">
                                            {new Date(event.event_date).toLocaleDateString(i18n.language)}
                                        </div>
                                        <span className={`impact-label ${impactClass}`}>
                                            {t('events_module.impact_display', { level: event.impact_level })}
                                        </span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>

            {/* PREMIUM MODAL - ADD EVENT */}
            {modalOpen && (
                <div className="premium-modal-overlay" onClick={() => setModalOpen(false)}>
                    <div className="premium-modal-card" onClick={e => e.stopPropagation()}>
                        <div className="sheet-handle"></div>
                        <div className="modal-header-v2">
                            <h2>{t('events_module.new_title')}</h2>
                            <button className="btn-close-v2" onClick={() => setModalOpen(false)}>×</button>
                        </div>

                        <div className="premium-form-grid">
                            <div>
                                <label className="field-label">{t('events_module.title_label')}</label>
                                <input
                                    className="input-soft"
                                    placeholder={t('events_module.title_placeholder')}
                                    value={formData.title}
                                    onChange={e => setFormData({ ...formData, title: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="field-label">{t('events_module.impact_level_label')}</label>
                                <div className="impact-control">
                                    <div className="impact-label-row">
                                        <span className="label-text">{t('events_module.impact_question')}</span>
                                        <span className="impact-value">{formData.impact_level}/10</span>
                                    </div>
                                    <input
                                        type="range"
                                        min="1"
                                        max="10"
                                        className="premium-slider"
                                        value={formData.impact_level}
                                        onChange={e => setFormData({ ...formData, impact_level: e.target.value })}
                                    />
                                </div>
                            </div>

                            <button className="btn-premium-submit" onClick={handleAdd}>
                                {t('events_module.add_button')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* DETAIL VIEW */}
            {selectedEvent && (
                <div className="premium-modal-overlay" onClick={() => setSelectedEvent(null)}>
                    <div className="detail-stage" onClick={e => e.stopPropagation()}>
                        <div className="sheet-handle"></div>
                        <span className="detail-header-pill" style={{ background: '#FEF6EF', color: '#F57F17' }}>{t('events_module.impact_display', { level: selectedEvent.impact_level })}</span>

                        <div
                            className="avatar-sphere"
                            style={{ margin: '15px auto 20px', width: '120px', height: '120px', fontSize: '3.5rem', background: '#FFFDF0', boxShadow: '0 10px 30px rgba(245, 127, 23, 0.15)' }}
                        >
                            📅
                        </div>

                        <h2 style={{ color: 'var(--text-main)', margin: '0 0 5px' }}>{selectedEvent.title}</h2>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            {new Date(selectedEvent.event_date).toLocaleDateString(i18n.language, {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                            })}
                        </p>

                        <hr style={{ margin: '25px 0', opacity: 0.1, width: '100%' }} />

                        <div className="detail-content-scroll">
                            <div style={{ textAlign: 'left' }}>
                                {/* Content details could go here, currently empty per design */}
                            </div>
                        </div>

                        <div className="detail-actions" style={{ gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                            <button className="btn-pill btn-pill-secondary" onClick={() => setSelectedEvent(null)} style={{ gridColumn: 'span 2' }}>
                                {t('events_module.close')}
                            </button>
                            <button className="btn-pill btn-pill-primary" onClick={() => {
                                onAnalyze('EVENT', selectedEvent.id, selectedEvent.title);
                                setSelectedEvent(null);
                            }}>
                                {t('events_module.deep_analysis')}
                            </button>
                            <button className="btn-pill btn-pill-primary" onClick={() => {
                                onCheckIn('EVENT', selectedEvent.id, selectedEvent.title);
                                setSelectedEvent(null);
                            }}>
                                {t('events_module.check_in')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
