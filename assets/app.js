mermaid.initialize({ startOnLoad: false, theme: 'neutral', fontFamily: 'Noto Sans KR, Inter, sans-serif' });

marked.use({
  breaks: true,
  gfm: true,
  html: true,
  renderer: {
    code({ text, lang }) {
      if (lang === 'mermaid') {
        return `<div class="mermaid">${text}</div>`;
      }
      if (!lang) lang = '';
      const validLang = lang && hljs.getLanguage(lang) ? lang : null;
      const highlighted = validLang
        ? hljs.highlight(text, { language: validLang }).value
        : (lang ? hljs.highlightAuto(text).value : text.replace(/&/g, '&amp;').replace(/</g, '&lt;'));
      const langLabel = lang ? `<div class="code-lang">${lang}</div>` : '';
      return `<div style="position:relative">${langLabel}<pre class="hljs"><code>${highlighted}</code></pre></div>`;
    }
  }
});

let META = {};

async function loadDoc(docPath) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.doc === docPath);
  });

  const meta = META[docPath] || { title: docPath.split('/').pop().replace('.md', ''), desc: '' };
  document.getElementById('post-title').textContent = meta.title;
  document.getElementById('post-desc').textContent = meta.desc;
  document.getElementById('content').innerHTML =
    '<p style="color:#9ca3af;text-align:center;padding:60px 0">로딩 중...</p>';

  try {
    const res = await fetch('docs/' + docPath);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    let md = await res.text();
    // ASCII 아트 코드블록을 마커로 교체 (marked.parse 전에 처리)
    md = md.replace(/```\n\[개발자 맥북\][\s\S]*?```/g, '\n%%LOCAL_DEV_DIAGRAM%%\n');
    md = md.replace(/```\n\[인터넷 사용자\][\s\S]*?```/g, '\n%%PROD_DIAGRAM%%\n');
    let html = marked.parse(md);
    html = html.replace(/<p>%%LOCAL_DEV_DIAGRAM%%<\/p>/g, DIAGRAMS['LOCAL_DEV']);
    html = html.replace(/<p>%%PROD_DIAGRAM%%<\/p>/g, DIAGRAMS['PROD']);
    document.getElementById('content').innerHTML = html;
    document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
    await mermaid.run({ nodes: document.querySelectorAll('#content .mermaid') });
    window.scrollTo(0, 0);

    // URL 해시 업데이트 (뒤로가기 지원)
    history.pushState({ doc: docPath }, '', '#' + docPath);
  } catch (e) {
    document.getElementById('content').innerHTML =
      `<p style="color:#ef4444;padding:20px">오류: ${e.message}</p>`;
  }
}

function buildSidebar(manifest) {
  const sidebar = document.querySelector('.sidebar');

  // 브랜드 영역
  const brand = document.createElement('div');
  brand.className = 'sidebar-brand';
  brand.innerHTML = `<div class="name">${manifest.brand.name}</div><div class="sub">${manifest.brand.sub}</div>`;
  sidebar.appendChild(brand);

  // 그룹별 nav 아이템
  manifest.groups.forEach(group => {
    const groupEl = document.createElement('div');
    groupEl.className = 'nav-group';
    groupEl.textContent = group.name;
    sidebar.appendChild(groupEl);

    group.files.forEach(file => {
      META[file.path] = { title: file.title, desc: file.desc };
      const a = document.createElement('a');
      a.className = 'nav-item';
      a.dataset.doc = file.path;
      a.innerHTML = `<span class="dot"></span>${file.title}`;
      sidebar.appendChild(a);
    });
  });

  sidebar.addEventListener('click', e => {
    const item = e.target.closest('.nav-item');
    if (item && item.dataset.doc) loadDoc(item.dataset.doc);
  });
}

async function init() {
  const res = await fetch('docs/manifest.json');
  const manifest = await res.json();
  buildSidebar(manifest);

  // 해시로 직접 링크 지원
  const hash = location.hash.slice(1);
  const firstDoc = manifest.groups[0].files[0].path;
  loadDoc(hash || firstDoc);
}

window.addEventListener('popstate', e => {
  if (e.state && e.state.doc) loadDoc(e.state.doc);
});

init();
