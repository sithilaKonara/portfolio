import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://yourdomain.com',
  compressHTML: true,
  build: {
    assets: '_assets',
  },
});
