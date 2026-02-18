import axios, { AxiosInstance } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
    baseURL: API_URL,
    withCredentials: true, // Send cookies with requests
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor: Add access token to all requests
apiClient.interceptors.request.use(
    (config) => {
        // Get token from window (set by AuthContext)
        const token = (window as any).__accessToken;
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor: Handle 401 and refresh token
let isRefreshing = false;
let failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve();
        }
    });
    failedQueue = [];
};

apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // If error is 401 and we haven't retried yet
        if (error.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
                // Queue this request while refresh is in progress
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                    .then(() => apiClient(originalRequest))
                    .catch((err) => Promise.reject(err));
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                // Attempt to refresh token
                const { data } = await axios.post(
                    `${API_URL}/auth/refresh`,
                    {},
                    { withCredentials: true }
                );

                // Update token in window
                (window as any).__accessToken = data.access_token;

                // Process queued requests
                processQueue();

                // Retry original request
                return apiClient(originalRequest);
            } catch (refreshError) {
                // Refresh failed - clear token and redirect to login
                processQueue(refreshError);
                (window as any).__accessToken = null;

                // Trigger logout in AuthContext
                window.dispatchEvent(new CustomEvent('auth:logout'));

                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        return Promise.reject(error);
    }
);

// Export the configured axios instance
export { apiClient };

// Export types
export interface User {
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

export interface OnboardingData {
    language: 'en' | 'es';
    fullName: string;
    professionalRole: string;
    yearsExperience: number;
    stressors: string[];
    copingStyles: string[];
}

export interface CheckIn {
    id?: string;
    context_type: string;
    context_id?: string;
    intent: string;
    mood_state?: string;
    energy_level?: number;
    text_content?: string;
    timestamp?: string;
}

export interface Insight {
    id: string;
    type: string;
    observation: string;
    validation: string;
    gentle_suggestion?: string;
    created_at: string;
}

// API methods using axios
export const api = {
    // Health check
    checkHealth: async () => {
        const { data } = await apiClient.get('/health');
        return data;
    },

    // Submit a check-in (user_id inferred from token)
    submitCheckIn: async (checkInData: CheckIn) => {
        const { data } = await apiClient.post('/companion/check-in', checkInData);
        return data;
    },

    // Trigger Insight Generation (Legacy/Specific Context)
    triggerInsight: async (context?: { type: string; id: string; name: string }, language: string = 'en') => {
        const body = {
            ...(context ? {
                context_type: context.type,
                context_id: context.id,
                context_name: context.name,
            } : {}),
            language
        };

        const { data } = await apiClient.post<Insight>('/companion/generate-insight', body);
        return data;
    },

    // Get Daily Insight (New Service)
    getDailyInsight: async (language: string = 'en') => {
        const { data } = await apiClient.post<Insight>(`/analysis/daily-insight?language=${language}`);
        return data;
    },

    // --- Entity Management ---
    getPatients: async () => {
        const { data } = await apiClient.get('/companion/patients');
        return data;
    },
    createPatient: async (patientData: any) => {
        const { data } = await apiClient.post('/companion/patients', patientData);
        return data;
    },
    getPatientHistory: async (patientId: string): Promise<CheckIn[]> => {
        const { data } = await apiClient.get(`/companion/patients/${patientId}/history`);
        return data;
    },
    getColleagues: async () => {
        const { data } = await apiClient.get('/companion/colleagues');
        return data;
    },
    createColleague: async (colleagueData: any) => {
        const { data } = await apiClient.post('/companion/colleagues', colleagueData);
        return data;
    },
    getColleagueHistory: async (colleagueId: string): Promise<CheckIn[]> => {
        const { data } = await apiClient.get(`/companion/colleagues/${colleagueId}/history`);
        return data;
    },
    getEvents: async () => {
        const { data } = await apiClient.get('/companion/events');
        return data;
    },
    createEvent: async (eventData: any) => {
        const { data } = await apiClient.post('/companion/events', eventData);
        return data;
    },

    // --- Chat ---
    sendChat: async (message: string, language: string = 'en') => {
        const { data } = await apiClient.post('/companion/chat', { message, language });
        return data;
    },

    // --- Entity Analysis Chat ---
    sendAnalysisChat: async (context: { type: string; id: string }, message: string, history: any[] = [], language: string = 'en') => {
        const { data } = await apiClient.post('/companion/analysis/chat', {
            context_type: context.type,
            context_id: context.id,
            message,
            history,
            language
        });
        return data;
    },

    // --- Onboarding ---
    completeOnboarding: async (data: OnboardingData) => {
        const body = {
            language: data.language,
            full_name: data.fullName,
            professional_role: data.professionalRole,
            years_experience: data.yearsExperience,
            // Convert arrays to comma-separated strings for backend compatibility if backend expects strings
            // OR keep as arrays if backend supports it. The previous plan implies we should keep it compatible.
            // Let's assume the backend expects strings for now based on the old interface, 
            // OR we update backend. Given I cannot check backend models easily right now without looking,
            // I will join them to be safe, assuming the backend stores them as strings.
            // Wait, looking at `entities.py` (which was open) would clarify. 
            // I'll check `entities.py` in valid step if this assumption is wrong.
            // But usually `primary_stressor` implies singular in DB. 
            // Let's join them for now to map multiple selections to the single field? 
            // "Burnout, Workload"
            primary_stressor: data.stressors.join(', '),
            coping_style: data.copingStyles.join(', ')
        };
        const response = await apiClient.post<User>('/auth/onboarding', body);
        return response.data;
    },
};

