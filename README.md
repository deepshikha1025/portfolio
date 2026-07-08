# Portfolio — Deepshikha Ranjan

## Project Structure

```
portfolio/
├── index.html          ← Built output (don't edit directly)
├── sketches.js         ← Sketch image config (names, order, categories)
├── projects.js         ← Projects config (title, desc, image, link)
├── admin.html          ← Live reorder dashboard (works on Vercel)
├── build.py            ← Rebuilds index.html from src/
├── dashboard.py        ← Local dashboard (sketches + projects)
├── start.sh            ← One command to build + launch dashboard
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

## Quick Start

Run everything in one go — builds `index.html` and opens the dashboard:

```
./start.sh
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

Opens `http://localhost:4444` → **Sketches** tab

- Upload new images to any category
- Remove images
- Drag & drop to reorder
- Hit **Save & Build** — saves `sketches.js` and rebuilds `index.html` automatically

## Managing Projects

### Locally — Add, Edit, Remove & Reorder

```
python3 dashboard.py
```

Opens `http://localhost:4444` → **Projects** tab

- Add a new project (title, description, tags, Behance link, image, accent color)
- Edit existing projects
- Upload project images directly
- Drag & drop to reorder — the first project is the large **featured** card
- Remove projects
- Hit **Save & Build** — saves `projects.js` and rebuilds `index.html` automatically

### Manually via config file

Edit `projects.js` directly — each project is an object:

```js
{
  title: "Project Name",
  desc: "Short description.",
  tags: "UI · Mobile",
  color: "#3FA7D6",
  bg: "#EBF1FF",
  rot: -1.5,
  href: "https://www.behance.net/...",
  img: "uploads/your-image.jpg",
}
```

Then run `python3 build.py`.

## Deploy

Push to the repo and Vercel picks up the changes automatically.
