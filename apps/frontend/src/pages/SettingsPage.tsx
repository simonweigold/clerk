import { useState, useEffect, useMemo } from 'react';
import { Eye, EyeOff, Check } from 'lucide-react';
import { getMcpConfigs, updateMcpConfig, getLlmConfigs, updateLlmConfig } from '../lib/api';
import type { McpConfig, LlmConfig } from '../lib/api';
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

// Known LLM Providers
const KNOWN_PROVIDERS = [
    {
        name: 'openai',
        label: 'OpenAI',
        vars: ['OPENAI_API_KEY'],
        models: ['gpt-5-mini', 'gpt-5', 'gpt-5.4']
    },
    {
        name: 'anthropic',
        label: 'Anthropic Claude',
        vars: ['ANTHROPIC_API_KEY'],
        models: ['claude-3-5-sonnet-latest', 'claude-3-opus-latest', 'claude-3-haiku-20240307']
    },
    {
        name: 'mistral',
        label: 'Mistral AI',
        vars: ['MISTRAL_API_KEY'],
        models: ['mistral-large-latest', 'mistral-small-latest', 'pixtral-large-latest']
    },
    {
        name: 'gemini',
        label: 'Google Gemini (API Key)',
        vars: ['GOOGLE_API_KEY'],
        models: ['gemini-1.5-pro', 'gemini-1.5-pro-exp-0827', 'gemini-1.5-flash']
    },
    {
        name: 'vertex',
        label: 'Google Vertex AI',
        vars: ['GOOGLE_CLOUD_PROJECT', 'GOOGLE_APPLICATION_CREDENTIALS_JSON'],
        models: ['gemini-1.5-pro', 'gemini-1.5-pro-exp-0827', 'gemini-1.5-flash']
    },
    {
        name: 'openrouter',
        label: 'OpenRouter',
        vars: ['OPENROUTER_API_KEY'],
        models: ['openai/gpt-5-mini', 'anthropic/claude-3.5-sonnet', 'google/gemini-1.5-pro']
    }
];

