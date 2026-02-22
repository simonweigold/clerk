import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { listKits, searchKits, toggleBookmark, type Kit } from '../lib/api';
import { useAuth } from '../hooks/useAuth';

/* ── Icons ─────────────────────────────────────────────────────────────── */

function GlobeIcon({ className = 'w-3.5 h-3.5' }: { className?: string }) {
    return (
        <svg className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418"
            />
        </svg>
    );
}

function UserIcon({ className = 'w-3.5 h-3.5' }: { className?: string }) {
    return (
        <svg className={className} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
            />
        </svg>
    );
}

function BookmarkIcon({ filled = false, className = 'w-4 h-4' }: { filled?: boolean; className?: string }) {
    return (
        <svg className={className} viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" fill={filled ? 'currentColor' : 'none'}>
            <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z"
            />
        </svg>
    );
}

/* ── Kit Card ──────────────────────────────────────────────────────────── */

function KitCard({
    kit,
    userId,
    onToggleBookmark,
}: {
    kit: Kit;
    userId?: string;
    onToggleBookmark?: (slug: string) => void;
}) {
    const isOwn = userId != null && kit.owner_id === userId;
    const isSaved = !isOwn && kit.is_bookmarked === true;

    const handleBookmarkClick = (e: React.MouseEvent) => {
        e.preventDefault(); // Don't navigate to kit detail
        e.stopPropagation();
        onToggleBookmark?.(kit.slug);
    };

    return (
        <Link to={`/kit/${kit.slug}`} className="card card-hoverable p-5 flex flex-col">
            <h3 className="text-lg font-semibold text-foreground mb-1 tracking-tight">
                {kit.name}
            </h3>
            {kit.description && (
                <p className="text-sm text-muted-foreground line-clamp-2">{kit.description}</p>
            )}
            <div className="flex items-center gap-2 mt-auto pt-3">
                {isOwn ? (
                    <span className="kit-owner-indicator kit-owner-mine" title="Your kit">
                        <UserIcon />
                        Yours
                    </span>
                ) : isSaved ? (
                    <span className="kit-owner-indicator kit-owner-saved" title="Saved to My Kits">
                        <BookmarkIcon filled className="w-3.5 h-3.5" />
                        Saved
                    </span>
                ) : (
                    <span className="kit-owner-indicator kit-owner-community" title="Community kit">
                        <GlobeIcon />
                        Community
                    </span>
                )}
                {kit.version_number && (
                    <span className="badge badge-primary">v{kit.version_number}</span>
                )}

                {/* Bookmark button — only for non-owned kits when logged in */}
                {userId && !isOwn && (
                    <button
                        type="button"
                        className={`kit-bookmark-btn${kit.is_bookmarked ? ' active' : ''}`}
                        onClick={handleBookmarkClick}
                        title={kit.is_bookmarked ? 'Remove from My Kits' : 'Save to My Kits'}
                    >
                        <BookmarkIcon filled={kit.is_bookmarked === true} className="w-4 h-4" />
                    </button>
                )}
            </div>
        </Link>
    );
}

/* ── Home Page ─────────────────────────────────────────────────────────── */

