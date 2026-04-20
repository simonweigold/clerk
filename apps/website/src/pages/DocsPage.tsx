import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useDocs } from '../hooks/useDocs';

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
          <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-xs font-medium text-emerald-700 pr-1">Copied!</span>
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <span className="text-xs font-medium pr-1">Copy</span>
        </>
      )}
    </button>
  );
}

/** Convert React children to plain text for generating heading IDs */
function nodeToText(node: any): string {
  if (typeof node === 'string') return node;
  if (typeof node === 'number') return String(node);
  if (Array.isArray(node)) return node.map(nodeToText).join('');
  if (node?.props?.children) return nodeToText(node.props.children);
  return '';
}

/** Generate a GitHub-style anchor ID from heading text */
function toHeadingId(children: any): string {
  return nodeToText(children)
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim();
}

export default function DocsPage() {
  const { '*': urlPath } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { navigation, currentDoc, timestamp, loading, error, loadDoc } = useDocs();

  // Load the doc whenever the URL path changes
  useEffect(() => {
    if (urlPath) {
      loadDoc(urlPath);
    } else if (navigation.length > 0) {
      // Default to the index file of the first section
      const firstDoc = navigation[0]?.files.find(f => f.isIndex) ?? navigation[0]?.files[0];
      if (firstDoc) {
        navigate(`/docs/${firstDoc.path}`, { replace: true });
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlPath, navigation]);

  // Scroll to top on doc change, or to the anchor if there's a hash
  useEffect(() => {
    if (loading || !currentDoc) return;
    const hash = location.hash;
    if (hash) {
      setTimeout(() => {
        const el = document.getElementById(hash.slice(1));
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 50);
    } else {
      window.scrollTo(0, 0);
    }
  }, [currentDoc?.path, loading, location.hash]);

  const isActive = (filePath: string) => {
    const current = location.pathname.replace(/^\/docs\/?/, '');
    return current === filePath;
  };

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-600 rounded-md border border-red-100 flex items-center gap-2 mt-8 max-w-6xl mx-auto">
        <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        {error}
      </div>
    );
  }

  const linkClass = 'text-primary hover:text-primary/80 transition-colors underline underline-offset-4 decoration-primary/30 hover:decoration-primary';

  return (
    <div className="flex h-full max-w-6xl mx-auto">
      {/* Mobile header */}
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

      {/* Sidebar */}
      <div
        id="docs-sidebar"
        className="w-full md:w-64 border-r border-border pr-6 py-6 hidden md:block overflow-y-auto bg-slate-50 md:bg-transparent px-4 md:px-0"
      >
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
          Documentation
        </h2>
        <nav className="space-y-6 text-sm">
          {navigation.map((section) => {
            // Find the index file (README) for this section — used as the section heading link
            const indexFile = section.files.find(f => f.isIndex);
            const visibleFiles = indexFile
              ? section.files.filter(f => !f.isIndex)
              : section.files;

            return (
              <div key={section.name}>
                {indexFile ? (
                  <Link
                    to={`/docs/${indexFile.path}`}
                    className={`block font-semibold mb-2 px-3 transition-colors hover:text-primary ${
                      isActive(indexFile.path) ? 'text-primary' : 'text-foreground'
                    }`}
                  >
                    {section.name}
                  </Link>
                ) : (
                  <h3 className="font-semibold text-foreground mb-2 px-3">{section.name}</h3>
                )}
                {visibleFiles.length > 0 && (
                  <div className="space-y-1">
                    {visibleFiles.map((file) => (
                      <Link
                        key={file.path}
                        to={`/docs/${file.path}`}
                        className={`block px-3 py-2 rounded-md transition-colors ${
                          isActive(file.path)
                            ? 'bg-primary/10 text-primary font-medium'
                            : 'text-foreground/70 hover:bg-muted hover:text-foreground'
                        }`}
                      >
                        {file.title}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </div>

      {/* Main content */}
      <div id="docs-content" className="flex-1 px-4 md:px-10 py-8 overflow-y-auto bg-white">
        {loading && !currentDoc ? (
          <div className="animate-pulse space-y-4 mt-8">
            <div className="h-8 bg-muted rounded w-1/3 mb-8"></div>
            <div className="h-4 bg-muted rounded w-full"></div>
            <div className="h-4 bg-muted rounded w-5/6"></div>
            <div className="h-4 bg-muted rounded w-4/5"></div>
          </div>
        ) : currentDoc ? (
          <>
            <div className="prose prose-slate max-w-none prose-code:before:content-none prose-code:after:content-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ node, children, ...props }) => {
                    const id = toHeadingId(children);
                    return <h1 id={id} className="!text-4xl !font-extrabold !tracking-tight text-black !mt-16 !mb-10 pb-2" {...props}>{children}</h1>;
                  },
                  h2: ({ node, children, ...props }) => {
                    const id = toHeadingId(children);
                    return <h2 id={id} className="!text-3xl !font-bold tracking-tight text-black !mt-14 !mb-8" {...props}>{children}</h2>;
                  },
                  h3: ({ node, children, ...props }) => {
                    const id = toHeadingId(children);
                    return <h3 id={id} className="!text-2xl !font-semibold tracking-tight text-black !mt-12 !mb-6" {...props}>{children}</h3>;
                  },
                  p: ({ node, ...props }) => (
                    <p className="leading-8 text-foreground !my-6 text-lg" {...props} />
                  ),
                  ul: ({ node, ...props }) => (
                    <ul className="list-disc pl-8 !my-6 space-y-3 text-lg text-foreground" {...props} />
                  ),
                  ol: ({ node, ...props }) => (
                    <ol className="list-decimal pl-8 !my-6 space-y-3 text-lg text-foreground" {...props} />
                  ),
                  li: ({ node, ...props }) => <li className="leading-8" {...props} />,
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
                  blockquote: ({ node, ...props }) => (
                    <blockquote className="border-l-4 border-primary pl-4 italic text-muted-foreground my-6" {...props} />
                  ),
                  hr: () => <hr className="my-8 border-slate-200" />,
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
                        <pre
                          className="bg-slate-50 border border-slate-200 text-slate-900 p-5 rounded-xl overflow-x-auto font-mono text-sm leading-relaxed shadow-sm"
                          {...props}
                        >
                          {children}
                        </pre>
                      </div>
                    );
                  },
                  code: ({ node, inline, ...props }: any) => {
                    if (inline) {
                      return (
                        <code
                          className="text-primary bg-primary/5 border border-primary/10 px-1.5 py-0.5 rounded-md font-mono text-sm mx-0.5"
                          {...props}
                        />
                      );
                    }
                    return <code className="font-mono text-sm" {...props} />;
                  },
                  a: ({ node, ...props }) => {
                    const href = props.href || '';

                    // External links open in new tab
                    if (href.startsWith('http') || href.startsWith('mailto:')) {
                      return (
                        <a
                          {...props}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={linkClass}
                        />
                      );
                    }

                    // Hash-only links: scroll to heading within the current page
                    if (href.startsWith('#')) {
                      return (
                        <a
                          {...props}
                          className={`${linkClass} cursor-pointer`}
                          onClick={(e) => {
                            e.preventDefault();
                            const id = href.slice(1);
                            const el = document.getElementById(id);
                            if (el) el.scrollIntoView({ behavior: 'smooth' });
                            navigate(`${location.pathname}${href}`, { replace: true });
                          }}
                        />
                      );
                    }

                    // Internal doc links: resolve relative path and navigate
                    return (
                      <a
                        {...props}
                        className={`${linkClass} cursor-pointer`}
                        onClick={(e) => {
                          e.preventDefault();
                          const currentPath = currentDoc?.path || 'README';
                          const basePath = `${window.location.origin}/docs/${currentPath}`;
                          const url = new URL(href, basePath);
                          let navPath = url.pathname.replace(/^\/docs\/?/, '');
                          navPath = navPath.replace(/\/{2,}/g, '/');
                          if (navPath.endsWith('.md')) navPath = navPath.slice(0, -3);
                          navigate(`/docs/${navPath}${url.search}${url.hash}`);
                        }}
                      />
                    );
                  },
                }}
              >
                {currentDoc.content}
              </ReactMarkdown>
            </div>

            {/* Timestamp footer */}
            {timestamp && (
              <div className="mt-12 pt-6 border-t border-border">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Documentation last updated: {timestamp.updated_at_formatted}</span>
                </div>
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
