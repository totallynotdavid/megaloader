# Docs

The [manual](https://totallynotdavid.github.io/megaloader) is a VitePress site.
Its pages are in `megaloader/`, and
[`megaloader/readme.md`](megaloader/readme.md) is their index.

```bash
mise run docs-serve   # bun install, then vitepress dev at http://localhost:5173
mise run docs-build   # output in megaloader/.vitepress/dist
```

Without mise, run `bun install` in this folder, then `bun run docs:dev` or
`bun run docs:build`. A build that finds a dead link exits 1 and prints
`[vitepress] N dead link(s) found.`

Format before committing:

```bash
mise run format-docs
mise run validate-snippets
```

`format-docs` runs biome on the Vue components and prettier on the Markdown.
`validate-snippets` checks that Python blocks parse. It skips blocks that
contain `...` and function signatures with no body.

A push to `main` that changes `apps/docs/` runs `.github/workflows/deploy.yml`.
It builds the site with `VITE_BASE=/megaloader/` and publishes it to GitHub
Pages. The live demo reads the API address from `VITE_API_URL`.