export default function HomePage() {
    const { user } = useAuth();
    const [kits, setKits] = useState<Kit[]>([]);
    const [loading, setLoading] = useState(true);       // initial full-page load
    const [refreshing, setRefreshing] = useState(false); // background refresh (subtle)
    const [query, setQuery] = useState('');
    const [filter, setFilter] = useState<'all' | 'mine'>('all');
    const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

    // Client-side cache: avoids re-fetching when toggling back
    const cacheRef = useRef<Record<string, Kit[]>>({});

    const cacheKey = (q: string, f: string) => `${f}:${q}`;

    // Initial load
    useEffect(() => {
        listKits()
            .then((data) => {
                setKits(data.kits);
                cacheRef.current[cacheKey('', 'all')] = data.kits;
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    // Fetch kits — uses cache if available, otherwise fetches with subtle loading
    const fetchKits = async (q: string, f: 'all' | 'mine') => {
        const key = cacheKey(q, f);

        // Instant switch if cached
        const cached = cacheRef.current[key];
        if (cached) {
            setKits(cached);
            // Still refresh in background (silent, no loading indicator)
            try {
                const data = q.trim() || f === 'mine'
                    ? await searchKits(q, f)
                    : await listKits();
                cacheRef.current[key] = data.kits;
                setKits(data.kits);
            } catch { /* silent */ }
            return;
        }

        // Not cached — show subtle refresh indicator
        setRefreshing(true);
        try {
            const data = q.trim() || f === 'mine'
                ? await searchKits(q, f)
                : await listKits();
            cacheRef.current[key] = data.kits;
            setKits(data.kits);
        } catch (err) {
            console.error(err);
        } finally {
            setRefreshing(false);
        }
    };

    const handleSearch = (value: string) => {
        setQuery(value);
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => fetchKits(value, filter), 300);
    };

    const handleFilterChange = (f: 'all' | 'mine') => {
        if (f === filter) return; // no-op if already on this tab
        setFilter(f);
        fetchKits(query, f);
    };

    const handleToggleBookmark = async (slug: string) => {
        try {
            const result = await toggleBookmark(slug);
            if (result.ok) {
                // Update the kit in current list
                setKits((prev) =>
                    prev.map((k) =>
                        k.slug === slug ? { ...k, is_bookmarked: result.is_bookmarked } : k
                    )
                );
                // Invalidate cache so next fetch gets fresh data
                cacheRef.current = {};
            }
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="fade-in">
            {/* Platform intro */}
            <div className="mb-12">
                <h1 className="text-4xl font-bold text-foreground mb-3 tracking-tight">
                    CLERK
                </h1>
                <p className="text-muted-foreground text-base max-w-xl leading-relaxed">
                    Community Library of Executable Reasoning Kits. Create, manage, and share
                    multi-step LLM reasoning workflows. Each kit defines a sequence of prompts
                    that build on each other, turning complex reasoning into reproducible
                    pipelines.
                </p>
                <p className="text-muted-foreground text-base max-w-xl leading-relaxed mt-2">
                    Kits can be public or private.{' '}
                    <Link
                        to="/auth/signup"
                        className="text-primary hover:underline font-medium"
                    >
                        Sign up
                    </Link>{' '}
                    to create and manage your own kits.
                </p>
            </div>

            {/* Page header */}
            <div className="flex items-end justify-between mb-8">
                <div>
                    <h2 className="text-2xl font-semibold text-foreground tracking-tight">
                        Reasoning Kits
                    </h2>
                    <p className="text-muted-foreground mt-1">
                        Browse and run executable reasoning workflows
                    </p>
                </div>
                {user && (
                    <Link to="/kit/new" className="btn btn-primary">
                        <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 4v16m8-8H4"
                            />
                        </svg>
                        New Kit
                    </Link>
                )}
            </div>

            {/* Search & filter row */}
            <div className="flex items-center gap-4 mb-8 flex-wrap">
                <input
                    type="search"
                    placeholder="Search kits..."
                    className="input max-w-md"
                    value={query}
                    onChange={(e) => handleSearch(e.target.value)}
                />

                {user && (
                    <div className="kit-filter-toggle ml-auto">
                        <button
                            type="button"
                            className={`kit-filter-btn${filter === 'all' ? ' active' : ''}`}
                            onClick={() => handleFilterChange('all')}
                        >
                            <GlobeIcon />
                            All Kits
                        </button>
                        <button
                            type="button"
                            className={`kit-filter-btn${filter === 'mine' ? ' active' : ''}`}
                            onClick={() => handleFilterChange('mine')}
                        >
                            <UserIcon />
                            My Kits
                        </button>
                    </div>
                )}
            </div>

            {/* Kit grid */}
            {loading ? (
                <div className="empty-state">
                    <div className="flex items-center justify-center gap-2">
                        <span className="pulse-dot" />
                        <span className="pulse-dot" />
                        <span className="pulse-dot" />
                    </div>
                </div>
            ) : kits.length === 0 && !refreshing ? (
                <div className="empty-state">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="48"
                        height="48"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                    </svg>
                    <p className="text-lg mb-1 font-medium">No kits found</p>
                    <p className="text-sm">
                        {query
                            ? 'Try a different search term.'
                            : filter === 'mine'
                                ? 'You haven\u2019t created or saved any kits yet.'
                                : 'Create your first reasoning kit to get started.'}
                    </p>
                </div>
            ) : refreshing && kits.length === 0 ? (
                <div className="empty-state">
                    <div className="flex items-center justify-center gap-2">
                        <span className="pulse-dot" />
                        <span className="pulse-dot" />
                        <span className="pulse-dot" />
                    </div>
                </div>
            ) : (
                <div
                    className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-children"
                    style={{
                        opacity: refreshing ? 0.5 : 1,
                        transition: 'opacity 0.15s ease',
                    }}
                >
                    {kits.map((kit) => (
                        <KitCard
                            key={kit.slug}
                            kit={kit}
                            userId={user?.id}
                            onToggleBookmark={handleToggleBookmark}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
