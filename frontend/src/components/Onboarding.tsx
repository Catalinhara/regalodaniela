import { useState } from 'react';
import './Onboarding.css';

interface OnboardingData {
    language: 'en' | 'es';
    fullName: string;
    professionalRole: string;
    yearsExperience: number;
    stressors: string[];
    copingStyles: string[];
}

interface OnboardingProps {
    onComplete: (data: OnboardingData) => void;
}

const Onboarding = ({ onComplete }: OnboardingProps) => {
    const [currentStep, setCurrentStep] = useState(1);
    const [data, setData] = useState<OnboardingData>({
        language: 'en',
        fullName: '',
        professionalRole: '',
        yearsExperience: 0,
        stressors: [],
        copingStyles: []
    });

    const totalSteps = 5;

    // Localized content
    const content = {
        en: {
            step1: {
                title: 'Welcome to ClaraMente',
                subtitle: 'Your safe space for professional well-being',
                question: 'Choose your language',
                note: 'This will personalize your entire experience'
            },
            step2: {
                title: 'Let\'s get to know you',
                subtitle: 'Help us create a personalized experience',
                nameLabel: 'Your Name',
                namePlaceholder: 'Dr. Sarah Johnson',
                roleLabel: 'Professional Role',
                roles: ['Therapist', 'Psychologist', 'Social Worker', 'Counselor', 'Psychiatrist', 'Other']
            },
            step3: {
                title: 'Your Experience',
                subtitle: 'Understanding your journey helps us support you better',
                question: 'How many years have you been practicing?',
                ranges: [
                    { label: 'Just starting (0-2 years)', value: 1 },
                    { label: 'Early career (3-5 years)', value: 4 },
                    { label: 'Experienced (6-10 years)', value: 8 },
                    { label: 'Seasoned (11-20 years)', value: 15 },
                    { label: 'Veteran (20+ years)', value: 25 }
                ]
            },
            step4: {
                title: 'What weighs on you?',
                subtitle: 'Select up to 3 challenges you are facing',
                question: 'What are your primary stressors?',
                options: [
                    { icon: '🔥', label: 'Burnout', value: 'burnout' },
                    { icon: '💼', label: 'Heavy Workload', value: 'workload' },
                    { icon: '💔', label: 'Emotional Drain', value: 'emotional_drain' },
                    { icon: '😰', label: 'Vicarious Trauma', value: 'vicarious_trauma' },
                    { icon: '⚖️', label: 'Work-Life Balance', value: 'work_life_balance' },
                    { icon: '🤝', label: 'Professional Isolation', value: 'isolation' }
                ]
            },
            step5: {
                title: 'Your Support Style',
                subtitle: 'Select up to 3 ways you process information',
                question: 'What are your natural coping approaches?',
                options: [
                    { icon: '🧠', label: 'Analytical', desc: 'I think through patterns and solutions', value: 'analytical' },
                    { icon: '💭', label: 'Reflective', desc: 'I process emotions and experiences', value: 'reflective' },
                    { icon: '🤲', label: 'Relational', desc: 'I seek support from others', value: 'relational' },
                    { icon: '🎯', label: 'Action-Oriented', desc: 'I focus on immediate next steps', value: 'action_oriented' }
                ]
            },
            continue: 'Continue',
            back: 'Back',
            finish: 'Complete Setup'
        },
        es: {
            step1: {
                title: 'Bienvenido a ClaraMente',
                subtitle: 'Tu espacio seguro para el bienestar profesional',
                question: 'Elige tu idioma',
                note: 'Esto personalizará toda tu experiencia'
            },
            step2: {
                title: 'Conozcámonos',
                subtitle: 'Ayúdanos a crear una experiencia personalizada',
                nameLabel: 'Tu Nombre',
                namePlaceholder: 'Dra. María García',
                roleLabel: 'Rol Profesional',
                roles: ['Terapeuta', 'Psicólogo/a', 'Trabajador/a Social', 'Consejero/a', 'Psiquiatra', 'Otro']
            },
            step3: {
                title: 'Tu Experiencia',
                subtitle: 'Entender tu trayectoria nos ayuda a apoyarte mejor',
                question: '¿Cuántos años llevas ejerciendo?',
                ranges: [
                    { label: 'Recién empezando (0-2 años)', value: 1 },
                    { label: 'Carrera inicial (3-5 años)', value: 4 },
                    { label: 'Con experiencia (6-10 años)', value: 8 },
                    { label: 'Experimentado/a (11-20 años)', value: 15 },
                    { label: 'Veterano/a (20+ años)', value: 25 }
                ]
            },
            step4: {
                title: '¿Qué te pesa?',
                subtitle: 'Selecciona hasta 3 desafíos que enfrentas',
                question: '¿Cuáles son tus principales fuentes de estrés?',
                options: [
                    { icon: '🔥', label: 'Agotamiento', value: 'burnout' },
                    { icon: '💼', label: 'Carga de Trabajo', value: 'workload' },
                    { icon: '💔', label: 'Desgaste Emocional', value: 'emotional_drain' },
                    { icon: '😰', label: 'Trauma Vicario', value: 'vicarious_trauma' },
                    { icon: '⚖️', label: 'Balance Vida-Trabajo', value: 'work_life_balance' },
                    { icon: '🤝', label: 'Aislamiento Profesional', value: 'isolation' }
                ]
            },
            step5: {
                title: 'Tu Estilo de Apoyo',
                subtitle: 'Selecciona hasta 3 formas de procesar',
                question: '¿Cuáles son tus enfoques naturales de afrontamiento?',
                options: [
                    { icon: '🧠', label: 'Analítico', desc: 'Pienso en patrones y soluciones', value: 'analytical' },
                    { icon: '💭', label: 'Reflexivo', desc: 'Proceso emociones y experiencias', value: 'reflective' },
                    { icon: '🤲', label: 'Relacional', desc: 'Busco apoyo de otros', value: 'relational' },
                    { icon: '🎯', label: 'Orientado a la Acción', desc: 'Me enfoco en próximos pasos', value: 'action_oriented' }
                ]
            },
            continue: 'Continuar',
            back: 'Atrás',
            finish: 'Completar Configuración'
        }
    };

    const t = content[data.language];

    const nextStep = () => {
        if (currentStep < totalSteps) {
            setCurrentStep(prev => prev + 1);
        } else {
            onComplete(data);
        }
    };

    const prevStep = () => {
        if (currentStep > 1) {
            setCurrentStep(prev => prev - 1);
        }
    };

    // Auto-advance Logic Helpers
    const setLanguage = (lang: 'en' | 'es') => {
        setData({ ...data, language: lang });
        // Small delay for visual feedback before auto-advance
        setTimeout(() => {
            setCurrentStep(2);
        }, 300);
    };

    const setRole = (role: string) => {
        setData({ ...data, professionalRole: role });
        // No auto-advance here because name might not be filled
    };

    const setExperience = (years: number) => {
        setData({ ...data, yearsExperience: years });
        setTimeout(() => {
            setCurrentStep(4);
        }, 300);
    };

    // Multi-select Logic
    const toggleStressor = (value: string) => {
        const current = data.stressors || []; // Safety fallback
        if (current.includes(value)) {
            setData({ ...data, stressors: current.filter(v => v !== value) });
        } else {
            if (current.length < 3) {
                setData({ ...data, stressors: [...current, value] });
            }
        }
    };

    const toggleCoping = (value: string) => {
        const current = data.copingStyles || []; // Safety fallback
        if (current.includes(value)) {
            setData({ ...data, copingStyles: current.filter(v => v !== value) });
        } else {
            if (current.length < 3) {
                setData({ ...data, copingStyles: [...current, value] });
            }
        }
    };

    const canContinue = () => {
        switch (currentStep) {
            case 1: return true;
            case 2: return data.fullName.trim() !== '' && data.professionalRole !== '';
            case 3: return data.yearsExperience > 0;
            case 4: return data.stressors.length > 0;
            case 5: return data.copingStyles.length > 0;
            default: return false;
        }
    };

    return (
        <div className="onboarding-overlay">
            <div className="onboarding-container">
                {/* Progress Bar */}
                <div className="onboarding-progress">
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{ width: `${(currentStep / totalSteps) * 100}%` }}
                        />
                    </div>
                    <div className="progress-label">
                        {currentStep} / {totalSteps}
                    </div>
                </div>

                {/* Step 1: Language Selection */}
                {currentStep === 1 && (
                    <div className="step step-1 active">
                        <div className="step-header">
                            <div className="step-icon">🌍</div>
                            <h1>{t.step1.title}</h1>
                            <p className="step-subtitle">{t.step1.subtitle}</p>
                        </div>

                        <div className="step-body">
                            <h2 className="question">{t.step1.question}</h2>
                            <div className="language-grid">
                                <button
                                    className={`lang-card ${data.language === 'en' ? 'selected' : ''}`}
                                    onClick={() => setLanguage('en')}
                                >
                                    <div className="lang-flag">🇺🇸</div>
                                    <div className="lang-name">English</div>
                                </button>
                                <button
                                    className={`lang-card ${data.language === 'es' ? 'selected' : ''}`}
                                    onClick={() => setLanguage('es')}
                                >
                                    <div className="lang-flag">🇪🇸</div>
                                    <div className="lang-name">Español</div>
                                </button>
                            </div>
                            <p className="step-note">{t.step1.note}</p>
                        </div>
                    </div>
                )}

                {/* Step 2: Name & Role */}
                {currentStep === 2 && (
                    <div className="step step-2 active">
                        <div className="step-header">
                            <div className="step-icon">👋</div>
                            <h1>{t.step2.title}</h1>
                            <p className="step-subtitle">{t.step2.subtitle}</p>
                        </div>

                        <div className="step-body">
                            <div className="form-group">
                                <label>{t.step2.nameLabel}</label>
                                <input
                                    type="text"
                                    className="onboarding-input"
                                    placeholder={t.step2.namePlaceholder}
                                    value={data.fullName}
                                    onChange={(e) => setData({ ...data, fullName: e.target.value })}
                                />
                            </div>

                            <div className="form-group">
                                <label>{t.step2.roleLabel}</label>
                                <div className="role-grid">
                                    {t.step2.roles.map((role) => (
                                        <button
                                            key={role}
                                            className={`role-btn ${data.professionalRole === role ? 'selected' : ''}`}
                                            onClick={() => setRole(role)}
                                        >
                                            {role}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 3: Experience */}
                {currentStep === 3 && (
                    <div className="step step-3 active">
                        <div className="step-header">
                            <div className="step-icon">📚</div>
                            <h1>{t.step3.title}</h1>
                            <p className="step-subtitle">{t.step3.subtitle}</p>
                        </div>

                        <div className="step-body">
                            <h2 className="question">{t.step3.question}</h2>
                            <div className="options-list">
                                {t.step3.ranges.map((range) => (
                                    <button
                                        key={range.value}
                                        className={`option-card ${data.yearsExperience === range.value ? 'selected' : ''}`}
                                        onClick={() => setExperience(range.value)}
                                    >
                                        <span className="option-label">{range.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 4: Primary Stressor (Multi-select) */}
                {currentStep === 4 && (
                    <div className="step step-4 active">
                        <div className="step-header">
                            <div className="step-icon">💭</div>
                            <h1>{t.step4.title}</h1>
                            <p className="step-subtitle">{t.step4.subtitle}</p>
                        </div>

                        <div className="step-body">
                            <h2 className="question">{t.step4.question}</h2>
                            <div className="options-grid">
                                {t.step4.options.map((option) => {
                                    const isSelected = data.stressors.includes(option.value);
                                    return (
                                        <button
                                            key={option.value}
                                            className={`icon-card ${isSelected ? 'selected' : ''}`}
                                            onClick={() => toggleStressor(option.value)}
                                        >
                                            <div className="icon-card-icon">{option.icon}</div>
                                            <div className="icon-card-label">{option.label}</div>
                                            {isSelected && <div className="selection-badge">✓</div>}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 5: Coping Style (Multi-select) */}
                {currentStep === 5 && (
                    <div className="step step-5 active">
                        <div className="step-header">
                            <div className="step-icon">🌱</div>
                            <h1>{t.step5.title}</h1>
                            <p className="step-subtitle">{t.step5.subtitle}</p>
                        </div>

                        <div className="step-body">
                            <h2 className="question">{t.step5.question}</h2>
                            <div className="options-list">
                                {t.step5.options.map((option) => {
                                    const isSelected = data.copingStyles.includes(option.value);
                                    return (
                                        <button
                                            key={option.value}
                                            className={`option-card detailed ${isSelected ? 'selected' : ''}`}
                                            onClick={() => toggleCoping(option.value)}
                                        >
                                            <div className="option-icon">{option.icon}</div>
                                            <div className="option-text">
                                                <div className="option-label">{option.label}</div>
                                                <div className="option-desc">{option.desc}</div>
                                            </div>
                                            {isSelected && <div className="selection-badge">✓</div>}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                )}

                {/* Navigation */}
                <div className="onboarding-navigation">
                    {currentStep > 1 && (
                        <button className="btn-onboarding btn-back" onClick={prevStep}>
                            ← {t.back}
                        </button>
                    )}
                    <button
                        className="btn-onboarding btn-continue"
                        onClick={nextStep}
                        disabled={!canContinue()}
                    >
                        {currentStep === totalSteps ? t.finish : t.continue} →
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Onboarding;
