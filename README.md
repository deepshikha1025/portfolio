# Portfolio — Deepshikha Ranjan

## Project Structure

```
portfolio/
├── index.html          ← Built output (don't edit directly)
├── sketches.js         ← Sketch image config (names, order, categories)
├── admin.html          ← Live reorder dashboard (works on Vercel)
├── build.py            ← Rebuilds index.html from src/
├── dashboard.py        ← Local dashboard (upload, remove, reorder)
├── uploads/            ← All image files
├── src/
│   ├── app.js              ← App logic
│   ├── image-loader.js     ← Image lazy-load script
│   ├── sections/
│   │   ├── nav.html        ← Navigation bar
│   │   ├── home.html       ← Landing section
│   │   ├── journey.html    ← "My journey" timeline
│   │   ├── sketches.html   ← Sketches gallery layout
│   │   ├── projects.html   ← Projects / case studies
│   │   ├── contact.html    ← Contact form
│   │   └── footer.html     ← Footer
│   └── styles/
│       ├── app.css         ← Custom CSS
│       ├── shimmer.css     ← Image loading effect
│       ├── fonts.css       ← Google Fonts
│       └── remixicon.css   ← Icon library
```

## Editing the Site

Edit files in `src/`, then rebuild:

```
python3 build.py
```

Never edit `index.html` directly — it's a generated bundle.

## Managing Sketch Images

### On Vercel (live) — Reorder

Open `yoursite.vercel.app/admin.html`

- Drag & drop to reorder images within or between categories
- Shows position numbers on each image
- Works on mobile too (long-press to drag)
- Hit **Download sketches.js** → replace the file locally → `python3 build.py` → push

### Locally — Upload, Remove & Reorder

```
python3 dashboard.py
```

Opens `http://localhost:4444`

- Upload new images to any category
- Remove images
- Drag & drop to reorder
- Hit **Save & Build** — saves `sketches.js` and rebuilds `index.html` automatically

## Deploy

Push to the repo and Vercel picks up the changes automatically.
