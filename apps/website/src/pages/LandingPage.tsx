import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import LifecycleAnimation from "../components/LifecycleAnimation";

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="landing fade-in">
      {/* Hero */}
      <section className="pt-24 pb-10 text-center">
        <span className="eyebrow">Open-source · Reasoning kits</span>
        <h1 className="mt-6 max-w-3xl mx-auto">
          Multi-step LLM workflows
          <br />
          you can <span className="acc">score</span>.
        </h1>
        <p className="sub mt-6 max-w-xl mx-auto">
          OpenClerk packages expert reasoning into reusable pipelines where
          every step is judged. Quality becomes measured, not guessed.
        </p>
        <div className="mt-10 flex items-center justify-center gap-3.5 flex-wrap">
          {user ? (
            <Link to="/app" className="btn-landing btn-solid">Go to App</Link>
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
            View on GitHub
          </a>
        </div>
      </section>

      {/* The animation is the explanation */}
      <section className="pb-16">
        <div className="max-w-[760px] mx-auto">
          <LifecycleAnimation />
        </div>
      </section>

      {/* Three quiet points, no cards, no icons */}
      <section className="hairline py-14">
        <div className="max-w-3xl mx-auto grid sm:grid-cols-3 gap-10 text-center">
          <Point title="Kits" line="Executable multi-step workflows, versioned like code." />
          <Point title="Evaluation first" line="A judge model scores every run out of 100." />
          <Point title="Open" line="MIT licensed and self-hostable." />
        </div>
      </section>

      {/* Roadmap strip */}
      <section className="hairline py-14 text-center">
        <p className="sub max-w-md mx-auto">
          The same kits can later be{" "}
          <span className="text-foreground font-medium">
            distilled into a small, fast model
          </span>{" "}
          that knows the workflow natively.
        </p>
        <div className="mt-7 inline-flex items-center text-sm font-medium">
          <span className="px-4 py-2 border-y border-l border-[var(--hairline)] rounded-l-[10px] text-[var(--brand)]">Author</span>
          <span className="px-2 text-gray-300">→</span>
          <span className="px-4 py-2 border-y border-[var(--hairline)] text-[var(--muted-l)]">Evaluate</span>
          <span className="px-2 text-gray-300">→</span>
          <span className="px-4 py-2 border-y border-[var(--hairline)] text-[var(--muted-l)]">Compile</span>
          <span className="px-2 text-gray-300">→</span>
          <span className="px-4 py-2 border-y border-r border-[var(--hairline)] rounded-r-[10px] text-[var(--brand)]">Distill</span>
        </div>
      </section>

      {/* Footer note */}
      <section className="hairline py-8 text-center text-sm text-[var(--muted-l)]">
        CLERK · Community Library of Executable Reasoning Kits · MIT License
      </section>
    </div>
  );
}

function Point({ title, line }: { title: string; line: string }) {
  return (
    <div>
      <span className="inline-block w-2 h-2 rounded-full bg-[var(--brand)] mb-3" />
      <h3 className="font-semibold text-base mb-1">{title}</h3>
      <p className="text-sm text-[var(--muted-l)]">{line}</p>
    </div>
  );
}
