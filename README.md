# Portfolio

This repository is a personal portfolio website built with Astro, Tailwind CSS, and TypeScript.

## Features

- Static site built with Astro
- Tailwind CSS for styling
- Interactive components in `src/components`
- Scripts for development and production builds

## Requirements

- Node.js 18+ (recommended)
- npm or yarn

## Local development

1. Install dependencies

```bash
npm install
```

2. Start the dev server

```bash
npm run dev
```

3. Open the site at `http://localhost:3000`

## Build for production

```bash
npm run build
npm run preview
```

## Project structure

```
astro.config.mjs
package.json
postcss.config.js
tailwind.config.js
tsconfig.json
public/
  terminal.js
  styles/
    tokens.css
scripts/
  fetch-github.py
src/
  env.d.ts
  components/
    Footer.astro
    GlassPanel.astro
    InteractiveTerminal.astro
    Navigation.astro
    StatusBadge.astro
    TerminalHeader.astro
  data/
    github-stats.json
    posts.json
    repos.json
  layouts/
    Layout.astro
  pages/
    articles.astro
    contact.astro
    experience.astro
    index.astro
```

- `src/` – site source (pages, layouts, components)
- `public/` – static assets
- `scripts/` – helper scripts
- `package.json` – scripts and dependencies

## Contributing

Fixes and improvements are welcome. Open an issue or submit a PR.

## License

This project is provided "as-is". Add a license if desired.

## Contact

Created by Sithila.
