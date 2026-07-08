class Component extends DCLogic {
  state = { screen: 'home', step: 0, cName: '', cEmail: '', cMsg: '', overrides: {}, selected: null, portraitImg: 'uploads/portrait.png', pX: 0, pY: 0, pScale: 1 };
  fileRef = React.createRef();

  componentDidMount() {
    try {
      const raw = localStorage.getItem('dr_sketch_overrides');
      if (raw) this.setState({ overrides: JSON.parse(raw) || {} });
    } catch (e) {}
    try {
      const p = localStorage.getItem('dr_portrait');
      if (p) { const o = JSON.parse(p); if (o && o.img) this.setState({ portraitImg: o.img, pX: o.x || 0, pY: o.y || 0, pScale: o.scale || 1 }); }
    } catch (e) {}
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
    if (typeof window !== 'undefined') { try { window.scrollTo(0, 0); } catch (e) {} }
  }

  renderVals() {
    const screen = this.state.screen;

    const nav = [
      { key: 'home', label: 'Home' },
      { key: 'journey', label: 'My journey' },
      { key: 'sketches', label: 'My sketches' },
      { key: 'projects', label: 'My projects' },
      { key: 'contact', label: 'Contact me' },
    ].map((n) => ({ ...n, active: n.key === screen, onClick: () => this.go(n.key) }));

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

    const hasPortrait = !!this.state.portraitImg;
    return {
      isHome: screen === 'home', isJourney: screen === 'journey', isSketches: screen === 'sketches', isProjects: screen === 'projects', isContact: screen === 'contact',
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
      goHome: () => this.go('home'), goJourney: () => this.go('journey'), goSketches: () => this.go('sketches'), goProjects: () => this.go('projects'), goContact: () => this.go('contact'),
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
