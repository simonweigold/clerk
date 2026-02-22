import { useEffect, useState, type FormEvent } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getKit, updateKit } from '../lib/api';
import { useToast } from '../hooks/useToast';

export default function KitEditPage() {
    const { slug } = useParams<{ slug: string }>();
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const navigate = useNavigate();
    const { addToast } = useToast();

    useEffect(() => {
        if (!slug) return;
        getKit(slug)
            .then((data) => {
                setName(data.kit.name);
                setDescription(data.kit.description || '');
            })
            .catch((err) => addToast('error', err instanceof Error ? err.message : 'Failed to load kit.'))
            .finally(() => setLoading(false));
    }, [slug]);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!slug) return;
        setSaving(true);
        try {
            await updateKit(slug, name, description);
            addToast('success', 'Kit updated.');
            navigate(`/kit/${slug}`);
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Update failed.');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="empty-state fade-in">
                <div className="flex items-center justify-center gap-2">
                    <span className="pulse-dot" /><span className="pulse-dot" /><span className="pulse-dot" />
                </div>
            </div>
        );
    }

    return (
        <div className="fade-in max-w-lg">
            <nav className="text-sm text-muted-foreground mb-6">
                <Link to="/" className="hover:text-foreground transition-colors">Kits</Link>
                <span className="mx-2">/</span>
                <Link to={`/kit/${slug}`} className="hover:text-foreground transition-colors">{name}</Link>
                <span className="mx-2">/</span>
                <span className="text-foreground">Edit</span>
            </nav>

            <h1 className="text-3xl font-bold text-foreground mb-6 tracking-tight">Edit Kit</h1>

            <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                    <label className="label" htmlFor="kit-name">Name</label>
                    <input type="text" id="kit-name" className="input" required value={name} onChange={(e) => setName(e.target.value)} />
                </div>
                <div>
                    <label className="label" htmlFor="kit-description">Description <span className="text-muted-foreground font-normal">(optional)</span></label>
                    <textarea id="kit-description" className="input" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
                </div>
                <div className="flex gap-3 pt-2">
                    <button type="submit" className="btn btn-primary" disabled={saving}>
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                    <Link to={`/kit/${slug}`} className="btn btn-ghost">Cancel</Link>
                </div>
            </form>
        </div>
    );
}
