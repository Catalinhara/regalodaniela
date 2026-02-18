import React, { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react';

interface User {
    id: string;
    email: string;
    full_name?: string;
    is_active: boolean;
    language: string;

    // Onboarding Profile Fields
    onboarding_completed: boolean;
    professional_role?: string;
    years_experience?: number;
    primary_stressor?: string;
    coping_style?: string;

    created_at: string;
}

interface AuthContextType {
    user: User | null;
    accessToken: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    loginWithGoogle: (credential: string) => Promise<void>;
    register: (email: string, password: string, fullName?: string) => Promise<void>;
    logout: () => Promise<void>;
    refreshToken: () => Promise<boolean>;
    setAccessToken: (token: string | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

interface AuthProviderProps {
    children: ReactNode;
}

const API_URL = import.meta.env.VITE_API_URL ||
    (typeof window !== 'undefined' && window.location.hostname !== 'localhost'
        ? `http://${window.location.hostname}:8000`
        : 'http://localhost:8000');

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [accessToken, setAccessTokenState] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const refreshPromise = useRef<Promise<boolean> | null>(null);

    const isAuthenticated = !!user && !!accessToken;

    // Set access token and expose to API client
    const setAccessToken = (token: string | null) => {
        setAccessTokenState(token);
        // Expose to API client
        if (typeof window !== 'undefined') {
            (window as any).__accessToken = token;
        }
    };

    // Auto-restore session on mount
    useEffect(() => {
        const restoreSession = async () => {
            try {
                await refreshToken();
            } catch (error) {
                console.error('Failed to restore session:', error);
            } finally {
                // Always clear loading state after attempting to restore session
                setIsLoading(false);
            }
        };
        restoreSession();
    }, []);

    const register = async (email: string, password: string, fullName?: string) => {
        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Important for cookies
                body: JSON.stringify({
                    email,
                    password,
                    full_name: fullName,
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Registration failed');
            }

            const data = await response.json();
            setUser(data.user);
            setAccessToken(data.access_token);
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    };

    const login = async (email: string, password: string) => {
        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Important for cookies
                body: JSON.stringify({ email, password }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            setUser(data.user);
            setAccessToken(data.access_token);
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    };

    const loginWithGoogle = async (credential: string) => {
        try {
            console.log('Google login attempt initiated with credential');
            const response = await fetch(`${API_URL}/auth/google`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ credential }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Google Login failed');
            }

            const data = await response.json();
            setUser(data.user);
            setAccessToken(data.access_token);
        } catch (error) {
            console.error('Google Login error:', error);
            throw error;
        }
    };

    const refreshToken = async (): Promise<boolean> => {
        // Mutex: If a refresh is already in progress, return the existing promise
        if (refreshPromise.current) {
            return refreshPromise.current;
        }

        refreshPromise.current = (async () => {
            try {
                const response = await fetch(`${API_URL}/auth/refresh`, {
                    method: 'POST',
                    credentials: 'include', // Send HTTP-only cookie
                });

                if (!response.ok) {
                    return false;
                }

                const data = await response.json();
                setAccessToken(data.access_token);

                // Get user profile
                const userResponse = await fetch(`${API_URL}/auth/me`, {
                    headers: {
                        'Authorization': `Bearer ${data.access_token}`,
                    },
                });

                if (userResponse.ok) {
                    const userData = await userResponse.json();
                    setUser(userData);
                    return true;
                }

                return false;
            } catch (error) {
                console.error('Token refresh error:', error);
                return false;
            } finally {
                refreshPromise.current = null;
            }
        })();

        return refreshPromise.current;
    };

    const logout = async () => {
        try {
            await fetch(`${API_URL}/auth/logout`, {
                method: 'POST',
                headers: accessToken ? {
                    'Authorization': `Bearer ${accessToken}`,
                } : {},
                credentials: 'include',
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            setUser(null);
            setAccessToken(null);
        }
    };

    const value: AuthContextType = {
        user,
        accessToken,
        isAuthenticated,
        isLoading,
        login,
        loginWithGoogle,
        register,
        logout,
        refreshToken,
        setAccessToken,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
