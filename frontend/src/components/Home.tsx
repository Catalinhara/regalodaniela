import React from 'react';
import './Home.css';

interface HomeProps {
    onNavigate: (view: 'PATIENTS' | 'COLLEAGUES' | 'EVENTS') => void;
    onChat: () => void;
}

export const Home: React.FC<HomeProps> = ({ onNavigate, onChat }) => {
    return (
        <div className="home-container">
            <div className="welcome-banner">
                <h2 className="welcome-heading">Welcome Back, Companion.</h2>
                <p>Select a context to manage or check in.</p>
            </div>

            <div className="nav-grid">
                <button className="nav-card" onClick={() => onNavigate('PATIENTS')}>
                    <span className="nav-icon">👥</span>
                    <h3>Patients</h3>
                    <p>Manage care contexts</p>
                </button>

                <button className="nav-card" onClick={() => onNavigate('COLLEAGUES')}>
                    <span className="nav-icon">🤝</span>
                    <h3>Colleagues</h3>
                    <p>Track professional relationships</p>
                </button>

                <button className="nav-card" onClick={() => onNavigate('EVENTS')}>
                    <span className="nav-icon">📅</span>
                    <h3>Events</h3>
                    <p>Log upcoming challenges</p>
                </button>
            </div>

            <div className="secondary-actions">
                <button className="chat-fab" onClick={onChat} title="Talk to Companion">
                    💬
                </button>
            </div>
        </div>
    );
};
