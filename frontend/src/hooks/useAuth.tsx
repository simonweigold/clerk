import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { getMe, type User } from '../lib/api';

interface AuthContextType {
    user: User | null;
    supabaseConfigured: boolean;
    loading: boolean;
    refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    supabaseConfigured: false,
    loading: true,
    refresh: async () => { },
});

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [supabaseConfigured, setSupabaseConfigured] = useState(false);
    const [loading, setLoading] = useState(false);

    const refresh = async () => {
        setLoading(true);
        try {
            const data = await getMe();
            setUser(data.user);
            setSupabaseConfigured(data.supabase_configured);
        } catch {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // Non-blocking auth check - start with null user, verify in background
        getMe()
            .then((data) => {
                setUser(data.user);
                setSupabaseConfigured(data.supabase_configured);
            })
            .catch(() => {
                setUser(null);
            });
    }, []);

    return (
        <AuthContext.Provider value={{ user, supabaseConfigured, loading, refresh }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}
