#!/usr/bin/env python3
"""
Portfolio Dashboard — manage all portfolio content.

Usage:  python3 dashboard.py
Opens:  http://localhost:4444

Tabs: Sketches, Projects, Journey, Skills, Socials
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
BUILD_PY = os.path.join(BASE, 'build.py')

CONFIG_FILES = {
    'sketches':  (os.path.join(BASE, 'sketches.js'),  'SKETCH_CATEGORIES'),
    'projects':  (os.path.join(BASE, 'projects.js'),  'PROJECT_DEFINITIONS'),
    'journey':   (os.path.join(BASE, 'journey.js'),   'JOURNEY_STEPS'),
    'skills':    (os.path.join(BASE, 'skills.js'),    'SKILL_DEFINITIONS'),
    'socials':   (os.path.join(BASE, 'socials.js'),   'SOCIAL_LINKS'),
}


def _parse_js_array(filepath, var_name):
    with open(filepath, 'r') as f:
        src = f.read()
    match = re.search(rf'var {var_name}\s*=\s*(\[.*?\]);', src, re.DOTALL)
    if not match:
        return []
    raw = match.group(1)
    raw = re.sub(r'^\s*//[^\n]*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r"'([^']*)',", r'"\1",', raw)
    raw = re.sub(r"'([^']*)'\s*([}\]])", r'"\1" \2', raw)
    raw = re.sub(r'(?<=[{,\n])\s*(\w+)\s*:', r' "\1":', raw)
    raw = re.sub(r',\s*([}\]])', r' \1', raw)
    return json.loads(raw)


def read_all():
    return {k: _parse_js_array(path, var) for k, (path, var) in CONFIG_FILES.items()}


def _write_js(filepath, var_name, comment_lines, data, fields):
    lines = ['/*']
    for c in comment_lines:
        lines.append(' * ' + c if c else ' *')
    lines += [' */', '', '// eslint-disable-next-line no-unused-vars', f'var {var_name} = [']
    for item in data:
        lines.append('  {')
        for key in fields:
            val = item.get(key, '')
            if isinstance(val, (int, float)):
                lines.append(f'    {key}: {val},')
            else:
                lines.append(f'    {key}: {json.dumps(val)},')
        lines.append('  },')
    lines += ['];', '']
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines))


def write_sketches(data):
    lines = ['/*', ' * ─── SKETCHES CONFIG ───',
        ' * Edit filenames to change images, reorder lines to change display order.',
        ' */', '', '// eslint-disable-next-line no-unused-vars', 'var SKETCH_CATEGORIES = [']
    for cat in data:
        lines.append('')
        lines.append(f'  // ── {cat["title"]} ──')
        lines.append('  {')
        for k in ('title', 'note', 'icon', 'color'):
            lines.append(f'    {k}: {json.dumps(cat.get(k, ""))},')
        lines.append('    files: [')
        for fn in cat.get('files', []):
            lines.append(f'      {json.dumps(fn)},')
        lines.append('    ],')
        lines.append('  },')
    lines += ['];', '']
    with open(CONFIG_FILES['sketches'][0], 'w') as f:
        f.write('\n'.join(lines))


def write_all(payload):
    write_sketches(payload.get('sketches', []))
    _write_js(CONFIG_FILES['projects'][0], 'PROJECT_DEFINITIONS',
              ['─── PROJECTS CONFIG ───', 'First project is the large featured card.'],
              payload.get('projects', []),
              ['title', 'desc', 'tags', 'color', 'bg', 'rot', 'href', 'img'])
    _write_js(CONFIG_FILES['journey'][0], 'JOURNEY_STEPS',
              ['─── JOURNEY CONFIG ───', 'Each step is a panel in the storyboard.'],
              payload.get('journey', []),
              ['title', 'icon', 'color', 'bg', 'body'])
    _write_js(CONFIG_FILES['skills'][0], 'SKILL_DEFINITIONS',
              ['─── SKILLS CONFIG ───', '"What I do" cards on the home page.'],
              payload.get('skills', []),
              ['label', 'icon', 'color', 'rot', 'sub'])
    _write_js(CONFIG_FILES['socials'][0], 'SOCIAL_LINKS',
              ['─── SOCIAL LINKS CONFIG ───', 'Social media links in the contact section.'],
              payload.get('socials', []),
              ['label', 'icon', 'color', 'href'])


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portfolio Dashboard</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f5f1eb; color:#201B13; min-height:100vh; }

.topbar { background:#201B13; color:#FCF8F0; padding:16px 28px; display:flex; align-items:center; justify-content:space-between; gap:16px; position:sticky; top:0; z-index:100; flex-wrap:wrap; }
.topbar h1 { font-size:20px; font-weight:700; }
.topbar .actions { display:flex; gap:10px; flex-wrap:wrap; }
.btn { padding:8px 18px; border:2px solid #201B13; border-radius:10px; font-weight:600; font-size:14px; cursor:pointer; transition:all .15s; }
.btn-primary { background:#59C29D; color:#fff; border-color:#59C29D; }
.btn-primary:hover { background:#4ab08c; }
.btn-secondary { background:#fff; color:#201B13; }
.btn-secondary:hover { background:#f0ece4; }
.btn-danger { background:#FF6F61; color:#fff; border-color:#FF6F61; }
.btn-danger:hover { background:#e55a4d; }
.btn:disabled { opacity:.5; cursor:not-allowed; }

.tabs { display:flex; gap:0; margin-bottom:24px; border-bottom:2.5px solid #201B13; overflow-x:auto; }
.tab { padding:12px 20px; font-weight:700; font-size:15px; cursor:pointer; border:2.5px solid transparent; border-bottom:none; border-radius:12px 12px 0 0; margin-bottom:-2.5px; transition:all .15s; white-space:nowrap; }
.tab:hover { background:rgba(139,109,255,.06); }
.tab.active { background:#fff; border-color:#201B13; }

.toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:#201B13; color:#FCF8F0; padding:12px 24px; border-radius:12px; font-weight:600; font-size:14px; z-index:200; display:none; box-shadow:0 4px 20px rgba(0,0,0,.25); }
.toast.show { display:block; animation:fadeInUp .3s ease; }
@keyframes fadeInUp { from{opacity:0;transform:translateX(-50%) translateY(12px)} to{opacity:1;transform:translateX(-50%) translateY(0)} }

.container { max-width:1200px; margin:0 auto; padding:24px; }
.section { display:none; }
.section.active { display:block; }

/* Sketches */
.category { background:#fff; border:2.5px solid #201B13; border-radius:16px; margin-bottom:24px; box-shadow:4px 4px 0 rgba(32,27,19,.15); overflow:hidden; }
.cat-header { padding:16px 20px; display:flex; align-items:center; gap:12px; border-bottom:2px dashed rgba(32,27,19,.15); flex-wrap:wrap; }
.cat-dot { width:14px; height:14px; border-radius:50%; border:2px solid #201B13; flex:none; }
.cat-title { font-size:20px; font-weight:700; }
.cat-note { font-size:14px; opacity:.6; }
.cat-count { font-size:13px; font-weight:600; background:#f0ece4; padding:3px 10px; border-radius:999px; margin-left:auto; }
.image-grid { display:flex; flex-wrap:wrap; gap:16px; padding:20px; min-height:100px; transition:background .15s; }
.image-grid.drag-over { background:rgba(89,194,157,.08); }
.empty-msg { font-size:15px; opacity:.4; font-style:italic; padding:20px; }
.image-card { position:relative; width:150px; cursor:grab; transition:transform .12s; user-select:none; }
.image-card:hover { transform:translateY(-3px); }
.image-card.dragging { opacity:.4; transform:scale(.95); }
.image-card .thumb { width:150px; height:150px; object-fit:cover; border:2.5px solid #201B13; border-radius:10px; display:block; background:#f2ede3; pointer-events:none; }
.image-card .name { font-size:11px; font-weight:600; margin-top:5px; text-align:center; word-break:break-all; opacity:.7; }
.image-card .remove-btn { position:absolute; top:-8px; right:-8px; width:24px; height:24px; background:#FF6F61; color:#fff; border:2px solid #201B13; border-radius:50%; font-size:14px; font-weight:700; cursor:pointer; display:flex; align-items:center; justify-content:center; opacity:0; transition:opacity .15s; line-height:1; }
.image-card:hover .remove-btn { opacity:1; }
.add-zone { width:150px; min-height:150px; border:2.5px dashed rgba(32,27,19,.25); border-radius:10px; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px; cursor:pointer; color:#8B6DFF; font-size:13px; font-weight:600; transition:background .15s; }
.add-zone:hover { background:rgba(139,109,255,.06); }

/* Cards (projects, journey, skills, socials) */
.card-list { display:flex; flex-direction:column; gap:14px; }
.card { background:#fff; border:2.5px solid #201B13; border-radius:16px; box-shadow:4px 4px 0 rgba(32,27,19,.15); display:flex; gap:16px; padding:16px; align-items:center; cursor:grab; transition:transform .12s; user-select:none; }
.card:hover { transform:translateY(-2px); }
.card.dragging { opacity:.4; }
.card.featured { border-color:#FFC53D; box-shadow:4px 4px 0 #FFC53D; }
.card-thumb { width:100px; height:70px; object-fit:cover; border:2px solid #201B13; border-radius:8px; background:#f2ede3; flex:none; }
.card-info { flex:1; min-width:0; }
.card-info h3 { font-size:15px; margin-bottom:3px; }
.card-info p { font-size:13px; opacity:.7; margin-bottom:2px; }
.card-info .tags { font-size:12px; font-weight:600; color:#8B6DFF; }
.card-info .link { font-size:11px; opacity:.4; word-break:break-all; }
.card-actions { display:flex; gap:8px; flex:none; }
.card-badge { font-size:11px; font-weight:700; background:#FFC53D; border:2px solid #201B13; border-radius:999px; padding:2px 10px; }
.card-icon { width:40px; height:40px; border-radius:50%; border:2px solid #201B13; display:flex; align-items:center; justify-content:center; font-size:20px; color:#fff; flex:none; }
.add-card { border:2.5px dashed rgba(32,27,19,.25); border-radius:16px; padding:18px; text-align:center; cursor:pointer; font-weight:600; font-size:15px; color:#8B6DFF; transition:background .15s; }
.add-card:hover { background:rgba(139,109,255,.06); }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,.5); z-index:150; display:flex; align-items:center; justify-content:center; }
.modal { background:#fff; border:2.5px solid #201B13; border-radius:16px; padding:28px; width:520px; max-width:90vw; max-height:90vh; overflow-y:auto; box-shadow:6px 6px 0 rgba(32,27,19,.3); }
.modal h2 { font-size:20px; margin-bottom:16px; }
.modal label { display:block; font-weight:600; font-size:14px; margin-bottom:4px; margin-top:14px; }
.modal input[type=text], .modal textarea { width:100%; padding:8px 12px; border:2px solid #201B13; border-radius:8px; font-size:14px; font-family:inherit; }
.modal textarea { resize:vertical; min-height:60px; }
.modal .modal-actions { display:flex; gap:10px; margin-top:20px; justify-content:flex-end; }
.color-row { display:flex; gap:8px; margin-top:6px; flex-wrap:wrap; }
.color-swatch { width:32px; height:32px; border-radius:50%; border:3px solid transparent; cursor:pointer; transition:border-color .15s; }
.color-swatch:hover, .color-swatch.active { border-color:#201B13; }
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
  <div class="tabs" id="tabsBar"></div>
  <div id="sketches-section" class="section active"></div>
  <div id="projects-section" class="section"></div>
  <div id="journey-section" class="section"></div>
  <div id="skills-section" class="section"></div>
  <div id="socials-section" class="section"></div>
</div>
<div class="toast" id="toast"></div>
<div id="modalRoot"></div>

<script>
const TABS = ['Sketches','Projects','Journey','Skills','Socials'];
const COLORS = [
  {color:'#3FA7D6',bg:'#EBF1FF',label:'Blue'},
  {color:'#FF6F61',bg:'#FFF3EB',label:'Red'},
  {color:'#8B6DFF',bg:'#EFEBFF',label:'Purple'},
  {color:'#59C29D',bg:'#E0FAEC',label:'Green'},
  {color:'#E0A400',bg:'#FFFAEB',label:'Yellow'},
];
const COLORS_EXT = [...COLORS, {color:'#FF6F61',bg:'#FFEBEC',label:'Red alt'}];

let D = { sketches:[], projects:[], journey:[], skills:[], socials:[] };
let dirty = false, activeTab = 'sketches';

function esc(s) { const d=document.createElement('div'); d.textContent=s||''; return d.innerHTML; }
function showToast(msg,ms) { const t=document.getElementById('toast'); t.textContent=msg; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),ms||2500); }
function markDirty() { dirty=true; document.getElementById('saveBtn').textContent='Save & Build *'; }
function closeModal() { document.getElementById('modalRoot').innerHTML=''; }
function colorPicker(id, bgId, current) {
  return `<div class="color-row">${COLORS.map(c=>`<div class="color-swatch ${current===c.color?'active':''}" style="background:${c.color}" onclick="document.getElementById('${id}').value='${c.color}';document.getElementById('${bgId}').value='${c.bg}';document.querySelectorAll('#${id}_row .color-swatch').forEach(s=>s.classList.remove('active'));this.classList.add('active')"></div>`).join('')}</div>`;
}

// ── Tabs ──
function renderTabs() {
  document.getElementById('tabsBar').innerHTML = TABS.map(t=>`<div class="tab ${t.toLowerCase()===activeTab?'active':''}" onclick="switchTab('${t.toLowerCase()}')">${t}</div>`).join('');
}
function switchTab(t) {
  activeTab=t; renderTabs();
  TABS.forEach(n=>document.getElementById(n.toLowerCase()+'-section').classList.toggle('active', n.toLowerCase()===t));
}

// ── Load & Save ──
async function loadData() { const r=await fetch('/api/config'); D=await r.json(); render(); }
async function saveAll() {
  const btn=document.getElementById('saveBtn'); btn.disabled=true; btn.textContent='Saving...';
  try {
    const r=await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(D)});
    const res=await r.json();
    if(res.ok){dirty=false;btn.textContent='Save & Build';showToast('Saved & rebuilt index.html');}
    else{showToast('Error: '+(res.error||'Unknown'),4000);btn.textContent='Save & Build';}
  } catch(e){showToast('Save failed: '+e.message,4000);btn.textContent='Save & Build';}
  btn.disabled=false;
}
window.onbeforeunload=()=>dirty?'Unsaved changes':null;

// ══════════════════════════════════════
//  SKETCHES
// ══════════════════════════════════════
let skDC=-1, skDI=-1;
function renderSketches() {
  document.getElementById('sketches-section').innerHTML = D.sketches.map((cat,ci)=>`
    <div class="category"><div class="cat-header">
      <div class="cat-dot" style="background:${cat.color}"></div>
      <span class="cat-title">${esc(cat.title)}</span><span class="cat-note">${esc(cat.note)}</span>
      <span class="cat-count">${cat.files.length} images</span>
    </div><div class="image-grid" data-cat="${ci}" ondragover="event.preventDefault();event.dataTransfer.dropEffect='move';this.classList.add('drag-over')" ondragleave="if(!this.contains(event.relatedTarget))this.classList.remove('drag-over')" ondrop="skDrop(event,${ci})">
      ${cat.files.length===0?'<div class="empty-msg">No images</div>':''}
      ${cat.files.map((f,fi)=>`<div class="image-card" draggable="true" data-cat="${ci}" data-idx="${fi}" ondragstart="skDC=${ci};skDI=${fi};this.classList.add('dragging')" ondragend="this.classList.remove('dragging');document.querySelectorAll('.drag-over').forEach(e=>e.classList.remove('drag-over'))">
        <img class="thumb" src="/uploads/${encodeURIComponent(f)}" loading="lazy">
        <div class="name">${esc(f)}</div>
        <div class="remove-btn" onclick="if(confirm('Remove ${esc(f).replace(/'/g,"\\'")}?')){D.sketches[${ci}].files.splice(${fi},1);markDirty();render()}">&times;</div>
      </div>`).join('')}
      <div class="add-zone" onclick="skUpload(${ci})"><div style="font-size:28px">+</div>Add</div>
    </div></div>`).join('');
}
function skDrop(e,tc){e.preventDefault();e.currentTarget.classList.remove('drag-over');if(skDC<0)return;
  const f=D.sketches[skDC].files[skDI],cards=[...e.currentTarget.querySelectorAll('.image-card')];
  let di=D.sketches[tc].files.length;
  for(let i=0;i<cards.length;i++){const r=cards[i].getBoundingClientRect();if(e.clientX<r.left+r.width/2){di=parseInt(cards[i].dataset.idx);break;}}
  D.sketches[skDC].files.splice(skDI,1);if(skDC===tc&&skDI<di)di--;D.sketches[tc].files.splice(di,0,f);skDC=-1;skDI=-1;markDirty();render();}
function skUpload(ci){const inp=document.createElement('input');inp.type='file';inp.accept='image/*';inp.multiple=true;
  inp.onchange=async()=>{for(const f of inp.files){const fd=new FormData();fd.append('file',f);try{const r=await fetch('/api/upload',{method:'POST',body:fd});const res=await r.json();if(res.filename)D.sketches[ci].files.push(res.filename);}catch(e){showToast('Upload failed',4000);}}markDirty();render();showToast('Images added');};inp.click();}

// ══════════════════════════════════════
//  GENERIC CARD LIST (projects, journey, skills, socials)
// ══════════════════════════════════════
function dragList(key){let di=-1;
  window['dl_'+key+'_start']=function(e,i){di=i;e.target.closest('.card').classList.add('dragging');e.dataTransfer.effectAllowed='move';};
  window['dl_'+key+'_end']=function(e){di=-1;e.target.closest('.card').classList.remove('dragging');};
  window['dl_'+key+'_over']=function(e){e.preventDefault();e.dataTransfer.dropEffect='move';};
  window['dl_'+key+'_drop']=function(e,ti){e.preventDefault();if(di<0||di===ti)return;const item=D[key].splice(di,1)[0];D[key].splice(ti,0,item);di=-1;markDirty();render();showToast('Reordered');};
}
dragList('projects');dragList('journey');dragList('skills');dragList('socials');

// ══════════════════════════════════════
//  PROJECTS
// ══════════════════════════════════════
function renderProjects(){
  document.getElementById('projects-section').innerHTML=`
    <p style="font-size:14px;opacity:.6;margin-bottom:16px">First project is the <strong>featured</strong> card. Drag to reorder.</p>
    <div class="card-list">${D.projects.map((p,i)=>`
      <div class="card ${i===0?'featured':''}" draggable="true" ondragstart="dl_projects_start(event,${i})" ondragend="dl_projects_end(event)" ondragover="dl_projects_over(event)" ondrop="dl_projects_drop(event,${i})">
        ${p.img&&p.img.startsWith('uploads/')?`<img class="card-thumb" src="/${esc(p.img)}">`:'<div class="card-thumb" style="display:flex;align-items:center;justify-content:center;color:#8B6DFF;font-size:11px">No img</div>'}
        <div class="card-info"><h3>${esc(p.title)} ${i===0?'<span class="card-badge">Featured</span>':''}</h3><p>${esc(p.desc)}</p><div class="tags">${esc(p.tags)}</div><div class="link">${esc(p.href)}</div></div>
        <div class="card-actions"><button class="btn btn-secondary" onclick="event.stopPropagation();projModal(${i})" style="padding:6px 12px;font-size:13px">Edit</button><button class="btn btn-danger" onclick="event.stopPropagation();if(confirm('Remove?')){D.projects.splice(${i},1);markDirty();render()}" style="padding:6px 12px;font-size:13px">&times;</button></div>
      </div>`).join('')}
      <div class="add-card" onclick="projModal(-1)">+ Add new project</div>
    </div>`;
}
function projModal(idx){
  const isNew=idx<0, p=isNew?{title:'',desc:'',tags:'',color:'#3FA7D6',bg:'#EBF1FF',rot:0,href:'',img:''}:{...D.projects[idx]};
  document.getElementById('modalRoot').innerHTML=`<div class="modal-overlay" onclick="if(event.target===this)closeModal()"><div class="modal">
    <h2>${isNew?'Add':'Edit'} Project</h2>
    <label>Title</label><input type="text" id="m_title" value="${esc(p.title)}">
    <label>Description</label><textarea id="m_desc">${esc(p.desc)}</textarea>
    <label>Tags</label><input type="text" id="m_tags" value="${esc(p.tags)}">
    <label>Behance / Link</label><input type="text" id="m_href" value="${esc(p.href)}">
    <label>Image</label><div style="display:flex;gap:8px"><input type="text" id="m_img" value="${esc(p.img)}" style="flex:1"><button class="btn btn-secondary" onclick="doUpload(function(fn){document.getElementById('m_img').value='uploads/'+fn})" style="padding:6px 12px;font-size:13px">Upload</button></div>
    <label>Color</label><div id="m_color_row">${colorPicker('m_color','m_bg',p.color)}</div><input type="hidden" id="m_color" value="${p.color}"><input type="hidden" id="m_bg" value="${p.bg}">
    <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="projSave(${idx})">Save</button></div>
  </div></div>`;
}
function projSave(idx){
  const p={title:document.getElementById('m_title').value.trim(),desc:document.getElementById('m_desc').value.trim(),tags:document.getElementById('m_tags').value.trim(),
    color:document.getElementById('m_color').value,bg:document.getElementById('m_bg').value,rot:idx>=0?D.projects[idx].rot:[1.5,-1.5,2,-2][D.projects.length%4],
    href:document.getElementById('m_href').value.trim(),img:document.getElementById('m_img').value.trim()};
  if(!p.title){showToast('Title required');return;}
  if(idx<0)D.projects.push(p);else D.projects[idx]=p;closeModal();markDirty();render();showToast(idx<0?'Added':'Updated');
}

// ══════════════════════════════════════
//  JOURNEY
// ══════════════════════════════════════
function renderJourney(){
  document.getElementById('journey-section').innerHTML=`
    <p style="font-size:14px;opacity:.6;margin-bottom:16px">Timeline steps in the "My journey" storyboard. Drag to reorder.</p>
    <div class="card-list">${D.journey.map((s,i)=>`
      <div class="card" draggable="true" ondragstart="dl_journey_start(event,${i})" ondragend="dl_journey_end(event)" ondragover="dl_journey_over(event)" ondrop="dl_journey_drop(event,${i})">
        <div class="card-icon" style="background:${s.color}"><i class="${esc(s.icon)}"></i></div>
        <div class="card-info"><h3>${esc(s.title)}</h3><p>${esc(s.body)}</p></div>
        <div class="card-actions"><button class="btn btn-secondary" onclick="event.stopPropagation();journeyModal(${i})" style="padding:6px 12px;font-size:13px">Edit</button><button class="btn btn-danger" onclick="event.stopPropagation();if(confirm('Remove?')){D.journey.splice(${i},1);markDirty();render()}" style="padding:6px 12px;font-size:13px">&times;</button></div>
      </div>`).join('')}
      <div class="add-card" onclick="journeyModal(-1)">+ Add step</div>
    </div>`;
}
function journeyModal(idx){
  const isNew=idx<0, s=isNew?{title:'',icon:'ri-star-line',color:'#3FA7D6',bg:'#EBF1FF',body:''}:{...D.journey[idx]};
  document.getElementById('modalRoot').innerHTML=`<div class="modal-overlay" onclick="if(event.target===this)closeModal()"><div class="modal">
    <h2>${isNew?'Add':'Edit'} Step</h2>
    <label>Title</label><input type="text" id="m_title" value="${esc(s.title)}">
    <label>Story</label><textarea id="m_body" style="min-height:100px">${esc(s.body)}</textarea>
    <label>Icon (e.g. ri-bank-line) — <a href="https://remixicon.com" target="_blank">browse icons</a></label><input type="text" id="m_icon" value="${esc(s.icon)}">
    <label>Color</label><div id="m_color_row">${colorPicker('m_color','m_bg',s.color)}</div><input type="hidden" id="m_color" value="${s.color}"><input type="hidden" id="m_bg" value="${s.bg}">
    <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="journeySave(${idx})">Save</button></div>
  </div></div>`;
}
function journeySave(idx){
  const s={title:document.getElementById('m_title').value.trim(),body:document.getElementById('m_body').value.trim(),
    icon:document.getElementById('m_icon').value.trim(),color:document.getElementById('m_color').value,bg:document.getElementById('m_bg').value};
  if(!s.title){showToast('Title required');return;}
  if(idx<0)D.journey.push(s);else D.journey[idx]=s;closeModal();markDirty();render();showToast(idx<0?'Added':'Updated');
}

// ══════════════════════════════════════
//  SKILLS
// ══════════════════════════════════════
function renderSkills(){
  document.getElementById('skills-section').innerHTML=`
    <p style="font-size:14px;opacity:.6;margin-bottom:16px">"What I do" cards on the home page. Drag to reorder.</p>
    <div class="card-list">${D.skills.map((s,i)=>`
      <div class="card" draggable="true" ondragstart="dl_skills_start(event,${i})" ondragend="dl_skills_end(event)" ondragover="dl_skills_over(event)" ondrop="dl_skills_drop(event,${i})">
        <div class="card-icon" style="background:${s.color}"><i class="${esc(s.icon)}"></i></div>
        <div class="card-info"><h3>${esc(s.label)}</h3><p>${esc(s.sub)}</p></div>
        <div class="card-actions"><button class="btn btn-secondary" onclick="event.stopPropagation();skillModal(${i})" style="padding:6px 12px;font-size:13px">Edit</button><button class="btn btn-danger" onclick="event.stopPropagation();if(confirm('Remove?')){D.skills.splice(${i},1);markDirty();render()}" style="padding:6px 12px;font-size:13px">&times;</button></div>
      </div>`).join('')}
      <div class="add-card" onclick="skillModal(-1)">+ Add skill</div>
    </div>`;
}
function skillModal(idx){
  const isNew=idx<0, s=isNew?{label:'',icon:'ri-star-line',color:'#3FA7D6',rot:0,sub:''}:{...D.skills[idx]};
  document.getElementById('modalRoot').innerHTML=`<div class="modal-overlay" onclick="if(event.target===this)closeModal()"><div class="modal">
    <h2>${isNew?'Add':'Edit'} Skill</h2>
    <label>Label</label><input type="text" id="m_label" value="${esc(s.label)}">
    <label>Description</label><input type="text" id="m_sub" value="${esc(s.sub)}">
    <label>Icon — <a href="https://remixicon.com" target="_blank">browse icons</a></label><input type="text" id="m_icon" value="${esc(s.icon)}">
    <label>Color</label><div id="m_color_row">${colorPicker('m_color','m_bg',s.color)}</div><input type="hidden" id="m_color" value="${s.color}"><input type="hidden" id="m_bg" value="">
    <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="skillSave(${idx})">Save</button></div>
  </div></div>`;
}
function skillSave(idx){
  const s={label:document.getElementById('m_label').value.trim(),sub:document.getElementById('m_sub').value.trim(),
    icon:document.getElementById('m_icon').value.trim(),color:document.getElementById('m_color').value,
    rot:idx>=0?D.skills[idx].rot:[-2,1.5,-1,2,-1.5,1][D.skills.length%6]};
  if(!s.label){showToast('Label required');return;}
  if(idx<0)D.skills.push(s);else D.skills[idx]=s;closeModal();markDirty();render();showToast(idx<0?'Added':'Updated');
}

// ══════════════════════════════════════
//  SOCIALS
// ══════════════════════════════════════
function renderSocials(){
  document.getElementById('socials-section').innerHTML=`
    <p style="font-size:14px;opacity:.6;margin-bottom:16px">Social media links in the contact section.</p>
    <div class="card-list">${D.socials.map((s,i)=>`
      <div class="card" draggable="true" ondragstart="dl_socials_start(event,${i})" ondragend="dl_socials_end(event)" ondragover="dl_socials_over(event)" ondrop="dl_socials_drop(event,${i})">
        <div class="card-icon" style="background:${s.color}"><i class="${esc(s.icon)}"></i></div>
        <div class="card-info"><h3>${esc(s.label)}</h3><div class="link">${esc(s.href)}</div></div>
        <div class="card-actions"><button class="btn btn-secondary" onclick="event.stopPropagation();socialModal(${i})" style="padding:6px 12px;font-size:13px">Edit</button><button class="btn btn-danger" onclick="event.stopPropagation();if(confirm('Remove?')){D.socials.splice(${i},1);markDirty();render()}" style="padding:6px 12px;font-size:13px">&times;</button></div>
      </div>`).join('')}
      <div class="add-card" onclick="socialModal(-1)">+ Add social link</div>
    </div>`;
}
function socialModal(idx){
  const isNew=idx<0, s=isNew?{label:'',icon:'ri-links-line',color:'#3FA7D6',href:''}:{...D.socials[idx]};
  document.getElementById('modalRoot').innerHTML=`<div class="modal-overlay" onclick="if(event.target===this)closeModal()"><div class="modal">
    <h2>${isNew?'Add':'Edit'} Social Link</h2>
    <label>Label (e.g. LinkedIn)</label><input type="text" id="m_label" value="${esc(s.label)}">
    <label>URL</label><input type="text" id="m_href" value="${esc(s.href)}">
    <label>Icon — <a href="https://remixicon.com" target="_blank">browse icons</a></label><input type="text" id="m_icon" value="${esc(s.icon)}">
    <label>Color</label><div id="m_color_row">${colorPicker('m_color','m_bg',s.color)}</div><input type="hidden" id="m_color" value="${s.color}"><input type="hidden" id="m_bg" value="">
    <div class="modal-actions"><button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="socialSave(${idx})">Save</button></div>
  </div></div>`;
}
function socialSave(idx){
  const s={label:document.getElementById('m_label').value.trim(),href:document.getElementById('m_href').value.trim(),
    icon:document.getElementById('m_icon').value.trim(),color:document.getElementById('m_color').value};
  if(!s.label){showToast('Label required');return;}
  if(idx<0)D.socials.push(s);else D.socials[idx]=s;closeModal();markDirty();render();showToast(idx<0?'Added':'Updated');
}

// ── Upload helper ──
function doUpload(cb){const inp=document.createElement('input');inp.type='file';inp.accept='image/*';
  inp.onchange=async()=>{if(!inp.files.length)return;const fd=new FormData();fd.append('file',inp.files[0]);
  try{const r=await fetch('/api/upload',{method:'POST',body:fd});const res=await r.json();if(res.filename){cb(res.filename);showToast('Uploaded');}}catch(e){showToast('Upload failed',4000);}};inp.click();}

// ── Render all ──
function render() { renderTabs(); renderSketches(); renderProjects(); renderJourney(); renderSkills(); renderSocials(); }
loadData();
</script>
<link href="https://cdn.jsdelivr.net/npm/remixicon@4.5.0/fonts/remixicon.css" rel="stylesheet">
</body>
</html>"""


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ('/', ''):
            body = DASHBOARD_HTML.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == '/api/config':
            try: self._json(read_all())
            except Exception as e: self._json({'error': str(e)}, 500)
            return
        if path.startswith('/uploads/'):
            filename = urllib.parse.unquote(path[len('/uploads/'):])
            filepath = os.path.join(UPLOADS, filename)
            if not os.path.abspath(filepath).startswith(os.path.abspath(UPLOADS)):
                self.send_error(403); return
            if not os.path.isfile(filepath):
                self.send_error(404); return
            ext = os.path.splitext(filename)[1].lower()
            mime = {'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.gif':'image/gif','.webp':'image/webp','.svg':'image/svg+xml'}.get(ext,'application/octet-stream')
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
                body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
                write_all(body)
                result = subprocess.run(['python3', BUILD_PY], cwd=BASE, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    self._json({'ok': False, 'error': result.stderr or result.stdout}, 500)
                else:
                    self._json({'ok': True})
            except Exception as e:
                self._json({'ok': False, 'error': str(e)}, 500)
            return
        if path == '/api/upload':
            try:
                ct = self.headers.get('Content-Type', '')
                if 'multipart/form-data' not in ct:
                    self._json({'error': 'Expected multipart'}, 400); return
                boundary = ct.split('boundary=')[1].strip()
                body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                for part in body.split(('--' + boundary).encode()):
                    if b'filename="' not in part: continue
                    he = part.find(b'\r\n\r\n')
                    hr = part[:he].decode('utf-8', errors='replace')
                    fd = part[he+4:]
                    if fd.endswith(b'\r\n'): fd = fd[:-2]
                    fm = re.search(r'filename="([^"]+)"', hr)
                    if not fm: continue
                    safe = re.sub(r'[^\w\-.]', '_', fm.group(1))
                    dest = os.path.join(UPLOADS, safe)
                    c = 1; base, ext = os.path.splitext(safe)
                    while os.path.exists(dest):
                        safe = f'{base}_{c}{ext}'; dest = os.path.join(UPLOADS, safe); c += 1
                    with open(dest, 'wb') as f: f.write(fd)
                    self._json({'filename': safe}); return
                self._json({'error': 'No file'}, 400)
            except Exception as e:
                self._json({'error': str(e)}, 500)
            return
        self.send_error(404)


if __name__ == '__main__':
    server = http.server.HTTPServer(('127.0.0.1', PORT), DashboardHandler)
    url = f'http://localhost:{PORT}'
    print(f'Portfolio Dashboard running at {url}')
    print('Press Ctrl+C to stop\n')
    try: webbrowser.open(url)
    except: pass
    try: server.serve_forever()
    except KeyboardInterrupt: print('\nStopped.'); server.server_close()
