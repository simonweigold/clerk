import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getExecution, getDownloadUrl, updateExecutionLabel } from '../lib/api';
import { useToast } from '../hooks/useToast';

interface StepData {
    step_number: number;
    display_name?: string;
    output_id: string;
    input_text?: string;
    output_text?: string;
    output_char_count?: number;
    evaluation_score?: number;
    model_used?: string;
    tokens_used?: number;
    latency_ms?: number;
}

interface ExecData {
    id: string;
    kit_name?: string;
    status: string;
    label?: string;
    storage_mode: string;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
    steps: StepData[];
}

function fmt(d: Date) {
    const m = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${m[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()} at ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}

function StatusBadge({ status }: { status: string }) {
    if (status === 'completed') return <span className="badge" style={{ background: '#f0fdf4', color: '#166534', borderColor: '#bbf7d0' }}>Completed</span>;
    if (status === 'failed') return <span className="badge" style={{ background: '#fef2f2', color: '#991b1b', borderColor: '#fecaca' }}>Failed</span>;
    return <span className="badge" style={{ background: '#eff6ff', color: '#1e40af', borderColor: '#bfdbfe' }}>Running</span>;
}

export default function ExecutionDetailPage() {
    const { slug, runId } = useParams<{ slug: string; runId: string }>();
    const [data, setData] = useState<ExecData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [editLabel, setEditLabel] = useState(false);
    const [labelVal, setLabelVal] = useState('');
    const { addToast } = useToast();

    useEffect(() => {
        if (!slug || !runId) return;
        getExecution(slug, runId)
            .then((d) => {
                if ((d as Record<string, unknown>).error) { setError((d as Record<string, unknown>).error as string); return; }
                setData(d as unknown as ExecData);
                setLabelVal((d as unknown as ExecData).label || '');
            })
            .catch((err) => setError(err instanceof Error ? err.message : 'Failed.'))
            .finally(() => setLoading(false));
    }, [slug, runId]);

    const saveLabel = async () => {
        if (!slug || !runId) return;
        try {
            const res = await updateExecutionLabel(slug, runId, labelVal);
            if (res.ok && data) setData({ ...data, label: labelVal || undefined });
            setEditLabel(false);
        } catch { addToast('error', 'Failed to save label.'); }
    };

    if (loading) return <div className="empty-state fade-in"><div className="flex items-center justify-center gap-2"><span className="pulse-dot" /><span className="pulse-dot" /><span className="pulse-dot" /></div></div>;
    if (error || !data) return <div className="fade-in"><div className="flash flash-error">{error || 'Not found.'}</div><Link to={`/kit/${slug}/history`} className="btn btn-ghost mt-4">Back</Link></div>;

    const sd = data.started_at ? new Date(data.started_at) : null;
    const totalTokens = data.steps.reduce((s, st) => s + (st.tokens_used || 0), 0);
    let duration = '';
    if (data.started_at && data.completed_at) {
        const dur = Math.round((new Date(data.completed_at).getTime() - new Date(data.started_at).getTime()) / 1000);
        duration = dur < 60 ? `${dur}s` : `${Math.floor(dur / 60)}m ${dur % 60}s`;
    }

    return (
        <div className="fade-in">
            <nav className="text-sm text-muted-foreground mb-6">
                <Link to="/" className="hover:text-foreground transition-colors">Kits</Link>
                <span className="mx-2">/</span>
                <Link to={`/kit/${slug}`} className="hover:text-foreground transition-colors">{data.kit_name || slug}</Link>
                <span className="mx-2">/</span>
                <Link to={`/kit/${slug}/history`} className="hover:text-foreground transition-colors">History</Link>
                <span className="mx-2">/</span>
                <span className="text-foreground">Detail</span>
            </nav>

            <div className="flex items-start justify-between mb-6">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold tracking-tight">{data.label || data.kit_name || slug}</h1>
                        <StatusBadge status={data.status} />
                    </div>
                    <p className="text-muted-foreground mt-1">{sd ? fmt(sd) : 'Unknown date'}</p>
                </div>
                <div className="flex items-center gap-3">
                    {data.status === 'paused' && (
                        <Link to={`/kit/${slug}/run?resume=${runId}`} className="btn btn-primary btn-sm flex items-center gap-1.5 shadow-sm">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            Resume Execution
                        </Link>
                    )}
                    <a href={getDownloadUrl(slug!, runId!, 'md')} className="btn btn-secondary btn-sm">↓ MD</a>
                    <a href={getDownloadUrl(slug!, runId!, 'json')} className="btn btn-secondary btn-sm">↓ JSON</a>
                    <Link to={`/kit/${slug}/history`} className="btn btn-secondary">Back to History</Link>
                </div>
            </div>

            {/* Label editor */}
            <div className="mb-6">
                {editLabel ? (
                    <div className="flex items-center gap-2">
                        <input className="input" style={{ maxWidth: '320px', fontSize: '0.875rem' }} value={labelVal} onChange={e => setLabelVal(e.target.value)} placeholder="Add a label..." maxLength={255} />
                        <button className="btn btn-primary btn-sm" onClick={saveLabel}>Save</button>
                        <button className="btn btn-ghost btn-sm" onClick={() => setEditLabel(false)}>Cancel</button>
                    </div>
                ) : (
                    <button className="text-sm text-muted-foreground hover:text-foreground transition-colors" onClick={() => setEditLabel(true)}>
                        {data.label ? <>Label: <strong>{data.label}</strong> ✎</> : <em>No label — click to add one</em>}
                    </button>
                )}
            </div>

            {/* Metadata */}
            <div className="card mb-8 p-4">
                <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(140px,1fr))' }}>
                    <div><div className="text-xs text-muted-foreground mb-1">Status</div><div className="font-medium">{data.status.charAt(0).toUpperCase() + data.status.slice(1)}</div></div>
                    <div><div className="text-xs text-muted-foreground mb-1">Steps</div><div className="font-medium">{data.steps.length}</div></div>
                    <div><div className="text-xs text-muted-foreground mb-1">Storage</div><div className="font-medium">{data.storage_mode}</div></div>
                    {duration && <div><div className="text-xs text-muted-foreground mb-1">Duration</div><div className="font-medium">{duration}</div></div>}
                    {totalTokens > 0 && <div><div className="text-xs text-muted-foreground mb-1">Total Tokens</div><div className="font-medium">{totalTokens.toLocaleString()}</div></div>}
                    {data.steps.length > 0 && data.steps[0].model_used && <div><div className="text-xs text-muted-foreground mb-1">Model</div><div className="font-medium">{data.steps[0].model_used}</div></div>}
                </div>
                {data.error_message && <div className="mt-3 text-sm" style={{ color: '#991b1b' }}>{data.error_message}</div>}
            </div>

            {/* Steps */}
            <div className="stream-container">
                {data.steps.map((step, idx) => <StepCard key={step.step_number} step={step} idx={idx} />)}
            </div>
        </div>
    );
}

