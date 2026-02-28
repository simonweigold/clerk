/**
 * API client for CLERK backend.
 * All API calls go through this module for consistent error handling.
 */

const API_BASE = '/api';

export class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let message = `Request failed with status ${response.status}`;
        try {
            const data = await response.json();
            message = data.detail || data.error || message;
        } catch {
            // ignore json parse error
        }
        throw new ApiError(message, response.status);
    }
    return response.json();
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface User {
    id: string;
    email: string;
    display_name?: string;
}

export interface AuthResponse {
    ok: boolean;
    user?: User;
    error?: string;
    redirect?: string;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    return handleResponse<AuthResponse>(res);
}

export async function signup(email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    return handleResponse<AuthResponse>(res);
}

export async function logout(): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
    return handleResponse<AuthResponse>(res);
}

export async function resetPassword(email: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
    });
    return handleResponse<AuthResponse>(res);
}

export async function getMe(): Promise<{ user: User | null; supabase_configured: boolean }> {
    const res = await fetch(`${API_BASE}/auth/me`);
    return handleResponse(res);
}

// ─── Kits ────────────────────────────────────────────────────────────────────

export interface Kit {
    id: string;
    name: string;
    slug: string;
    description: string;
    version_number?: number;
    created_at?: string;
    owner_id?: string;
    is_public?: boolean;
    is_bookmarked?: boolean;
}

export interface Resource {
    number: number;
    resource_id: string;
    filename: string;
    display_name?: string;
    is_dynamic?: boolean;
    extracted_text?: string;
    file_size_bytes?: number;
    mime_type?: string;
}

export interface Step {
    number: number;
    output_id: string;
    prompt_template: string;
    display_name?: string;
}

export interface KitDetail {
    kit: Kit;
    resources: Resource[];
    steps: Step[];
    source: string;
    is_owner: boolean;
}

export async function listKits(): Promise<{ kits: Kit[] }> {
    const res = await fetch(`${API_BASE}/kits`);
    return handleResponse(res);
}

export async function searchKits(query: string, filter: string = 'all'): Promise<{ kits: Kit[] }> {
    const params = new URLSearchParams({ q: query, filter });
    const res = await fetch(`${API_BASE}/kits/search?${params.toString()}`);
    return handleResponse(res);
}

export async function getKit(slug: string): Promise<KitDetail> {
    const res = await fetch(`${API_BASE}/kits/${slug}/detail`);
    return handleResponse(res);
}

export async function toggleBookmark(slug: string): Promise<{ ok: boolean; is_bookmarked: boolean }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/bookmark`, { method: 'POST' });
    return handleResponse(res);
}

export async function createKit(name: string, description: string): Promise<{ ok: boolean; slug: string }> {
    const res = await fetch(`${API_BASE}/kits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
    });
    return handleResponse(res);
}

export async function updateKit(slug: string, name: string, description: string): Promise<{ ok: boolean }> {
    const res = await fetch(`${API_BASE}/kits/${slug}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
    });
    return handleResponse(res);
}

export async function deleteKit(slug: string): Promise<{ ok: boolean }> {
    const res = await fetch(`${API_BASE}/kits/${slug}`, { method: 'DELETE' });
    return handleResponse(res);
}

// ─── Resources ───────────────────────────────────────────────────────────────

export async function addResource(
    slug: string,
    data: FormData
): Promise<{ ok: boolean }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/resources`, {
        method: 'POST',
        body: data,
    });
    return handleResponse(res);
}

export async function updateResource(
    slug: string,
    number: number,
    data: FormData
): Promise<{ ok: boolean }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/resources/${number}/update`, {
        method: 'POST',
        body: data,
    });
    return handleResponse(res);
}

export async function deleteResource(slug: string, number: number): Promise<{ ok: boolean }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/resources/${number}`, { method: 'DELETE' });
    return handleResponse(res);
}

// ─── Steps ───────────────────────────────────────────────────────────────────

