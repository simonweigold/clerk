import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ToastContainer } from '../hooks/useToast';

export default function Layout() {
    const { user, supabaseConfigured } = useAuth();
    const location = useLocation();

    const isActive = (path: string) => {
        if (path === '/') return location.pathname === '/';
        return location.pathname.startsWith(path);
    };

    return (
        <div className="min-h-screen flex flex-col bg-white font-sans text-foreground antialiased">
            {/* Navigation — frosted glass */}
            <header className="sticky top-0 z-50 border-b border-border bg-white/80 backdrop-blur-lg">
                <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link to="/" className="clerk-logo" id="clerk-logo">
                        <span className="clerk-dot" />
                        <span className="clerk-dot" />
                        <span className="clerk-dot" />
                        <span className="clerk-dot" />
                        <span className="clerk-dot" />
                    </Link>
                    <nav className="flex items-center gap-2">
                        <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
                            Kits
                        </Link>
                        {user && (
                            <Link
                                to="/kit/new"
                                className={`nav-link ${isActive('/kit/new') ? 'active' : ''}`}
                            >
                                Create
                            </Link>
                        )}
                        {supabaseConfigured && (
                            <>
                                {user ? (
                                    <>
                                        <span className="text-sm text-muted-foreground ml-2">
                                            {user.email}
                                        </span>
                                        <Link to="/auth/logout" className="btn btn-ghost btn-sm ml-1">
                                            Sign Out
                                        </Link>
                                    </>
                                ) : (
                                    <Link to="/auth/login" className="btn btn-ghost btn-sm ml-2">
                                        Sign In
                                    </Link>
                                )}
                            </>
                        )}
                    </nav>
                </div>
            </header>

            {/* Toast messages */}
            <ToastContainer />

            {/* Main content */}
            <main className="max-w-5xl mx-auto px-6 py-10 flex-1 w-full">
                <Outlet />
            </main>

            {/* Footer */}
            <footer className="bg-muted/50 border-t border-border">
                <div className="max-w-5xl mx-auto px-6 py-4 text-center text-sm text-muted-foreground">
                    CLERK &mdash; Community Library of Executable Reasoning Kits
                </div>
            </footer>
        </div>
    );
}
