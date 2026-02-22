import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { listExecutions, type ExecutionRun } from '../lib/api';
import { useToast } from '../hooks/useToast';

function formatDate(d: Date) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`;
}

function formatTime(d: Date) {
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}

function StatusBadge({ status }: { status: string }) {
    if (status === 'completed') return <span className="badge" style={{ background: '#f0fdf4', color: '#166534', borderColor: '#bbf7d0' }}>Completed</span>;
    if (status === 'failed') return <span className="badge" style={{ background: '#fef2f2', color: '#991b1b', borderColor: '#fecaca' }}>Failed</span>;
    return <span className="badge" style={{ background: '#eff6ff', color: '#1e40af', borderColor: '#bfdbfe' }}>Running</span>;
}

export default function KitHistoryPage() {
    const { slug } = useParams<{ slug: string }>();
    const [runs, setRuns] = useState<ExecutionRun[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { addToast } = useToast();

    useEffect(() => {
        if (!slug) return;
        listExecutions(slug)
            .then((data) => {
                if ('error' in data && (data as Record<string, unknown>).error) setError((data as Record<string, unknown>).error as string);
                setRuns(data.runs || []);
            })
            .catch((err) => { setError(err instanceof Error ? err.message : 'Failed.'); addToast('error', 'Failed to load history.'); })
            .finally(() => setLoading(false));
    }, [slug]);

    return (
        <div className="fade-in">
            <nav className="text-sm text-muted-foreground mb-6">
                <Link to="/" className="hover:text-foreground transition-colors">Kits</Link>
                <span className="mx-2">/</span>
                <Link to={`/kit/${slug}`} className="hover:text-foreground transition-colors">{slug}</Link>
                <span className="mx-2">/</span>
                <span className="text-foreground">History</span>
            </nav>
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Execution History</h1>
                    <p className="text-muted-foreground mt-1">Past runs of <strong>{slug}</strong></p>
                </div>
                <div className="flex items-center gap-3">
                    <Link to={`/kit/${slug}/run`} className="btn btn-primary">Run Kit</Link>
                    <Link to={`/kit/${slug}`} className="btn btn-secondary">Back to Kit</Link>
                </div>
            </div>
            {error && <div className="flash flash-error mb-6">{error}</div>}
            {loading ? (
                <div className="empty-state"><div className="flex items-center justify-center gap-2"><span className="pulse-dot" /><span className="pulse-dot" /><span className="pulse-dot" /></div></div>
            ) : runs.length === 0 ? (
                <div className="empty-state">
                    <p className="text-lg mb-1 font-medium">No executions yet</p>
                    <p className="text-sm">Run this kit to see your execution history here.</p>
                    <Link to={`/kit/${slug}/run`} className="btn btn-primary mt-4 inline-flex">Run Kit</Link>
                </div>
            ) : (
                <div className="stream-container">
                    {runs.map((run, idx) => {
                        const sd = run.started_at ? new Date(run.started_at) : null;
                        const ds = sd ? formatDate(sd) : 'Unknown';
                        const ts = sd ? formatTime(sd) : '';
                        const meta: string[] = [`${run.total_steps} step${run.total_steps !== 1 ? 's' : ''}`];
                        if (run.completed_at && run.started_at) {
                            const dur = Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000);
                            meta.push(dur < 60 ? `${dur}s` : `${Math.floor(dur / 60)}m ${dur % 60}s`);
                        }
                        return (
                            <Link key={run.id} to={`/kit/${slug}/history/${run.id}`} className="card card-hoverable block" style={{ textDecoration: 'none', color: 'inherit', animationDelay: `${idx * 0.04}s` }}>
                                <div className="flex items-center justify-between p-4">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-3 mb-1">
                                            <span className="font-medium">{run.label || `${slug} — ${ds}`}</span>
                                            <StatusBadge status={run.status} />
                                        </div>
                                        <div className="text-xs text-muted-foreground flex items-center gap-2">
                                            <span>{ds}{ts ? ` at ${ts}` : ''}</span><span>·</span><span>{meta.join(' · ')}</span>
                                        </div>
                                    </div>
                                    <svg className="w-5 h-5 text-muted-foreground flex-shrink-0 ml-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6" /></svg>
                                </div>
                            </Link>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
