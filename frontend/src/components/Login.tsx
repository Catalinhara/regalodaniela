import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { GoogleLogin } from '@react-oauth/google';
import './Auth.css';

interface LoginProps {
    onSwitchToRegister: () => void;
}

export const Login: React.FC<LoginProps> = ({ onSwitchToRegister }) => {
    const { t } = useTranslation();
    const { login, loginWithGoogle } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await login(email, password);
        } catch (err: any) {
            setError(err.message || 'Login failed. Please check your credentials.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-container">
            {/* ATMOSPHERIC BACKGROUND BLOBS */}
            <div className="auth-blob blob-1"></div>
            <div className="auth-blob blob-2"></div>
            <div className="auth-blob blob-3"></div>

            <div className="auth-card">
                <h1 className="auth-title">{t('auth.welcome_back')}</h1>
                <p className="auth-subtitle">{t('auth.subtitle')}</p>

                {error && <div className="auth-error">{error}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label htmlFor="email">{t('auth.email')}</label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            placeholder="you@example.com"
                            autoComplete="email"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">{t('auth.password')}</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            placeholder="••••••••"
                            autoComplete="current-password"
                        />
                    </div>

                    <button
                        type="submit"
                        className="auth-button"
                        disabled={isLoading}
                    >
                        {isLoading ? t('common.loading') : t('auth.login_button')}
                    </button>
                </form>

                <div className="divider-container">
                    <div className="divider-line"></div>
                    <span className="divider-text">OR</span>
                    <div className="divider-line"></div>
                </div>

                <div className="google-login-container">
                    <GoogleLogin
                        onSuccess={credentialResponse => {
                            if (credentialResponse.credential) {
                                loginWithGoogle(credentialResponse.credential)
                                    .catch(() => setError('Google Login Failed'));
                            }
                        }}
                        onError={() => {
                            setError('Google Login Failed');
                        }}
                        useOneTap={false}
                        auto_select={false}
                    />
                </div>

                <div className="auth-footer">
                    <p>
                        {t('auth.signup_link')}
                        <button
                            type="button"
                            onClick={onSwitchToRegister}
                            className="auth-link"
                            style={{ marginLeft: '4px' }}
                        >
                            {t('auth.create_one')}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};
