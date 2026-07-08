#!/usr/bin/env python3
"""
Sketches Dashboard — visual editor for sketch images.

Usage:  python3 dashboard.py
Opens:  http://localhost:4444

Features:
  - See all categories with image thumbnails
  - Drag & drop to reorder images within a category
  - Move images between categories
  - Add new images (upload files)
  - Remove images
  - Save changes → updates sketches.js & rebuilds index.html
"""

import http.server
import json
import os
import re
import shutil
import subprocess
import urllib.parse
import webbrowser

PORT = 4444
BASE = os.path.dirname(os.path.abspath(__file__))
UPLOADS = os.path.join(BASE, 'uploads')
SKETCHES_JS = os.path.join(BASE, 'sketches.js')
BUILD_PY = os.path.join(BASE, 'build.py')

# ── Parse sketches.js ──

def read_config():
    with open(SKETCHES_JS, 'r') as f:
        src = f.read()
    # Extract the array between [ ... ];
    match = re.search(r'var SKETCH_CATEGORIES\s*=\s*(\[.*?\]);', src, re.DOTALL)
    if not match:
        return []
    raw = match.group(1)
    # Remove JS comments
    raw = re.sub(r'//[^\n]*', '', raw)
    # Convert single-quoted strings to double-quoted
    raw = re.sub(r"'([^']*)',", r'"\1",', raw)
    raw = re.sub(r"'([^']*)'\s*([}\]])", r'"\1" \2', raw)
    # Add quotes around unquoted keys
    raw = re.sub(r'(?<=[{,\n])\s*(\w+)\s*:', r' "\1":', raw)
    # Remove trailing commas before ] or }
    raw = re.sub(r',\s*([}\]])', r' \1', raw)
    return json.loads(raw)


def write_config(categories):
    lines = [
        '/*',
        ' * ─── SKETCHES CONFIG ───',
        ' * Edit filenames to change images, reorder lines to change display order.',
        ' * To swap an image: replace the filename here AND the file in uploads/',
        ' * To reorder: move the filename line up or down within its category',
        ' * To move between categories: cut a filename from one "files" array, paste into another',
        ' */',
        '',
        '// eslint-disable-next-line no-unused-vars',
        'var SKETCH_CATEGORIES = [',
    ]
    for i, cat in enumerate(categories):
        lines.append('')
        lines.append(f'  // ── {cat["title"]} ──')
        lines.append('  {')
        lines.append(f'    title: {json.dumps(cat["title"])},')
        lines.append(f'    note: {json.dumps(cat["note"])},')
        lines.append(f'    icon: {json.dumps(cat["icon"])},')
        lines.append(f'    color: {json.dumps(cat["color"])},')
        lines.append('    files: [')
        for f in cat['files']:
            lines.append(f'      {json.dumps(f)},')
        lines.append('    ],')
        lines.append('  },')
    lines.append('];')
    lines.append('')
    with open(SKETCHES_JS, 'w') as f:
        f.write('\n'.join(lines))


