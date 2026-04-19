import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import type { ReactNode } from 'react';

interface AuthGuardProps {
    children: ReactNode;
    fallback?: ReactNode;
}

export default function AuthGuard({ children, fallback }: AuthGuardProps) {
    const { user, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <div className="flex items-center gap-2">
                    <span className="pulse-dot" />
                    <span className="pulse-dot" />
                    <span className="pulse-dot" />
                </div>
            </div>
        );
    }

    if (!user) {
        // Redirect to login, preserving the intended destination
        if (fallback) {
            return <>{fallback}</>;
        }
        return <Navigate to="/auth/login" state={{ from: location.pathname }} replace />;
    }

    return <>{children}</>;
}
