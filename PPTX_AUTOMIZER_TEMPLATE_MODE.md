# PPTX Automizer Template Mode

This branch switches export from browser-side `PptxGenJS` to backend-side `pptx-automizer` so the application can build presentations from a real `.pptx` template.

## Flow

1. User uploads a source document.
2. Backend converts it to text/markdown.
3. Backend generates structured slide JSON.
4. Frontend previews/edit slides as JSON.
5. Export button sends slides back to backend.
6. Backend launches `backend/pptx_worker/export-template.mjs`.
7. `pptx-automizer` clones template slides and injects text into named PowerPoint shapes.

## Default template

- PPTX: `backend/storage/templates/default-template.pptx`
- Config: `backend/storage/templates/default-template.config.json`

You can also upload a permanent template once:

- `POST /api/presentation/default-template`

## Template contract

Recommended shape names in PowerPoint Selection Pane (`Alt+F10`):

- `TITLE`
- `SUBTITLE`
- `BODY`

Recommended template slides:

- Slide 1: cover layout
- Slide 2: repeatable content layout

## API

- `POST /api/presentation/generate-json`
- `POST /api/presentation/export-template`
- `POST /api/presentation/export-template-with-upload`
- `GET /api/presentation/default-template`
- `POST /api/presentation/default-template`

## Important limitation

This implementation focuses on text placeholders. Image/chart placeholders from an existing template are not fully mapped yet.
