import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from './context/AuthContext';
import { Login } from './components/Login';
import { Register } from './components/Register';
import { CheckInForm } from './components/CheckInForm';
import { Dashboard } from './components/Dashboard';
import { PatientList } from './components/PatientList';
import { ColleagueList } from './components/ColleagueList';
import { EventList } from './components/EventList';
import { ChatInterface } from './components/ChatInterface';
import { AnalysisChat } from './components/AnalysisChat';
import Onboarding from './components/Onboarding';
import { BirthdayCard } from './components/BirthdayCard';
import { api, Insight } from './api/client';
import ReactMarkdown from 'react-markdown';
import './App.css'
import './components/InsightCard.css';

type ViewState = 'HOME' | 'PATIENTS' | 'COLLEAGUES' | 'EVENTS' | 'CHAT' | 'ANALYSIS';

function App() {
    const { t, i18n } = useTranslation();
    const { isAuthenticated, isLoading, logout, user } = useAuth();
    const [authView, setAuthView] = useState<'login' | 'register'>('login');
    const [view, setView] = useState<ViewState>('HOME');
    const [insight, setInsight] = useState<Insight | null>(null);
    const [checkingInContext, setCheckingInContext] = useState<{ type: string, id: string, name: string } | null>(null);
    const [analyzingContext, setAnalyzingContext] = useState<{ type: string, id: string, name: string } | null>(null);
    const [counts, setCounts] = useState({ patients: 0, colleagues: 0, events: 0 });
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [isInsightModalOpen, setIsInsightModalOpen] = useState(false);
    const [insightUnread, setInsightUnread] = useState(false);
    const [showBirthdayCard, setShowBirthdayCard] = useState(true);

    // Auto-Insight removal: We now fetch this as part of dashboard data to avoid race conditions
    // and ensure single source of truth.


    // Fetch counts for dashboard
    useEffect(() => {
        if (!isAuthenticated) return;

        const fetchCounts = async () => {
            try {
                const [patients, colleagues, events, , dailyInsight] = await Promise.all([
                    api.getPatients(),
                    api.getColleagues(),
                    api.getEvents(),
                    api.checkHealth(), // Placeholder for context, maybe add api.getContext()
                    api.getDailyInsight(i18n.language).catch(() => null) // Allow insight to fail gracefully
                ]);

                // Calculate simple counts
                setCounts({
                    patients: (patients as any[]).length,
                    colleagues: (colleagues as any[]).length,
                    events: (events as any[]).length
                });

                // Set insight
                setInsight(dailyInsight);

                // Check read status
                if (dailyInsight) {
                    const lastRead = localStorage.getItem(`insight_read_${user?.id}`);
                    const today = new Date().toDateString();
                    if (lastRead !== today) {
                        setInsightUnread(true);
                    }
                }

            } catch (e) {
                console.error("Failed to load dashboard data", e);
            }
        };
        fetchCounts();
    }, [isAuthenticated, view, i18n.language]); // Refresh counts when view or language changes

    // Show loading screen while checking auth
    if (isLoading) {
        return <div className="loading-screen">Loading...</div>;
    }

    // Show auth screens if not authenticated
    if (!isAuthenticated) {
        return authView === 'login'
            ? <Login onSwitchToRegister={() => setAuthView('register')} />
            : <Register onSwitchToLogin={() => setAuthView('login')} />;
    }

    // Show birthday card on every login
    if (isAuthenticated && user && showBirthdayCard) {
        return <BirthdayCard onContinue={() => {
            setShowBirthdayCard(false);
        }} />;
    }

    // Show onboarding for new users (from backend User model)
    if (isAuthenticated && user && !user.onboarding_completed) {
        return <Onboarding onComplete={async (data) => {
            try {
                console.log('Submitting onboarding data:', data);
                const updatedUser = await api.completeOnboarding(data);
                console.log('Onboarding completed!', updatedUser);

                // Set app language
                i18n.changeLanguage(data.language);

                // Reload page to refresh user context
                window.location.reload();
            } catch (error) {
                console.error('Failed to complete onboarding:', error);
                alert('Failed to save onboarding data. Please try again.');
            }
        }} />;
    }

    const handleCheckIn = (type: string, id: string, name: string) => {
        setCheckingInContext({ type, id, name });
    };

    const handleAnalyze = async (type: string, id: string, name: string) => {
        setAnalyzingContext({ type, id, name });
        setView('ANALYSIS');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const renderView = () => {
        if (checkingInContext) {
            return (
                <CheckInForm
                    initialContextType={checkingInContext.type}
                    initialContextId={checkingInContext.id}
                    initialContextName={checkingInContext.name}
                    onCancel={() => setCheckingInContext(null)}
                    onSuccess={() => setCheckingInContext(null)}
                />
            );
        }

        switch (view) {
            case 'PATIENTS':
                return <PatientList onCheckIn={handleCheckIn} onAnalyze={handleAnalyze} onBack={() => setView('HOME')} />;
            case 'COLLEAGUES':
                return <ColleagueList onCheckIn={handleCheckIn} onAnalyze={handleAnalyze} onBack={() => setView('HOME')} />;
            case 'EVENTS':
                return <EventList onCheckIn={handleCheckIn} onAnalyze={handleAnalyze} onBack={() => setView('HOME')} />;
            case 'CHAT':
                return <ChatInterface onBack={() => setView('HOME')} />;
            case 'ANALYSIS':
                return analyzingContext ? (
                    <AnalysisChat
                        context={analyzingContext}
                        onBack={() => {
                            setAnalyzingContext(null);
                            setView('HOME');
                        }}
                    />
                ) : <Dashboard user={user || undefined} onNavigate={(p) => setView(p.toUpperCase() as ViewState)} patientCount={counts.patients} colleagueCount={counts.colleagues} eventCount={counts.events} />;
            case 'HOME':
            default:
                return (
                    <>
                        <Dashboard
                            user={user || undefined}
                            insight={insight || undefined}
                            onNavigate={(page) => {
                                if (page === 'chat') {
                                    setView('CHAT');
                                } else {
                                    setView(page.toUpperCase() as ViewState);
                                }
                            }}
                            patientCount={counts.patients}
                            colleagueCount={counts.colleagues}
                            eventCount={counts.events}
                        />
                        {isInsightModalOpen && insight && (
                            <div className="insight-modal-overlay" onClick={() => setIsInsightModalOpen(false)}>
                                <div className="insight-modal" onClick={e => e.stopPropagation()}>
                                    <div className="modal-header">
                                        <div className="modal-badge">Daily Reflection</div>
                                        <div style={{ fontSize: '1.2rem' }}>✨</div>
                                    </div>
                                    <div className="revealed-details">
                                        <div className="detail-group">
                                            <div style={{ fontStyle: 'italic', fontWeight: 600, fontSize: '1.2rem', marginBottom: '1.5rem' }}>
                                                <ReactMarkdown>{`"${insight.observation}"`}</ReactMarkdown>
                                            </div>
                                        </div>
                                        <div className="detail-group">
                                            <label>Validation</label>
                                            <div className="markdown-content">
                                                <ReactMarkdown>{insight.validation}</ReactMarkdown>
                                            </div>
                                        </div>
                                        {insight.gentle_suggestion && (
                                            <div className="detail-group suggestion">
                                                <label>A Mindful Step Forward</label>
                                                <div className="markdown-content">
                                                    <ReactMarkdown>{insight.gentle_suggestion}</ReactMarkdown>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                    <div className="modal-footer">
                                        <button className="btn-close-modal" onClick={() => setIsInsightModalOpen(false)}>
                                            Close
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
                );
        }
    };

    const getUserInitials = (name: string) => {
        if (!name) return '??';
        const parts = name.trim().split(' ');
        if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
        return name.substring(0, 2).toUpperCase();
    };

    return (
        <div className="app-container">
            {!checkingInContext && view === 'HOME' && (
                <header className="app-header">
                    <div className="header-inner">
                        <div className="logo-section" onClick={() => setView('HOME')} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <div className="logo-icon" style={{ fontSize: '1.5rem' }}>✨</div>
                            <h1 style={{ margin: 0, fontSize: '1.3rem' }}>ClaraMente</h1>
                        </div>

                        {/* Always show Insight Icon */}
                        <div
                            className="insight-header-trigger"
                            onClick={() => {
                                if (insight) {
                                    setIsInsightModalOpen(true);
                                    setInsightUnread(false);
                                    localStorage.setItem(`insight_read_${user?.id}`, new Date().toDateString());
                                }
                            }}
                            title="Daily Reflection"
                            style={{ opacity: insight ? 1 : 0.5, cursor: insight ? 'pointer' : 'default' }}
                        >
                            ✨
                            {insightUnread && insight && <div className="notif-dot" />}
                        </div>

                        <div className="header-actions">
                            <div className="user-identity" style={{ position: 'relative' }}>
                                <div
                                    className="user-avatar-circle clickable"
                                    title={user?.full_name}
                                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                                >
                                    {getUserInitials(user?.full_name || 'User')}
                                </div>
                                {isDropdownOpen && (
                                    <div className="profile-dropdown">
                                        <div className="dropdown-item clickable" onClick={logout}>
                                            {t('auth.login') === 'Login' ? 'Logout' : 'Cerrar Sesión'}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </header>
            )}
            <main className="app-content">
                {renderView()}
            </main>
        </div>
    );
}

export default App
