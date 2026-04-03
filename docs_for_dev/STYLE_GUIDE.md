# CLERK Frontend – Comprehensive Styling Guide

> A complete reference for reproducing the CLERK design system. This guide covers every visual decision in the frontend — from color tokens and typography to layout grids, component anatomy, animations, and interaction states — so that any developer can build a pixel-accurate implementation.

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Color System](#2-color-system)
3. [Typography](#3-typography)
4. [Spacing & Border Radius](#4-spacing--border-radius)

---

## 1. Design Philosophy

CLERK follows a **modern, premium aesthetic** that balances professionalism with contemporary design:

- **Sans-serif typography** — body text uses **Inter** for clarity and modern feel; the logo uses **Bodoni Moda SC** for editorial authority.
- **Clean white canvas** — white backgrounds with glassmorphism surfaces (backdrop-blur + translucent fills) for depth.
- **Soft shadows over borders** — components use subtle box-shadows and translucent backgrounds rather than hard borders.
- **Micro-animations** — cards lift on hover, buttons scale, grids stagger in, progress bars shimmer. All animations respect `prefers-reduced-motion`.
- **Generous sizing** — larger fonts (1rem base), taller inputs, bigger border-radii for a comfortable, spacious feel.

---

## 2. Color System

All colors are defined as CSS custom properties on `:root` and consumed via Tailwind's extended `colors` config.

### 2.1 Core Palette

| Token | Value | Usage |
|---|---|---|
| `--color-background` | `#ffffff` | Page & section backgrounds |
| `--color-foreground` | `#111418` | Primary text, headings |
| `--color-border` | `rgba(0,0,0,0.1)` | Dividers, section borders |
| `--color-muted` | `#f4f6f9` | Muted surface fill (hover states, sidebars) |
| `--color-muted-foreground` | `#6b7280` | Secondary text, placeholders, timestamps |

### 2.2 Brand / Primary

| Token | Value | Usage |
|---|---|---|
| `--color-primary` | `19 13 221` (RGB) → `#130DDD` | Logo, buttons, links, highlights |
| `--color-primary-foreground` | `255 255 255` (RGB) → `#ffffff` | Text on primary-colored surfaces |

### 2.3 Semantic Colors

| Token | Value | Usage |
|---|---|---|
| `--color-secondary` / `-foreground` | `#f4f6f9` / `#111418` | Secondary buttons, tags |
| `--color-destructive` / `-foreground` | `#ef4444` / `#ffffff` | Delete actions, error states |
| `--color-ring` | `rgba(19,13,221,0.18)` | Focus ring glow |

### 2.4 Shadows

| Token | Description |
|---|---|
| `--shadow-sm` | Subtle lift: `0 1px 2px rgba(0,0,0,0.04)` |
| `--shadow-md` | Card hover: `0 2px 8px rgba(0,0,0,0.06)` |
| `--shadow-lg` | Elevated panels: `0 4px 16px rgba(0,0,0,0.08)` |
| `--shadow-glow` | Primary glow: `0 4px 24px rgba(19,13,221,0.12)` |

---

## 3. Typography

### 3.1 Font Families

| Family | Font | Usage | Google Fonts |
|---|---|---|---|
| **Logo** | Bodoni Moda SC | `clerk-logo` class | `Bodoni+Moda+SC:ital,opsz,wght@0,6..96,400..900;1,6..96,400..900` |
| **Body / UI** | Inter | Default body font | `Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900` |

### 3.2 Logo Treatment

```css
.clerk-logo {
  font-family: 'Bodoni Moda SC', serif;
  font-size: 1.5rem;
  font-weight: 850;
  color: #130DDD;
  letter-spacing: 0.8em;
}
```

### 3.3 Size Scale

| Context | Size |
|---|---|
| Body text | `1rem` (16px) |
| Labels, inputs | `0.9375rem` (15px) |
| Small text | `0.875rem` (14px) |
| Extra small | `0.75rem` (12px) |
| Page headings | `text-3xl` – `text-4xl` |
| Section headings | `text-xl` – `text-2xl` |

### 3.4 Weight Usage

| Context | Weight |
|---|---|
| Body text | `400` (normal) |
| Labels, subtitles | `500` (medium) |
| Section headings | `600` (semibold) |
| Page titles, bold accents | `700` (bold) |
| Logo | `850` |

---

## 4. Spacing & Border Radius

### 4.1 Border Radius Tokens

| Token | Value | Usage |
|---|---|---|
| `--radius-sm` | `0.375rem` (6px) | Focus rings |
| `--radius-md` | `0.625rem` (10px) | Buttons, inputs |
| `--radius-lg` | `0.75rem` (12px) | Cards, step cards |
| `--radius-xl` | `1rem` (16px) | Glass cards, auth panels |
| `--radius-2xl` | `1.25rem` (20px) | Large panels |

Components use `rounded-md` or `rounded-lg` by default. The design embraces softer, larger radii for a friendly modern feel.
