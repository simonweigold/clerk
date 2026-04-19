import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { deleteKit, updateKit, addResource, deleteResource, updateResource, addStep, deleteStep, updateStep, addTool, updateTool, deleteTool, formatToolName, type Resource, type Step, type Tool, type AvailableTool } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { useKitDetail, kitKeys } from '../hooks/useKits';
import { PromptTextarea } from '../components/PromptTextarea';

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
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const confirmDelete = async () => {
        setIsDeleting(true);
        try {
            await deleteResource(slug, resource.number);
            addToast('success', 'Resource deleted.');
            onRefresh();
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Delete failed.');
        } finally {
            setIsDeleting(false);
            setShowDeleteModal(false);
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
                            <button onClick={() => setShowDeleteModal(true)} className="btn btn-ghost btn-sm text-destructive" title="Delete">
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
                        <label className="label text-xs">Display Name <span className="text-muted-foreground font-normal">(optional)</span></label>
                        <input type="text" className="input text-sm" value={editDisplayName} onChange={(e) => setEditDisplayName(e.target.value)} placeholder="Resource name" />
                    </div>

                    {editMode === 'file' && (
                        <div>
                            <label className="label text-xs">File</label>
                            <input type="file" className="input text-sm py-2" onChange={(e) => setEditFile(e.target.files?.[0] || null)} />
                        </div>
                    )}

                    {(editMode === 'text' || editMode === 'dynamic') && (
                        <div>
                            <label className="label text-xs">{editMode === 'dynamic' ? 'Dynamic Value (JS Expression)' : 'Text Content'}</label>
                            <textarea className="input text-sm font-mono" rows={4} value={editText} onChange={(e) => setEditText(e.target.value)} />
                        </div>
                    )}

                    <div className="flex gap-2 pt-2">
                        <button onClick={handleSave} className="btn btn-primary btn-sm" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                        <button onClick={() => setEditing(false)} className="btn btn-ghost btn-sm">Cancel</button>
                    </div>
                </div>
            )}
            {!editing && resource.extracted_text && (
                <div className="step-card-body">
                    <pre className={`content-preview text-sm mt-0 ${expanded ? '' : 'line-clamp-3'}`}>
                        {resource.extracted_text}
                    </pre>
                    {resource.extracted_text.length > 200 && (
                        <button onClick={() => setExpanded(!expanded)} className="text-xs text-primary mt-2 hover:underline">
                            {expanded ? 'Show less' : 'Show more'}
                        </button>
                    )}
                </div>
            )}
            {showDeleteModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm fade-in">
                    <div className="card p-6 max-w-md w-full shadow-lg">
                        <h2 className="text-xl font-bold mb-2">Delete Resource</h2>
                        <p className="text-muted-foreground mb-6">
                            Are you sure you want to delete <strong>{resource.display_name || resource.filename}</strong>?
                        </p>
                        <div className="flex justify-end gap-3">
                            <button className="btn btn-ghost" onClick={() => setShowDeleteModal(false)} disabled={isDeleting}>Cancel</button>
                            <button className="btn btn-destructive" onClick={confirmDelete} disabled={isDeleting}>{isDeleting ? 'Deleting...' : 'Delete'}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function StepCard({ step, slug, isOwner, onRefresh, resources, steps, tools }: {
    step: Step; slug: string; isOwner: boolean; onRefresh: () => void;
    resources: Resource[]; steps: Step[]; tools: Tool[];
}) {
    const { addToast } = useToast();
    const [editing, setEditing] = useState(false);
    const [editPrompt, setEditPrompt] = useState(step.prompt_template);
    const [editDisplayName, setEditDisplayName] = useState(step.display_name || '');
    const [saving, setSaving] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const confirmDelete = async () => {
        setIsDeleting(true);
        try {
            await deleteStep(slug, step.number);
            addToast('success', 'Step deleted.');
            onRefresh();
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Delete failed.');
        } finally {
            setIsDeleting(false);
            setShowDeleteModal(false);
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
                <span className="flex items-center gap-2">
                    <span className="step-number">{step.number}</span>
                    <span className="font-medium">{step.display_name || `Step ${step.number}`}</span>
                </span>
                {isOwner && (
                    <span className="flex items-center gap-2">
                        <button onClick={() => { setEditing(!editing); setEditPrompt(step.prompt_template); setEditDisplayName(step.display_name || ''); }} className="btn btn-ghost btn-sm" title="Edit">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                            </svg>
                        </button>
                        <button onClick={() => setShowDeleteModal(true)} className="btn btn-ghost btn-sm text-destructive" title="Delete">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" /><path d="M10 11v6" /><path d="M14 11v6" />
                            </svg>
                        </button>
                    </span>
                )}
            </div>
            {editing ? (
                <div className="step-card-body space-y-4 border-t border-border pt-3">
                    <div>
                        <label className="label text-xs">Display Name <span className="text-muted-foreground font-normal">(optional)</span></label>
                        <input type="text" className="input text-sm" value={editDisplayName} onChange={(e) => setEditDisplayName(e.target.value)} placeholder="Step name" />
                    </div>
                    <div>
                        <label className="label text-xs">Prompt Template</label>
                        <PromptTextarea className="input text-sm font-mono" rows={6} value={editPrompt} onChange={(e) => setEditPrompt(e.target.value)} resources={resources} steps={steps} tools={tools} />
                    </div>
                    <div className="flex gap-2 pt-1">
                        <button onClick={handleSave} className="btn btn-primary btn-sm" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                        <button onClick={() => setEditing(false)} className="btn btn-ghost btn-sm">Cancel</button>
                    </div>
                </div>
            ) : (
                <div className="step-card-body">
                    <pre className="content-preview text-sm mt-0">{step.prompt_template}</pre>
                    <p className="text-xs text-muted-foreground mt-2">
                        Output ID: <code className="bg-muted px-1 py-0.5 rounded">{step.output_id}</code>
                    </p>
                </div>
            )}
            {showDeleteModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm fade-in">
                    <div className="card p-6 max-w-md w-full shadow-lg">
                        <h2 className="text-xl font-bold mb-2">Delete Step</h2>
                        <p className="text-muted-foreground mb-6">
                            Are you sure you want to delete step <strong>{step.display_name || step.number}</strong>?
                        </p>
                        <div className="flex justify-end gap-3">
                            <button className="btn btn-ghost" onClick={() => setShowDeleteModal(false)} disabled={isDeleting}>Cancel</button>
                            <button className="btn btn-destructive" onClick={confirmDelete} disabled={isDeleting}>{isDeleting ? 'Deleting...' : 'Delete'}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function ToolCard({ tool, slug, isOwner, onRefresh }: { tool: Tool; slug: string; isOwner: boolean; onRefresh: () => void; }) {
    const { addToast } = useToast();
    const [editing, setEditing] = useState(false);
    const [editDisplayName, setEditDisplayName] = useState(tool.display_name || '');
    const [editConfiguration, setEditConfiguration] = useState(tool.configuration || '');
    const [saving, setSaving] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const confirmDelete = async () => {
        setIsDeleting(true);
        try {
            const toolNumber = parseInt(tool.tool_id.replace('tool_', ''), 10);
            await deleteTool(slug, toolNumber);
            addToast('success', 'Tool removed.');
            onRefresh();
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Remove failed.');
        } finally {
            setIsDeleting(false);
            setShowDeleteModal(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const toolNumber = parseInt(tool.tool_id.replace('tool_', ''), 10);
            await updateTool(slug, toolNumber, editDisplayName, editConfiguration);
            addToast('success', 'Tool updated.');
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
                    <span className="font-medium text-purple-600 dark:text-purple-400">
                        {tool.display_name || formatToolName(tool.tool_name)}
                    </span>
                    <span className="text-xs text-muted-foreground">({tool.tool_id})</span>
                    {tool.display_name && (
                        <span className="text-xs text-muted-foreground ml-2 uppercase font-mono tracking-widest">{tool.tool_name}</span>
                    )}
                    {tool.source && tool.source !== 'builtin' && (
                        <span className="badge badge-outline text-[10px] ml-1">{tool.source}</span>
                    )}
                </span>
                <span className="flex items-center gap-2">
                    {isOwner && (
                        <>
                            <button onClick={() => { setEditing(!editing); setEditDisplayName(tool.display_name || ''); setEditConfiguration(tool.configuration || ''); }} className="btn btn-ghost btn-sm" title="Edit">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                </svg>
                            </button>
                            <button onClick={() => setShowDeleteModal(true)} className="btn btn-ghost btn-sm text-destructive" title="Remove">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        </>
                    )}
                </span>
            </div>
            {editing && (
                <div className="step-card-body space-y-4 border-t border-border pt-3">
                    <div>
                        <label className="label text-xs">Display Name <span className="text-muted-foreground font-normal">(optional)</span></label>
                        <input type="text" className="input text-sm" value={editDisplayName} onChange={(e) => setEditDisplayName(e.target.value)} placeholder="Readable name" />
                    </div>
                    <div>
                        <label className="label text-xs">Configuration JSON <span className="text-muted-foreground font-normal">(optional)</span></label>
                        <textarea className="input text-sm font-mono" rows={3} value={editConfiguration} onChange={(e) => setEditConfiguration(e.target.value)} placeholder='{"key": "value"}' />
                    </div>
                    <div className="flex gap-2 pt-1">
                        <button onClick={handleSave} className="btn btn-primary btn-sm" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                        <button onClick={() => setEditing(false)} className="btn btn-ghost btn-sm">Cancel</button>
                    </div>
                </div>
            )}
            {!editing && tool.configuration && (
                <div className="step-card-body">
                    <div className="text-xs text-muted-foreground mt-1 mb-1 font-semibold uppercase tracking-wider">Configuration</div>
                    <pre className="content-preview text-xs mt-0 overflow-x-auto font-mono bg-muted/50 p-2 rounded border border-border">
                        {tool.configuration}
                    </pre>
                </div>
            )}
            {showDeleteModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm fade-in">
                    <div className="card p-6 max-w-md w-full shadow-lg">
                        <h2 className="text-xl font-bold mb-2">Remove Tool</h2>
                        <p className="text-muted-foreground mb-6">
                            Are you sure you want to remove <strong>{tool.display_name || formatToolName(tool.tool_name)}</strong> from this kit?
                        </p>
                        <div className="flex justify-end gap-3">
                            <button
                                className="btn btn-ghost"
                                onClick={() => setShowDeleteModal(false)}
                                disabled={isDeleting}
                            >
                                Cancel
                            </button>
                            <button
                                className="btn btn-destructive"
                                onClick={confirmDelete}
                                disabled={isDeleting}
                            >
                                {isDeleting ? 'Removing...' : 'Remove'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── LAZY LOADED TOOL FORM ────────────────────────────────────────────────────

function AddToolForm({ slug, onRefresh }: { slug: string; onRefresh: () => void }) {
    const { addToast } = useToast();
    const [isExpanded, setIsExpanded] = useState(false);
    const [availableTools, setAvailableTools] = useState<AvailableTool[]>([]);
    const [selectedTool, setSelectedTool] = useState<string>('');
    const [displayName, setDisplayName] = useState('');
    const [configuration, setConfiguration] = useState('');
    const [loading, setLoading] = useState(false);
    const [fetchingTools, setFetchingTools] = useState(false);
    const [hasLoadedTools, setHasLoadedTools] = useState(false);

    // Lazy load tools only when form is expanded
    const handleExpand = async () => {
        setIsExpanded(true);
        if (!hasLoadedTools && !fetchingTools) {
            setFetchingTools(true);
            try {
                const { getAvailableTools } = await import('../lib/api');
                const data = await getAvailableTools();
                setAvailableTools(data.tools);
                if (data.tools.length > 0) setSelectedTool(data.tools[0].name);
                setHasLoadedTools(true);
            } catch (err) {
                addToast('error', err instanceof Error ? err.message : 'Failed to fetch available tools.');
            } finally {
                setFetchingTools(false);
            }
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedTool) return;
        setLoading(true);
        try {
            await addTool(slug, selectedTool, displayName, configuration);
            addToast('success', 'Tool added to kit.');
            setDisplayName('');
            setConfiguration('');
            onRefresh();
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Add tool failed.');
        } finally {
            setLoading(false);
        }
    };

    if (!isExpanded) {
        return (
            <button 
                onClick={handleExpand}
                className="card p-5 flex items-center gap-2 text-muted-foreground hover:text-foreground hover:border-purple-500/30 transition-colors border-dashed border-2"
            >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <span>Attach Tool</span>
            </button>
        );
    }

    if (fetchingTools) return <div className="card p-5 animate-pulse"><div className="h-4 bg-muted rounded w-1/4 mb-4"></div><div className="h-10 bg-muted rounded"></div></div>;

    if (availableTools.length === 0) return null;

    const selectedToolDef = availableTools.find(t => t.name === selectedTool);

    return (
        <form onSubmit={handleSubmit} className="card p-5 space-y-4 border-purple-500/20 shadow-sm shadow-purple-500/10">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    <h3 className="font-semibold text-foreground">Attach Tool</h3>
                </div>
                <button 
                    type="button" 
                    onClick={() => setIsExpanded(false)}
                    className="btn btn-ghost btn-sm"
                >
                    Cancel
                </button>
            </div>

            <div>
                <label className="label">Select Tool</label>
                <select className="input" value={selectedTool} onChange={e => setSelectedTool(e.target.value)} required>
                    {Object.entries(
                        availableTools.reduce((acc, t) => {
                            const source = t.source || 'builtin';
                            if (!acc[source]) acc[source] = [];
                            acc[source].push(t);
                            return acc;
                        }, {} as Record<string, AvailableTool[]>)
                    ).map(([source, tools]) => (
                        <optgroup key={source} label={source === 'builtin' ? 'Built-in Tools' : `MCP: ${source}`}>
                            {tools.map(t => (
                                <option key={t.name} value={t.name}>{formatToolName(t.name)}</option>
                            ))}
                        </optgroup>
                    ))}
                </select>
                {selectedToolDef && (
                    <p className="text-xs text-muted-foreground mt-1.5">{selectedToolDef.description}</p>
                )}
            </div>

            <div>
                <label className="label">Display Name <span className="text-muted-foreground font-normal">(optional)</span></label>
                <input type="text" className="input text-sm" value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="Readable name" />
            </div>

            <div>
                <label className="label flex justify-between">
                    <span>Configuration <span className="text-muted-foreground font-normal">(optional JSON)</span></span>
                </label>
                <textarea className="input text-sm font-mono" rows={2} value={configuration} onChange={(e) => setConfiguration(e.target.value)} placeholder='{"key": "value"}' />
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading || !selectedTool}>
                {loading ? 'Attaching...' : 'Attach Tool'}
            </button>
        </form>
    );
}

// ─── END TOOL COMPONENTS ──────────────────────────────────────────────────────

function AddStepForm({ slug, onRefresh, resources, steps, tools }: { slug: string; onRefresh: () => void; resources: Resource[]; steps: Step[]; tools: Tool[] }) {
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
                <PromptTextarea className="input" rows={6} value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Enter your LLM prompt..." required resources={resources} steps={steps} tools={tools} />
                <p className="text-xs text-muted-foreground mt-1.5">
                    Use <code className="bg-muted px-1.5 py-0.5 rounded-md text-xs">{'{'}<span>resource_N</span>{'}'}</code>, <code className="bg-muted px-1.5 py-0.5 rounded-md text-xs">{'{'}<span>workflow_N</span>{'}'}</code>, and <code className="bg-muted px-1.5 py-0.5 rounded-md text-xs">{'{'}<span>tool_N</span>{'}'}</code> for placeholders.
                </p>
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Adding...' : 'Add Step'}
            </button>
        </form>
    );
}

function AddResourceForm({ slug, onRefresh }: { slug: string; onRefresh: () => void }) {
    const [mode, setMode] = useState<'file' | 'text' | 'dynamic'>('file');
    const [file, setFile] = useState<File | null>(null);
    const [text, setText] = useState('');
    const [displayName, setDisplayName] = useState('');
    const [loading, setLoading] = useState(false);
    const { addToast } = useToast();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const fd = new FormData();
            fd.append('display_name', displayName);
            if (mode === 'dynamic') {
                fd.append('is_dynamic', 'on');
                if (text.trim()) fd.append('text_content', text);
            } else if (mode === 'file' && file) {
                fd.append('file', file);
            } else if (mode === 'text' && text.trim()) {
                fd.append('text_content', text);
            }
            await addResource(slug, fd);
            addToast('success', 'Resource added.');
            setFile(null);
            setText('');
            setDisplayName('');
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
            <div className="flex gap-2">
                <button type="button" onClick={() => { setMode('file'); setText(''); setFile(null); }} className={`btn btn-sm ${mode === 'file' ? 'btn-primary' : 'btn-ghost'}`}>File Upload</button>
                <button type="button" onClick={() => { setMode('text'); setText(''); setFile(null); }} className={`btn btn-sm ${mode === 'text' ? 'btn-primary' : 'btn-ghost'}`}>Text Input</button>
                <button type="button" onClick={() => { setMode('dynamic'); setText(''); setFile(null); }} className={`btn btn-sm ${mode === 'dynamic' ? 'btn-primary' : 'btn-ghost'}`}>Dynamic Resource</button>
            </div>

            <div>
                <label className="label">Display Name <span className="text-muted-foreground font-normal">(optional)</span></label>
                <input type="text" className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="Resource name" />
            </div>

            {mode === 'file' && (
                <div>
                    <label className="label">File</label>
                    <input type="file" className="input py-2" onChange={(e) => setFile(e.target.files?.[0] || null)} required={mode === 'file'} />
                </div>
            )}

            {(mode === 'text' || mode === 'dynamic') && (
                <div>
                    <label className="label">{mode === 'dynamic' ? 'Dynamic Value (JS Expression)' : 'Text Content'}</label>
                    <textarea className="input font-mono" rows={6} value={text} onChange={(e) => setText(e.target.value)} required />
                </div>
            )}

            <button type="submit" className="btn btn-primary" disabled={loading || (mode === 'file' && !file) || ((mode === 'text' || mode === 'dynamic') && !text.trim())}>
                {loading ? 'Adding...' : 'Add Resource'}
            </button>
        </form>
    );
}

export default function KitDetailPage() {
    const { slug } = useParams<{ slug: string }>();
    const { user } = useAuth();
    const { addToast } = useToast();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    // Use React Query for kit data with caching
    const { data: kit, isLoading, error } = useKitDetail(slug || '');

    const [editingKit, setEditingKit] = useState<'name' | 'description' | null>(null);
    const [editName, setEditName] = useState('');
    const [editDescription, setEditDescription] = useState('');
    const [savingKit, setSavingKit] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const handleSaveKitDetails = async () => {
        if (!slug || !kit) return;
        setSavingKit(true);
        try {
            await updateKit(slug, editName, editDescription);
            addToast('success', 'Kit details updated.');
            setEditingKit(null);
            // Invalidate and refetch
            queryClient.invalidateQueries({ queryKey: kitKeys.detail(slug) });
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Update failed.');
        } finally {
            setSavingKit(false);
        }
    };

    const handleRefresh = () => {
        if (slug) {
            queryClient.invalidateQueries({ queryKey: kitKeys.detail(slug) });
        }
    };

    const confirmDelete = async () => {
        if (!slug) return;
        setIsDeleting(true);
        try {
            await deleteKit(slug);
            addToast('success', 'Kit deleted.');
            navigate('/');
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Delete failed.');
            setIsDeleting(false);
            setShowDeleteModal(false);
        }
    };

    if (isLoading) {
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
                <div className="flash flash-error">{error instanceof Error ? error.message : 'Kit not found.'}</div>
                <Link to="/" className="btn btn-ghost mt-4">Back to Kits</Link>
            </div>
        );
    }

    // Handle error case from API
    if ('error' in kit && !kit.kit) {
        return (
            <div className="fade-in">
                <div className="flash flash-error">{(kit as unknown as { error: string }).error}</div>
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
                    <div className="flex items-center gap-2 mb-2 group min-h-[40px]">
                        {editingKit === 'name' ? (
                            <div className="flex items-center gap-2">
                                <input type="text" className="input text-3xl font-bold tracking-tight py-1 h-auto" value={editName} onChange={(e) => setEditName(e.target.value)} autoFocus />
                                <button onClick={handleSaveKitDetails} className="btn btn-primary btn-sm" disabled={savingKit}>Save</button>
                                <button onClick={() => setEditingKit(null)} className="btn btn-ghost btn-sm">Cancel</button>
                            </div>
                        ) : (
                            <>
                                <h1 className="text-3xl font-bold tracking-tight">{kit.kit.name}</h1>
                                {kit.is_owner && (
                                    <button onClick={() => { setEditingKit('name'); setEditName(kit.kit.name); setEditDescription(kit.kit.description || ''); }} className="btn btn-ghost btn-sm opacity-0 group-hover:opacity-100 transition-opacity p-1" title="Edit Title">
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                        </svg>
                                    </button>
                                )}
                            </>
                        )}
                    </div>

                    <div className="group flex items-start gap-2 mb-3 min-h-[24px]">
                        {editingKit === 'description' ? (
                            <div className="flex-1 space-y-2">
                                <textarea className="input" rows={3} value={editDescription} onChange={(e) => setEditDescription(e.target.value)} autoFocus />
                                <div className="flex gap-2">
                                    <button onClick={handleSaveKitDetails} className="btn btn-primary btn-sm" disabled={savingKit}>Save</button>
                                    <button onClick={() => setEditingKit(null)} className="btn btn-ghost btn-sm">Cancel</button>
                                </div>
                            </div>
                        ) : (
                            <>
                                {(kit.kit.description || kit.is_owner) && (
                                    <p className={`text-muted-foreground max-w-xl ${!kit.kit.description ? 'italic opacity-50' : ''}`}>
                                        {kit.kit.description || 'No description provided.'}
                                    </p>
                                )}
                                {kit.is_owner && (
                                    <button onClick={() => { setEditingKit('description'); setEditName(kit.kit.name); setEditDescription(kit.kit.description || ''); }} className="btn btn-ghost btn-sm opacity-0 group-hover:opacity-100 transition-opacity p-1 mt-0.5" title="Edit Description">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                        </svg>
                                    </button>
                                )}
                            </>
                        )}
                    </div>

                    <div className="flex items-center gap-2 mt-3">
                        {kit.kit.version_number && <span className="badge badge-primary">v{kit.kit.version_number}</span>}
                        <span className="badge">{kit.source}</span>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <Link to={`/kit/${slug}/run`} className="btn btn-primary">Run Kit</Link>
                    {user && <Link to={`/kit/${slug}/history`} className="btn btn-secondary">History</Link>}
                    {kit.is_owner && (
                        <button onClick={() => setShowDeleteModal(true)} className="btn btn-ghost text-destructive">Delete</button>
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
                            <ResourceCard key={r.number} resource={r} slug={slug!} isOwner={kit.is_owner} onRefresh={handleRefresh} />
                        ))}
                    </div>
                )}
                {kit.is_owner && (
                    <div className="mt-6">
                        <AddResourceForm slug={slug!} onRefresh={handleRefresh} />
                    </div>
                )}
            </section>

            <hr className="divider" />

            {/* Tools */}
            <section className="mb-10">
                <h2 className="text-xl font-semibold mb-4 tracking-tight">
                    Tools ({kit.tools?.length || 0})
                </h2>
                {(!kit.tools || kit.tools.length === 0) ? (
                    <div className="empty-state py-8">
                        <p className="text-sm">No tools attached to this kit.</p>
                    </div>
                ) : (
                    <div className="stream-container grid grid-cols-1 md:grid-cols-2 gap-4">
                        {kit.tools.map((t) => (
                            <ToolCard key={t.tool_id} tool={t} slug={slug!} isOwner={kit.is_owner} onRefresh={handleRefresh} />
                        ))}
                    </div>
                )}
                {kit.is_owner && (
                    <div className="mt-6">
                        <AddToolForm slug={slug!} onRefresh={handleRefresh} />
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
                            <StepCard key={s.number} step={s} slug={slug!} isOwner={kit.is_owner} onRefresh={handleRefresh} resources={kit.resources} steps={kit.steps} tools={kit.tools || []} />
                        ))}
                    </div>
                )}
                {kit.is_owner && (
                    <div className="mt-6">
                        <AddStepForm slug={slug!} onRefresh={handleRefresh} resources={kit.resources} steps={kit.steps} tools={kit.tools || []} />
                    </div>
                )}
            </section>

            {showDeleteModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm fade-in">
                    <div className="card p-6 max-w-md w-full shadow-lg">
                        <h2 className="text-xl font-bold mb-2">Delete Kit</h2>
                        <p className="text-muted-foreground mb-6">
                            Are you sure you want to delete the kit <strong>{kit.kit.name}</strong>? This action cannot be undone.
                        </p>
                        <div className="flex justify-end gap-3">
                            <button className="btn btn-ghost" onClick={() => setShowDeleteModal(false)} disabled={isDeleting}>Cancel</button>
                            <button className="btn btn-destructive" onClick={confirmDelete} disabled={isDeleting}>{isDeleting ? 'Deleting...' : 'Delete'}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
