import { useState, useEffect, useCallback } from 'react';

export interface DocManifest {
  generated_at: string;
  generated_at_human: string;
  source: string;
  files: string[];
}

export interface DocTimestamp {
  updated_at: string;
  updated_at_formatted: string;
}

export interface DocFile {
  path: string;
  content: string;
  title: string;
}

export interface DocSection {
  name: string;
  files: DocNavItem[];
}

export interface DocNavItem {
  path: string;
  title: string;
  section: string;
  /** True for README/index files — used by sidebar to make the section heading clickable */
  isIndex?: boolean;
}

// Maps directory names to human-readable section names
const DIR_NAMES: Record<string, string> = {
  'cli': 'CLI Commands',
  'ui': 'UI Features',
  'user-guide': 'User Guide',
  'integration': 'Integration',
  'contributing': 'Contributing',
  'deployment': 'Deployment',
};

// Desired section ordering — General always first
const SECTION_ORDER = ['General', 'User Guide', 'Integration', 'Deployment', 'Contributing', 'CLI Commands', 'UI Features'];

export function useDocs() {
  const [manifest, setManifest] = useState<DocManifest | null>(null);
  const [timestamp, setTimestamp] = useState<DocTimestamp | null>(null);
  const [currentDoc, setCurrentDoc] = useState<DocFile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [navigation, setNavigation] = useState<DocSection[]>([]);

  // Load manifest and timestamp
  useEffect(() => {
    const loadManifest = async () => {
      try {
        const [manifestRes, timestampRes] = await Promise.all([
          fetch('/docs/manifest.json'),
          fetch('/docs/timestamp.json'),
        ]);

        if (!manifestRes.ok || !timestampRes.ok) {
          throw new Error('Failed to load documentation metadata');
        }

        const manifestData = await manifestRes.json();
        const timestampData = await timestampRes.json();

        setManifest(manifestData);
        setTimestamp(timestampData);

        const sections = buildNavigation(manifestData.files);
        setNavigation(sections);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    loadManifest();
  }, []);

  // Load a specific doc file — path should be WITHOUT .md extension
  const loadDoc = useCallback(async (path: string) => {
    setLoading(true);
    // Normalize: strip any .md suffix before fetching so we don't double it
    const normalizedPath = path.replace(/\.md$/i, '');
    try {
      const response = await fetch(`/docs/${normalizedPath}.md`);
      if (!response.ok) {
        throw new Error(`Failed to load document: ${path}`);
      }
      const content = await response.text();
      const title = extractTitle(content) || formatTitle(normalizedPath.split('/').pop() || normalizedPath);

      setCurrentDoc({ path: normalizedPath, content, title });
      return { path: normalizedPath, content, title };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Find the index/README doc for a section
  const findSectionIndex = useCallback((sectionName: string): string | null => {
    const section = navigation.find(s => s.name.toLowerCase() === sectionName.toLowerCase());
    if (!section) return null;

    const indexFile = section.files.find(f =>
      f.path.toLowerCase().endsWith('readme') ||
      f.path.toLowerCase().endsWith('index')
    );
    return indexFile?.path || section.files[0]?.path || null;
  }, [navigation]);

  return {
    manifest,
    timestamp,
    currentDoc,
    navigation,
    loading,
    error,
    loadDoc,
    findSectionIndex,
  };
}

// Build navigation structure from file list
function buildNavigation(files: string[]): DocSection[] {
  const sections: Map<string, DocNavItem[]> = new Map();
  const rootFiles: DocNavItem[] = [];

  files.forEach(file => {
    // Paths in the manifest include .md — strip it for clean URLs
    const pathWithoutExt = file.replace(/\.md$/i, '');
    const parts = pathWithoutExt.split('/');

    if (parts.length === 1) {
      // Root level file — the README is the index for "General"
      const stem = parts[0];
      rootFiles.push({
        path: pathWithoutExt,
        title: formatRootTitle(stem),
        section: 'General',
        isIndex: stem.toLowerCase() === 'readme',
      });
    } else {
      // Nested file
      const dirKey = parts[0];
      const fileName = parts[parts.length - 1];
      const sectionName = DIR_NAMES[dirKey] || formatSectionName(dirKey);

      if (!sections.has(sectionName)) {
        sections.set(sectionName, []);
      }

      sections.get(sectionName)!.push({
        path: pathWithoutExt,
        title: formatFileTitle(fileName, dirKey),
        section: sectionName,
        isIndex: fileName.toLowerCase() === 'readme',
      });
    }
  });

  const result: DocSection[] = [];

  // Add root files first under "General"
  if (rootFiles.length > 0) {
    // README goes first inside General, then alphabetically
    rootFiles.sort((a, b) => {
      const aIsReadme = a.path.toLowerCase() === 'readme';
      const bIsReadme = b.path.toLowerCase() === 'readme';
      if (aIsReadme && !bIsReadme) return -1;
      if (!aIsReadme && bIsReadme) return 1;
      return a.title.localeCompare(b.title);
    });
    result.push({ name: 'General', files: rootFiles });
  }

  // Sort other sections by the preferred order, then alphabetically
  const sortedSections = Array.from(sections.entries()).sort((a, b) => {
    const indexA = SECTION_ORDER.indexOf(a[0]);
    const indexB = SECTION_ORDER.indexOf(b[0]);
    if (indexA !== -1 && indexB !== -1) return indexA - indexB;
    if (indexA !== -1) return -1;
    if (indexB !== -1) return 1;
    return a[0].localeCompare(b[0]);
  });

  sortedSections.forEach(([name, sectionFiles]) => {
    // README first, then alphabetically
    sectionFiles.sort((a, b) => {
      const aIsReadme = a.path.toLowerCase().endsWith('/readme');
      const bIsReadme = b.path.toLowerCase().endsWith('/readme');
      if (aIsReadme && !bIsReadme) return -1;
      if (!aIsReadme && bIsReadme) return 1;
      return a.title.localeCompare(b.title);
    });
    result.push({ name, files: sectionFiles });
  });

  return result;
}

// Format title for root-level files
function formatRootTitle(stem: string): string {
  if (stem.toLowerCase() === 'readme') return 'Introduction';
  return formatTitle(stem);
}

// Format title for a file inside a directory
function formatFileTitle(stem: string, dirKey: string): string {
  if (stem.toLowerCase() === 'readme') {
    // Use a short label based on the section, e.g. "User Guide" → "Overview"
    const sectionName = DIR_NAMES[dirKey] || formatSectionName(dirKey);
    return sectionName + ' Overview';
  }
  return formatTitle(stem);
}

// Format filename stem to a display title
function formatTitle(stem: string): string {
  const spaced = stem.replace(/[-_]/g, ' ');
  return spaced
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

// Format directory name to a section title
function formatSectionName(name: string): string {
  const spaced = name.replace(/[-_]/g, ' ');
  return spaced
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

// Extract title from markdown content
function extractTitle(content: string): string | null {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : null;
}