function StepCard({ step, idx }: { step: StepData; idx: number }) {
    const [expanded, setExpanded] = useState(false);
    const header = step.display_name
        ? `Step ${step.step_number} — ${step.display_name}`
        : `Step ${step.step_number} — ${step.output_id}`;
    const meta: string[] = [];
    if (step.latency_ms) meta.push(`${(step.latency_ms / 1000).toFixed(1)}s`);
    if (step.tokens_used) meta.push(`${step.tokens_used} tokens`);
    if (step.evaluation_score != null) meta.push(`Eval: ${step.evaluation_score}/100`);

    return (
        <div className="step-card fade-in" style={{ animationDelay: `${idx * 0.04}s` }}>
            <div className="step-card-header flex items-center justify-between">
                <span>{header} {step.display_name && <span className="text-xs text-muted-foreground">({step.output_id})</span>}</span>
                <span className="flex items-center gap-2">
                    <span className="badge badge-primary">Done</span>
                    {meta.length > 0 && <span className="text-xs text-muted-foreground">{meta.join(' · ')}</span>}
                </span>
            </div>
            <div className="step-card-body">
                {step.input_text && (
                    <div className="mb-3">
                        <button className="btn btn-ghost btn-sm p-1 flex items-center gap-1.5" onClick={() => setExpanded(!expanded)}>
                            <svg className={`w-4 h-4 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" /></svg>
                            <span className="text-xs text-muted-foreground">Prompt</span>
                        </button>
                        {expanded && <div className="content-preview text-xs mt-2" style={{ maxHeight: '24rem', overflowY: 'auto' }}>{step.input_text}</div>}
                    </div>
                )}
                {step.output_text ? (
                    <div className="content-preview" style={{ whiteSpace: 'pre-wrap' }}>{step.output_text}</div>
                ) : step.output_char_count != null ? (
                    <p className="text-sm text-muted-foreground"><em>Anonymous mode — {step.output_char_count} characters</em></p>
                ) : null}
            </div>
        </div>
    );
}
