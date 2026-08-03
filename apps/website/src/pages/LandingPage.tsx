import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import LifecycleAnimation from "../components/LifecycleAnimation";

export default function LandingPage() {
  const { user } = useAuth();
  const [showHero, setShowHero] = useState(false);

  return (
    <div className="landing">
      <div className="relative min-h-[80vh] flex items-center justify-center">
        <div
          className={`absolute inset-0 flex items-center justify-center px-6 transition-opacity duration-700 ${
            showHero ? "opacity-0 pointer-events-none" : "opacity-100"
          }`}
        >
          <LifecycleAnimation onComplete={() => setShowHero(true)} />
        </div>

        <div
          className={`text-center px-6 transition-opacity duration-700 ${
            showHero ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
        >
          <h1 className="max-w-3xl mx-auto">
            Multi-step LLM workflows
            <br />
            you can <span className="acc">score</span>.
          </h1>
          <p className="sub mt-5 max-w-md mx-auto">
            Reusable reasoning pipelines, judged out of 100.
          </p>
          <div className="mt-9 flex items-center justify-center gap-3.5 flex-wrap">
            {user ? (
              <Link to="/app" className="btn-landing btn-solid">
                Go to App
              </Link>
            ) : (
              <Link to="/auth/signup" className="btn-landing btn-solid">
                Sign Up for Early Access
              </Link>
            )}
            <a
              href="https://github.com/simonweigold/clerk"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-landing btn-line"
            >
              GitHub
            </a>
          </div>
          <footer className="mt-16 text-sm text-[var(--muted-l)]">
            OpenClerk · MIT License
          </footer>
        </div>
      </div>
    </div>
  );
}
