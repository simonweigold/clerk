import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getKit, deleteKit, addResource, deleteResource, updateResource, addStep, deleteStep, updateStep, type KitDetail, type Resource, type Step } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';

function ResourceCard({ resource, slug, isOwner, onRefresh }: {
    resource: Resource; slug: string; isOwner: boolean; onRefresh: () => void;
}) {
    const { addToast } = useToast();
    const [expanded, setExpanded] = useState(false);
    const [editing, setEditing] = useState(false);
    const [editDisplayName, setEditDisplayName] = useState(resource.display_name || '');
    const getInitialMode = () => resource.is_dynamic ? 'dynamic' : (resource.mime_type === 'text/plain' || resource.filename?.endsWith('.txt') ? 'text' : 'file');
    const [editMode, setEditMode] = useState<'file' | 'text' | 'dynamic'>(getInitialMode);
    const [editFile, setEditFile] = useState<File | null>(null);
    const [editText, setEditText] = useState('');
    const [saving, setSaving] = useState(false);

    const handleDelete = async () => {
        if (!confirm('Delete this resource?')) return;
        try {
            await deleteResource(slug, resource.number);
            addToast('success', 'Resource deleted.');
            onRefresh();
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Delete failed.');
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const fd = new FormData();
            fd.append('display_name', editDisplayName);
            if (editMode === 'dynamic') {
                fd.append('is_dynamic', 'on');
                if (editText.trim()) fd.append('text_content', editText);
            } else if (editMode === 'file' && editFile) {
                fd.append('file', editFile);
            } else if (editMode === 'text' && editText.trim()) {
                fd.append('text_content', editText);
            }
            await updateResource(slug, resource.number, fd);
            addToast('success', 'Resource updated.');
            setEditing(false);
            onRefresh();
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Update failed.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="step-card">
            <div className="step-card-header flex items-center justify-between">
                <span className="flex items-center gap-2">
                    <span className="font-medium">{resource.display_name || resource.filename}</span>
                    {resource.is_dynamic && <span className="badge badge-primary">Dynamic</span>}
                </span>
                <span className="flex items-center gap-2">
                    {isOwner && (
                        <>
                            <button onClick={() => {
                                setEditing(!editing);
                                setEditDisplayName(resource.display_name || '');
                                const mode = getInitialMode();
                                setEditMode(mode);
                                setEditFile(null);
                                setEditText((mode === 'dynamic' || mode === 'text') && resource.extracted_text ? resource.extracted_text : '');
                            }} className="btn btn-ghost btn-sm" title="Edit">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                </svg>
                            </button>
                            <button onClick={handleDelete} className="btn btn-ghost btn-sm text-destructive" title="Delete">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" /><path d="M10 11v6" /><path d="M14 11v6" />
                                </svg>
                            </button>
                        </>
                    )}
                </span>
            </div>
            {editing && (
                <div className="step-card-body space-y-4 border-t border-border pt-3">
                    <div className="flex gap-2">
                        <button type="button" onClick={() => { setEditMode('file'); setEditText(''); setEditFile(null); }} className={`btn btn-sm ${editMode === 'file' ? 'btn-primary' : 'btn-ghost'}`}>File Upload</button>
                        <button type="button" onClick={() => { setEditMode('text'); setEditText(''); setEditFile(null); }} className={`btn btn-sm ${editMode === 'text' ? 'btn-primary' : 'btn-ghost'}`}>Text Input</button>
                        <button type="button" onClick={() => { setEditMode('dynamic'); setEditText(resource.is_dynamic && resource.extracted_text ? resource.extracted_text : ''); setEditFile(null); }} className={`btn btn-sm ${editMode === 'dynamic' ? 'btn-primary' : 'btn-ghost'}`}>Dynamic Resource</button>
                    </div>

                    <div>
                        <label className="label text-xs">Display Name</label>
                        <input type="text" className="input" value={editDisplayName} onChange={(e) => setEditDisplayName(e.target.value)} placeholder="Readable name" />
                    </div>

                    {editMode === 'file' && (
                        <div>
                            <label className="label text-xs">Replace file <span className="text-muted-foreground font-normal">(optional)</span></label>
                            <input type="file" className="input text-sm" onChange={(e) => setEditFile(e.target.files?.[0] || null)} />
                        </div>
                    )}

                    {editMode === 'text' && (
                        <div>
                            <label className="label text-xs">Replace content with text <span className="text-muted-foreground font-normal">(optional)</span></label>
                            <textarea className="input text-sm" rows={4} value={editText} onChange={(e) => setEditText(e.target.value)} placeholder="Paste new text content..." />
                        </div>
                    )}

                    {editMode === 'dynamic' && (
                        <div className="text-sm text-muted-foreground space-y-2">
                            <p className="text-xs">Dynamic resources let users provide custom input when running the kit. The value will be replaced at execution time.</p>
                            <div>
                                <label className="label text-xs">Update Default Content <span className="text-muted-foreground font-normal">(optional)</span></label>
                                <textarea className="input text-sm" rows={3} value={editText} onChange={(e) => setEditText(e.target.value)} placeholder="Default or placeholder text..." />
                            </div>
                        </div>
                    )}

                    <div className="flex gap-2 pt-1">
                        <button onClick={handleSave} className="btn btn-primary btn-sm" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                        <button onClick={() => setEditing(false)} className="btn btn-ghost btn-sm">Cancel</button>
                    </div>
                </div>
            )}
            {!editing && resource.extracted_text && (
                <div className="step-card-body">
                    <button
                        className="btn btn-ghost btn-sm p-1 flex items-center gap-1.5"
                        onClick={() => setExpanded(!expanded)}
                    >
                        <svg className={`w-4 h-4 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                        <span className="text-xs text-muted-foreground">Preview</span>
                    </button>
                    {expanded && (
                        <div className="content-preview text-xs mt-2" style={{ maxHeight: '24rem', overflowY: 'auto' }}>
                            {resource.extracted_text}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function StepCard({ step, slug, isOwner, onRefresh }: {
    step: Step; slug: string; isOwner: boolean; onRefresh: () => void;
}) {
    const { addToast } = useToast();
    const [expanded, setExpanded] = useState(false);
    const [editing, setEditing] = useState(false);
    const [editPrompt, setEditPrompt] = useState(step.prompt_template);
    const [editDisplayName, setEditDisplayName] = useState(step.display_name || '');
    const [saving, setSaving] = useState(false);

    const handleDelete = async () => {
        if (!confirm('Delete this step?')) return;
        try {
            await deleteStep(slug, step.number);
            addToast('success', 'Step deleted.');
            onRefresh();
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Delete failed.');
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await updateStep(slug, step.number, editPrompt, editDisplayName);
            addToast('success', 'Step updated.');
            setEditing(false);
            onRefresh();
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Update failed.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="step-card">
            <div className="step-card-header flex items-center justify-between">
                <span>
                    Step {step.number}
                    {step.display_name && <span> — {step.display_name}</span>}
                    <span className="text-xs text-muted-foreground ml-2">({step.output_id})</span>
                </span>
                <span className="flex items-center gap-2">
                    {isOwner && (
                        <>
                            <button onClick={() => { setEditing(!editing); setEditPrompt(step.prompt_template); setEditDisplayName(step.display_name || ''); }} className="btn btn-ghost btn-sm" title="Edit">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                </svg>
                            </button>
                            <button onClick={handleDelete} className="btn btn-ghost btn-sm text-destructive" title="Delete">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" /><path d="M10 11v6" /><path d="M14 11v6" />
                                </svg>
                            </button>
                        </>
                    )}
                </span>
            </div>
            {editing ? (
                <div className="step-card-body space-y-3 border-t border-border pt-3">
                    <div>
                        <label className="label text-xs">Display Name</label>
                        <input type="text" className="input" value={editDisplayName} onChange={(e) => setEditDisplayName(e.target.value)} placeholder="Step name" />
                    </div>
                    <div>
                        <label className="label text-xs">Prompt Template</label>
                        <textarea className="input" rows={8} value={editPrompt} onChange={(e) => setEditPrompt(e.target.value)} />
                    </div>
                    <div className="flex gap-2 pt-1">
                        <button onClick={handleSave} className="btn btn-primary btn-sm" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                        <button onClick={() => setEditing(false)} className="btn btn-ghost btn-sm">Cancel</button>
                    </div>
                </div>
            ) : (
                <div className="step-card-body">
                    <button
                        className="btn btn-ghost btn-sm p-1 flex items-center gap-1.5"
                        onClick={() => setExpanded(!expanded)}
                    >
                        <svg className={`w-4 h-4 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                        </svg>
                        <span className="text-xs text-muted-foreground">Prompt</span>
                    </button>
                    {expanded && (
                        <div className="content-preview text-xs mt-2" style={{ maxHeight: '24rem', overflowY: 'auto' }}>
                            {step.prompt_template}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function AddResourceForm({ slug, onRefresh }: { slug: string; onRefresh: () => void }) {
    const [mode, setMode] = useState<'file' | 'text' | 'dynamic'>('file');
    const [displayName, setDisplayName] = useState('');
    const [textContent, setTextContent] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const { addToast } = useToast();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const fd = new FormData();
            if (displayName) fd.append('display_name', displayName);
            if (mode === 'dynamic') {
                fd.append('is_dynamic', 'on');
                fd.append('text_content', textContent || `{${displayName || 'input'}}`);
            } else if (mode === 'file' && file) {
                fd.append('file', file);
            } else if (mode === 'text') {
                fd.append('text_content', textContent);
            }
            await addResource(slug, fd);
            addToast('success', 'Resource added.');
            setDisplayName(''); setTextContent(''); setFile(null);
            onRefresh();
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Add failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="card p-5 space-y-4">
            <h3 className="font-semibold text-foreground">Add Resource</h3>

            {/* Tab toggle */}
            <div className="flex gap-2">
                <button type="button" onClick={() => setMode('file')} className={`btn btn-sm ${mode === 'file' ? 'btn-primary' : 'btn-ghost'}`}>File Upload</button>
                <button type="button" onClick={() => setMode('text')} className={`btn btn-sm ${mode === 'text' ? 'btn-primary' : 'btn-ghost'}`}>Text Input</button>
                <button type="button" onClick={() => setMode('dynamic')} className={`btn btn-sm ${mode === 'dynamic' ? 'btn-primary' : 'btn-ghost'}`}>Dynamic Resource</button>
            </div>

            <div>
                <label className="label">Display Name <span className="text-muted-foreground font-normal">(optional)</span></label>
                <input type="text" className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="Readable name" />
            </div>

            {mode === 'file' && (
                <div>
                    <label className="label">File</label>
                    <input type="file" className="input" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                </div>
            )}

            {mode === 'text' && (
                <div>
                    <label className="label">Content</label>
                    <textarea className="input" rows={5} value={textContent} onChange={(e) => setTextContent(e.target.value)} placeholder="Paste text content..." />
                </div>
            )}

            {mode === 'dynamic' && (
                <div className="text-sm text-muted-foreground space-y-2">
                    <p>Dynamic resources let users provide custom input when running the kit. The value will be replaced at execution time.</p>
                    <div>
                        <label className="label">Default Content <span className="text-muted-foreground font-normal">(optional)</span></label>
                        <textarea className="input" rows={3} value={textContent} onChange={(e) => setTextContent(e.target.value)} placeholder="Default or placeholder text..." />
                    </div>
                </div>
            )}

            <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Adding...' : 'Add Resource'}
            </button>
        </form>
    );
}

function AddStepForm({ slug, onRefresh }: { slug: string; onRefresh: () => void }) {
    const [prompt, setPrompt] = useState('');
    const [displayName, setDisplayName] = useState('');
    const [loading, setLoading] = useState(false);
    const { addToast } = useToast();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await addStep(slug, prompt, displayName);
            addToast('success', 'Step added.');
            setPrompt(''); setDisplayName('');
            onRefresh();
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Add failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="card p-5 space-y-4">
            <h3 className="font-semibold text-foreground">Add Workflow Step</h3>
            <div>
                <label className="label">Display Name <span className="text-muted-foreground font-normal">(optional)</span></label>
                <input type="text" className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="Step name" />
            </div>
            <div>
                <label className="label">Prompt Template</label>
                <textarea className="input" rows={6} value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Enter your LLM prompt..." required />
                <p className="text-xs text-muted-foreground mt-1.5">
                    Use <code className="bg-muted px-1.5 py-0.5 rounded-md text-xs">{'{'}<span>resource_N</span>{'}'}</code> and <code className="bg-muted px-1.5 py-0.5 rounded-md text-xs">{'{'}<span>workflow_N</span>{'}'}</code> for placeholders.
                </p>
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Adding...' : 'Add Step'}
            </button>
        </form>
    );
}

export default function KitDetailPage() {
    const { slug } = useParams<{ slug: string }>();
    const [kit, setKit] = useState<KitDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { user } = useAuth();
    const { addToast } = useToast();
    const navigate = useNavigate();

    const fetchKit = async () => {
        if (!slug) return;
        try {
            const data = await getKit(slug);
            // Backend may return { error: "..." } with 200 status
            if ('error' in data && !data.kit) {
                setError((data as unknown as { error: string }).error);
            } else {
                setKit(data);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load kit.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchKit(); }, [slug]);

    const handleDelete = async () => {
        if (!slug || !confirm('Are you sure you want to delete this kit? This action cannot be undone.')) return;
        try {
            await deleteKit(slug);
            addToast('success', 'Kit deleted.');
            navigate('/');
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Delete failed.');
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

    if (error || !kit) {
        return (
            <div className="fade-in">
                <div className="flash flash-error">{error || 'Kit not found.'}</div>
                <Link to="/" className="btn btn-ghost mt-4">Back to Kits</Link>
            </div>
        );
    }

    return (
        <div className="fade-in">
            {/* Breadcrumb */}
            <nav className="text-sm text-muted-foreground mb-6">
                <Link to="/" className="hover:text-foreground transition-colors">Kits</Link>
                <span className="mx-2">/</span>
                <span className="text-foreground">{kit.kit.name}</span>
            </nav>

            {/* Header */}
            <div className="flex items-start justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight mb-2">{kit.kit.name}</h1>
                    {kit.kit.description && (
                        <p className="text-muted-foreground max-w-xl">{kit.kit.description}</p>
                    )}
                    <div className="flex items-center gap-2 mt-3">
                        {kit.kit.version_number && <span className="badge badge-primary">v{kit.kit.version_number}</span>}
                        <span className="badge">{kit.source}</span>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <Link to={`/kit/${slug}/run`} className="btn btn-primary">Run Kit</Link>
                    {user && <Link to={`/kit/${slug}/history`} className="btn btn-secondary">History</Link>}
                    {kit.is_owner && (
                        <>
                            <Link to={`/kit/${slug}/edit`} className="btn btn-ghost">Edit</Link>
                            <button onClick={handleDelete} className="btn btn-ghost text-destructive">Delete</button>
                        </>
                    )}
                </div>
            </div>

            <hr className="divider" />

            {/* Resources */}
            <section className="mb-10">
                <h2 className="text-xl font-semibold mb-4 tracking-tight">
                    Resources ({kit.resources.length})
                </h2>
                {kit.resources.length === 0 ? (
                    <div className="empty-state py-8">
                        <p className="text-sm">No resources yet.</p>
                    </div>
                ) : (
                    <div className="stream-container">
                        {kit.resources.map((r) => (
                            <ResourceCard key={r.number} resource={r} slug={slug!} isOwner={kit.is_owner} onRefresh={fetchKit} />
                        ))}
                    </div>
                )}
                {kit.is_owner && (
                    <div className="mt-6">
                        <AddResourceForm slug={slug!} onRefresh={fetchKit} />
                    </div>
                )}
            </section>

            <hr className="divider" />

            {/* Workflow Steps */}
            <section>
                <h2 className="text-xl font-semibold mb-4 tracking-tight">
                    Workflow Steps ({kit.steps.length})
                </h2>
                {kit.steps.length === 0 ? (
                    <div className="empty-state py-8">
                        <p className="text-sm">No steps yet.</p>
                    </div>
                ) : (
                    <div className="stream-container">
                        {kit.steps.map((s) => (
                            <StepCard key={s.number} step={s} slug={slug!} isOwner={kit.is_owner} onRefresh={fetchKit} />
                        ))}
                    </div>
                )}
                {kit.is_owner && (
                    <div className="mt-6">
                        <AddStepForm slug={slug!} onRefresh={fetchKit} />
                    </div>
                )}
            </section>
        </div>
    );
}
