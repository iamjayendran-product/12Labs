// Tiny DOM helpers. All server text goes through textContent (never innerHTML).
function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === 'class') e.className = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else if (k === 'style') e.setAttribute('style', v);
    else if (v === true) e.setAttribute(k, '');
    else e.setAttribute(k, v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false) continue;
    e.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return e;
}

async function api(path, opts) {
  const res = await fetch('/api/pmos' + path, opts && opts.body
    ? { ...opts, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(opts.body) }
    : opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Request failed (' + res.status + ')');
  return data;
}

function toast(msg, isError) {
  const t = h('div', { class: 'toast' + (isError ? ' error' : ''), role: 'status', 'data-testid': 'toast' }, msg);
  document.body.append(t);
  setTimeout(() => t.remove(), 3500);
}

function renderNav(active) {
  const links = [['sources.html', 'Sources'], ['backlog.html', 'Backlog & RICE'], ['roadmap.html', 'Roadmap'], ['/', 'Chat']];
  document.body.prepend(h('header', { class: 'top' },
    h('h1', {}, 'PM OS · 12Labs'),
    h('nav', {}, links.map(([href, label]) =>
      h('a', { href: href.startsWith('/') ? href : '/pmos/' + href, class: label === active ? 'active' : '' }, label)))));
}

const usd = n => '$' + Math.round(n / 1000) + 'k';
const fmtTs = ts => ts.replace('T', ' ').replace('Z', ' UTC');
const SOURCE_LABEL = { voc: 'Voice of customer', crm: 'CRM', fireflies: 'Fireflies', support: 'NPS / support', commitment: 'Commitment' };
const srcBadge = s => h('span', { class: 'badge src-' + s }, SOURCE_LABEL[s] || s);
