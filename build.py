#!/usr/bin/env python3
"""
Build script — assembles src/ files back into index.html

Usage:  python3 build.py

Edit the readable files in src/, then run this to rebuild.
Files you'll typically edit:
  src/sections/nav.html        — Navigation bar
  src/sections/home.html       — Home / landing section
  src/sections/journey.html    — "My journey" timeline
  src/sections/sketches.html   — Sketches gallery layout
  src/sections/projects.html   — Projects / case studies
  src/sections/contact.html    — Contact form
  src/sections/footer.html     — Footer
  src/app.js                   — All app logic (component class)
  src/styles/app.css           — Your custom CSS
  src/styles/shimmer.css       — Image loading shimmer effect
  sketches.js                  — Sketch image config (already external)
"""

import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, 'src')

def read(path):
    with open(os.path.join(SRC, path), 'r') as f:
        return f.read()

def read_root(path):
    with open(os.path.join(BASE, path), 'r') as f:
        return f.read()

# --- Assemble the template (the inner app HTML) ---

template = '<!DOCTYPE html>\n<html><head>\n'

# Shimmer CSS
template += '<style>\n' + read('styles/shimmer.css').strip() + '\n</style>\n'

# Meta tags + head script
template += '<meta charset="utf-8">\n'
template += '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
template += '<script src="9a8de12c-6e3c-46ae-9af6-124d0f714242"></script>\n'

template += '</head>\n<body>\n<x-dc>\n<helmet>\n'

# Helmet links (font preconnects)
template += read('helmet-links.html').strip() + '\n'

# Google Fonts CSS
template += '<style>\n' + read('styles/fonts.css').strip() + '\n</style>\n'

# Remix Icon CSS
template += '<style>\n' + read('styles/remixicon.css').strip() + '\n</style>\n'

# DC Logic script
template += '<script src="d03dabc6-2d82-4c61-bb28-6a69d20c3f96"></script>\n'

# App CSS
template += '<style>\n' + read('styles/app.css').strip() + '\n</style>\n'

template += '</helmet>\n\n'

# Layout open (app wrapper divs)
template += read('layout-open.html').strip() + '\n\n    '

# Sections
for section in ['nav', 'home', 'journey', 'sketches', 'projects', 'contact', 'footer']:
    template += read(f'sections/{section}.html').strip() + '\n\n    '

# Layout close (closing divs)
template += read('layout-close.html').strip() + '\n\n\n'

template += '</x-dc>\n\n'

# App JS
script_tag = read('app-script-tag.txt').strip()
template += script_tag + '\n'
template += read('app.js').strip() + '\n'
template += '</script>\n\n\n\n'

# Image loader
template += '<script>\n' + read('image-loader.js').strip() + '\n</script>\n'
template += '</body></html>'

# --- Assemble the outer index.html ---
outer_before = read_root('src/outer-before.html')
outer_after = read_root('src/outer-after.html')

# The template goes inside a <script type="__bundler/template"> tag as JSON.
# Escape </ as <\u002F so </script> inside the template doesn't break the outer tag.
template_json = json.dumps(template).replace('</', '<\\u002F')

output = outer_before
output += '<script type="__bundler/template">\n'
output += template_json + '\n'
output += '  </script>\n'
output += outer_after

# Write output
with open(os.path.join(BASE, 'index.html'), 'w') as f:
    f.write(output)

print(f'Built index.html ({len(output):,} chars)')
print('Done!')