export default function SettingsPage() {
    const { user } = useAuth();
    const { addToast } = useToast();
    const [mcpConfigs, setMcpConfigs] = useState<McpConfig[]>([]);
    const [llmConfigs, setLlmConfigs] = useState<LlmConfig[]>([]);
    const [loading, setLoading] = useState(true);

    // Track manually added (but maybe not yet saved) providers/servers
    const [addedProviders, setAddedProviders] = useState<string[]>([]);
    const [addedServers, setAddedServers] = useState<string[]>([]);
    const [savingProviders, setSavingProviders] = useState<Record<string, boolean>>({});
    const [savingServers, setSavingServers] = useState<Record<string, boolean>>({});

    useEffect(() => {
        if (!user) return;
        loadConfigs();
    }, [user]);

    async function loadConfigs() {
        try {
            const [mcpRes, llmRes] = await Promise.all([
                getMcpConfigs(),
                getLlmConfigs()
            ]);
            setMcpConfigs(mcpRes.configs || []);
            setLlmConfigs(llmRes.configs || []);
        } catch (err: unknown) {
            console.error(err);
            addToast('error', 'Failed to load configurations');
        } finally {
            setLoading(false);
        }
    }

    async function handleSaveLlm(providerName: string, envVars: Record<string, string>, selectedModel: string, isActive: boolean) {
        setSavingProviders(prev => ({ ...prev, [providerName]: true }));
        try {
            await updateLlmConfig(providerName, envVars, selectedModel, isActive);
            addToast('success', 'LLM Provider saved successfully');
            loadConfigs();
            // If it was deactivated, remove it from the "added" list so it disappears
            if (!isActive) {
                setAddedProviders(prev => prev.filter(p => p !== providerName));
            }
        } catch (err: unknown) {
            console.error(err);
            addToast('error', 'Failed to save LLM configuration');
        } finally {
            setSavingProviders(prev => ({ ...prev, [providerName]: false }));
        }
    }

    async function handleSaveMcp(serverName: string, envVars: Record<string, string>, isActive: boolean) {
        setSavingServers(prev => ({ ...prev, [serverName]: true }));
        try {
            await updateMcpConfig(serverName, envVars, isActive);
            addToast('success', 'MCP Configuration saved successfully');
            loadConfigs();
            // If it was deactivated, remove it from the "added" list so it disappears
            if (!isActive) {
                setAddedServers(prev => prev.filter(s => s !== serverName));
            }
        } catch (err: unknown) {
            console.error(err);
            addToast('error', 'Failed to save MCP configuration');
        } finally {
            setSavingServers(prev => ({ ...prev, [serverName]: false }));
        }
    }

    // Derived lists of what should be visible
    const visibleProviders = useMemo(() => {
        return KNOWN_PROVIDERS.filter(p => {
            const isSavedActive = llmConfigs.some(c => c.provider_name === p.name && c.is_active);
            const isManuallyAdded = addedProviders.includes(p.name);
            return isSavedActive || isManuallyAdded;
        });
    }, [KNOWN_PROVIDERS, llmConfigs, addedProviders]);

    const visibleServers = useMemo(() => {
        return KNOWN_SERVERS.filter(s => {
            const isSavedActive = mcpConfigs.some(c => c.server_name === s.name && c.is_active);
            const isManuallyAdded = addedServers.includes(s.name);
            return isSavedActive || isManuallyAdded;
        });
    }, [KNOWN_SERVERS, mcpConfigs, addedServers]);

    const availableProvidersToAdd = KNOWN_PROVIDERS.filter(p => !visibleProviders.includes(p));
    const availableServersToAdd = KNOWN_SERVERS.filter(s => !visibleServers.includes(s));

    if (loading) {
        return (
            <div className="empty-state fade-in min-h-[50vh] flex items-center justify-center">
                <div className="flex items-center justify-center gap-2">
                    <span className="pulse-dot" /><span className="pulse-dot" /><span className="pulse-dot" />
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-8">Settings & Integrations</h1>

            <p className="text-muted-foreground mb-8">
                View your account details and configure custom API keys for MCP servers and LLM Providers.
                These credentials will be securely stored and used only during your own kit executions.
                If left empty, the global system credentials will be used as a fallback if available.
            </p>

            <div className="space-y-8">
                {/* Account Settings Section */}
                <div className="card p-6">
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center text-primary">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                        </div>
                        Account Information
                    </h2>

                    <div className="space-y-4 max-w-2xl mt-4">
                        <div>
                            <label className="block text-sm font-medium mb-1.5 font-mono text-xs text-muted-foreground">Email Address</label>
                            <div className="p-2 bg-muted/30 rounded border border-border text-sm">
                                {user?.email}
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1.5 font-mono text-xs text-muted-foreground">Account ID</label>
                            <div className="p-2 bg-muted/30 rounded border border-border text-sm font-mono text-xs">
                                {user?.id}
                            </div>
                        </div>
                        {user?.display_name && (
                            <div>
                                <label className="block text-sm font-medium mb-1.5 font-mono text-xs text-muted-foreground">Display Name</label>
                                <div className="p-2 bg-muted/30 rounded border border-border text-sm">
                                    {user.display_name}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="divider flex items-center justify-between">
                    <span>LLM Providers</span>
                    {availableProvidersToAdd.length > 0 && (
                        <div className="flex items-center gap-2">
                            <select
                                className="select select-sm text-sm py-1 bg-muted/50 border-transparent hover:border-border cursor-pointer transition-colors"
                                onChange={(e) => {
                                    const val = e.target.value;
                                    if (val) {
                                        setAddedProviders(prev => [...prev, val]);
                                    }
                                }}
                                value=""
                            >
                                <option value="" disabled>+ Add Provider</option>
                                {availableProvidersToAdd.map(p => (
                                    <option key={p.name} value={p.name}>{p.label}</option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>

                {visibleProviders.length === 0 ? (
                    <div className="text-center p-8 border border-dashed rounded-lg text-muted-foreground text-sm">
                        No active LLM providers. Add one above to configure credentials.
                    </div>
                ) : (
                    visibleProviders.map(provider => {
                        const existingConfig = llmConfigs.find(c => c.provider_name === provider.name);
                        const isNewlyAdded = addedProviders.includes(provider.name);
                        return (
                            <LlmProviderForm
                                key={provider.name}
                                provider={provider}
                                existingConfig={existingConfig}
                                isNewlyAdded={isNewlyAdded}
                                isSaving={savingProviders[provider.name]}
                                onSave={(envVars, selectedModel, isActive) => handleSaveLlm(provider.name, envVars, selectedModel, isActive)}
                            />
                        );
                    })
                )}

                <div className="divider flex items-center justify-between mt-12">
                    <span>MCP Servers</span>
                    {availableServersToAdd.length > 0 && (
                        <div className="flex items-center gap-2">
                            <select
                                className="select select-sm text-sm py-1 bg-muted/50 border-transparent hover:border-border cursor-pointer transition-colors"
                                onChange={(e) => {
                                    const val = e.target.value;
                                    if (val) {
                                        setAddedServers(prev => [...prev, val]);
                                    }
                                }}
                                value=""
                            >
                                <option value="" disabled>+ Add Server</option>
                                {availableServersToAdd.map(s => (
                                    <option key={s.name} value={s.name}>{s.label}</option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>

                {visibleServers.length === 0 ? (
                    <div className="text-center p-8 border border-dashed rounded-lg text-muted-foreground text-sm">
                        No active MCP servers. Add one above to configure credentials.
                    </div>
                ) : (
                    visibleServers.map(server => {
                        const existingConfig = mcpConfigs.find(c => c.server_name === server.name);
                        const isNewlyAdded = addedServers.includes(server.name);
                        return (
                            <ServerConfigForm
                                key={server.name}
                                server={server}
                                existingConfig={existingConfig}
                                isNewlyAdded={isNewlyAdded}
                                isSaving={savingServers[server.name]}
                                onSave={(envVars, isActive) => handleSaveMcp(server.name, envVars, isActive)}
                            />
                        );
                    })
                )}
            </div>
        </div>
    );
}

function LlmProviderForm({
    provider,
    existingConfig,
    isNewlyAdded,
    isSaving,
    onSave
}: {
    provider: typeof KNOWN_PROVIDERS[0];
    existingConfig?: LlmConfig;
    isNewlyAdded?: boolean;
    isSaving?: boolean;
    onSave: (envVars: Record<string, string>, selectedModel: string, isActive: boolean) => void;
}) {
    const [formVars, setFormVars] = useState<Record<string, string>>(
        existingConfig?.env_vars || {}
    );
    const [selectedModel, setSelectedModel] = useState<string>(
        existingConfig?.selected_model || provider.models[0]
    );
    const [isActive, setIsActive] = useState<boolean>(
        isNewlyAdded ? true : (existingConfig?.is_active ?? true)
    );
    const [visibleVars, setVisibleVars] = useState<Record<string, boolean>>({});
    const [isSaved, setIsSaved] = useState(false);

    const showSecret = (v: string) => setVisibleVars(prev => ({ ...prev, [v]: true }));
    const hideSecret = (v: string) => setVisibleVars(prev => ({ ...prev, [v]: false }));

    useEffect(() => {
        setFormVars(existingConfig?.env_vars || {});
        setSelectedModel(existingConfig?.selected_model || provider.models[0]);
        setIsActive(isNewlyAdded ? true : (existingConfig?.is_active ?? true));
        setIsSaved(false);
    }, [existingConfig, isNewlyAdded]);

    useEffect(() => {
        if (isSaved) {
            const timer = setTimeout(() => setIsSaved(false), 2000);
            return () => clearTimeout(timer);
        }
    }, [isSaved]);

    const handleSave = () => {
        setIsSaved(false);
        onSave(formVars, selectedModel, isActive);
        setIsSaved(true);
    };

    const handleFormChange = (newVars: Record<string, string>) => {
        setFormVars(newVars);
        setIsSaved(false);
    };

    const handleModelChange = (model: string) => {
        setSelectedModel(model);
        setIsSaved(false);
    };

    const handleActiveChange = (active: boolean) => {
        setIsActive(active);
        setIsSaved(false);
    };

    return (
        <div className="card p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center text-primary">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                </div>
                {provider.label}
            </h2>

            <div className="flex items-center gap-3 mt-2 mb-6">
                <label className="relative inline-flex items-center cursor-pointer">
                    <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={isActive}
                        onChange={(e) => handleActiveChange(e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    <span className="ml-3 text-sm font-medium text-slate-700 dark:text-slate-300">
                        {isActive ? 'Active Provider' : 'Set Active'}
                    </span>
                </label>
            </div>

            <div className="space-y-4 max-w-2xl">
                <div>
                    <label className="block text-sm font-medium mb-1.5 font-mono text-xs">Default Model</label>
                    <select
                        className="select w-full"
                        value={selectedModel}
                        onChange={(e) => handleModelChange(e.target.value)}
                    >
                        {provider.models.map(m => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>
                </div>

                {provider.vars.map(v => (
                    <div key={v}>
                        <label className="block text-sm font-medium mb-1.5 font-mono text-xs">{v}</label>
                        {v === 'GOOGLE_APPLICATION_CREDENTIALS_JSON' ? (
                            <textarea
                                className="input w-full h-24 py-2 font-mono text-xs"
                                value={formVars[v] || ''}
                                onChange={(e) => handleFormChange({ ...formVars, [v]: e.target.value })}
                                placeholder={`Paste JSON content for ${v}`}
                            />
                        ) : (
                            <div className="relative">
                                <input
                                    type={
                                        (v.includes('KEY') || v.includes('SECRET') || v.includes('TOKEN')) && !visibleVars[v]
                                            ? 'password'
                                            : 'text'
                                    }
                                    className="input w-full pr-10"
                                    value={formVars[v] || ''}
                                    onChange={(e) => handleFormChange({ ...formVars, [v]: e.target.value })}
                                    placeholder={`Enter ${v}`}
                                />
                                {(v.includes('KEY') || v.includes('SECRET') || v.includes('TOKEN')) && (
                                    <button
                                        type="button"
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                        onMouseDown={() => showSecret(v)}
                                        onMouseUp={() => hideSecret(v)}
                                        onMouseLeave={() => hideSecret(v)}
                                        title="Hold to show secret"
                                    >
                                        {visibleVars[v] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                ))}

                <div className="pt-4 flex items-center justify-end">
                    <button
                        className={`btn btn-primary min-w-[130px] ${isSaving ? 'opacity-70 cursor-not-allowed' : ''} ${isSaved ? 'bg-green-600 hover:bg-green-700 border-green-600 text-white' : ''}`}
                        disabled={isSaving}
                        onClick={handleSave}
                    >
                        {isSaving ? (
                            <div className="flex items-center justify-center gap-1.5 w-full">
                                <span className="pulse-dot w-1.5 h-1.5 bg-current" />
                                <span className="pulse-dot w-1.5 h-1.5 bg-current animation-delay-150" />
                                <span className="pulse-dot w-1.5 h-1.5 bg-current animation-delay-300" />
                            </div>
                        ) : isSaved ? (
                            <div className="flex items-center justify-center gap-1.5 w-full">
                                <Check className="w-4 h-4" />
                                <span>Saved</span>
                            </div>
                        ) : 'Save Settings'}
                    </button>
                </div>
            </div>
        </div>
    );
}

function ServerConfigForm({
    server,
    existingConfig,
    isNewlyAdded,
    isSaving,
    onSave
}: {
    server: typeof KNOWN_SERVERS[0];
    existingConfig?: McpConfig;
    isNewlyAdded?: boolean;
    isSaving?: boolean;
    onSave: (envVars: Record<string, string>, isActive: boolean) => void;
}) {
    const [formVars, setFormVars] = useState<Record<string, string>>(
        existingConfig?.env_vars || {}
    );
    const [isActive, setIsActive] = useState<boolean>(
        isNewlyAdded ? true : (existingConfig?.is_active ?? true)
    );
    const [visibleVars, setVisibleVars] = useState<Record<string, boolean>>({});
    const [isSaved, setIsSaved] = useState(false);

    const showSecret = (v: string) => setVisibleVars(prev => ({ ...prev, [v]: true }));
    const hideSecret = (v: string) => setVisibleVars(prev => ({ ...prev, [v]: false }));

    useEffect(() => {
        setFormVars(existingConfig?.env_vars || {});
        setIsActive(isNewlyAdded ? true : (existingConfig?.is_active ?? true));
        setIsSaved(false);
    }, [existingConfig, isNewlyAdded]);

    useEffect(() => {
        if (isSaved) {
            const timer = setTimeout(() => setIsSaved(false), 2000);
            return () => clearTimeout(timer);
        }
    }, [isSaved]);

    const handleSave = () => {
        setIsSaved(false);
        onSave(formVars, isActive);
        setIsSaved(true);
    };

    const handleFormChange = (newVars: Record<string, string>) => {
        setFormVars(newVars);
        setIsSaved(false);
    };

    const handleActiveChange = (active: boolean) => {
        setIsActive(active);
        setIsSaved(false);
    };

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

            <div className="flex items-center gap-3 mt-2 mb-6">
                <label className="relative inline-flex items-center cursor-pointer">
                    <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={isActive}
                        onChange={(e) => handleActiveChange(e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    <span className="ml-3 text-sm font-medium text-slate-700 dark:text-slate-300">
                        {isActive ? 'Enabled' : 'Disabled'}
                    </span>
                </label>
            </div>

            <div className="space-y-4 max-w-2xl">
                {server.vars.map(v => (
                    <div key={v}>
                        <label className="block text-sm font-medium mb-1.5 font-mono text-xs">{v}</label>
                        <div className="relative">
                            <input
                                type={
                                    (v.includes('KEY') || v.includes('SECRET') || v.includes('TOKEN')) && !visibleVars[v]
                                        ? 'password'
                                        : 'text'
                                }
                                className="input w-full pr-10"
                                value={formVars[v] || ''}
                                onChange={(e) => handleFormChange({ ...formVars, [v]: e.target.value })}
                                placeholder={`Enter ${v}`}
                            />
                            {(v.includes('KEY') || v.includes('SECRET') || v.includes('TOKEN')) && (
                                <button
                                    type="button"
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                    onMouseDown={() => showSecret(v)}
                                    onMouseUp={() => hideSecret(v)}
                                    onMouseLeave={() => hideSecret(v)}
                                    title="Hold to show secret"
                                >
                                    {visibleVars[v] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            )}
                        </div>
                    </div>
                ))}

                <div className="pt-4 flex items-center justify-end">
                    <button
                        className={`btn btn-primary min-w-[130px] ${isSaving ? 'opacity-70 cursor-not-allowed' : ''} ${isSaved ? 'bg-green-600 hover:bg-green-700 border-green-600 text-white' : ''}`}
                        disabled={isSaving}
                        onClick={handleSave}
                    >
                        {isSaving ? (
                            <div className="flex items-center justify-center gap-1.5 w-full">
                                <span className="pulse-dot w-1.5 h-1.5 bg-current" />
                                <span className="pulse-dot w-1.5 h-1.5 bg-current animation-delay-150" />
                                <span className="pulse-dot w-1.5 h-1.5 bg-current animation-delay-300" />
                            </div>
                        ) : isSaved ? (
                            <div className="flex items-center justify-center gap-1.5 w-full">
                                <Check className="w-4 h-4" />
                                <span>Saved</span>
                            </div>
                        ) : 'Save Settings'}
                    </button>
                </div>
            </div>
        </div>
    );
}