export async function addStep(
    slug: string,
    prompt: string,
    displayName: string
): Promise<{ ok: boolean }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/steps`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, display_name: displayName }),
    });
    return handleResponse(res);
}

export async function updateStep(
    slug: string,
    number: number,
    prompt: string,
    displayName: string
): Promise<{ ok: boolean }> {
    const fd = new FormData();
    fd.append('prompt', prompt);
    fd.append('display_name', displayName);
    const res = await fetch(`${API_BASE}/kits/${slug}/steps/${number}/update`, {
        method: 'POST',
        body: fd,
    });
    return handleResponse(res);
}

export async function deleteStep(slug: string, number: number): Promise<{ ok: boolean }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/steps/${number}`, { method: 'DELETE' });
    return handleResponse(res);
}

// ─── Execution ───────────────────────────────────────────────────────────────

export interface ExecutionConfig {
    evaluate: boolean;
    evaluation_mode: 'transparent' | 'anonymous';
    dynamic_resources?: Record<string, string | File>;
}

export async function startExecution(
    slug: string,
    config: ExecutionConfig
): Promise<{ execution_id: string; error?: string }> {
    const hasFiles = config.dynamic_resources && Object.values(config.dynamic_resources).some((val) => val instanceof File);

    if (hasFiles) {
        const fd = new FormData();
        fd.append('evaluate', config.evaluate ? 'true' : 'false');
        fd.append('evaluation_mode', config.evaluation_mode);
        if (config.dynamic_resources) {
            for (const [key, val] of Object.entries(config.dynamic_resources)) {
                if (val instanceof File) {
                    fd.append(`dynamic_resource_file_${key}`, val);
                } else {
                    fd.append(`dynamic_resource_text_${key}`, val);
                }
            }
        }
        const res = await fetch(`${API_BASE}/kits/${slug}/execute`, {
            method: 'POST',
            body: fd,
        });
        return handleResponse(res);
    }

    const res = await fetch(`${API_BASE}/kits/${slug}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
    });
    return handleResponse(res);
}

export async function submitEvaluation(
    slug: string,
    executionId: string,
    step: number,
    score: number
): Promise<{ ok: boolean }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/evaluate-step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ execution_id: executionId, step, score }),
    });
    return handleResponse(res);
}

export function getSSEUrl(slug: string, executionId: string): string {
    return `${API_BASE}/kits/${slug}/execute/${executionId}/stream`;
}

export async function pauseExecution(slug: string, executionId: string): Promise<{ ok: boolean; error?: string }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/executions/${executionId}/pause`, {
        method: 'POST',
    });
    return handleResponse(res);
}

export async function resumeExecution(slug: string, runId: string): Promise<{ execution_id: string; error?: string }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/execute/resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: runId }),
    });
    return handleResponse(res);
}

export async function deleteExecution(slug: string, runId: string): Promise<{ ok: boolean; error?: string }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/executions/${runId}`, {
        method: 'DELETE',
    });
    return handleResponse(res);
}

// ─── Execution History ───────────────────────────────────────────────────────

export interface ExecutionRun {
    id: string;
    label?: string;
    started_at: string;
    completed_at?: string;
    status: string;
    total_steps: number;
    completed_steps: number;
}

export async function listExecutions(slug: string): Promise<{ runs: ExecutionRun[] }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/executions`);
    return handleResponse(res);
}

export async function getExecution(slug: string, runId: string): Promise<Record<string, unknown>> {
    const res = await fetch(`${API_BASE}/kits/${slug}/executions/${runId}`);
    return handleResponse(res);
}

export async function updateExecutionLabel(
    slug: string,
    runId: string,
    label: string
): Promise<{ ok: boolean }> {
    const res = await fetch(`${API_BASE}/kits/${slug}/executions/${runId}/label`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label }),
    });
    return handleResponse(res);
}

export function getDownloadUrl(slug: string, runId: string, format: 'md' | 'json'): string {
    return `${API_BASE}/kits/${slug}/executions/${runId}/download?format=${format}`;
}
