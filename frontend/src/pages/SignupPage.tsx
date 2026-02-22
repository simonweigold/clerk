import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { signup as apiSignup } from '../lib/api';
import { useToast } from '../hooks/useToast';

export default function SignupPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { addToast } = useToast();

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const data = await apiSignup(email, password);
            if (data.ok) {
                addToast('success', 'Account created. Please check your email for confirmation.');
                navigate('/auth/login');
            } else {
                addToast('error', data.error || 'Could not create account.');
            }
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Sign up failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-sm mx-auto fade-in">
            <div className="glass-card">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold mb-3 tracking-tight">Create Account</h1>
                    <p className="text-muted-foreground">
                        Create an account to build and manage your own reasoning kits, track
                        executions, and share workflows with others.
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
                        <label htmlFor="password" className="label">Password</label>
                        <input
                            type="password"
                            id="password"
                            className="input"
                            placeholder="Choose a password"
                            required
                            autoComplete="new-password"
                            minLength={6}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                        <p className="text-xs text-muted-foreground mt-1.5">Minimum 6 characters.</p>
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary btn-lg w-full"
                        disabled={loading}
                    >
                        {loading ? 'Creating...' : 'Create Account'}
                    </button>
                </form>

                <p className="text-center text-sm text-muted-foreground mt-6">
                    Already have an account?{' '}
                    <Link to="/auth/login" className="text-primary hover:underline font-medium">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    );
}
