# Template mode for pptx-automizer

Place your permanent PowerPoint template here as:

- `default-template.pptx`
- `default-template.config.json`

## Minimal contract

The config maps template slide numbers and PowerPoint shape names:

```json
{
  "layouts": {
    "cover": {
      "sourceSlide": 1,
      "shapes": {
        "title": "TITLE",
        "subtitle": "SUBTITLE",
        "body": "BODY"
      }
    },
    "content": {
      "sourceSlide": 2,
      "shapes": {
        "title": "TITLE",
        "body": "BODY"
      }
    }
  }
}
```

## Important

Open PowerPoint → Home → Arrange → Selection Pane (or `Alt+F10`) and rename text placeholders/shapes to match config names, for example `TITLE`, `SUBTITLE`, `BODY`.

If no config exists, the exporter falls back to the first text shape as title and the second text shape as body.
