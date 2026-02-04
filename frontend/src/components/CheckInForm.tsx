import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import './CheckInForm.css';

interface CheckInFormProps {
    initialContextType?: string;
    initialContextId?: string;
    initialContextName?: string;
    onCancel?: () => void;
    onSuccess?: () => void;
}

export const CheckInForm: React.FC<CheckInFormProps> = ({
    initialContextType = 'SELF',
    initialContextId,
    initialContextName = 'Myself',
    onCancel,
    onSuccess
}) => {
    const { t } = useTranslation();
    const [step, setStep] = useState(1);
    const [mood, setMood] = useState<string | null>(null);
    const [energy, setEnergy] = useState<number>(5);
    const [intent, setIntent] = useState<string | null>(null);
    const [note, setNote] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Reset form when context changes
    useEffect(() => {
        setStep(1);
        setMood(null);
        setEnergy(5);
        setIntent(null);
        setNote('');
    }, [initialContextId]);

    const intents = [
        { id: 'RELEASE', label: t('check_in.intents.RELEASE'), icon: '💨' },
        { id: 'TRACK', label: t('check_in.intents.TRACK'), icon: '📊' },
        { id: 'SEEK_CLARITY', label: t('check_in.intents.SEEK_CLARITY'), icon: '💡' },
        { id: 'SEEK_VALIDATION', label: t('check_in.intents.SEEK_VALIDATION'), icon: '💜' },
        { id: 'SEEK_DISTANCE', label: t('check_in.intents.SEEK_DISTANCE'), icon: '🌙' },
    ];

    const handleSubmit = async () => {
        if (!mood || !intent) return;
        setIsSubmitting(true);
        try {
            // Payload must match CheckInCreate DTO exactly
            await api.submitCheckIn({
                context_type: initialContextType,
                context_id: initialContextId,
                intent: intent,
                mood_state: mood,
                energy_level: energy,
                text_content: note
            });
            alert(t('check_in.success'));
            setStep(1);
            setMood(null);
            setEnergy(5);
            setIntent(null);
            setNote('');
            if (onSuccess) onSuccess();
        } catch (e) {
            console.error(e);
            alert(t('check_in.error'));
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className={`checkin-viewport ctx-${initialContextType.toLowerCase()}`}>
            {/* Atmospheric Background */}
            <div className="bg-blob blob-1"></div>
            <div className="bg-blob blob-2"></div>
            <div className="bg-blob blob-3"></div>

            <div className="checkin-glass-card">
                <div className="sheet-handle"></div>
                {/* Header Section */}
                <div className="checkin-header-v2">
                    <div className="header-left">
                        <span className="context-pill">{t('check_in.title_prefix')} <strong>{initialContextName}</strong></span>
                    </div>
                    {onCancel && (
                        <button className="btn-close-clean" onClick={onCancel} title="Close">
                            ✕
                        </button>
                    )}
                </div>

                <div className="checkin-content-scroll">
                    {step === 1 && (
                        <div className="step-content-v2">
                            <h2 className="step-title">{t('check_in.step1_title')}</h2>
                            <div className="mood-organic-grid">
                                {['CALM', 'CONTENT', 'ENERGIZED', 'ANXIOUS', 'FRUSTRATED', 'DRAINED'].map((m) => (
                                    <button
                                        key={m}
                                        className={`mood-sphere-btn mood-${m.toLowerCase()} ${mood === m ? 'active' : ''}`}
                                        onClick={() => setMood(m)}
                                    >
                                        <span className="mood-label">{t(`check_in.moods.${m}`)}</span>
                                    </button>
                                ))}
                            </div>

                            {mood && (
                                <div className="mood-followup-v2 slide-up">
                                    <div className="energy-control-v2">
                                        <div className="energy-label-row">
                                            <span className="label-text">{t('check_in.energy_label')}</span>
                                            <span className="energy-value">{energy}/10</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="1" max="10"
                                            className="premium-slider"
                                            value={energy}
                                            onChange={(e) => setEnergy(parseInt(e.target.value))}
                                        />
                                    </div>
                                    <button className="btn-premium-next" onClick={() => setStep(2)}>
                                        {t('check_in.next_button')} <span>→</span>
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    {step === 2 && (
                        <div className="step-content-v2 slide-in">
                            <h2 className="step-title">{t('check_in.step2_title')}</h2>
                            <div className="intent-organic-grid">
                                {intents.map((i, idx) => (
                                    <button
                                        key={i.id}
                                        className={`intent-sphere-btn intent-${i.id.toLowerCase()} ${intent === i.id ? 'active' : ''}`}
                                        style={{ animationDelay: `${idx * 0.15}s` } as React.CSSProperties}
                                        onClick={() => setIntent(i.id)}
                                    >
                                        <div className="intent-sphere-glow"></div>
                                        <span className="intent-icon">{i.icon}</span>
                                        <span className="intent-label">{i.label}</span>
                                    </button>
                                ))}
                            </div>

                            {intent && (
                                <div className="step-actions-v2 slide-up">
                                    <textarea
                                        className="premium-textarea"
                                        placeholder={t('check_in.note_placeholder')}
                                        value={note}
                                        onChange={e => setNote(e.target.value)}
                                    />
                                    <div className="final-actions-v2">
                                        <button className="btn-back-soft" onClick={() => setStep(1)}>{t('common.back')}</button>
                                        <button
                                            className="btn-premium-submit"
                                            onClick={handleSubmit}
                                            disabled={isSubmitting}
                                        >
                                            {isSubmitting ? t('check_in.submitting') : t('check_in.submit_button')}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
