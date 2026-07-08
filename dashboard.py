#!/usr/bin/env python3
"""
Portfolio Dashboard — manage sketches & projects.

Usage:  python3 dashboard.py
Opens:  http://localhost:4444

Sketches: reorder, upload, remove images across categories.
Projects: add, edit, remove, reorder project cards.
Save & Build: writes config files and rebuilds index.html.
"""

import http.server
import json
import os
import re
import subprocess
import urllib.parse
import webbrowser

PORT = 4444
BASE = os.path.dirname(os.path.abspath(__file__))
UPLOADS = os.path.join(BASE, 'uploads')
SKETCHES_JS = os.path.join(BASE, 'sketches.js')
PROJECTS_JS = os.path.join(BASE, 'projects.js')
BUILD_PY = os.path.join(BASE, 'build.py')


def _parse_js_array(filepath, var_name):
    with open(filepath, 'r') as f:
        src = f.read()
    match = re.search(rf'var {var_name}\s*=\s*(\[.*?\]);', src, re.DOTALL)
    if not match:
        return []
    raw = match.group(1)
    # Remove only line comments that start at beginning of line (not // inside URLs)
    raw = re.sub(r'^\s*//[^\n]*', '', raw, flags=re.MULTILINE)
    # Convert single-quoted strings to double-quoted
    raw = re.sub(r"'([^']*)',", r'"\1",', raw)
    raw = re.sub(r"'([^']*)'\s*([}\]])", r'"\1" \2', raw)
    # Add quotes around unquoted keys
    raw = re.sub(r'(?<=[{,\n])\s*(\w+)\s*:', r' "\1":', raw)
    # Remove trailing commas before ] or }
    raw = re.sub(r',\s*([}\]])', r' \1', raw)
    return json.loads(raw)


def read_sketches():
    return _parse_js_array(SKETCHES_JS, 'SKETCH_CATEGORIES')


def read_projects():
    return _parse_js_array(PROJECTS_JS, 'PROJECT_DEFINITIONS')


def write_sketches(categories):
    lines = [
        '/*', ' * ─── SKETCHES CONFIG ───',
        ' * Edit filenames to change images, reorder lines to change display order.',
        ' * To swap an image: replace the filename here AND the file in uploads/',
        ' * To reorder: move the filename line up or down within its category',
        ' * To move between categories: cut a filename from one "files" array, paste into another',
        ' */', '', '// eslint-disable-next-line no-unused-vars',
        'var SKETCH_CATEGORIES = [',
    ]
    for cat in categories:
        lines.append('')
        lines.append(f'  // ── {cat["title"]} ──')
        lines.append('  {')
        lines.append(f'    title: {json.dumps(cat["title"])},')
        lines.append(f'    note: {json.dumps(cat["note"])},')
        lines.append(f'    icon: {json.dumps(cat["icon"])},')
        lines.append(f'    color: {json.dumps(cat["color"])},')
        lines.append('    files: [')
        for fn in cat['files']:
            lines.append(f'      {json.dumps(fn)},')
        lines.append('    ],')
        lines.append('  },')
    lines.append('];')
    lines.append('')
    with open(SKETCHES_JS, 'w') as f:
        f.write('\n'.join(lines))


