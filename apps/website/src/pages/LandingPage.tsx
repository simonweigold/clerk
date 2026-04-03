import { Link } from 'react-router-dom';
import { ArrowRight, Github, Layers, Zap, Shield, Upload } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function LandingPage() {
    const { user } = useAuth();

    return (
        <div className="fade-in">
            {/* Hero Section */}
            <section className="py-20 md:py-28 text-center">
                <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-6 tracking-tight">
                    Executable Reasoning
                    <br />
                    <span className="text-primary">Made Simple</span>
                </h1>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
                    CLERK is the community library for multi-step LLM reasoning workflows.
                    Create, share, and run reasoning kits — from simple prompts to complex
                    LangGraph-powered pipelines.
                </p>
                <div className="flex items-center justify-center gap-4 flex-wrap">
                    {user ? (
                        <Link to="/app" className="btn btn-primary btn-lg">
                            Go to App
                            <ArrowRight className="w-5 h-5" />
                        </Link>
                    ) : (
                        <Link to="/auth/signup" className="btn btn-primary btn-lg">
                            Sign Up for Early Access
                            <ArrowRight className="w-5 h-5" />
                        </Link>
                    )}
                    <a
                        href="https://github.com/clerk/clerk"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-secondary btn-lg"
                    >
                        <Github className="w-5 h-5" />
                        View on GitHub
                    </a>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-16 border-t border-border">
                <div className="text-center mb-12">
                    <h2 className="text-3xl font-bold mb-3">Why CLERK?</h2>
                    <p className="text-muted-foreground max-w-lg mx-auto">
                        Everything you need to build and share executable reasoning workflows
                    </p>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <FeatureCard
                        icon={<Layers className="w-6 h-6" />}
                        title="Multi-Step Workflows"
                        description="Chain prompts together with dependencies. Each step builds on the previous, creating complex reasoning pipelines."
                    />
                    <FeatureCard
                        icon={<Zap className="w-6 h-6" />}
                        title="LangGraph Powered"
                        description="Built on LangGraph for robust, stateful execution. Handle loops, branching, and conditional logic with ease."
                    />
                    <FeatureCard
                        icon={<Shield className="w-6 h-6" />}
                        title="Self-Hostable"
                        description="Own your data. Deploy CLERK on your own infrastructure with full control over your reasoning workflows."
                    />
                    <FeatureCard
                        icon={<Upload className="w-6 h-6" />}
                        title="Kit Marketplace"
                        description="Share your reasoning kits with the community. Discover and use workflows created by others."
                    />
                </div>
            </section>

            {/* How It Works Section */}
            <section className="py-16 border-t border-border">
                <div className="text-center mb-12">
                    <h2 className="text-3xl font-bold mb-3">How It Works</h2>
                    <p className="text-muted-foreground max-w-lg mx-auto">
                        Get started with executable reasoning in three simple steps
                    </p>
                </div>

                <div className="grid md:grid-cols-3 gap-8">
                    <StepCard
                        number={1}
                        title="Install"
                        description="Set up CLERK locally or self-host. One command to get the CLI and web interface running."
                    />
                    <StepCard
                        number={2}
                        title="Define a Kit"
                        description="Create a reasoning kit with prompts, resources, and workflow steps. Version control your reasoning."
                    />
                    <StepCard
                        number={3}
                        title="Execute"
                        description="Run your kit with any input. Watch the reasoning unfold step by step, with full visibility into the process."
                    />
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 text-center border-t border-border">
                <h2 className="text-3xl font-bold mb-4">Ready to get started?</h2>
                <p className="text-muted-foreground max-w-lg mx-auto mb-8">
                    Join the early access list and be the first to experience the future of executable reasoning.
                </p>
                <div className="flex items-center justify-center gap-4 flex-wrap">
                    {user ? (
                        <Link to="/app" className="btn btn-primary btn-lg">
                            Go to Early Access
                            <ArrowRight className="w-5 h-5" />
                        </Link>
                    ) : (
                        <Link to="/auth/signup" className="btn btn-primary btn-lg">
                            Sign Up for Early Access
                            <ArrowRight className="w-5 h-5" />
                        </Link>
                    )}
                </div>
            </section>

            {/* Footer */}
            <footer className="py-8 border-t border-border">
                <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-6">
                        <a
                            href="https://github.com/clerk/clerk"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-foreground transition-colors"
                        >
                            GitHub
                        </a>
                        <Link to="/docs" className="hover:text-foreground transition-colors">
                            Documentation
                        </Link>
                    </div>
                    <p>CLERK — Community Library of Executable Reasoning Kits</p>
                </div>
            </footer>
        </div>
    );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
    return (
        <div className="glass-card text-center p-6">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mx-auto mb-4 text-primary">
                {icon}
            </div>
            <h3 className="font-semibold text-lg mb-2">{title}</h3>
            <p className="text-sm text-muted-foreground">{description}</p>
        </div>
    );
}

function StepCard({ number, title, description }: { number: number; title: string; description: string }) {
    return (
        <div className="text-center">
            <div className="w-12 h-12 rounded-full bg-primary text-white flex items-center justify-center mx-auto mb-4 text-lg font-bold">
                {number}
            </div>
            <h3 className="font-semibold text-lg mb-2">{title}</h3>
            <p className="text-sm text-muted-foreground">{description}</p>
        </div>
    );
}
