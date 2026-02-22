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
    const [loading, setLoading] = useState(true);

    const refresh = async () => {
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
        refresh();
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
