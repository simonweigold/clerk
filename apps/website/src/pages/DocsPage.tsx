import { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getDocsList, getDocContent, type DocItem } from '../lib/api';

export default function DocsPage() {
    return (
        <div className="flex h-full max-w-6xl mx-auto">
                <div className="md:hidden p-4 border-b border-border flex items-center justify-between">
                    <span className="font-semibold text-sm">Documentation Menu</span>
                    <button 
                        onClick={() => {
                            const sidebar = document.getElementById('docs-sidebar');
                            if (sidebar) sidebar.classList.toggle('hidden');
                        }}
                        className="p-2 bg-muted rounded-md hover:bg-muted/80 text-foreground"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                </div>
                <DocsSidebar />
                <div className="flex-1 px-4 md:px-10 py-8 overflow-y-auto bg-white">
                <Routes>
                    <Route path="/" element={<DocViewer slug="README" />} />
                    <Route path="*" element={<DocViewerWrapper />} />
                </Routes>
            </div>
        </div>
    );
}

function DocViewerWrapper() {
    // We use a splat route so this works for nested stuff like ui/overview
    const [slug, setSlug] = useState<string>('');
    const location = useLocation();

    useEffect(() => {
        // Remove leading "/docs/" from the pathname
        let path = location.pathname.replace(/^\/docs\/?/, '') || 'README';
        // Strip trailing .md if present to fix 404s
        if (path.endsWith('.md')) {
            path = path.slice(0, -3);
        }
        setSlug(path);
    }, [location.pathname]);

    if (!slug) return null;
    return <DocViewer slug={slug} />;
}

function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);
    return (
        <button
            onClick={() => {
                navigator.clipboard.writeText(text);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            }}
            className="absolute top-3 right-3 p-1.5 bg-white border border-slate-200 hover:bg-slate-100 rounded-md transition-colors text-slate-600 shadow-sm z-10 opacity-0 group-hover:opacity-100 focus:opacity-100 flex items-center gap-1.5"
            title="Copy code"
        >
            {copied ? (
                <>
                    <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                    <span className="text-xs font-medium text-emerald-700 pr-1">Copied!</span>
                </>
            ) : (
                <>
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                    <span className="text-xs font-medium pr-1">Copy</span>
                </>
            )}
        </button>
    );
}



function DocsSidebar() {
    const [docs, setDocs] = useState<DocItem[]>([]);
    const [loading, setLoading] = useState(true);
    const location = useLocation();

    useEffect(() => {
        getDocsList().then(res => {
            setDocs(res.docs || []);
            setLoading(false);
        }).catch(err => {
            console.error('Failed to load docs list', err);
            setLoading(false);
        });
    }, []);

    const isActive = (slug: string) => {
        let path = location.pathname.replace(/^\/docs\/?/, '') || 'README';
        if (path.endsWith('.md')) path = path.slice(0, -3);
        return path === slug;
    };

    if (loading) {
        return (
            <div className="w-64 border-r border-border pr-4 py-6 hidden md:block">
                <div className="animate-pulse space-y-4">
                    <div className="h-4 bg-muted rounded w-3/4"></div>
                    <div className="h-4 bg-muted rounded w-1/2"></div>
                    <div className="h-4 bg-muted rounded w-5/6"></div>
                </div>
            </div>
        );
    }

    const DIR_NAMES: Record<string, string> = {
        'cli': 'CLI Commands',
        'ui': 'UI Features',
        'user-guide': 'User Guide',
        'integration': 'Integration',
        'contributing': 'Contributing'
    };

    const groupedDocs: Record<string, DocItem[]> = {};
    docs.forEach(doc => {
        const parts = doc.slug.split('/');
        let dir = 'General';
        if (parts.length > 1) {
            const rawDir = parts[0];
            dir = DIR_NAMES[rawDir] || (rawDir.charAt(0).toUpperCase() + rawDir.slice(1));
        }
        if (!groupedDocs[dir]) groupedDocs[dir] = [];
        groupedDocs[dir].push(doc);
    });

    // Custom order - User-centric docs first
    const order = ['User Guide', 'Integration', 'Contributing', 'General', 'CLI Commands', 'UI Features'];
    const groups = Object.keys(groupedDocs).sort((a, b) => {
        const indexA = order.indexOf(a);
        const indexB = order.indexOf(b);
        if (indexA !== -1 && indexB !== -1) return indexA - indexB;
        if (indexA !== -1) return -1;
        if (indexB !== -1) return 1;
        return a.localeCompare(b);
    });

    return (
        <div id="docs-sidebar" className="w-full md:w-64 border-r border-border pr-6 py-6 hidden md:block overflow-y-auto bg-slate-50 md:bg-transparent px-4 md:px-0">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
                Documentation
            </h2>
            <nav className="space-y-6 text-sm">
                {groups.map(dir => (
                    <div key={dir}>
                        <h3 className="font-semibold text-foreground mb-2 px-3">{dir}</h3>
                        <div className="space-y-1">
                            {groupedDocs[dir].map(doc => (
                                <Link
                                    key={doc.slug}
                                    to={`/docs/${doc.slug === 'README' ? '' : doc.slug}`}
                                    className={`block px-3 py-2 rounded-md transition-colors ${
                                        isActive(doc.slug)
                                            ? 'bg-primary/10 text-primary font-medium'
                                            : 'text-foreground/70 hover:bg-muted hover:text-foreground'
                                    }`}
                                >
                                    {doc.title}
                                </Link>
                            ))}
                        </div>
                    </div>
                ))}
            </nav>
        </div>
    );
}

