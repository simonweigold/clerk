import { Link } from 'react-router-dom';
import { CheckCircle, Github, LogOut, Mail } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function EarlyAccessPage() {
    const { user } = useAuth();

    return (
        <div className="max-w-2xl mx-auto py-20 fade-in">
            <div className="glass-card text-center py-16 px-8">
                <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
                    <CheckCircle className="w-10 h-10 text-green-600" />
                </div>

                <h1 className="text-4xl font-bold mb-4">You're on the List!</h1>

                <p className="text-lg text-muted-foreground mb-6">
                    Thanks for signing up for early access. You're now part of the CLERK community.
                </p>

                {user?.email && (
                    <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mb-8">
                        <Mail className="w-4 h-4" />
                        <span>{user.email}</span>
                    </div>
                )}

                <div className="bg-muted/50 rounded-lg p-6 mb-8">
                    <h2 className="font-semibold mb-3">What's Coming</h2>
                    <ul className="text-sm text-muted-foreground space-y-2 text-left">
                        <li className="flex items-start gap-2">
                            <span className="text-primary">•</span>
                            <span>Full access to the kit marketplace and reasoning workflows</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-primary">•</span>
                            <span>Create and manage your own reasoning kits</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-primary">•</span>
                            <span>Execute multi-step LLM reasoning pipelines</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-primary">•</span>
                            <span>Share kits with the community</span>
                        </li>
                    </ul>
                </div>

                <p className="text-sm text-muted-foreground mb-8">
                    We'll notify you via email as soon as full access is available.
                    In the meantime, check out the documentation and GitHub repository.
                </p>

                <div className="flex items-center justify-center gap-4 flex-wrap">
                    <a
                        href="https://github.com/clerk/clerk"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-secondary"
                    >
                        <Github className="w-4 h-4" />
                        View on GitHub
                    </a>
                    <Link to="/docs" className="btn btn-ghost">
                        Read Docs
                    </Link>
                    <Link to="/auth/logout" className="btn btn-ghost text-muted-foreground">
                        <LogOut className="w-4 h-4" />
                        Sign Out
                    </Link>
                </div>
            </div>
        </div>
    );
}
