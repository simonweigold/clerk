import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { createKit } from '../lib/api';
import { useToast } from '../hooks/useToast';

export default function KitCreatePage() {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { addToast } = useToast();

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const data = await createKit(name, description);
            if (data.ok) {
                addToast('success', 'Kit created.');
                navigate(`/kit/${data.slug}`);
            }
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Create failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fade-in max-w-lg">
            <nav className="text-sm text-muted-foreground mb-6">
                <Link to="/" className="hover:text-foreground transition-colors">Kits</Link>
                <span className="mx-2">/</span>
                <span className="text-foreground">Create</span>
            </nav>

            <h1 className="text-3xl font-bold text-foreground mb-6 tracking-tight">Create a Reasoning Kit</h1>

            <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                    <label className="label" htmlFor="kit-name">Name</label>
                    <input type="text" id="kit-name" className="input" placeholder="My Reasoning Kit" required autoFocus value={name} onChange={(e) => setName(e.target.value)} />
                    <p className="text-xs text-muted-foreground mt-1.5">A readable name for your kit. A URL-friendly slug will be generated automatically.</p>
                </div>
                <div>
                    <label className="label" htmlFor="kit-description">Description <span className="text-muted-foreground font-normal">(optional)</span></label>
                    <textarea id="kit-description" className="input" rows={3} placeholder="Describe what this reasoning kit does..." value={description} onChange={(e) => setDescription(e.target.value)} />
                </div>
                <div className="flex gap-3 pt-2">
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? 'Creating...' : 'Create Kit'}
                    </button>
                    <Link to="/" className="btn btn-ghost">Cancel</Link>
                </div>
            </form>

            <hr className="divider mt-8" />

            <div className="text-sm text-muted-foreground">
                <p className="font-medium text-foreground mb-2">What's next?</p>
                <p>After creating your kit, you can add resources (files your workflow references) and workflow steps
                    (sequential LLM instructions). Each step can reference resources with <code className="bg-muted px-1.5 py-0.5 rounded-md text-xs">{'{'}<span>resource_N</span>{'}'}</code> and outputs of earlier
                    steps with <code className="bg-muted px-1.5 py-0.5 rounded-md text-xs">{'{'}<span>workflow_N</span>{'}'}</code>.</p>
            </div>
        </div>
    );
}