function DocViewer({ slug }: { slug: string }) {
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        setLoading(true);
        setError('');
        getDocContent(slug)
            .then(res => {
                setContent(res.content);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setError('Failed to load document.');
                setLoading(false);
            });
    }, [slug]);

    if (loading) {
        return (
            <div className="animate-pulse space-y-4 mt-8">
                <div className="h-8 bg-muted rounded w-1/3 mb-8"></div>
                <div className="h-4 bg-muted rounded w-full"></div>
                <div className="h-4 bg-muted rounded w-5/6"></div>
                <div className="h-4 bg-muted rounded w-4/5"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 bg-red-50 text-red-600 rounded-md border border-red-100 flex items-center gap-2 mt-8">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                {error}
            </div>
        );
    }

    return (
        <div className="prose prose-slate max-w-none prose-code:before:content-none prose-code:after:content-none">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    h1: ({node, ...props}) => <h1 className="!text-4xl !font-extrabold !tracking-tight text-black !mt-16 !mb-10 pb-2" {...props} />,
                    h2: ({node, ...props}) => <h2 className="!text-3xl !font-bold tracking-tight text-black !mt-14 !mb-8" {...props} />,
                    h3: ({node, ...props}) => <h3 className="!text-2xl !font-semibold tracking-tight text-black !mt-12 !mb-6" {...props} />,
                    p: ({node, ...props}) => <p className="leading-8 text-foreground !my-6 text-lg" {...props} />,
                    ul: ({node, ...props}) => <ul className="list-disc pl-8 !my-6 space-y-3 text-lg text-foreground" {...props} />,
                    ol: ({node, ...props}) => <ol className="list-decimal pl-8 !my-6 space-y-3 text-lg text-foreground" {...props} />,
                    li: ({node, ...props}) => <li className="leading-8" {...props} />,
                    table: ({ node, ...props }) => (
                        <div className="my-8 w-full overflow-y-auto">
                            <table className="w-full text-left border-collapse" {...props} />
                        </div>
                    ),
                    th: ({ node, ...props }) => (
                        <th className="border-b-2 border-slate-200 px-4 py-3 font-semibold text-slate-800" {...props} />
                    ),
                    td: ({ node, ...props }) => (
                        <td className="border-b border-slate-100 px-4 py-3 text-slate-600" {...props} />
                    ),
                    pre: ({ node, children, ...props }: any) => {
                        const extractText = (child: any): string => {
                            if (typeof child === 'string') return child;
                            if (Array.isArray(child)) return child.map(extractText).join('');
                            if (child && child.props && child.props.children) return extractText(child.props.children);
                            return '';
                        };
                        const codeText = extractText(children);
                        return (
                            <div className="relative group my-8">
                                <CopyButton text={codeText} />
                                <pre className="bg-slate-50 border border-slate-200 text-slate-900 p-5 rounded-xl overflow-x-auto font-mono text-sm leading-relaxed shadow-sm" {...props}>
                                    {children}
                                </pre>
                            </div>
                        );
                    },
                    code: ({ node, inline, ...props }: any) => {
                        if (inline) {
                            return <code className="text-primary bg-primary/5 border border-primary/10 px-1.5 py-0.5 rounded-md font-mono text-sm mx-0.5" {...props} />
                        }
                        return <code className="font-mono text-sm" {...props} />
                    },
                    a: ({ node, ...props }) => {
                        const href = props.href || '';
                        
                        // External links normal behavior
                        if (href.startsWith('http') || href.startsWith('mailto:')) {
                            return <a {...props} target="_blank" rel="noopener noreferrer" className="text-primary hover:text-primary/80 transition-colors underline underline-offset-4 decoration-primary/30 hover:decoration-primary" />;
                        }

                        // Internal hash
                        if (href.startsWith('#')) {
                            return <a {...props} className="text-primary hover:text-primary/80 transition-colors underline underline-offset-4 decoration-primary/30 hover:decoration-primary" />;
                        }

                        return (
                            <a
                                {...props}
                                className="text-primary hover:text-primary/80 transition-colors underline underline-offset-4 decoration-primary/30 hover:decoration-primary cursor-pointer"
                                onClick={(e) => {
                                    e.preventDefault();
                                    const basePath = `${window.location.origin}/docs/${slug === 'README' ? 'README' : slug}`;
                                    const url = new URL(href, basePath);
                                    let navPath = url.pathname.replace(/^\/docs\/?/, '');
                                    // if resolving up dir created double slashes remove them
                                    navPath = navPath.replace(/\/{2,}/g, '/');
                                    navigate(`/docs/${navPath}${url.search}${url.hash}`);
                                }}
                            >
                                {props.children}
                            </a>
                        );
                    }
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
