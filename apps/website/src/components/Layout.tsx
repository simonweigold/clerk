import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { ToastContainer } from "../hooks/useToast";
import { LogOut, Github } from "lucide-react";

export default function Layout() {
  const { user, supabaseConfigured, loading } = useAuth();
  const location = useLocation();

  // Determine if we're on a landing page route
  const isLandingRoute = location.pathname === "/";
  // Determine if we're on an app route (hidden routes that still exist in codebase)
  const isAppRoute = ["/home", "/kit/", "/settings", "/app"].some(
    (path) => location.pathname === path || location.pathname.startsWith(path),
  );

  // isActive function disabled with app navigation links
  // const isActive = (path: string) => {
  //   if (path === "/") return location.pathname === "/";
  //   return location.pathname.startsWith(path);
  // };

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
            {isLandingRoute ? (
              // Landing page navigation
              <>
                <Link to="/docs" className="nav-link">
                  Docs
                </Link>
                <a
                  href="https://github.com/simonweigold/clerk"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="nav-link"
                >
                  <Github className="w-4 h-4" />
                </a>
                {loading ? (
                  <div className="flex items-center justify-center ml-2 w-8 h-8">
                    <span className="pulse-dot" />
                  </div>
                ) : user ? (
                  <Link to="/app" className="btn btn-primary btn-sm ml-2">
                    App
                  </Link>
                ) : (
                  <>
                    <Link
                      to="/auth/login"
                      className="btn btn-ghost btn-sm ml-2"
                    >
                      Sign In
                    </Link>
                    <Link
                      to="/auth/signup"
                      className="btn btn-primary btn-sm ml-2"
                    >
                      Sign Up
                    </Link>
                  </>
                )}
              </>
            ) : (
              // App/Auth navigation
              <>
                {!isAppRoute && (
                  <Link to="/" className="nav-link">
                    Home
                  </Link>
                )}
                {/* App navigation links disabled for launch */}
                {/* {isAppRoute && user && (
                  <>
                    <Link
                      to="/home"
                      className={`nav-link ${isActive("/home") ? "active" : ""}`}
                    >
                      Kits
                    </Link>
                    <Link
                      to="/docs"
                      className={`nav-link ${isActive("/docs") ? "active" : ""}`}
                    >
                      Docs
                    </Link>
                    <Link
                      to="/kit/new"
                      className={`nav-link ${isActive("/kit/new") ? "active" : ""}`}
                    >
                      Create
                    </Link>
                  </>
                )} */}
                {loading ? (
                  <div className="flex items-center justify-center ml-2 w-8 h-8">
                    <span className="pulse-dot" />
                  </div>
                ) : supabaseConfigured ? (
                  <>
                    {user ? (
                      <>
                        {/* Settings link disabled for launch */}
                        {/* <Link
                          to="/settings"
                          className="btn btn-ghost btn-sm ml-2 px-2"
                          title="Account Settings"
                        >
                          <Settings className="w-4 h-4" />
                        </Link> */}
                        <Link
                          to="/auth/logout"
                          className="btn btn-ghost btn-sm ml-1 px-2"
                          title="Sign Out"
                        >
                          <LogOut className="w-4 h-4" />
                        </Link>
                      </>
                    ) : (
                      !isLandingRoute && (
                        <Link
                          to="/auth/login"
                          className="btn btn-ghost btn-sm ml-2"
                        >
                          Sign In
                        </Link>
                      )
                    )}
                  </>
                ) : null}
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

      {/* Footer - only show on non-landing pages (LandingPage has its own footer) */}
      {!isLandingRoute && (
        <footer className="bg-muted/50 border-t border-border">
          <div className="max-w-5xl mx-auto px-6 py-4 text-center text-sm text-muted-foreground">
            CLERK &mdash; Community Library of Executable Reasoning Kits
          </div>
        </footer>
      )}
    </div>
  );
}