def write_projects(projects):
    lines = [
        '/*', ' * ─── PROJECTS CONFIG ───',
        ' * The first project is the large featured card.',
        ' * Reorder entries to change which is featured.',
        ' *',
        ' * Available colors: #3FA7D6 (blue), #FF6F61 (red), #8B6DFF (purple),',
        ' *                   #59C29D (green), #E0A400 (yellow)',
        ' * bg should be a matching pastel: #EBF1FF, #FFF3EB, #EFEBFF, #E0FAEC, #FFFAEB',
        ' */', '', '// eslint-disable-next-line no-unused-vars',
        'var PROJECT_DEFINITIONS = [',
    ]
    for p in projects:
        lines.append('  {')
        lines.append(f'    title: {json.dumps(p.get("title", ""))},')
        lines.append(f'    desc: {json.dumps(p.get("desc", ""))},')
        lines.append(f'    tags: {json.dumps(p.get("tags", ""))},')
        lines.append(f'    color: {json.dumps(p.get("color", "#3FA7D6"))},')
        lines.append(f'    bg: {json.dumps(p.get("bg", "#EBF1FF"))},')
        lines.append(f'    rot: {p.get("rot", 0)},')
        lines.append(f'    href: {json.dumps(p.get("href", ""))},')
        lines.append(f'    img: {json.dumps(p.get("img", ""))},')
        lines.append('  },')
    lines.append('];')
    lines.append('')
    with open(PROJECTS_JS, 'w') as f:
        f.write('\n'.join(lines))


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portfolio Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f1eb; color: #201B13; min-height: 100vh; }

  .topbar { background: #201B13; color: #FCF8F0; padding: 16px 28px; display: flex; align-items: center; justify-content: space-between; gap: 16px; position: sticky; top: 0; z-index: 100; flex-wrap: wrap; }
  .topbar h1 { font-size: 20px; font-weight: 700; }
  .topbar .actions { display: flex; gap: 10px; flex-wrap: wrap; }
  .btn { padding: 8px 18px; border: 2px solid #201B13; border-radius: 10px; font-weight: 600; font-size: 14px; cursor: pointer; transition: all .15s; }
  .btn-primary { background: #59C29D; color: #fff; border-color: #59C29D; }
  .btn-primary:hover { background: #4ab08c; }
  .btn-secondary { background: #fff; color: #201B13; }
  .btn-secondary:hover { background: #f0ece4; }
  .btn-danger { background: #FF6F61; color: #fff; border-color: #FF6F61; }
  .btn-danger:hover { background: #e55a4d; }
  .btn:disabled { opacity: .5; cursor: not-allowed; }

  .tabs { display: flex; gap: 0; margin-bottom: 24px; border-bottom: 2.5px solid #201B13; }
  .tab { padding: 12px 24px; font-weight: 700; font-size: 16px; cursor: pointer; border: 2.5px solid transparent; border-bottom: none; border-radius: 12px 12px 0 0; margin-bottom: -2.5px; transition: all .15s; }
  .tab:hover { background: rgba(139,109,255,.06); }
  .tab.active { background: #fff; border-color: #201B13; }

  .toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #201B13; color: #FCF8F0; padding: 12px 24px; border-radius: 12px; font-weight: 600; font-size: 14px; z-index: 200; display: none; box-shadow: 0 4px 20px rgba(0,0,0,.25); }
  .toast.show { display: block; animation: fadeInUp .3s ease; }
  @keyframes fadeInUp { from { opacity:0; transform: translateX(-50%) translateY(12px); } to { opacity:1; transform: translateX(-50%) translateY(0); } }

  .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
  .section { display: none; }
  .section.active { display: block; }

  /* ── Sketches ── */
  .category { background: #fff; border: 2.5px solid #201B13; border-radius: 16px; margin-bottom: 24px; box-shadow: 4px 4px 0 rgba(32,27,19,.15); overflow: hidden; }
  .cat-header { padding: 16px 20px; display: flex; align-items: center; gap: 12px; border-bottom: 2px dashed rgba(32,27,19,.15); flex-wrap: wrap; }
  .cat-dot { width: 14px; height: 14px; border-radius: 50%; border: 2px solid #201B13; flex: none; }
  .cat-title { font-size: 20px; font-weight: 700; }
  .cat-note { font-size: 14px; opacity: .6; }
  .cat-count { font-size: 13px; font-weight: 600; background: #f0ece4; padding: 3px 10px; border-radius: 999px; margin-left: auto; }

  .image-grid { display: flex; flex-wrap: wrap; gap: 16px; padding: 20px; min-height: 100px; transition: background .15s; }
  .image-grid.drag-over { background: rgba(89,194,157,.08); }
  .empty-msg { font-size: 15px; opacity: .4; font-style: italic; padding: 20px; }

  .image-card { position: relative; width: 150px; cursor: grab; transition: transform .12s; user-select: none; }
  .image-card:hover { transform: translateY(-3px); }
  .image-card.dragging { opacity: .4; transform: scale(.95); }
  .image-card .thumb { width: 150px; height: 150px; object-fit: cover; border: 2.5px solid #201B13; border-radius: 10px; display: block; background: #f2ede3; pointer-events: none; }
  .image-card .name { font-size: 11px; font-weight: 600; margin-top: 5px; text-align: center; word-break: break-all; opacity: .7; }
  .image-card .remove-btn { position: absolute; top: -8px; right: -8px; width: 24px; height: 24px; background: #FF6F61; color: #fff; border: 2px solid #201B13; border-radius: 50%; font-size: 14px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity .15s; line-height: 1; }
  .image-card:hover .remove-btn { opacity: 1; }

  .add-zone { width: 150px; min-height: 150px; border: 2.5px dashed rgba(32,27,19,.25); border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; cursor: pointer; color: #8B6DFF; font-size: 13px; font-weight: 600; transition: background .15s; }
  .add-zone:hover { background: rgba(139,109,255,.06); }

  /* ── Projects ── */
  .proj-list { display: flex; flex-direction: column; gap: 16px; }
  .proj-card { background: #fff; border: 2.5px solid #201B13; border-radius: 16px; box-shadow: 4px 4px 0 rgba(32,27,19,.15); display: flex; gap: 16px; padding: 16px; align-items: center; cursor: grab; transition: transform .12s; user-select: none; }
  .proj-card:hover { transform: translateY(-2px); }
  .proj-card.dragging { opacity: .4; }
  .proj-card.featured { border-color: #FFC53D; box-shadow: 4px 4px 0 #FFC53D; }
  .proj-thumb { width: 120px; height: 80px; object-fit: cover; border: 2px solid #201B13; border-radius: 8px; background: #f2ede3; flex: none; }
  .proj-info { flex: 1; min-width: 0; }
  .proj-info h3 { font-size: 16px; margin-bottom: 4px; }
  .proj-info p { font-size: 13px; opacity: .7; margin-bottom: 4px; }
  .proj-info .proj-tags { font-size: 12px; font-weight: 600; color: #8B6DFF; }
  .proj-info .proj-link { font-size: 12px; opacity: .5; word-break: break-all; }
  .proj-actions { display: flex; gap: 8px; flex: none; }
  .proj-badge { font-size: 11px; font-weight: 700; background: #FFC53D; border: 2px solid #201B13; border-radius: 999px; padding: 2px 10px; }

  .add-proj-btn { border: 2.5px dashed rgba(32,27,19,.25); border-radius: 16px; padding: 20px; text-align: center; cursor: pointer; font-weight: 600; font-size: 15px; color: #8B6DFF; transition: background .15s; }
  .add-proj-btn:hover { background: rgba(139,109,255,.06); }

  /* ── Modal ── */
  .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 150; display: flex; align-items: center; justify-content: center; }
  .modal { background: #fff; border: 2.5px solid #201B13; border-radius: 16px; padding: 28px; width: 520px; max-width: 90vw; max-height: 90vh; overflow-y: auto; box-shadow: 6px 6px 0 rgba(32,27,19,.3); }
  .modal h2 { font-size: 20px; margin-bottom: 16px; }
  .modal label { display: block; font-weight: 600; font-size: 14px; margin-bottom: 4px; margin-top: 14px; }
  .modal input[type=text], .modal textarea, .modal select { width: 100%; padding: 8px 12px; border: 2px solid #201B13; border-radius: 8px; font-size: 14px; font-family: inherit; }
  .modal textarea { resize: vertical; min-height: 60px; }
  .modal .modal-actions { display: flex; gap: 10px; margin-top: 20px; justify-content: flex-end; }
  .modal .color-row { display: flex; gap: 8px; margin-top: 6px; flex-wrap: wrap; }
  .modal .color-swatch { width: 32px; height: 32px; border-radius: 50%; border: 3px solid transparent; cursor: pointer; transition: border-color .15s; }
  .modal .color-swatch:hover, .modal .color-swatch.active { border-color: #201B13; }
</style>
</head>
<body>

<div class="topbar">
  <h1>Portfolio Dashboard</h1>
  <div class="actions">
    <button class="btn btn-secondary" onclick="location.reload()">Reload</button>
    <button class="btn btn-primary" id="saveBtn" onclick="saveAll()">Save & Build</button>
  </div>
</div>

<div class="container">
  <div class="tabs">
    <div class="tab active" onclick="switchTab('sketches')">Sketches</div>
    <div class="tab" onclick="switchTab('projects')">Projects</div>
  </div>

  <div id="sketches-section" class="section active"></div>
  <div id="projects-section" class="section"></div>
</div>
<div class="toast" id="toast"></div>
<div id="modalRoot"></div>

<script>
let SKETCHES = [];
let PROJECTS = [];
let dirty = false;
let activeTab = 'sketches';

async function loadData() {
  const [sRes, pRes] = await Promise.all([fetch('/api/sketches'), fetch('/api/projects')]);
  SKETCHES = await sRes.json();
  PROJECTS = await pRes.json();
  render();
}

function switchTab(tab) {
  activeTab = tab;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.textContent.toLowerCase().includes(tab)));
  document.getElementById('sketches-section').classList.toggle('active', tab === 'sketches');
  document.getElementById('projects-section').classList.toggle('active', tab === 'projects');
}

function markDirty() {
  dirty = true;
  document.getElementById('saveBtn').textContent = 'Save & Build *';
}

function showToast(msg, ms) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), ms || 2500);
}

function esc(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }

// ══════════════════════════════════════════
//  SKETCHES
// ══════════════════════════════════════════

function renderSketches() {
  document.getElementById('sketches-section').innerHTML = SKETCHES.map((cat, ci) => `
    <div class="category" data-cat="${ci}">
      <div class="cat-header">
        <div class="cat-dot" style="background:${cat.color}"></div>
        <span class="cat-title">${esc(cat.title)}</span>
        <span class="cat-note">${esc(cat.note)}</span>
        <span class="cat-count">${cat.files.length} images</span>
      </div>
      <div class="image-grid" data-cat="${ci}"
           ondragover="skDragOver(event)" ondrop="skDrop(event, ${ci})" ondragleave="skDragLeave(event)">
        ${cat.files.length === 0 ? '<div class="empty-msg">No images in this category</div>' : ''}
        ${cat.files.map((f, fi) => `
          <div class="image-card" draggable="true" data-cat="${ci}" data-idx="${fi}"
               ondragstart="skDragStart(event, ${ci}, ${fi})" ondragend="skDragEnd(event)">
            <img class="thumb" src="/uploads/${encodeURIComponent(f)}" alt="${esc(f)}" loading="lazy">
            <div class="name">${esc(f)}</div>
            <div class="remove-btn" onclick="skRemove(${ci}, ${fi})" title="Remove">&times;</div>
          </div>
        `).join('')}
        <div class="add-zone" onclick="skUpload(${ci})">
          <div style="font-size:28px">+</div>
          Add images
        </div>
      </div>
    </div>
  `).join('');
}

let skDragCat = -1, skDragIdx = -1;
function skDragStart(e, ci, fi) { skDragCat = ci; skDragIdx = fi; e.target.classList.add('dragging'); e.dataTransfer.effectAllowed = 'move'; }
function skDragEnd(e) { e.target.classList.remove('dragging'); document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over')); }
function skDragOver(e) { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; e.currentTarget.classList.add('drag-over'); }
function skDragLeave(e) { if (!e.currentTarget.contains(e.relatedTarget)) e.currentTarget.classList.remove('drag-over'); }
function skDrop(e, targetCat) {
  e.preventDefault(); e.currentTarget.classList.remove('drag-over');
  if (skDragCat < 0) return;
  const file = SKETCHES[skDragCat].files[skDragIdx];
  const cards = [...e.currentTarget.querySelectorAll('.image-card')];
  let dropIdx = SKETCHES[targetCat].files.length;
  for (let i = 0; i < cards.length; i++) { const r = cards[i].getBoundingClientRect(); if (e.clientX < r.left + r.width/2) { dropIdx = parseInt(cards[i].dataset.idx); break; } }
  SKETCHES[skDragCat].files.splice(skDragIdx, 1);
  if (skDragCat === targetCat && skDragIdx < dropIdx) dropIdx--;
  SKETCHES[targetCat].files.splice(dropIdx, 0, file);
  skDragCat = -1; skDragIdx = -1; markDirty(); render();
}
function skRemove(ci, fi) {
  const f = SKETCHES[ci].files[fi];
  if (!confirm('Remove "' + f + '" from ' + SKETCHES[ci].title + '?')) return;
  SKETCHES[ci].files.splice(fi, 1); markDirty(); render(); showToast('Removed ' + f);
}
function skUpload(ci) {
  const input = document.createElement('input'); input.type = 'file'; input.accept = 'image/*'; input.multiple = true;
  input.onchange = async () => {
    const files = [...input.files]; if (!files.length) return;
    const btn = document.getElementById('saveBtn'); btn.disabled = true; btn.textContent = 'Uploading...';
    for (const file of files) {
      const fd = new FormData(); fd.append('file', file);
      try { const r = await fetch('/api/upload', { method: 'POST', body: fd }); const res = await r.json(); if (res.filename) SKETCHES[ci].files.push(res.filename); }
      catch (err) { showToast('Upload failed: ' + err.message, 4000); }
    }
    btn.disabled = false; markDirty(); render(); showToast('Added ' + files.length + ' image(s)');
  };
  input.click();
}

// ══════════════════════════════════════════
//  PROJECTS
// ══════════════════════════════════════════

const COLORS = [
  { color: '#3FA7D6', bg: '#EBF1FF', label: 'Blue' },
  { color: '#FF6F61', bg: '#FFF3EB', label: 'Red' },
  { color: '#8B6DFF', bg: '#EFEBFF', label: 'Purple' },
  { color: '#59C29D', bg: '#E0FAEC', label: 'Green' },
  { color: '#E0A400', bg: '#FFFAEB', label: 'Yellow' },
];

function renderProjects() {
  document.getElementById('projects-section').innerHTML = `
    <p style="font-size:14px;opacity:.6;margin-bottom:16px;">The first project is the <strong>featured</strong> card (shown large). Drag to reorder.</p>
    <div class="proj-list">
      ${PROJECTS.map((p, i) => `
        <div class="proj-card ${i === 0 ? 'featured' : ''}" draggable="true" data-pidx="${i}"
             ondragstart="pjDragStart(event, ${i})" ondragend="pjDragEnd(event)"
             ondragover="pjDragOver(event, ${i})" ondrop="pjDrop(event, ${i})">
          ${p.img && p.img.startsWith('uploads/') ? '<img class="proj-thumb" src="/' + esc(p.img) + '" onerror="this.style.background=\'#ffe0e0\'">' : '<div class="proj-thumb" style="display:flex;align-items:center;justify-content:center;color:#8B6DFF;font-size:12px;">No image</div>'}
          <div class="proj-info">
            <h3>${esc(p.title)} ${i === 0 ? '<span class="proj-badge">Featured</span>' : ''}</h3>
            <p>${esc(p.desc)}</p>
            <div class="proj-tags">${esc(p.tags)}</div>
            <div class="proj-link">${esc(p.href)}</div>
          </div>
          <div class="proj-actions">
            <button class="btn btn-secondary" onclick="event.stopPropagation(); projEdit(${i})" style="padding:6px 12px;font-size:13px;">Edit</button>
            <button class="btn btn-danger" onclick="event.stopPropagation(); projRemove(${i})" style="padding:6px 12px;font-size:13px;">&times;</button>
          </div>
        </div>
      `).join('')}
      <div class="add-proj-btn" onclick="projAdd()">+ Add new project</div>
    </div>
  `;
}

let pjDragIdx = -1;
function pjDragStart(e, i) { pjDragIdx = i; e.target.classList.add('dragging'); e.dataTransfer.effectAllowed = 'move'; }
function pjDragEnd(e) { pjDragIdx = -1; e.target.classList.remove('dragging'); }
function pjDragOver(e, i) { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; }
function pjDrop(e, targetIdx) {
  e.preventDefault();
  if (pjDragIdx < 0 || pjDragIdx === targetIdx) return;
  const item = PROJECTS.splice(pjDragIdx, 1)[0];
  PROJECTS.splice(targetIdx, 0, item);
  pjDragIdx = -1; markDirty(); render();
  showToast('Reordered — ' + (targetIdx === 0 ? 'now featured!' : 'moved'));
}

function projRemove(i) {
  if (!confirm('Remove project "' + PROJECTS[i].title + '"?')) return;
  PROJECTS.splice(i, 1); markDirty(); render(); showToast('Project removed');
}

function projEdit(i) { projModal(i); }
function projAdd() { projModal(-1); }

function projModal(idx) {
  const isNew = idx < 0;
  const p = isNew ? { title: '', desc: '', tags: '', color: '#3FA7D6', bg: '#EBF1FF', rot: 0, href: '', img: '' } : { ...PROJECTS[idx] };

  const root = document.getElementById('modalRoot');
  root.innerHTML = `
    <div class="modal-overlay" onclick="if(event.target===this)closeModal()">
      <div class="modal">
        <h2>${isNew ? 'Add Project' : 'Edit Project'}</h2>
        <label>Title</label>
        <input type="text" id="pf_title" value="${esc(p.title)}">
        <label>Description</label>
        <textarea id="pf_desc">${esc(p.desc)}</textarea>
        <label>Tags (e.g. "UI · Mobile")</label>
        <input type="text" id="pf_tags" value="${esc(p.tags)}">
        <label>Behance / Link URL</label>
        <input type="text" id="pf_href" value="${esc(p.href)}">
        <label>Image (path in uploads/)</label>
        <div style="display:flex;gap:8px;align-items:center;">
          <input type="text" id="pf_img" value="${esc(p.img)}" style="flex:1">
          <button class="btn btn-secondary" onclick="projUploadImg()" style="padding:6px 12px;font-size:13px;white-space:nowrap;">Upload</button>
        </div>
        <label>Accent Color</label>
        <div class="color-row">
          ${COLORS.map(c => `<div class="color-swatch ${p.color === c.color ? 'active' : ''}" style="background:${c.color}" title="${c.label}" onclick="pickColor(this, '${c.color}', '${c.bg}')"></div>`).join('')}
        </div>
        <input type="hidden" id="pf_color" value="${p.color}">
        <input type="hidden" id="pf_bg" value="${p.bg}">
        <div class="modal-actions">
          <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
          <button class="btn btn-primary" onclick="projSaveModal(${idx})">Save</button>
        </div>
      </div>
    </div>
  `;
}

function pickColor(el, color, bg) {
  document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('pf_color').value = color;
  document.getElementById('pf_bg').value = bg;
}

function closeModal() { document.getElementById('modalRoot').innerHTML = ''; }

function projUploadImg() {
  const input = document.createElement('input'); input.type = 'file'; input.accept = 'image/*';
  input.onchange = async () => {
    if (!input.files.length) return;
    const fd = new FormData(); fd.append('file', input.files[0]);
    try {
      const r = await fetch('/api/upload', { method: 'POST', body: fd });
      const res = await r.json();
      if (res.filename) {
        document.getElementById('pf_img').value = 'uploads/' + res.filename;
        showToast('Uploaded: ' + res.filename);
      }
    } catch (err) { showToast('Upload failed', 4000); }
  };
  input.click();
}

function projSaveModal(idx) {
  const p = {
    title: document.getElementById('pf_title').value.trim(),
    desc: document.getElementById('pf_desc').value.trim(),
    tags: document.getElementById('pf_tags').value.trim(),
    color: document.getElementById('pf_color').value,
    bg: document.getElementById('pf_bg').value,
    rot: (idx >= 0 ? PROJECTS[idx].rot : [1.5, -1.5, 2, -2][PROJECTS.length % 4]),
    href: document.getElementById('pf_href').value.trim(),
    img: document.getElementById('pf_img').value.trim(),
  };
  if (!p.title) { showToast('Title is required'); return; }
  if (idx < 0) PROJECTS.push(p);
  else PROJECTS[idx] = p;
  closeModal(); markDirty(); render();
  showToast(idx < 0 ? 'Project added' : 'Project updated');
}

// ══════════════════════════════════════════
//  SAVE
// ══════════════════════════════════════════

function render() { renderSketches(); renderProjects(); }

async function saveAll() {
  const btn = document.getElementById('saveBtn');
  btn.disabled = true; btn.textContent = 'Saving...';
  try {
    const res = await fetch('/api/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sketches: SKETCHES, projects: PROJECTS }),
    });
    const result = await res.json();
    if (result.ok) { dirty = false; btn.textContent = 'Save & Build'; showToast('Saved & rebuilt index.html'); }
    else { showToast('Error: ' + (result.error || 'Unknown'), 4000); btn.textContent = 'Save & Build'; }
  } catch (err) { showToast('Save failed: ' + err.message, 4000); btn.textContent = 'Save & Build'; }
  btn.disabled = false;
}

window.onbeforeunload = () => dirty ? 'Unsaved changes' : null;
loadData();
</script>
</body>
</html>"""


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json_response(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(body)

    def _html_response(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path in ('/', ''):
            self._html_response(DASHBOARD_HTML)
            return

        if path == '/api/sketches':
            try: self._json_response(read_sketches())
            except Exception as e: self._json_response({'error': str(e)}, 500)
            return

        if path == '/api/projects':
            try: self._json_response(read_projects())
            except Exception as e: self._json_response({'error': str(e)}, 500)
            return

        if path.startswith('/uploads/'):
            filename = urllib.parse.unquote(path[len('/uploads/'):])
            filepath = os.path.join(UPLOADS, filename)
            if not os.path.abspath(filepath).startswith(os.path.abspath(UPLOADS)):
                self.send_error(403); return
            if not os.path.isfile(filepath):
                self.send_error(404); return
            ext = os.path.splitext(filename)[1].lower()
            mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                        '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml'}
            with open(filepath, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', mime_map.get(ext, 'application/octet-stream'))
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
                body = json.loads(self.rfile.read(length))
                write_sketches(body['sketches'])
                write_projects(body['projects'])
                result = subprocess.run(
                    ['python3', BUILD_PY], cwd=BASE,
                    capture_output=True, text=True, timeout=30
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
                    self._json_response({'error': 'Expected multipart/form-data'}, 400); return
                boundary = content_type.split('boundary=')[1].strip()
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                for part in body.split(('--' + boundary).encode()):
                    if b'filename="' not in part:
                        continue
                    header_end = part.find(b'\r\n\r\n')
                    headers_raw = part[:header_end].decode('utf-8', errors='replace')
                    file_data = part[header_end + 4:]
                    if file_data.endswith(b'\r\n'):
                        file_data = file_data[:-2]
                    fn_match = re.search(r'filename="([^"]+)"', headers_raw)
                    if not fn_match:
                        continue
                    safe_name = re.sub(r'[^\w\-.]', '_', fn_match.group(1))
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
    print(f'Portfolio Dashboard running at {url}')
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
