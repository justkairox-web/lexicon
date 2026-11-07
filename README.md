# Lexicon

A personal dictionary PWA: add words (with or without meanings), quiz yourself with flashcards,
multiple choice, or write-a-sentence with AI feedback. Dark, minimal, phone-first.

- `public/` — the app (index.html, service worker, manifest, icons)
- `api/dict_sync.py` — cloud sync through Upstash Redis
- `api/dict_check.py` — AI sentence checker (Claude)

## Environment variables (Vercel → Settings → Environment Variables)

| Name | What it is |
|---|---|
| `JARVIS_PASSWORD` | The password you type into the app's Settings |
| `ANTHROPIC_API_KEY` | Your Anthropic API key (powers sentence feedback) |
| `KV_REST_API_URL` | Upstash Redis REST URL |
| `KV_REST_API_TOKEN` | Upstash Redis REST token |

Optional: `DICT_MODEL` to change the model used for feedback.
