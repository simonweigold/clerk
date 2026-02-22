import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { logout as apiLogout } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';

export default function LogoutPage() {
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { refresh } = useAuth();
    const { addToast } = useToast();

    const handleLogout = async () => {
        setLoading(true);
        try {
            await apiLogout();
            await refresh();
            addToast('info', 'Signed out.');
            navigate('/');
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Sign out failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-sm mx-auto fade-in">
            <div className="glass-card">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold mb-3 tracking-tight">Sign Out</h1>
                    <p className="text-muted-foreground">Are you sure you want to sign out?</p>
                </div>

                <div className="space-y-4">
                    <button
                        onClick={handleLogout}
                        className="btn btn-primary btn-lg w-full"
                        disabled={loading}
                    >
                        {loading ? 'Signing out...' : 'Sign Out'}
                    </button>
                    <Link to="/" className="btn btn-ghost w-full block text-center">
                        Cancel
                    </Link>
                </div>

                <p className="text-center text-sm text-muted-foreground mt-6">
                    You will be redirected to the home page after signing out.
                </p>
            </div>
        </div>
    );
}
