import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { resetPassword as apiResetPassword } from '../lib/api';
import { useToast } from '../hooks/useToast';

export default function ResetPasswordPage() {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { addToast } = useToast();

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const data = await apiResetPassword(email);
            if (data.ok) {
                addToast('success', 'If an account with that email exists, a reset link has been sent.');
                navigate('/auth/login');
            } else {
                addToast('error', data.error || 'Something went wrong.');
            }
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Reset failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-sm mx-auto fade-in">
            <div className="glass-card">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold mb-3 tracking-tight">Reset Password</h1>
                    <p className="text-muted-foreground">
                        Enter your email address and we'll send you a link to reset your password.
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

                    <button
                        type="submit"
                        className="btn btn-primary btn-lg w-full"
                        disabled={loading}
                    >
                        {loading ? 'Sending...' : 'Send Reset Link'}
                    </button>
                </form>

                <p className="text-center text-sm text-muted-foreground mt-6">
                    Remember your password?{' '}
                    <Link to="/auth/login" className="text-primary hover:underline font-medium">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    );
}
