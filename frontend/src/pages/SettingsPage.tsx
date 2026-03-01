import { useState, useEffect } from 'react';
import { getMcpConfigs, updateMcpConfig } from '../lib/api';
import type { McpConfig } from '../lib/api';
import { useToast } from '../hooks/useToast';
import { useAuth } from '../hooks/useAuth';

// Known servers and their expected env vars
const KNOWN_SERVERS = [
    {
        name: 'google-sheets',
        label: 'Google Sheets',
        vars: ['GOOGLE_SHEETS_SERVICE_ACCOUNT_PATH', 'GOOGLE_SHEETS_DRIVE_FOLDER_ID']
    },
    {
        name: 'airtable',
        label: 'Airtable',
        vars: ['AIRTABLE_API_KEY']
    }
];

export default function SettingsPage() {
    const { user } = useAuth();
    const { addToast } = useToast();
    const [configs, setConfigs] = useState<McpConfig[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) return;
        loadConfigs();
    }, [user]);

    async function loadConfigs() {
        try {
            const res = await getMcpConfigs();
            setConfigs(res.configs || []);
        } catch (err: unknown) {
            console.error(err);
            addToast('error', 'Failed to load configurations');
        } finally {
            setLoading(false);
        }
    }

    async function handleSave(serverName: string, envVars: Record<string, string>) {
        try {
            await updateMcpConfig(serverName, envVars);
            addToast('success', 'Configuration saved successfully');
            loadConfigs();
        } catch (err: unknown) {
            console.error(err);
            addToast('error', 'Failed to save configuration');
        }
    }

    if (loading) {
        return (
            <div className="flex h-[calc(100vh-64px)] items-center justify-center text-muted">
                <span className="animate-pulse">Loading settings...</span>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-8">Settings & Integrations</h1>

            <p className="text-muted-foreground mb-8">
                Provide your custom API keys and credentials for MCP servers here.
                These credentials will be securely stored and used only during your own kit executions.
                If left empty, the global system credentials will be used as a fallback if available.
            </p>

            <div className="space-y-8">
                {KNOWN_SERVERS.map(server => {
                    const existingConfig = configs.find(c => c.server_name === server.name);

                    return (
                        <ServerConfigForm
                            key={server.name}
                            server={server}
                            existingConfig={existingConfig}
                            onSave={(envVars) => handleSave(server.name, envVars)}
                        />
                    );
                })}
            </div>
        </div>
    );
}

function ServerConfigForm({
    server,
    existingConfig,
    onSave
}: {
    server: typeof KNOWN_SERVERS[0];
    existingConfig?: McpConfig;
    onSave: (envVars: Record<string, string>) => void;
}) {
    const [formVars, setFormVars] = useState<Record<string, string>>(
        existingConfig?.env_vars || {}
    );

    // Update local state if the server configs reload
    useEffect(() => {
        setFormVars(existingConfig?.env_vars || {});
    }, [existingConfig]);

    return (
        <div className="card p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center text-primary">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                </div>
                {server.label} Integration
            </h2>

            <div className="space-y-4 max-w-2xl mt-6">
                {server.vars.map(v => (
                    <div key={v}>
                        <label className="block text-sm font-medium mb-1.5 font-mono text-xs">{v}</label>
                        <input
                            type={v.includes('KEY') || v.includes('SECRET') || v.includes('TOKEN') ? 'password' : 'text'}
                            className="input w-full"
                            value={formVars[v] || ''}
                            onChange={(e) => setFormVars({ ...formVars, [v]: e.target.value })}
                            placeholder={`Enter ${v}`}
                        />
                    </div>
                ))}

                <div className="pt-4 flex items-center justify-end">
                    <button
                        className="btn btn-primary"
                        onClick={() => onSave(formVars)}
                    >
                        Save Credentials
                    </button>
                </div>
            </div>
        </div>
    );
}
