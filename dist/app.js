(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const normalized = (s) => s.toLowerCase().replace(/ё/g, 'е').replace(/[^a-zа-я0-9]+/g,' ').trim();
  const clean = (s) => s.replace(/\s*\(вирт\)/gi, '').trim();
  const href = (n) => '#/category/' + n.id;
  const main = $('#content');
  const search = $('#search');
  const results = $('#search-results');
  const dialog = $('#tree-dialog');
  let data, byId, current, gridView = true;
  const icon = (name) => {
    let path = '<path d="m5 19 5-5M14 10l5-5M12 4a6 6 0 0 0 7 8l-9 9-4-4 9-9A6 6 0 0 1 12 4Z"/>';
    if (/измер|размет|нивелир|уровн|рулет|контрол/i.test(name)) path='<path d="M3 8h18v9H3zM7 8v5m4-5v3m4-3v5m4-5v3"/>';
    else if (/сверл|долб|шуруп|электроинструм/i.test(name)) path='<path d="M4 5h12l3 3v4H9l-1 9H4l1-9H3V7h1ZM19 8h3M10 5V2m3 3V2"/>';
    else if (/платформ|аккум|питан|заряд/i.test(name)) path='<rect x="5" y="6" width="15" height="13" rx="2"/><path d="M2 10v5m18-5h2v5h-2M13 8l-4 5h5l-3 4"/>';
    else if (/оснаст|расход|диск|бит|пил|рез/i.test(name)) path='<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2"/><path d="m12 2 2 3m8 7-3 2M12 22l-2-3M2 12l3-2m14-5-1 4m1 10-4-1M5 19l1-4M5 5l4 1"/>';
    else if (/защит|безопас|сиз|каск/i.test(name)) path='<path d="M4 13v-2a8 8 0 0 1 16 0v2M3 13h18v5H3zM9 3v7m6-7v7"/>';
    else if (/хран|ящик|набор|комплект/i.test(name)) path='<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V3h8v4M3 13h18m-11-2v4h4v-4"/>';
    else if (/стен|этап|строит|демонт|фундамент|отдел|установ/i.test(name)) path='<path d="M3 21h18M5 21V9l7-6 7 6v12M9 21v-7h6v7M3 11l9-8 9 8"/>';
    return '<svg viewBox="0 0 24 24" aria-hidden="true">'+path+'</svg>';
  };
  function ancestors(n) { const a=[]; while(n){a.unshift(n);n=n.parent?byId.get(n.parent):null;}return a; }
  function path(n) { return ancestors(n).map(x=>clean(x.name)).join(' › '); }
  function descendants(n) { return n.children.flatMap(id=>{const c=byId.get(id);return c.children.length?descendants(c):[c];}); }
  function plural(num, forms) { const v=num%100; return forms[v>10&&v<20?2:num%10===1?0:num%10>1&&num%10<5?1:2]; }
  function sectionCount(num) { return `${num} ${plural(num,['раздел','раздела','разделов'])}`; }
  function count(n) { return n.children.length ? (n.name==='Подбор по этапам работ'?`${n.children.length} ${plural(n.children.length,['этап','этапа','этапов'])}`:sectionCount(n.children.length)) : 'Категория'; }
  function card(n, i, stage) {
    const media=n.image?`<span class="photo-card-media"><img src="${esc(n.image)}" alt="" loading="lazy" decoding="async"></span>`:`<span class="card-icon">${icon(n.name)}</span>`;
    return `<a class="photo-card" href="${href(n)}">${stage?`<span class="stage-badge">${String(i+1).padStart(2,'0')}</span>`:''}${media}<span class="photo-card-copy"><strong>${esc(clean(n.name))}</strong><small>${esc(count(n))}</small></span></a>`;
  }
  function row(n) {return `<a class="category-row" href="${href(n)}"><span><strong>${esc(clean(n.name))}</strong>${n.virtual?' <span class="tag">Виртуальная</span>':''}${n.children.length?`<small>${esc(count(n))}</small>`:''}</span><span class="arrow" aria-hidden="true">›</span></a>`;}
  function breadcrumbs(n) {
    const a=n?ancestors(n):[];
    return `<nav class="breadcrumbs" aria-label="Навигация"><a href="#/">Каталог</a><span aria-hidden="true">›</span>${a.length?'<a href="#/">Ремонт и строительство</a>':'<span>Ремонт и строительство</span>'}${a.map((x,i)=>`<span aria-hidden="true">›</span>${i===a.length-1?`<span aria-current="page">${esc(clean(x.name))}</span>`:`<a href="${href(x)}">${esc(clean(x.name))}</a>`}`).join('')}</nav>`;
  }
  function home() {
    const roots=data.roots.map(id=>byId.get(id));
    const popularNames=['Электроинструменты','Для сверления, долбления, закручивания','Измерительный инструмент','Строительное оборудование'];
    const popular=popularNames.map(name=>data.nodes.find(n=>n.name===name)).filter(Boolean);
    main.innerHTML=breadcrumbs()+`<section class="page-intro"><h1>Ремонт и строительство</h1></section><section class="entry-grid" aria-label="Разделы каталога">${roots.map((n,i)=>card(n,i,false)).join('')}</section><section class="section-block"><div class="section-heading"><h2>Категории каталога</h2></div><div class="popular-grid">${popular.map(n=>`<article class="popular-card"><a class="popular-card-title" href="${href(n)}">${esc(n.name)}</a><div>${descendants(n).slice(0,4).map(x=>`<a href="${href(x)}">${esc(clean(x.name))}</a>`).join('')}</div></article>`).join('')}</div></section><div class="source-strip"><span>Названия, порядок и вложенность сохранены по обновлённой структуре каталога.</span><button data-open-tree>Посмотреть дерево структуры →</button></div>`;
  }
  function category(n) {
    const children=n.children.map(id=>byId.get(id));
    const stage=n.name==='Подбор по этапам работ';
    const branch=ancestors(n)[0];
    const introduction=n.children.length ? '' : (n.virtual?'Виртуальная категория из структуры каталога. Товарное наполнение и фильтры подбора уточняются.':branch.name==='Аккумуляторные платформы'?'Аккумуляторная платформа из структуры каталога. Состав совместимых категорий здесь пока не детализирован.':'Категория из структуры каталога.');
    main.innerHTML=breadcrumbs(n)+`<section class="page-intro"><div class="eyebrow"><span>${esc(branch.name)}</span>${n.virtual?'<span class="tag">Виртуальная категория</span>':''}</div><h1>${esc(clean(n.name))}</h1></section>`;
    if(children.length){
      const isGrid=gridView;
      main.innerHTML+=`<div class="list-heading"><p>${sectionCount(children.length)} · порядок из структуры каталога</p><div class="view-toggle" aria-label="Вид каталога"><button data-view="grid" aria-pressed="${gridView}">Карточки</button><button data-view="list" aria-pressed="${!gridView}">Список</button></div></div><section class="${isGrid?'category-grid':'category-list'}" aria-label="${esc(clean(n.name))}">${children.map((x,i)=>isGrid?card(x,i,stage):row(x)).join('')}</section>`;
    }else{
      const external=n.url && n.url.startsWith('https://www.dns-shop.ru/');
      main.innerHTML+=`<section class="leaf-panel"><span class="card-icon">${icon(n.name)}</span><div class="leaf-copy"><h2>${esc(clean(n.name))}</h2><p>${esc(introduction)}</p>${external?`<a class="primary-link" href="${esc(n.url)}" target="_blank" rel="noopener">${n.virtual?'Базовая категория DNS':'Посмотреть в DNS'} <span aria-hidden="true">↗</span></a>`:''}<div class="leaf-meta">Источник: ${esc(data.source.label || data.source.sheet || 'Структура каталога')} · ${esc(n.cells.join(', '))}</div></div></section>`;
      if(n.parent){const related=byId.get(n.parent).children.filter(id=>id!==n.id).map(id=>byId.get(id));if(related.length)main.innerHTML+=`<section class="section-block"><div class="section-heading"><h2>В этом же разделе</h2><span>${related.length} категорий</span></div><div class="related-grid">${related.slice(0,12).map(row).join('')}</div></section>`;}
    }
  }
  function find(q) {
    const words=normalized(q).split(' ').filter(Boolean);
    if(!words.length)return [];
    return data.nodes.filter(n=>words.every(w=>n.searchText.includes(w))).sort((a,b)=>{
      const an=normalized(a.name),bn=normalized(b.name),v=normalized(q);
      return Number(bn===v)-Number(an===v)||Number(bn.startsWith(v))-Number(an.startsWith(v))||a.level-b.level;
    });
  }
  function resultLink(n){return `<a href="${href(n)}"><strong>${esc(clean(n.name))}</strong><small>${esc(path(n))}</small></a>`;}
  function searchPage(q){
    const found=find(q);
    main.innerHTML=breadcrumbs()+`<section class="page-intro"><h1>Поиск по каталогу</h1><p>«${esc(q)}» · найдено: ${found.length}</p></section>`+(found.length?`<div class="search-page-list">${found.map(resultLink).join('')}</div>`:`<section class="empty"><h2>Ничего не найдено</h2><p>Попробуйте другое название инструмента или этапа работ.</p><a href="#/">Открыть каталог →</a></section>`);
  }
  function closeSearch(){results.hidden=true;search.setAttribute('aria-expanded','false');}
  function closeMenu(){ $('#catalog-menu').hidden=true;$('#catalog-toggle').setAttribute('aria-expanded','false'); }
  function render(){
    if(!data)return;
    closeSearch();closeMenu();if(dialog.open)dialog.close();
    const hash=location.hash || '#/';
    const match=hash.match(/^#\/category\/([a-z0-9]+)$/);
    current=match?byId.get(match[1]):null;
    const searchRoute=hash.startsWith('#/search/');
    if(current)category(current);
    else if(searchRoute){let q='';try{q=decodeURIComponent(hash.slice(9));}catch{}searchPage(q);search.value=q;}
    else if(hash==='#/'||hash==='#')home();
    else main.innerHTML=breadcrumbs()+`<section class="page-intro"><h1>Раздел не найден</h1></section><section class="empty"><p>Возможно, ссылка устарела.</p><a href="#/">Вернуться в каталог →</a></section>`;
    document.title=(current?clean(current.name):searchRoute?'Поиск по каталогу':data.title)+' — каталог DIY';
    window.scrollTo({top:0,behavior:'instant'});
  }
  function treeNode(n){return n.children.length?`<details data-node="${n.id}"><summary><span>${esc(n.name)}</span><small>${n.level} уровень · ${n.children.length}</small></summary><div class="tree-children">${n.children.map(id=>treeNode(byId.get(id))).join('')}</div></details>`:`<a href="${href(n)}">${esc(n.name)}</a>`;}
  function showTree(){
    if(!data)return;
    $('#tree-search').value='';buildTree();dialog.showModal();
  }
  function buildTree(){ $('#tree-content').innerHTML=data.roots.map(id=>treeNode(byId.get(id))).join(''); }
  $('#catalog-toggle').addEventListener('click',()=>{
    if(!data)return;
    const menu=$('#catalog-menu'); const open=menu.hidden;
    closeSearch();menu.hidden=!open;$('#catalog-toggle').setAttribute('aria-expanded',String(open));
    if(open)menu.innerHTML=`<div class="catalog-panel" role="navigation" aria-label="Каталог">${data.roots.map(id=>byId.get(id)).map(n=>`<section class="catalog-column"><h2><a href="${href(n)}">${esc(n.name)}</a></h2><div>${n.children.map(id=>byId.get(id)).map(c=>`<a href="${href(c)}">${esc(c.name)}</a>`).join('')}</div></section>`).join('')}</div>`;
  });
  $('#catalog-menu').addEventListener('click',e=>{if(e.target===$('#catalog-menu')||e.target.closest('a'))closeMenu();});
  $('#tree-open').addEventListener('click',showTree);
  $('#tree-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();if(e.target.closest('a')){dialog.close();if(e.target.closest('a').hash===location.hash)render();}});
  $('#tree-expand').addEventListener('click',()=>$('#tree-content').querySelectorAll('details').forEach(d=>d.open=true));
  $('#tree-collapse').addEventListener('click',()=>$('#tree-content').querySelectorAll('details').forEach(d=>d.open=false));
  $('#tree-search').addEventListener('input',e=>{const q=e.target.value.trim();if(!q){buildTree();return;}const found=find(q);$('#tree-content').innerHTML=`<p class="leaf-meta">Найдено: ${found.length}</p><div class="tree-search-results">${found.map(resultLink).join('')}</div>`;});
  main.addEventListener('click',e=>{
    if(e.target.closest('[data-open-tree]'))showTree();
    const toggle=e.target.closest('[data-view]');if(toggle){gridView=toggle.dataset.view==='grid';category(current);}
  });
  function updateSearch(){
    if(!data)return;
    const q=search.value.trim();if(!q){closeSearch();return;}
    closeMenu();const found=find(q);results.hidden=false;search.setAttribute('aria-expanded','true');
    results.innerHTML=found.length?found.slice(0,7).map(resultLink).join('')+`<a class="search-all" href="#/search/${encodeURIComponent(q)}">Все результаты (${found.length}) →</a>`:'<p>Ничего не найдено. Попробуйте другое название.</p>';
  }
  search.addEventListener('input',updateSearch);search.addEventListener('focus',()=>{if(search.value.trim())updateSearch();});
  results.addEventListener('click',e=>{if(e.target.closest('a'))closeSearch();});
  $('#search-form').addEventListener('submit',e=>{e.preventDefault();if(search.value.trim()){location.hash='/search/'+encodeURIComponent(search.value.trim());closeSearch();}});
  document.addEventListener('click',e=>{if(!e.target.closest('.search-wrap'))closeSearch();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeSearch();closeMenu();}if(e.key==='/'&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();search.focus();}});
  window.addEventListener('hashchange',render);
  fetch('catalog.json', {cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Каталог недоступен');return r.json();}).then(c=>{
    data=c;$('#source-summary').textContent=`${c.source.label || c.source.sheet || 'Структура каталога'} · ${c.source.snapshot}`;byId=new Map(c.nodes.map(n=>[n.id,n]));for(const n of c.nodes)n.searchText=normalized(n.name);render();
  }).catch(()=>{main.innerHTML='<section class="loading"><h1>Не удалось загрузить каталог</h1><p>Проверьте соединение и обновите страницу.</p><button onclick="location.reload()">Обновить страницу</button></section>';});
})();

