class Component extends DCLogic {
  state = { screen: 'home', step: 0, cName: '', cEmail: '', cMsg: '', overrides: {}, selected: null, portraitImg: 'uploads/portrait.png', pX: 0, pY: 0, pScale: 1, activeGame: 'puzzle', tttBoard: Array(9).fill(''), tttTurn: 'X', skPuzzle: 0, skBoard: null, skSel: -1, fpTiles: null, fpMoves: 0, fpImgIdx: 0 };
  fileRef = React.createRef();

  _routes = [
    { key: 'home',     label: 'Home' },
    { key: 'journey',  label: 'My journey' },
    { key: 'sketches', label: 'My sketches' },
    { key: 'projects', label: 'My projects' },
    { key: 'contact',  label: 'Contact me' },
    { key: 'games',    label: 'Games' },
  ];

  componentDidMount() {
    try {
      const raw = localStorage.getItem('dr_sketch_overrides');
      if (raw) this.setState({ overrides: JSON.parse(raw) || {} });
    } catch (e) {}
    try {
      const p = localStorage.getItem('dr_portrait');
      if (p) { const o = JSON.parse(p); if (o && o.img) this.setState({ portraitImg: o.img, pX: o.x || 0, pY: o.y || 0, pScale: o.scale || 1 }); }
    } catch (e) {}
    const keys = this._routes.map(r => r.key);
    const hash = (location.hash || '').replace('#', '');
    if (hash && keys.includes(hash)) this.setState({ screen: hash });
    window.addEventListener('hashchange', () => {
      const h = (location.hash || '').replace('#', '');
      if (h && keys.includes(h) && h !== this.state.screen) this.setState({ screen: h });
    });
  }

  persistPortrait() {
    try {
      const { portraitImg, pX, pY, pScale } = this.state;
      localStorage.setItem('dr_portrait', JSON.stringify({ img: portraitImg, x: pX, y: pY, scale: pScale }));
    } catch (e) {}
  }

