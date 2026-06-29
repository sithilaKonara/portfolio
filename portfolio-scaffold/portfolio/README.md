# SRE_CORE Portfolio

Personal portfolio — built with Astro, styled with design tokens from the Obsidian Terminal design system.

## Stack
- **Frontend:** Astro (static, zero JS by default)
- **Styling:** Plain CSS with custom properties (tokens.css)
- **Animations:** Motion One (add as needed per component)
- **Medium posts:** GitHub Actions cron → posts.json → Astro reads at build time
- **Hosting:** Cloudflare Pages (free tier)

## Local dev

```bash
npm install
npm run dev        # http://localhost:4321
npm run build      # outputs to dist/
npm run preview    # preview the build locally
```

## Medium RSS setup

1. Go to your GitHub repo → **Settings → Secrets → Actions**
2. Add a secret: `MEDIUM_USERNAME` = your Medium handle (without @)
3. The workflow at `.github/workflows/fetch-posts.yml` runs daily at 06:00 UTC
4. To trigger manually: **Actions → Fetch Medium Posts → Run workflow**

## Cloudflare Pages deploy

1. Push this repo to GitHub
2. Go to [Cloudflare Pages](https://pages.cloudflare.com/) → Create project → Connect to Git
3. Select your repo
4. Set build settings:
   - **Framework preset:** Astro
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
5. Deploy — every git push auto-deploys. Every posts.json commit triggers a rebuild.

## Project structure

```
src/
  pages/          ← index.astro, experience.astro, articles.astro, projects.astro, contact.astro
  layouts/        ← Base.astro (navbar + footer shell)
  components/     ← reusable .astro components
  styles/
    tokens.css    ← ALL design tokens (colors, type, spacing, components)
  data/
    posts.json    ← auto-updated by GitHub Actions
public/           ← static assets (favicon, og-image, etc)
.github/
  workflows/
    fetch-posts.yml
```

## Adding a new page

```astro
---
import Base from '../layouts/Base.astro';
---
<Base title="Page Title">
  <!-- your content here, tokens.css is already loaded -->
</Base>
```

## Design tokens quick reference

```css
/* Colors */
var(--c-cyan)        /* Electric Cyan — primary interactive */
var(--c-green)       /* Neon Green — success/OK */
var(--c-purple)      /* Circuit Purple — decorative */
var(--color-on-surface)          /* primary text */
var(--color-on-surface-variant)  /* muted text */

/* Typography classes */
.text-display    /* 48px / 800 weight */
.text-headline   /* 24px / 600 weight */
.text-body-lg    /* 18px body */
.text-mono       /* JetBrains Mono 14px */
.text-label      /* Mono 12px / all-caps / tracked */

/* Components */
.terminal-card   /* glassmorphic container */
.btn.btn-primary /* solid cyan CTA */
.btn.btn-ghost   /* outline cyan */
.chip            /* sharp-rect tech tag */
.status-badge    /* pulsing dot + label */
```
