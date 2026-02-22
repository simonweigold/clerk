import React, { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import type { Resource, Step } from '../lib/api';

interface PromptTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
    resources: Resource[];
    steps: Step[];
    value: string;
    onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}

interface Suggestion {
    id: string; // the string to insert, e.g. "resource_1" or "workflow_1"
    displayName: string;
    type: 'resource' | 'step';
}

function getCaretCoordinates(element: HTMLTextAreaElement, position: number) {
    const div = document.createElement('div');
    const style = div.style;
    const computed = window.getComputedStyle(element);

    style.whiteSpace = 'pre-wrap';
    style.wordWrap = 'break-word';
    style.position = 'absolute';
    style.visibility = 'hidden';

    const properties = [
        'direction', 'boxSizing', 'width', 'height', 'overflowX', 'overflowY',
        'borderTopWidth', 'borderRightWidth', 'borderBottomWidth', 'borderLeftWidth',
        'borderStyle', 'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft',
        'fontStyle', 'fontVariant', 'fontWeight', 'fontStretch', 'fontSize',
        'fontSizeAdjust', 'lineHeight', 'fontFamily', 'textAlign', 'textTransform',
        'textIndent', 'textDecoration', 'letterSpacing', 'wordSpacing', 'tabSize', 'MozTabSize'
    ];

    properties.forEach(prop => {
        style[prop as any] = computed[prop as any];
    });

    div.textContent = element.value.substring(0, position);

    const span = document.createElement('span');
    span.textContent = element.value.substring(position) || '.';
    div.appendChild(span);

    document.body.appendChild(div);
    const coordinates = {
        top: span.offsetTop + parseInt(computed.borderTopWidth || '0', 10),
        left: span.offsetLeft + parseInt(computed.borderLeftWidth || '0', 10),
        height: parseInt(computed.lineHeight || '20', 10)
    };
    document.body.removeChild(div);
    return coordinates;
}

export function PromptTextarea({ resources, steps, value, onChange, ...props }: PromptTextareaProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [isOpen, setIsOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [startIndex, setStartIndex] = useState(-1);

    const allSuggestions: Suggestion[] = [
        ...resources.map(r => ({
            id: `resource_${r.number}`,
            displayName: r.display_name || r.filename || `Resource ${r.number}`,
            type: 'resource' as const
        })),
        ...steps.map(s => ({
            id: `workflow_${s.number}`,
            displayName: s.display_name || `Step ${s.number}`,
            type: 'step' as const
        }))
    ];

    const filteredSuggestions = allSuggestions.filter(s =>
        s.id.toLowerCase().includes(query.toLowerCase()) ||
        s.displayName.toLowerCase().includes(query.toLowerCase())
    );

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        onChange(e);

        const el = e.target;
        const cursor = el.selectionStart;
        const textBeforeCursor = el.value.substring(0, cursor);

        const lastBraceIndex = textBeforeCursor.lastIndexOf('{');
        const lastCloseBraceIndex = textBeforeCursor.lastIndexOf('}');
        const lastSpaceIndex = textBeforeCursor.lastIndexOf(' ', cursor - 1);
        const lastNewlineIndex = textBeforeCursor.lastIndexOf('\n', cursor - 1);

        // check if '{' is the most recent boundary we opened
        if (lastBraceIndex !== -1 && lastBraceIndex > lastCloseBraceIndex) {
            // make sure there's no space or newline after the '{'
            if (lastSpaceIndex < lastBraceIndex && lastNewlineIndex < lastBraceIndex) {
                const currentQuery = textBeforeCursor.substring(lastBraceIndex + 1);
                const coords = getCaretCoordinates(el, cursor);
                // offset by small padding if needed, but getCaretCoordinates usually factors in padding
                setMenuPosition({ top: coords.top + coords.height, left: coords.left });
                setQuery(currentQuery);
                setStartIndex(lastBraceIndex);
                setIsOpen(true);
                setSelectedIndex(0);
                return;
            }
        }
        setIsOpen(false);
    };

    const insertSuggestion = (suggestion: Suggestion) => {
        if (!textareaRef.current) return;
        const el = textareaRef.current;
        const before = value.substring(0, startIndex);
        const after = value.substring(el.selectionStart);

        const newValue = `${before}{${suggestion.id}}${after}`;

        // Create synthetic event
        const event = {
            target: { value: newValue }
        } as React.ChangeEvent<HTMLTextAreaElement>;

        onChange(event);
        setIsOpen(false);

        // Restore focus and cursor pos
        setTimeout(() => {
            if (textareaRef.current) {
                const newCursorPos = startIndex + suggestion.id.length + 2;
                textareaRef.current.setSelectionRange(newCursorPos, newCursorPos);
                textareaRef.current.focus();
            }
        }, 0);
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (!isOpen) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex(prev => (prev + 1) % filteredSuggestions.length);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex(prev => (prev - 1 + filteredSuggestions.length) % filteredSuggestions.length);
        } else if (e.key === 'Enter' || e.key === 'Tab') {
            if (filteredSuggestions.length > 0) {
                e.preventDefault();
                insertSuggestion(filteredSuggestions[selectedIndex]);
            }
        } else if (e.key === 'Escape') {
            setIsOpen(false);
        }
    };

    // Close on click outside
    useEffect(() => {
        const handleClickOutside = () => setIsOpen(false);
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, []);

    return (
        <div className="relative w-full" onClick={e => e.stopPropagation()}>
            <textarea
                ref={textareaRef}
                value={value}
                onChange={handleInput}
                onKeyDown={handleKeyDown}
                {...props}
            />
            {isOpen && filteredSuggestions.length > 0 && (
                <ul
                    className="absolute z-50 bg-background border border-border rounded-md shadow-lg overflow-hidden py-1"
                    style={{
                        top: menuPosition.top,
                        left: menuPosition.left,
                        maxHeight: '200px',
                        overflowY: 'auto',
                        minWidth: '220px',
                        background: 'var(--color-background)',
                        borderColor: 'var(--color-border)'
                    }}
                >
                    {filteredSuggestions.map((suggestion, index) => (
                        <li
                            key={suggestion.id}
                            className="px-3 py-1.5 text-sm cursor-pointer flex flex-col"
                            style={{
                                backgroundColor: index === selectedIndex ? 'var(--color-muted)' : 'transparent'
                            }}
                            onClick={() => insertSuggestion(suggestion)}
                            onMouseEnter={() => setSelectedIndex(index)}
                        >
                            <span className="font-medium">{suggestion.displayName}</span>
                            <span className="text-xs text-muted-foreground font-mono" style={{ opacity: 0.8 }}>{`{${suggestion.id}}`}</span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
