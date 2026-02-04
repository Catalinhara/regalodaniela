import React from 'react';
import { useTranslation } from 'react-i18next';
import './Dashboard.css';
import ReactMarkdown from 'react-markdown';

interface DashboardProps {
    user?: { full_name?: string; professional_role?: string };
    insight?: { observation: string };
    onNavigate: (page: 'patients' | 'colleagues' | 'events' | 'chat') => void;
    patientCount?: number;
    colleagueCount?: number;
    eventCount?: number;
}

export const Dashboard: React.FC<DashboardProps> = ({
    user,
    insight,
    onNavigate,
    patientCount = 0,
    colleagueCount = 0,
    eventCount = 0
}) => {
    const { t } = useTranslation();

    // Extract first name from full_name
    const firstName = user?.full_name?.split(' ')[0] || 'there';

    return (
        <div className="dashboard-container">
            {/* ATMOSPHERIC BACKGROUND BLOBS */}
            <div className="bg-blob blob-1"></div>
            <div className="bg-blob blob-2"></div>
            <div className="bg-blob blob-3"></div>

            {/* HEADER GROUP: GREETING + QUOTE */}
            <div className="dashboard-header-group">
                <section className="dashboard-hero">
                    <h1 className="hero-greeting">
                        {t('dashboard.welcome_personal')}, {firstName}!
                    </h1>
                    <p className="hero-tagline">
                        {t('dashboard.tagline_personal')}
                    </p>
                </section>

                {/* DAILY QUOTE */}
                {insight && (
                    <div className="dashboard-insight-quote">
                        <ReactMarkdown>
                            {`"${insight.observation}"`}
                        </ReactMarkdown>
                    </div>
                )}
            </div>

            {/* MODULE CARDS GRID */}
            <div className="dashboard-grid">
                {/* PATIENTS CARD */}
                <div
                    className="module-card module-card-patients"
                    onClick={() => onNavigate('patients')}
                >
                    <div className="module-icon module-icon-patients">
                        🌿
                    </div>
                    <h2 className="module-title">{t('dashboard.patients.title')}</h2>
                    <p className="module-subtitle">{t('dashboard.patients.subtitle')}</p>
                    <div className="module-count module-count-patients">
                        {t('dashboard.patients.count', { count: patientCount })}
                    </div>
                </div>

                {/* COLLEAGUES CARD */}
                <div
                    className="module-card module-card-colleagues"
                    onClick={() => onNavigate('colleagues')}
                >
                    <div className="module-icon module-icon-colleagues">
                        💜
                    </div>
                    <h2 className="module-title">{t('dashboard.colleagues.title')}</h2>
                    <p className="module-subtitle">{t('dashboard.colleagues.subtitle')}</p>
                    <div className="module-count module-count-colleagues">
                        {t('dashboard.colleagues.count', { count: colleagueCount })}
                    </div>
                </div>

                {/* EVENTS CARD */}
                <div
                    className="module-card module-card-events"
                    onClick={() => onNavigate('events')}
                >
                    <div className="module-icon module-icon-events">
                        🔆
                    </div>
                    <h2 className="module-title">{t('dashboard.events.title')}</h2>
                    <p className="module-subtitle">{t('dashboard.events.subtitle')}</p>
                    <div className="module-count module-count-events">
                        {t('dashboard.events.count', { count: eventCount })}
                    </div>
                </div>

                {/* CHAT CARD */}
                <div
                    className="module-card module-card-chat"
                    onClick={() => onNavigate('chat')}
                >
                    <div className="module-icon module-icon-chat">
                        🤖
                    </div>
                    <h2 className="module-title">{t('dashboard.chat.title')}</h2>
                    <p className="module-subtitle">{t('dashboard.chat.subtitle')}</p>
                    <div className="module-count module-count-chat">
                        {t('dashboard.chat.status')}
                    </div>
                </div>
            </div>
        </div>
    );
};
