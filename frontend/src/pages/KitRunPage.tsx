import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import { getKit, startExecution, getSSEUrl, submitEvaluation, pauseExecution, resumeExecution, type Resource, type Tool } from '../lib/api';
import { useToast } from '../hooks/useToast';

interface StepResult {
    step: number;
    output_id: string;
    display_name?: string;
    prompt_preview?: string;
    result?: string;
    latency_ms?: number;
    tokens_used?: number;
    status: 'running' | 'done' | 'error' | 'awaiting-eval' | 'paused';
    error?: string;
}

export default function KitRunPage() {
    const { slug } = useParams<{ slug: string }>();
    const [searchParams] = useSearchParams();
    const resumeRunId = searchParams.get('resume');

    const [kitName, setKitName] = useState('');
    const [kitTools, setKitTools] = useState<Tool[]>([]);
    const [dynamicResources, setDynamicResources] = useState<Resource[]>([]);
    const [dynamicValues, setDynamicValues] = useState<Record<string, string | File>>({});
    const [dynamicModes, setDynamicModes] = useState<Record<string, 'text' | 'file'>>({});
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [isPausing, setIsPausing] = useState(false);
    const [evaluate, setEvaluate] = useState(false);
    const [evalMode, setEvalMode] = useState<'transparent' | 'anonymous'>('transparent');
    const [executionId, setExecutionId] = useState<string | null>(null);
    const [totalSteps, setTotalSteps] = useState(0);
    const [completedSteps, setCompletedSteps] = useState(0);
    const [steps, setSteps] = useState<StepResult[]>([]);
    const [done, setDone] = useState(false);
    const [isRunPaused, setIsRunPaused] = useState(false);
    const [resultRunId, setResultRunId] = useState<string | null>(null);
    const [evalStep, setEvalStep] = useState<number | null>(null);
    const [evalScore, setEvalScore] = useState(70);
    const { addToast } = useToast();

    // Auto-start resume if query param is set
    const hasResumed = useRef(false);

    useEffect(() => {
        if (!slug) return;
        getKit(slug)
            .then((data) => {
                setKitName(data.kit.name);
                if (data.tools) setKitTools(data.tools);
                setDynamicResources(data.resources.filter((r) => r.is_dynamic));
            })
            .catch((err) => addToast('error', err instanceof Error ? err.message : 'Failed to load kit.'))
            .finally(() => setLoading(false));
    }, [slug]);

    const doExecution = useCallback(async (isResume: boolean = false) => {
        if (!slug) return;
        setRunning(true);
        if (!isResume) {
            setSteps([]);
            setCompletedSteps(0);
        }
        setDone(false);
        setIsRunPaused(false);
        setResultRunId(null);
        setIsPausing(false);

        try {
            let data;
            if (isResume && resumeRunId) {
                data = await resumeExecution(slug, resumeRunId);
            } else {
                data = await startExecution(slug, {
                    evaluate,
                    evaluation_mode: evalMode,
                    dynamic_resources: Object.keys(dynamicValues).length > 0 ? dynamicValues : undefined,
                });
            }

            if (data.error) {
                addToast('error', data.error);
                setRunning(false);
                return;
            }

            const execId = data.execution_id;
            setExecutionId(execId);

            // Connect SSE
            const evtSource = new EventSource(getSSEUrl(slug, execId));

            evtSource.addEventListener('start', (e) => {
                const d = JSON.parse(e.data);
                setTotalSteps(d.total_steps);
                if (d.past_steps && d.past_steps.length > 0) {
                    setSteps(d.past_steps);
                    setCompletedSteps(d.past_steps.length);
                }
            });

            evtSource.addEventListener('step-start', (e) => {
                const d = JSON.parse(e.data);
                setSteps((prev) => [...prev, {
                    step: d.step,
                    output_id: d.output_id,
                    display_name: d.display_name,
                    status: 'running',
                }]);
            });

            evtSource.addEventListener('step-complete', (e) => {
                const d = JSON.parse(e.data);
                setSteps((prev) => prev.map((s) =>
                    s.step === d.step ? { ...s, ...d, status: 'done' } : s
                ));
                setCompletedSteps((c) => c + 1);
            });

            evtSource.addEventListener('step-await-eval', (e) => {
                const d = JSON.parse(e.data);
                setSteps((prev) => prev.map((s) =>
                    s.step === d.step ? { ...s, status: 'awaiting-eval' } : s
                ));
                setEvalStep(d.step);
            });

            evtSource.addEventListener('step-error', (e) => {
                const d = JSON.parse(e.data);
                setSteps((prev) => prev.map((s) =>
                    s.step === d.step ? { ...s, status: 'error', error: d.error } : s
                ));
            });

            evtSource.addEventListener('done', (e) => {
                const d = JSON.parse(e.data);
                setDone(true);
                setRunning(false);
                setIsPausing(false);
                setResultRunId(d.run_id || null);
                evtSource.close();
                if (d.status === 'completed') {
                    addToast('success', 'Execution completed.');
                } else if (d.status === 'paused') {
                    setIsRunPaused(true);
                    addToast('success', 'Execution paused.');
                } else {
                    addToast('error', d.error || 'Execution failed.');
                }
            });

            evtSource.onerror = () => {
                setRunning(false);
                setIsPausing(false);
                setDone(true);
                evtSource.close();
                addToast('error', 'Connection lost.');
            };

        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Execution failed.');
            setRunning(false);
            setIsPausing(false);
        }
    }, [slug, evaluate, evalMode, dynamicValues, resumeRunId]);

    const handleStart = useCallback(() => doExecution(false), [doExecution]);

    useEffect(() => {
        if (!loading && resumeRunId && !hasResumed.current) {
            hasResumed.current = true;
            doExecution(true);
        }
    }, [loading, resumeRunId, doExecution]);

    const handlePause = async () => {
        if (!slug || !executionId) return;
        setIsPausing(true);
        try {
            await pauseExecution(slug, executionId);
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Failed to pause execution.');
            setIsPausing(false);
        }
    };

    const handleEvalSubmit = async () => {
        if (!slug || !executionId || evalStep === null) return;
        try {
            await submitEvaluation(slug, executionId, evalStep, evalScore);
            setSteps((prev) => prev.map((s) =>
                s.step === evalStep ? { ...s, status: 'done' } : s
            ));
            setEvalStep(null);
        } catch (err) {
            addToast('error', err instanceof Error ? err.message : 'Evaluation failed.');
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

    const progress = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

    return (
        <div className="fade-in">
            {/* Breadcrumb */}
            <nav className="text-sm text-muted-foreground mb-6">
                <Link to="/" className="hover:text-foreground transition-colors">Kits</Link>
                <span className="mx-2">/</span>
                <Link to={`/kit/${slug}`} className="hover:text-foreground transition-colors">{kitName}</Link>
                <span className="mx-2">/</span>
                <span className="text-foreground">Run</span>
            </nav>

            <h1 className="text-3xl font-bold tracking-tight mb-2">Run {kitName}</h1>
            <p className="text-muted-foreground mb-8">Execute this reasoning kit's workflow.</p>

            {/* Config */}
            {!running && !done && !resumeRunId && (
                <div className="card p-6 mb-8 space-y-6">
                    {/* Dynamic resources */}
                    {dynamicResources.length > 0 && (
                        <div>
                            <h3 className="font-semibold text-foreground mb-3">Dynamic Resources</h3>
                            <div className="space-y-4">
                                {dynamicResources.map((r) => (
                                    <div key={r.resource_id} className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <label className="label mb-0">{r.display_name || r.filename}</label>
                                            <div className="flex gap-2">
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        setDynamicModes(prev => ({ ...prev, [r.resource_id]: 'text' }));
                                                        setDynamicValues(prev => ({ ...prev, [r.resource_id]: '' }));
                                                    }}
                                                    className={`btn btn-xs ${dynamicModes[r.resource_id] !== 'file' ? 'btn-primary' : 'btn-ghost'}`}
                                                >
                                                    Text Input
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        setDynamicModes(prev => ({ ...prev, [r.resource_id]: 'file' }));
                                                        setDynamicValues(prev => {
                                                            const newVals = { ...prev };
                                                            delete newVals[r.resource_id];
                                                            return newVals;
                                                        });
                                                    }}
                                                    className={`btn btn-xs ${dynamicModes[r.resource_id] === 'file' ? 'btn-primary' : 'btn-ghost'}`}
                                                >
                                                    File Upload
                                                </button>
                                            </div>
                                        </div>
                                        {dynamicModes[r.resource_id] === 'file' ? (
                                            <input
                                                type="file"
                                                className="input"
                                                onChange={(e) => {
                                                    const file = e.target.files?.[0];
                                                    if (file) {
                                                        setDynamicValues((prev) => ({ ...prev, [r.resource_id]: file }));
                                                    }
                                                }}
                                            />
                                        ) : (
                                            <textarea
                                                className="input"
                                                rows={3}
                                                placeholder={`Enter content for ${r.display_name || r.filename}...`}
                                                value={(dynamicValues[r.resource_id] as string) || ''}
                                                onChange={(e) => setDynamicValues((prev) => ({ ...prev, [r.resource_id]: e.target.value }))}
                                            />
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Attached Tools */}
                    {kitTools.length > 0 && (
                        <div>
                            <h3 className="font-semibold text-foreground mb-3">Attached Tools</h3>
                            <div className="flex flex-wrap gap-2">
                                {kitTools.map((t) => (
                                    <span key={t.tool_id} className="badge" style={{ background: 'var(--color-muted)', borderColor: 'var(--color-border)', color: 'var(--color-foreground)' }} title={t.tool_name}>
                                        <svg className="w-3.5 h-3.5 mr-1.5 text-purple-500 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                                        </svg>
                                        {t.display_name || t.tool_name}
                                    </span>
                                ))}
                            </div>
                            <p className="text-xs text-muted-foreground mt-2">These tools are available to the AI during execution.</p>
                        </div>
                    )}

                    {/* Evaluation settings */}
                    <div>
                        <h3 className="font-semibold text-foreground mb-3">Evaluation</h3>
                        <label className="flex items-center gap-2 text-sm cursor-pointer mb-3">
                            <input type="checkbox" checked={evaluate} onChange={(e) => setEvaluate(e.target.checked)} className="rounded" />
                            Enable step-by-step evaluation
                        </label>
                        {evaluate && (
                            <div className="flex gap-3 ml-6">
                                <label className="flex items-center gap-1.5 text-sm cursor-pointer">
                                    <input type="radio" name="evalMode" value="transparent" checked={evalMode === 'transparent'} onChange={() => setEvalMode('transparent')} />
                                    Transparent
                                </label>
                                <label className="flex items-center gap-1.5 text-sm cursor-pointer">
                                    <input type="radio" name="evalMode" value="anonymous" checked={evalMode === 'anonymous'} onChange={() => setEvalMode('anonymous')} />
                                    Anonymous
                                </label>
                            </div>
                        )}
                    </div>

                    <button onClick={handleStart} className="btn btn-primary btn-lg">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <polygon points="5 3 19 12 5 21 5 3" />
                        </svg>
                        Start Execution
                    </button>
                </div>
            )}

            {/* Progress bar */}
            {running && totalSteps > 0 && (
                <div className="mb-8">
                    <div className="flex items-center justify-between text-sm text-muted-foreground mb-2">
                        <span>Progress</span>
                        <div className="flex items-center gap-4">
                            <span>{completedSteps} / {totalSteps} steps ({progress}%)</span>
                            <button
                                onClick={handlePause}
                                disabled={isPausing}
                                className="btn btn-secondary btn-sm"
                            >
                                {isPausing ? 'Pausing...' : 'Pause Execution'}
                            </button>
                        </div>
                    </div>
                    <div className="progress-bar">
                        <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
                    </div>
                </div>
            )}

            {/* Step outputs */}
            {steps.length > 0 && (
                <div className="stream-container">
                    {steps.map((step) => (
                        <StepOutput
                            key={step.step}
                            step={step}
                            isEvaluating={evalStep === step.step}
                            evalScore={evalScore}
                            setEvalScore={setEvalScore}
                            onEvalSubmit={handleEvalSubmit}
                        />
                    ))}
                </div>
            )}

            {/* Done actions */}
            {done && (
                <div className="flex items-center gap-3 mt-8">
                    {isRunPaused ? (
                        <a href={`/kit/${slug}/run?resume=${resultRunId}`} className="btn btn-primary shadow-sm flex items-center gap-2">
                            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            Resume Execution
                        </a>
                    ) : (
                        <button onClick={() => { setDone(false); setSteps([]); setCompletedSteps(0); setTotalSteps(0); }} className="btn btn-primary">Run Again</button>
                    )}
                    {resultRunId && (
                        <Link to={`/kit/${slug}/history/${resultRunId}`} className="btn btn-secondary">View Details</Link>
                    )}
                    <Link to={`/kit/${slug}`} className="btn btn-ghost">Back to Kit</Link>
                </div>
            )}
        </div>
    );
}

function StepOutput({ step, isEvaluating, evalScore, setEvalScore, onEvalSubmit }: {
    step: StepResult;
    isEvaluating?: boolean;
    evalScore?: number;
    setEvalScore?: (s: number) => void;
    onEvalSubmit?: () => void;
}) {
    const [expanded, setExpanded] = useState(false);

    const statusBadge = step.status === 'done'
        ? <span className="badge" style={{ background: '#f0fdf4', color: '#166534', borderColor: '#bbf7d0' }}>Done</span>
        : step.status === 'error'
            ? <span className="badge" style={{ background: '#fef2f2', color: '#991b1b', borderColor: '#fecaca' }}>Error</span>
            : step.status === 'awaiting-eval'
                ? <span className="badge" style={{ background: '#eff6ff', color: '#1e40af', borderColor: '#bfdbfe' }}>Awaiting Eval</span>
                : step.status === 'paused'
                    ? <span className="badge" style={{ background: '#fffbeb', color: '#b45309', borderColor: '#fde68a' }}>Paused</span>
                    : <span className="badge badge-primary">Running</span>;

    const metaParts: string[] = [];
    if (step.latency_ms) metaParts.push(`${(step.latency_ms / 1000).toFixed(1)}s`);
    if (step.tokens_used) metaParts.push(`${step.tokens_used} tokens`);

    return (
        <div className="step-card fade-in">
            <div className="step-card-header flex items-center justify-between">
                <span>
                    Step {step.step}
                    {step.display_name && ` — ${step.display_name}`}
                    <span className="text-xs text-muted-foreground ml-2">({step.output_id})</span>
                </span>
                <span className="flex items-center gap-2">
                    {statusBadge}
                    {metaParts.length > 0 && (
                        <span className="text-xs text-muted-foreground">{metaParts.join(' · ')}</span>
                    )}
                </span>
            </div>
            <div className="step-card-body">
                {step.prompt_preview && (
                    <div className="mb-3">
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
                            <div className="content-preview text-xs mt-2" style={{ maxHeight: '40rem', overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                                {step.prompt_preview}
                            </div>
                        )}
                    </div>
                )}
                {step.status === 'running' && (
                    <div className="flex items-center gap-2 py-2">
                        <span className="pulse-dot" /><span className="pulse-dot" /><span className="pulse-dot" />
                    </div>
                )}
                {step.result && (
                    <div className="content-preview" style={{ whiteSpace: 'pre-wrap' }}>{step.result}</div>
                )}
                {isEvaluating && (
                    <div className="card p-5 mt-4 border-l-4 border-primary bg-background">
                        <h3 className="font-semibold mb-3">Evaluate Step {step.step}</h3>
                        <div className="flex items-center gap-4">
                            <input
                                type="range"
                                min={0}
                                max={100}
                                value={evalScore}
                                onChange={(e) => setEvalScore?.(Number(e.target.value))}
                                className="flex-1"
                            />
                            <span className="font-medium text-sm w-12 text-center">{evalScore}</span>
                            <button onClick={onEvalSubmit} className="btn btn-primary btn-sm">Submit</button>
                        </div>
                    </div>
                )}
                {step.error && (
                    <div className="flash flash-error mt-2 text-sm">{step.error}</div>
                )}
            </div>
        </div>
    );
}
