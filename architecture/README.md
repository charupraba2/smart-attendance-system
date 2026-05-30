Architecture diagram (Mermaid) and quick export instructions

Files:
- architecture.mmd — Mermaid source diagram

Render to SVG/PNG (option A: mermaid-cli)

1. Install Node.js/npm if needed, then install mermaid-cli:

```powershell
npm install -g @mermaid-js/mermaid-cli
```

2. Render SVG (from the `architecture` folder):

```powershell
mmdc -i architecture.mmd -o architecture.svg
```

Render PNG:

```powershell
mmdc -i architecture.mmd -o architecture.png
```

Option B: VS Code
- Install "Markdown Preview Mermaid Support" or "Mermaid Preview" extension.
- Open `architecture.mmd` and preview; use extension to export.

Notes
- The source file is: `architecture/architecture.mmd`.
- If you want, I can attempt to render `architecture.svg` here (requires `npm` + `@mermaid-js/mermaid-cli`).