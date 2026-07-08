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

    const rawSteps = [
      { title: 'Law college', icon: 'ri-bank-line', color: '#3FA7D6', bg: '#EBF1FF', body: 'Where it began. I genuinely believed law was the path I was meant to follow — and for a while, it truly was.' },
      { title: 'Law degree', icon: 'ri-graduation-cap-line', color: '#59C29D', bg: '#E0FAEC', body: 'Years of drafting notices, petitions and pleadings, studying case law and doing research — detailed work that demanded precision and clarity in everything I put on paper.' },
      { title: 'Advocate', icon: 'ri-scales-3-line', color: '#8B6DFF', bg: '#EFEBFF', body: 'Building a career. From the outside, everything looked exactly as it was supposed to — but something quiet kept nagging at me.' },
      { title: 'The frustration', icon: 'ri-error-warning-line', color: '#FF6F61', bg: '#FFEBEC', body: 'Using legal research tools and government portals, I was more bothered by their terrible design than by the case itself. It felt genuinely disrespectful to the people it was meant to serve.' },
      { title: 'Discovering UI/UX', icon: 'ri-lightbulb-flash-line', color: '#E0A400', bg: '#FFFAEB', body: 'One evening I really looked at Spotify. Someone sat down and made a thousand small decisions to make this feel this easy. I wasn\u2019t just a user anymore — I wanted to become one of them.' },
      { title: 'Researching courses', icon: 'ri-search-eye-line', color: '#3FA7D6', bg: '#EBF1FF', body: 'Reading in the margins of my legal life. A case study on redesigning a healthcare app for elderly users left me completely absorbed — and I met the words \u201cUI/UX design\u201d.' },
      { title: 'Certified — IIIT Bangalore', icon: 'ri-medal-line', color: '#59C29D', bg: '#E0FAEC', body: 'I learned it properly: user research, wireframing, prototyping, typography, colour, hierarchy, accessibility and design systems. Figma stopped being intimidating and started feeling like an extension of what I wanted to say.' },
      { title: 'Building projects', icon: 'ri-pencil-ruler-2-line', color: '#8B6DFF', bg: '#EFEBFF', body: 'Make, share, listen, improve — then do it all again. When someone said \u201cthis feels really intuitive\u201d, I knew exactly how much work had gone into earning those three words.' },
      { title: 'This portfolio', icon: 'ri-palette-line', color: '#FF6F61', bg: '#FFF3EB', body: 'I don\u2019t see my journey as \u201cleaving law\u201d. Law built my mind; design finally gave it somewhere it wanted to go.' },
    ];
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

    const skills = [
      { label: 'UX Research', icon: 'ri-search-eye-line', color: '#3FA7D6', rot: -2, sub: 'Competitive & SWOT analysis · Usability testing' },
      { label: 'Users & Empathy', icon: 'ri-group-line', color: '#59C29D', rot: 1.5, sub: 'Personas · Empathy maps · Journey & task flows' },
      { label: 'Design Thinking', icon: 'ri-lightbulb-flash-line', color: '#8B6DFF', rot: -1, sub: 'Problem solving · Storyboarding · Info architecture' },
      { label: 'UI & Visual Design', icon: 'ri-palette-line', color: '#FF6F61', rot: 2, sub: 'Wireframing · Responsive · Visual design' },
      { label: 'Prototyping', icon: 'ri-cursor-line', color: '#E0A400', rot: -1.5, sub: 'Interactive prototypes · Microinteractions' },
      { label: 'Spatial & AR/VR', icon: 'ri-vr-glasses-line', color: '#3FA7D6', rot: 1, sub: 'Spatial UI · AR/VR · Human-computer interaction' },
    ];

    const socials = [
      { label: 'LinkedIn', icon: 'ri-linkedin-box-fill', color: '#3FA7D6', href: 'https://www.linkedin.com/in/deepshikha-ranjan-981028b0/' },
      { label: 'Instagram', icon: 'ri-instagram-line', color: '#FF6F61', href: 'https://www.instagram.com/' },
      { label: 'Behance', icon: 'ri-behance-fill', color: '#8B6DFF', href: 'https://www.behance.net/deepshiranjan4' },
    ];

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