  handlePortraitFile(file) {
    if (!file || !/^image\//.test(file.type)) return;
    const reader = new FileReader();
    reader.onload = () => {
      const im = new Image();
      im.onload = () => {
        const max = 780; let w = im.width, h = im.height;
        const r = Math.min(1, max / Math.max(w, h));
        w = Math.round(w * r); h = Math.round(h * r);
        const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
        cv.getContext('2d').drawImage(im, 0, 0, w, h);
        let url; try { url = cv.toDataURL('image/jpeg', 0.85); } catch (e) { url = reader.result; }
        this.setState({ portraitImg: url, pX: 0, pY: 0, pScale: 1 }, () => this.persistPortrait());
      };
      im.src = reader.result;
    };
    reader.readAsDataURL(file);
  }

  portraitPointerDown(e) {
    if (!this.state.portraitImg) return;
    const start = { x: e.clientX, y: e.clientY, ox: this.state.pX, oy: this.state.pY };
    const move = (ev) => { this.setState({ pX: start.ox + (ev.clientX - start.x), pY: start.oy + (ev.clientY - start.y) }); };
    const up = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); this.persistPortrait(); };
    window.addEventListener('pointermove', move); window.addEventListener('pointerup', up);
  }

  go(s) {
    this.setState({ screen: s });
    if (typeof window !== 'undefined') { try { location.hash = s === 'home' ? '' : s; window.scrollTo(0, 0); } catch (e) {} }
  }

  renderVals() {
    const screen = this.state.screen;

    const nav = this._routes.map((n) => ({ ...n, active: n.key === screen, onClick: () => this.go(n.key) }));
    const is = {}, go = {};
    this._routes.forEach(r => { const c = r.key[0].toUpperCase() + r.key.slice(1); is['is' + c] = screen === r.key; go['go' + c] = () => this.go(r.key); });

    const rawSteps = window.JOURNEY_STEPS;
    const steps = rawSteps.map((s, i) => ({
      ...s,
      n: String(i + 1).padStart(2, '0'),
      active: i === this.state.step,
      delay: (i * 0.05).toFixed(2) + 's',
      glow: s.color + '44',
      tint: s.color + '0a',
      onClick: () => this.setState({ step: i }),
    }));
    const active = steps[this.state.step] || steps[0];

    const tapes = ['#FFC53D', '#FF6F61', '#3FA7D6', '#8B6DFF', '#59C29D'];
    const catDefs = window.SKETCH_CATEGORIES;
    let gk = 0;
    const baseCat = {};
    const order = [];
    catDefs.forEach((c, j) => { c.files.forEach((f) => { baseCat[f] = j; order.push(f); }); });
    const ov = this.state.overrides || {};
    const sel = this.state.selected;
    const effCat = (f) => (ov[f] !== undefined ? ov[f] : baseCat[f]);
    const clearSelect = () => this.setState({ selected: null });
    const moveTo = (f, j) => {
      this.setState((s) => {
        const no = { ...(s.overrides || {}), [f]: j };
        try { localStorage.setItem('dr_sketch_overrides', JSON.stringify(no)); } catch (e) {}
        return { overrides: no, selected: null };
      });
    };
    const categories = catDefs.map((c, j) => {
      const files = order.filter((f) => effCat(f) === j);
      const selHere = sel != null && effCat(sel) === j;
      return {
        title: c.title, note: c.note, icon: c.icon, color: c.color,
        empty: files.length === 0,
        showMoveHere: sel != null && !selHere,
        dropBg: (sel != null && !selHere) ? 'rgba(255,111,97,0.10)' : 'transparent',
        onDropHere: () => { if (sel != null && !selHere) { moveTo(sel, j); } },
        items: files.map((f, k) => ({
          src: encodeURI('uploads/' + f),
          sel: f === sel,
          scale: f === sel ? 1.05 : 1,
          z: f === sel ? 10 : 1,
          rot: ((k % 2 === 0) ? -1 : 1) * (1.5 + (k % 3)),
          tape: tapes[k % tapes.length],
          tapeRot: (k % 2 === 0 ? -1 : 1) * (4 + (k % 3) * 3),
          onSelect: (e) => { if (e && e.stopPropagation) e.stopPropagation(); this.setState((s) => ({ selected: s.selected === f ? null : f })); },
        })),
      };
    });
    const pastelBg = ['#EBF1FF', '#F1EEEA', '#EFEBFF', '#FFF3EB', '#FFFAEB', '#E0FAEC', '#EFEBFF'];
    const moveTargets = catDefs.map((c, j) => ({
      title: c.title,
      bg: pastelBg[j % pastelBg.length],
      onClick: (e) => { if (e && e.stopPropagation) e.stopPropagation(); if (sel != null) moveTo(sel, j); },
    }));
    const hasSelected = sel != null;
    const sketchCount = order.length;

    const projDefs = window.PROJECT_DEFINITIONS;
    const allProjects = projDefs.map((p, i) => ({
      ...p,
      id: 'project-' + (i + 1),
      href: p.href || 'https://www.behance.net/deepshiranjan4',
      hasImg: !!p.img,
      noImg: !p.img,
      imgEl: p.img ? React.createElement('img', { src: p.img, alt: p.title, style: i === 0 ? { display: 'block', width: '100%', height: '100%', minHeight: '250px', objectFit: 'cover' } : { display: 'block', width: '100%', height: '180px', objectFit: 'cover' } }) : null,
    }));
    const featured = allProjects[0];
    const projects = allProjects.slice(1);

    const skills = window.SKILL_DEFINITIONS;

    const socials = window.SOCIAL_LINKS;

    const bg = this.props.bgTexture || 'Dot grid';
    let patternBg = 'transparent';
    if (bg === 'Dot grid') patternBg = 'radial-gradient(rgba(32,27,19,0.10) 1.3px, transparent 1.3px) 0 0 / 22px 22px';
    else if (bg === 'Ruled lines') patternBg = 'repeating-linear-gradient(rgba(63,167,214,0.16) 0 1.5px, transparent 1.5px 30px)';

    const floaty = this.props.floatDoodles ?? true;
    const doodleAnim = floaty ? 'floaty 6s ease-in-out infinite' : 'none';
    const showAnnotations = this.props.showAnnotations ?? true;

    // ── Games ──
    const h = React.createElement;
    const activeGame = this.state.activeGame;

    // Tic-Tac-Toe
    const tttBoard = this.state.tttBoard;
    const tttTurn = this.state.tttTurn;
    const tttLines = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
    let tttWinner = null, tttWinLine = null;
    for (const ln of tttLines) { if (tttBoard[ln[0]] && tttBoard[ln[0]] === tttBoard[ln[1]] && tttBoard[ln[0]] === tttBoard[ln[2]]) { tttWinner = tttBoard[ln[0]]; tttWinLine = ln; break; } }
    const tttDraw = !tttWinner && tttBoard.every(v => v);
    const tttOver = !!tttWinner || tttDraw;
    const tttStatus = tttWinner ? tttWinner + ' wins!' : tttDraw ? "It's a draw!" : tttTurn + "'s turn";

    const tttEl = h('div', null,
      h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', width: 'fit-content', border: '3px solid #201B13', borderRadius: '16px', overflow: 'hidden' } },
        ...tttBoard.map((v, i) => {
          const row = Math.floor(i / 3), col = i % 3;
          const isWin = tttWinLine && tttWinLine.includes(i);
          return h('div', { key: i, onClick: () => { if (!v && !tttOver) { const b = [...tttBoard]; b[i] = tttTurn; this.setState({ tttBoard: b, tttTurn: tttTurn === 'X' ? 'O' : 'X' }); } },
            style: { width: 'clamp(80px, 22vw, 110px)', height: 'clamp(80px, 22vw, 110px)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 'clamp(32px, 9vw, 48px)', fontFamily: "'Shantell Sans'", fontWeight: 700, cursor: v || tttOver ? 'default' : 'pointer', background: isWin ? '#E0FAEC' : '#fff', color: v === 'X' ? '#FF6F61' : v === 'O' ? '#3FA7D6' : 'transparent', borderRight: col < 2 ? '2.5px solid #201B13' : 'none', borderBottom: row < 2 ? '2.5px solid #201B13' : 'none', transition: 'background .15s' }
          }, v || '·');
        })
      ),
      h('div', { style: { marginTop: '16px', display: 'flex', alignItems: 'center', gap: '16px' } },
        h('span', { style: { fontFamily: "'Shantell Sans'", fontWeight: 700, fontSize: '18px', color: tttWinner ? '#59C29D' : tttDraw ? '#E0A400' : '#201B13' } }, tttStatus),
        h('button', { onClick: () => this.setState({ tttBoard: Array(9).fill(''), tttTurn: 'X' }), style: { padding: '8px 18px', border: '2.5px solid #201B13', borderRadius: '12px', background: '#fff', fontFamily: "'Shantell Sans'", fontWeight: 600, fontSize: '14px', cursor: 'pointer', boxShadow: '3px 3px 0 #FFC53D' } }, 'New game')
      )
    );

    // Sudoku
    const SKP = [
      '530070000600195000098000060800060003400803001700020006060000280000419005000080079',
      '000260701680070090190004500820100040004602900050003028009300074040050036703018000',
      '006000200100802004020060080000300702090000060803006000030090050200508003005000900',
    ];
    const skIdx = this.state.skPuzzle || 0;
    const skPuzzle = SKP[skIdx];
    const skGiven = skPuzzle.split('').map(Number);
    const skBoard = this.state.skBoard || skGiven.slice();
    const skSel = this.state.skSel;
    const skErrs = new Set();
    for (let i = 0; i < 81; i++) { if (!skBoard[i]) continue; const r = Math.floor(i/9), c = i%9; for (let j = i+1; j < 81; j++) { if (!skBoard[j] || skBoard[i] !== skBoard[j]) continue; const r2 = Math.floor(j/9), c2 = j%9; if (r===r2 || c===c2 || (Math.floor(r/3)===Math.floor(r2/3) && Math.floor(c/3)===Math.floor(c2/3))) { skErrs.add(i); skErrs.add(j); } } }
    const skDone = skBoard.every(v => v) && skErrs.size === 0;
    const skSelR = skSel >= 0 ? Math.floor(skSel/9) : -1, skSelC = skSel >= 0 ? skSel%9 : -1;

    const sudokuEl = h('div', null,
      h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(9, 1fr)', width: 'fit-content', border: '3px solid #201B13', borderRadius: '12px', overflow: 'hidden' } },
        ...skBoard.map((v, i) => {
          const r = Math.floor(i/9), c = i%9, given = skGiven[i] !== 0, sel = i === skSel, err = skErrs.has(i);
          const hl = skSel >= 0 && !sel && (r === skSelR || c === skSelC || (Math.floor(r/3) === Math.floor(skSelR/3) && Math.floor(c/3) === Math.floor(skSelC/3)));
          return h('div', { key: i, onClick: () => { if (!given) this.setState({ skSel: sel ? -1 : i }); },
            style: { width: 'clamp(30px, 9vw, 44px)', height: 'clamp(30px, 9vw, 44px)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 'clamp(13px, 3.8vw, 20px)', fontFamily: "'Shantell Sans'", fontWeight: given ? 700 : 500, cursor: given ? 'default' : 'pointer', background: sel ? '#FFFAEB' : err && !given ? '#FFEBEC' : hl ? 'rgba(139,109,255,.06)' : '#fff', color: err && !given ? '#FF6F61' : given ? '#201B13' : '#8B6DFF', borderRight: c < 8 ? (c%3===2 ? '2.5px solid #201B13' : '1px solid #e0dbd0') : 'none', borderBottom: r < 8 ? (r%3===2 ? '2.5px solid #201B13' : '1px solid #e0dbd0') : 'none', transition: 'background .12s' }
          }, v || '');
        })
      ),
      h('div', { style: { display: 'flex', gap: '6px', marginTop: '16px', flexWrap: 'wrap', justifyContent: 'center' } },
        ...[1,2,3,4,5,6,7,8,9].map(n => h('button', { key: n, onClick: () => { if (skSel < 0 || skGiven[skSel]) return; const b = [...skBoard]; b[skSel] = n; this.setState({ skBoard: b }); },
          style: { width: 'clamp(32px, 9vw, 42px)', height: 'clamp(32px, 9vw, 42px)', border: '2.5px solid #201B13', borderRadius: '10px', background: '#fff', fontFamily: "'Shantell Sans'", fontWeight: 700, fontSize: 'clamp(14px, 4vw, 18px)', cursor: 'pointer' } }, n)),
        h('button', { key: 'clr', onClick: () => { if (skSel < 0 || skGiven[skSel]) return; const b = [...skBoard]; b[skSel] = 0; this.setState({ skBoard: b }); },
          style: { width: 'clamp(32px, 9vw, 42px)', height: 'clamp(32px, 9vw, 42px)', border: '2.5px solid #FF6F61', borderRadius: '10px', background: '#FFF3EB', fontFamily: "'Shantell Sans'", fontWeight: 700, fontSize: '14px', color: '#FF6F61', cursor: 'pointer' } }, '✕')
      ),
      h('div', { style: { marginTop: '14px', display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' } },
        skDone ? h('span', { style: { fontFamily: "'Shantell Sans'", fontWeight: 700, fontSize: '18px', color: '#59C29D' } }, 'Solved!') : null,
        h('span', { style: { fontFamily: "'Caveat'", fontSize: '16px', opacity: .6 } }, 'Puzzle ' + (skIdx + 1) + ' of ' + SKP.length),
        h('button', { onClick: () => { const ni = (skIdx + 1) % SKP.length; this.setState({ skPuzzle: ni, skBoard: SKP[ni].split('').map(Number), skSel: -1 }); },
          style: { padding: '6px 16px', border: '2.5px solid #201B13', borderRadius: '10px', background: '#fff', fontFamily: "'Shantell Sans'", fontWeight: 600, fontSize: '13px', cursor: 'pointer' } }, 'Next puzzle'),
        h('button', { onClick: () => this.setState({ skBoard: skGiven.slice(), skSel: -1 }),
          style: { padding: '6px 16px', border: '2.5px solid #FF6F61', borderRadius: '10px', background: '#FFF3EB', fontFamily: "'Shantell Sans'", fontWeight: 600, fontSize: '13px', color: '#FF6F61', cursor: 'pointer' } }, 'Reset')
      )
    );

    // 15 Puzzle (sliding tiles)
    const FP_IMGS = ['uploads/paintings_1.jpg','uploads/paintings_2.jpg','uploads/charcoal_1.jpg','uploads/modern_boho_1.jpg','uploads/rangoli_folkart_1.jpg','uploads/pencil_portraits_3.jpg'];
    const fpImgIdx = this.state.fpImgIdx || 0;
    const fpImg = FP_IMGS[fpImgIdx % FP_IMGS.length];
    const fpShuffle = () => {
      const tiles = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0];
      for (let i = tiles.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); const t = tiles[i]; tiles[i] = tiles[j]; tiles[j] = t; }
      let inv = 0; for (let i = 0; i < 16; i++) { for (let j = i + 1; j < 16; j++) { if (tiles[i] && tiles[j] && tiles[i] > tiles[j]) inv++; } }
      const blankRow = Math.floor(tiles.indexOf(0) / 4);
      if ((inv + blankRow) % 2 !== 1) { const a = tiles[0] === 0 ? 1 : 0; const b = tiles[1] === 0 ? 2 : 1; const t = tiles[a]; tiles[a] = tiles[b]; tiles[b] = t; }
      return tiles;
    };
    const fpTiles = this.state.fpTiles || fpShuffle();
    const fpBlank = fpTiles.indexOf(0);
    const fpSolved = fpTiles.every((v, i) => v === (i + 1) % 16);
    const fpMoves = this.state.fpMoves || 0;
    const fpSlide = (i) => {
      if (fpSolved) return;
      const br = Math.floor(fpBlank / 4), bc = fpBlank % 4, tr = Math.floor(i / 4), tc = i % 4;
      if ((Math.abs(br - tr) === 1 && bc === tc) || (Math.abs(bc - tc) === 1 && br === tr)) {
        const nt = [...fpTiles]; nt[fpBlank] = nt[i]; nt[i] = 0;
        this.setState({ fpTiles: nt, fpMoves: fpMoves + 1 });
      }
    };
    const fpSize = 'clamp(60px, 18vw, 85px)';

    const puzzleEl = h('div', { style: { display: 'flex', gap: 'clamp(16px, 4vw, 28px)', alignItems: 'flex-start', flexWrap: 'wrap' } },
      // Left: puzzle grid
      h('div', null,
        h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', width: 'fit-content', border: '3px solid #201B13', borderRadius: '14px', overflow: 'hidden', background: '#f2ede3' } },
          ...fpTiles.map((v, i) => {
            if (v === 0) return h('div', { key: 'blank', style: { width: fpSize, height: fpSize, background: fpSolved ? 'transparent' : '#f2ede3' } });
            const origR = Math.floor((v - 1) / 4), origC = (v - 1) % 4;
            const bgX = origC * 33.333, bgY = origR * 33.333;
            return h('div', { key: v, onClick: () => fpSlide(i),
              style: { width: fpSize, height: fpSize, backgroundImage: 'url(' + fpImg + ')', backgroundSize: '400% 400%', backgroundPosition: bgX + '% ' + bgY + '%', cursor: fpSolved ? 'default' : 'pointer', border: '1px solid rgba(32,27,19,.15)', transition: 'transform .1s', boxSizing: 'border-box' }
            });
          })
        ),
        h('div', { style: { marginTop: '14px', display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' } },
          fpSolved && fpMoves > 0 ? h('span', { style: { fontFamily: "'Shantell Sans'", fontWeight: 700, fontSize: '18px', color: '#59C29D' } }, 'Solved in ' + fpMoves + ' moves!') : h('span', { style: { fontFamily: "'Caveat'", fontSize: '16px', opacity: .6 } }, fpMoves + ' moves'),
          h('button', { onClick: () => this.setState({ fpTiles: fpShuffle(), fpMoves: 0 }),
            style: { padding: '8px 18px', border: '2.5px solid #201B13', borderRadius: '12px', background: '#fff', fontFamily: "'Shantell Sans'", fontWeight: 600, fontSize: '14px', cursor: 'pointer', boxShadow: '3px 3px 0 #59C29D' } }, 'Shuffle'),
          h('button', { onClick: () => { const ni = (fpImgIdx + 1) % FP_IMGS.length; this.setState({ fpImgIdx: ni, fpTiles: fpShuffle(), fpMoves: 0 }); },
            style: { padding: '8px 18px', border: '2.5px solid #201B13', borderRadius: '12px', background: '#fff', fontFamily: "'Shantell Sans'", fontWeight: 600, fontSize: '14px', cursor: 'pointer', boxShadow: '3px 3px 0 #8B6DFF' } }, 'Next artwork')
        )
      ),
      // Right: reference image
      h('div', { style: { flex: 'none' } },
        h('div', { style: { fontFamily: "'Caveat'", fontSize: '18px', color: '#8B6DFF', marginBottom: '8px', transform: 'rotate(2deg)' } }, 'Reference ↓'),
        h('img', { src: fpImg, style: { width: 'clamp(160px, 40vw, 260px)', height: 'clamp(160px, 40vw, 260px)', objectFit: 'cover', borderRadius: '14px', border: '2.5px solid #201B13', boxShadow: '4px 4px 0 #201B13', display: 'block' } })
      )
    );

    const hasPortrait = !!this.state.portraitImg;
    return {
      ...is,
      nav, steps, categories, sketchCount, moveTargets, hasSelected, clearSelect, projects, featured, socials, skills,
      hasPortrait, noPortrait: !hasPortrait, portraitImg: this.state.portraitImg,
      portraitEl: hasPortrait ? React.createElement('img', { src: this.state.portraitImg, draggable: false, alt: 'Deepshikha Ranjan', style: { position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: 'translate(' + this.state.pX + 'px, ' + this.state.pY + 'px) scale(' + this.state.pScale + ')', transformOrigin: 'center', userSelect: 'none', pointerEvents: 'none' } }) : null,
      pX: this.state.pX, pY: this.state.pY, pScale: this.state.pScale,
      portraitCursor: hasPortrait ? 'grab' : 'pointer',
      fileRef: this.fileRef,
      portraitPick: () => { if (this.fileRef.current) this.fileRef.current.click(); },
      portraitFrameClick: () => { if (!this.state.portraitImg && this.fileRef.current) this.fileRef.current.click(); },
      portraitFile: (e) => { this.handlePortraitFile(e.target.files && e.target.files[0]); },
      portraitDrop: (e) => { e.preventDefault(); const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]; if (f) this.handlePortraitFile(f); },
      portraitOver: (e) => { e.preventDefault(); },
      portraitPan: (e) => this.portraitPointerDown(e),
      portraitZoom: (e) => { const v = parseFloat(e.target.value); this.setState({ pScale: v }, () => this.persistPortrait()); },
      patternBg, doodleAnim, showAnnotations,
      activeTitle: active.title, activeBody: active.body, activeIcon: active.icon, activeColor: active.color, activeN: active.n,
      activeGame, isTTT: activeGame === 'ttt', isSudoku: activeGame === 'sudoku', isPuzzle: activeGame === 'puzzle',
      tttEl, sudokuEl, puzzleEl,
      tttTabBg: activeGame === 'ttt' ? '#FFC53D' : '#fff',
      tttTabColor: '#201B13',
      sudokuTabBg: activeGame === 'sudoku' ? '#8B6DFF' : '#fff',
      sudokuTabColor: activeGame === 'sudoku' ? '#fff' : '#201B13',
      puzzleTabBg: activeGame === 'puzzle' ? '#59C29D' : '#fff',
      puzzleTabColor: activeGame === 'puzzle' ? '#fff' : '#201B13',
      pickTTT: () => this.setState({ activeGame: 'ttt' }),
      pickSudoku: () => this.setState({ activeGame: 'sudoku' }),
      pickPuzzle: () => this.setState({ activeGame: 'puzzle' }),
      ...go,
      cName: this.state.cName, cEmail: this.state.cEmail, cMsg: this.state.cMsg,
      onName: (e) => this.setState({ cName: e.target.value }),
      onEmail: (e) => this.setState({ cEmail: e.target.value }),
      onMsg: (e) => this.setState({ cMsg: e.target.value }),
      sendMail: () => {
        const to = 'deepshikha.ranjan10@gmail.com';
        const subj = encodeURIComponent('Portfolio enquiry from ' + (this.state.cName || 'a visitor'));
        const body = encodeURIComponent((this.state.cMsg || '') + '\n\n— ' + (this.state.cName || '') + (this.state.cEmail ? ' (' + this.state.cEmail + ')' : ''));
        if (typeof window !== 'undefined') window.location.href = 'mailto:' + to + '?subject=' + subj + '&body=' + body;
      },
    };
  }
}