# ── Dashboard HTML ──

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sketches Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f1eb; color: #201B13; min-height: 100vh; }

  .topbar { background: #201B13; color: #FCF8F0; padding: 16px 28px; display: flex; align-items: center; justify-content: space-between; gap: 16px; position: sticky; top: 0; z-index: 100; }
  .topbar h1 { font-size: 20px; font-weight: 700; }
  .topbar .actions { display: flex; gap: 10px; }
  .btn { padding: 8px 18px; border: 2px solid #201B13; border-radius: 10px; font-weight: 600; font-size: 14px; cursor: pointer; transition: all .15s; }
  .btn-primary { background: #59C29D; color: #fff; border-color: #59C29D; }
  .btn-primary:hover { background: #4ab08c; }
  .btn-secondary { background: #fff; color: #201B13; }
  .btn-secondary:hover { background: #f0ece4; }
  .btn-danger { background: #FF6F61; color: #fff; border-color: #FF6F61; }
  .btn-danger:hover { background: #e55a4d; }
  .btn:disabled { opacity: .5; cursor: not-allowed; }

  .toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #201B13; color: #FCF8F0; padding: 12px 24px; border-radius: 12px; font-weight: 600; font-size: 14px; z-index: 200; display: none; box-shadow: 0 4px 20px rgba(0,0,0,.25); }
  .toast.show { display: block; animation: fadeInUp .3s ease; }
  @keyframes fadeInUp { from { opacity: 0; transform: translateX(-50%) translateY(12px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }

  .container { max-width: 1200px; margin: 0 auto; padding: 24px; }

  .category { background: #fff; border: 2.5px solid #201B13; border-radius: 16px; margin-bottom: 24px; box-shadow: 4px 4px 0 rgba(32,27,19,.15); overflow: hidden; }
  .cat-header { padding: 16px 20px; display: flex; align-items: center; gap: 12px; border-bottom: 2px dashed rgba(32,27,19,.15); flex-wrap: wrap; }
  .cat-dot { width: 14px; height: 14px; border-radius: 50%; border: 2px solid #201B13; flex: none; }
  .cat-title { font-size: 20px; font-weight: 700; }
  .cat-note { font-size: 14px; opacity: .6; }
  .cat-count { font-size: 13px; font-weight: 600; background: #f0ece4; padding: 3px 10px; border-radius: 999px; margin-left: auto; }
  .cat-actions { display: flex; gap: 6px; }

  .image-grid { display: flex; flex-wrap: wrap; gap: 16px; padding: 20px; min-height: 100px; }
  .image-grid.drag-over { background: rgba(89,194,157,.08); }
  .image-grid.empty-grid { justify-content: center; align-items: center; }
  .empty-msg { font-size: 15px; opacity: .4; font-style: italic; padding: 20px; }

  .image-card { position: relative; width: 150px; cursor: grab; transition: transform .12s, box-shadow .12s; }
  .image-card:hover { transform: translateY(-3px); }
  .image-card.dragging { opacity: .4; transform: scale(.95); }
  .image-card .thumb { width: 150px; height: 150px; object-fit: cover; border: 2.5px solid #201B13; border-radius: 10px; display: block; background: #f2ede3; }
  .image-card .name { font-size: 11px; font-weight: 600; margin-top: 5px; text-align: center; word-break: break-all; opacity: .7; }
  .image-card .remove-btn { position: absolute; top: -8px; right: -8px; width: 24px; height: 24px; background: #FF6F61; color: #fff; border: 2px solid #201B13; border-radius: 50%; font-size: 14px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity .15s; line-height: 1; }
  .image-card:hover .remove-btn { opacity: 1; }

  .drop-indicator { width: 4px; background: #3FA7D6; border-radius: 2px; margin: 0 -2px; min-height: 100px; align-self: stretch; transition: opacity .15s; }

  .add-zone { width: 150px; min-height: 150px; border: 2.5px dashed rgba(32,27,19,.25); border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; cursor: pointer; color: #8B6DFF; font-size: 13px; font-weight: 600; transition: background .15s; }
  .add-zone:hover { background: rgba(139,109,255,.06); }
  .add-zone i { font-size: 28px; }

  .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 150; display: flex; align-items: center; justify-content: center; }
  .modal { background: #fff; border: 2.5px solid #201B13; border-radius: 16px; padding: 28px; width: 420px; max-width: 90vw; box-shadow: 6px 6px 0 rgba(32,27,19,.3); }
  .modal h2 { font-size: 20px; margin-bottom: 16px; }
  .modal label { display: block; font-weight: 600; font-size: 14px; margin-bottom: 6px; margin-top: 14px; }
  .modal input[type=text] { width: 100%; padding: 8px 12px; border: 2px solid #201B13; border-radius: 8px; font-size: 14px; }
  .modal .modal-actions { display: flex; gap: 10px; margin-top: 20px; justify-content: flex-end; }

  .upload-area { border: 2.5px dashed rgba(32,27,19,.3); border-radius: 12px; padding: 24px; text-align: center; cursor: pointer; transition: background .15s; margin-top: 8px; }
  .upload-area:hover, .upload-area.drag-over { background: rgba(89,194,157,.08); border-color: #59C29D; }
  .upload-area input { display: none; }
  .upload-preview { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
  .upload-preview img { width: 80px; height: 80px; object-fit: cover; border-radius: 8px; border: 2px solid #201B13; }
</style>
</head>
<body>

<div class="topbar">
  <h1>Sketches Dashboard</h1>
  <div class="actions">
    <button class="btn btn-secondary" onclick="location.reload()">Reload</button>
    <button class="btn btn-primary" id="saveBtn" onclick="saveAll()">Save & Build</button>
  </div>
</div>

<div class="container" id="app"></div>
<div class="toast" id="toast"></div>

<script>
let DATA = [];
let dirty = false;

async function loadData() {
  const res = await fetch('/api/config');
  DATA = await res.json();
  render();
}

function markDirty() {
  dirty = true;
  document.getElementById('saveBtn').textContent = 'Save & Build *';
}

function showToast(msg, ms = 2500) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), ms);
}

function render() {
  const app = document.getElementById('app');
  app.innerHTML = DATA.map((cat, ci) => `
    <div class="category" data-cat="${ci}">
      <div class="cat-header">
        <div class="cat-dot" style="background:${cat.color}"></div>
        <span class="cat-title">${esc(cat.title)}</span>
        <span class="cat-note">${esc(cat.note)}</span>
        <span class="cat-count">${cat.files.length} images</span>
      </div>
      <div class="image-grid" data-cat="${ci}"
           ondragover="gridDragOver(event, ${ci})" ondrop="gridDrop(event, ${ci})" ondragleave="gridDragLeave(event)">
        ${cat.files.length === 0 ? '<div class="empty-msg">No images in this category</div>' : ''}
        ${cat.files.map((f, fi) => `
          <div class="image-card" draggable="true" data-cat="${ci}" data-idx="${fi}"
               ondragstart="cardDragStart(event, ${ci}, ${fi})"
               ondragend="cardDragEnd(event)">
            <img class="thumb" src="/uploads/${encodeURIComponent(f)}" alt="${esc(f)}" loading="lazy">
            <div class="name">${esc(f)}</div>
            <div class="remove-btn" onclick="removeImage(${ci}, ${fi})" title="Remove">&times;</div>
          </div>
        `).join('')}
        <div class="add-zone" onclick="openUpload(${ci})">
          <div style="font-size:28px">+</div>
          Add images
        </div>
      </div>
    </div>
  `).join('');
}

function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

// ── Drag & Drop reorder ──
let dragCat = -1, dragIdx = -1;

function cardDragStart(e, ci, fi) {
  dragCat = ci; dragIdx = fi;
  e.target.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', `${ci}:${fi}`);
}

function cardDragEnd(e) {
  e.target.classList.remove('dragging');
  document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
}

function gridDragOver(e, ci) {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
  e.currentTarget.classList.add('drag-over');
}

function gridDragLeave(e) {
  e.currentTarget.classList.remove('drag-over');
}

function gridDrop(e, targetCat) {
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');
  if (dragCat < 0) return;

  const file = DATA[dragCat].files[dragIdx];

  // Find drop position
  const grid = e.currentTarget;
  const cards = [...grid.querySelectorAll('.image-card')];
  let dropIdx = DATA[targetCat].files.length;

  for (let i = 0; i < cards.length; i++) {
    const rect = cards[i].getBoundingClientRect();
    const mid = rect.left + rect.width / 2;
    if (e.clientX < mid) { dropIdx = parseInt(cards[i].dataset.idx); break; }
  }

  // Remove from source
  DATA[dragCat].files.splice(dragIdx, 1);

  // Adjust index if same category and removing before insert point
  if (dragCat === targetCat && dragIdx < dropIdx) dropIdx--;

  // Insert at target
  DATA[targetCat].files.splice(dropIdx, 0, file);

  dragCat = -1; dragIdx = -1;
  markDirty();
  render();
}

// ── Remove ──
function removeImage(ci, fi) {
  const file = DATA[ci].files[fi];
  if (!confirm(`Remove "${file}" from ${DATA[ci].title}?`)) return;
  DATA[ci].files.splice(fi, 1);
  markDirty();
  render();
  showToast(`Removed ${file}`);
}

// ── Upload / Add ──
function openUpload(ci) {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.multiple = true;
  input.onchange = async () => {
    const files = [...input.files];
    if (!files.length) return;

    const btn = document.getElementById('saveBtn');
    btn.disabled = true;
    btn.textContent = 'Uploading...';

    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const result = await res.json();
        if (result.filename) {
          DATA[ci].files.push(result.filename);
        }
      } catch (err) {
        showToast('Upload failed: ' + err.message, 4000);
      }
    }

    btn.disabled = false;
    markDirty();
    render();
    showToast(`Added ${files.length} image(s) to ${DATA[ci].title}`);
  };
  input.click();
}

// ── Save ──
async function saveAll() {
  const btn = document.getElementById('saveBtn');
  btn.disabled = true;
  btn.textContent = 'Saving...';
  try {
    const res = await fetch('/api/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(DATA),
    });
    const result = await res.json();
    if (result.ok) {
      dirty = false;
      btn.textContent = 'Save & Build';
      showToast('Saved & rebuilt index.html');
    } else {
      showToast('Error: ' + (result.error || 'Unknown'), 4000);
      btn.textContent = 'Save & Build';
    }
  } catch (err) {
    showToast('Save failed: ' + err.message, 4000);
    btn.textContent = 'Save & Build';
  }
  btn.disabled = false;
}

window.onbeforeunload = () => dirty ? 'Unsaved changes' : null;
loadData();
</script>
</body>
</html>"""


# ── HTTP Server ──

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet logs

    def _cors(self):
        self.send_header('Cache-Control', 'no-cache')

    def _json_response(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _html_response(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path == '/' or path == '':
            self._html_response(DASHBOARD_HTML)
            return

        if path == '/api/config':
            try:
                config = read_config()
                self._json_response(config)
            except Exception as e:
                self._json_response({'error': str(e)}, 500)
            return

        # Serve uploads
        if path.startswith('/uploads/'):
            filename = urllib.parse.unquote(path[len('/uploads/'):])
            filepath = os.path.join(UPLOADS, filename)
            # Prevent path traversal
            if not os.path.abspath(filepath).startswith(os.path.abspath(UPLOADS)):
                self.send_error(403)
                return
            if not os.path.isfile(filepath):
                self.send_error(404)
                return
            ext = os.path.splitext(filename)[1].lower()
            mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                        '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml'}
            mime = mime_map.get(ext, 'application/octet-stream')
            with open(filepath, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', len(data))
            self.send_header('Cache-Control', 'max-age=60')
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_error(404)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path

        if path == '/api/save':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                categories = json.loads(body)
                write_config(categories)
                # Run build
                result = subprocess.run(
                    ['python3', BUILD_PY],
                    cwd=BASE, capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0:
                    self._json_response({'ok': False, 'error': result.stderr or result.stdout}, 500)
                else:
                    self._json_response({'ok': True, 'message': result.stdout.strip()})
            except Exception as e:
                self._json_response({'ok': False, 'error': str(e)}, 500)
            return

        if path == '/api/upload':
            try:
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' not in content_type:
                    self._json_response({'error': 'Expected multipart/form-data'}, 400)
                    return

                # Parse boundary
                boundary = content_type.split('boundary=')[1].strip()
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)

                # Simple multipart parser
                parts = body.split(('--' + boundary).encode())
                for part in parts:
                    if b'filename="' not in part:
                        continue
                    # Extract filename
                    header_end = part.find(b'\r\n\r\n')
                    headers_raw = part[:header_end].decode('utf-8', errors='replace')
                    file_data = part[header_end + 4:]
                    if file_data.endswith(b'\r\n'):
                        file_data = file_data[:-2]

                    fn_match = re.search(r'filename="([^"]+)"', headers_raw)
                    if not fn_match:
                        continue
                    original_name = fn_match.group(1)
                    # Sanitize filename
                    safe_name = re.sub(r'[^\w\-.]', '_', original_name)
                    # Avoid overwrites
                    dest = os.path.join(UPLOADS, safe_name)
                    counter = 1
                    base, ext = os.path.splitext(safe_name)
                    while os.path.exists(dest):
                        safe_name = f'{base}_{counter}{ext}'
                        dest = os.path.join(UPLOADS, safe_name)
                        counter += 1

                    with open(dest, 'wb') as f:
                        f.write(file_data)

                    self._json_response({'filename': safe_name})
                    return

                self._json_response({'error': 'No file found in upload'}, 400)
            except Exception as e:
                self._json_response({'error': str(e)}, 500)
            return

        self.send_error(404)


if __name__ == '__main__':
    server = http.server.HTTPServer(('127.0.0.1', PORT), DashboardHandler)
    url = f'http://localhost:{PORT}'
    print(f'Sketches Dashboard running at {url}')
    print('Press Ctrl+C to stop\n')
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
        server.server_close()
