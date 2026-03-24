import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { login as apiLogin } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { refresh } = useAuth();
    const { addToast } = useToast();

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const data = await apiLogin(email, password);
            if (data.ok) {
                await refresh();
                addToast('success', 'Signed in.');
                navigate('/');
            } else {
                addToast('error', data.error || 'Invalid credentials.');
            }
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Sign in failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-sm mx-auto fade-in">
            <div className="glass-card">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold mb-3 tracking-tight">Sign In</h1>
                    <p className="text-muted-foreground">
                        Sign in to create, manage, and track your reasoning kits.
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label htmlFor="email" className="label">Email</label>
                        <input
                            type="email"
                            id="email"
                            className="input"
                            placeholder="you@example.com"
                            required
                            autoComplete="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>

                    <div>
                        <div className="flex items-center justify-between">
                            <label htmlFor="password" className="label">Password</label>
                            <Link
                                to="/auth/reset-password"
                                className="text-xs text-primary hover:underline font-medium"
                            >
                                Forgot password?
                            </Link>
                        </div>
                        <input
                            type="password"
                            id="password"
                            className="input"
                            placeholder="Your password"
                            required
                            autoComplete="current-password"
                            minLength={6}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary btn-lg w-full"
                        disabled={loading}
                    >
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>

                <p className="text-center text-sm text-muted-foreground mt-6">
                    Don't have an account?{' '}
                    <Link to="/auth/signup" className="text-primary hover:underline font-medium">
                        Sign up
                    </Link>
                </p>
            </div>
        </div>
    );
}
