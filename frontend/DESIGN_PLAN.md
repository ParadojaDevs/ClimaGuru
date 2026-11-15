# ClimaGuru Admin Panel - Design Plan

## Subject Matter
ClimaGuru is a weather/climate monitoring platform. The admin panel manages user access to climate data, forecasting tools, and meteorological dashboards. The design should evoke: atmospheric science, weather stations, radar displays, climate data visualization.

## Color Palette (4-6 named hex values)

| Name | Hex | Usage |
|------|-----|-------|
| `atmosphere-deep` | `#0B1D3A` | Primary background - deep atmospheric pressure |
| `atmosphere-mid` | `#142D4E` | Panel/card backgrounds - mid-level atmosphere |
| `atmosphere-surface` | `#1E3A5F` | Elevated surfaces, hover states |
| `sky-horizon` | `#3A8FD6` | Primary accent - clear sky blue |
| `storm-front` | `#5B9BD5` | Secondary accent - approaching storm |
| `radar-active` | `#00D4AA` | Active/success states - radar returns |
| `warning-amber` | `#F5A623` | Warning states - weather alerts |
| `lightning` | `#FFFFFF` | Text on dark surfaces |
| `cloud-mist` | `#8FA3BF` | Muted text, disabled states |
| `pressure-line` | `#2A4A6B` | Borders, dividers - isobar lines |

## Typography

**Primary: "Space Grotesk"** - Technical, geometric sans-serif used in scientific displays and weather station readouts. Variable font for weight flexibility.

**Secondary: "JetBrains Mono"** - Monospace for data values (IDs, timestamps, coordinates) - evokes terminal/weather station output.

**Type Scale:**
- Display: `clamp(2.5rem, 5vw, 4rem)` / weight 600 / letter-spacing -0.02em
- H1: `clamp(1.75rem, 3vw, 2.5rem)` / weight 500
- H2: `clamp(1.25rem, 2vw, 1.5rem)` / weight 500
- H3: `1rem` / weight 600 / uppercase / letter-spacing 0.05em (section labels only)
- Body: `1rem` / weight 400 / line-height 1.6
- Small: `0.875rem` / weight 400 / line-height 1.5
- Data: `0.875rem` / JetBrains Mono / tabular-nums

## Layout Concept

**Weather Station Dashboard** - Not a generic card grid. The layout mirrors a meteorological workstation:

```
┌─────────────────────────────────────────────────────────────┐
│  CLIMAGURU                                    [User] [Logout] │  ← Top bar: station identifier
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │   CONTROL PANEL     │  │   ACTIVE READINGS           │  │  ← Asymmetric split
│  │   (User Form)       │  │   (User List)               │  │     35% / 65%
│  │                     │  │                             │  │
│  │  [Form Fields]      │  │  ┌─────────────────────┐   │  │
│  │                     │  │  │  Data Table         │   │  │
│  │  [Actions]          │  │  │  (monospace data)   │   │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Alignment:** Left-aligned content (like instrument readouts), data right-aligned in tables.

**Responsive:** Stack vertically on mobile, control panel collapses to accordion.

## Principles

1. **Instrument Aesthetic** - Every element feels like a weather station component: precise, functional, calibrated. No decorative shadows, no rounded corners on data surfaces.

2. **Data as Hero** - The user list is a readings table. Monospace for values, clear hierarchy. No "card" metaphor.

3. **Atmospheric Depth** - Layered dark backgrounds (atmosphere-deep → mid → surface) create depth like atmospheric pressure layers. No flat white cards.

4. **Deliberate Motion** - One page-load sequence: panels slide in from left/right like radar sweeps. No per-element fade-ups.

5. **Technical Clarity** - Copy is direct: "Station Access" not "User Management". "Active Readings" not "User List". "Log Entry" not "Create User".

6. **Restraint** - One accent color (sky-horizon) for primary actions. radar-active only for live/success states. warning-amber only for destructive actions.

## What We're Avoiding (Generic Defaults)

- ❌ White/cream cards with soft shadows (SaaS-card kit)
- ❌ Rounded corners on everything (12px everywhere)
- ❌ Gradient washes as decoration
- ❌ ALL-CAPS eyebrow labels above headings
- ❌ Middle-dot meta strings ("A · B · C")
- ❌ Spaced em-dash labels ("WORD — fragment")
- ❌ Tinted near-black (#0B0B0B) standing in for black
- ❌ Monospace for small labels only (use it for DATA)
- ❌ "→" appended to button text
- ❌ Scattered hover transitions on every element