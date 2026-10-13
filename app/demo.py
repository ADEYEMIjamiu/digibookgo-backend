"""
Demo page for digibookgo: visual store map + live route finder.

Served at /demo. The page runs in the browser and reads everything
from the same API (stores, map nodes/edges, products, markers, route),
so no extra setup or CORS settings are needed.

Optional URL parameters:
    /demo?code=LIDL-DEMO-DRINKS     start at that QR marker
    /demo?product=3                 auto-navigate to that product id
    /demo?store=1                   force a specific store id
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>digibookgo - Indoor Navigation Demo</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--text:#e2e8f0;--muted:#94a3b8;--accent:#38bdf8;--ok:#4ade80;--warn:#fbbf24}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--text)}
header{padding:16px 24px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}
h1{margin:0;font-size:20px}
h1 span{color:var(--accent)}
.sub{color:var(--muted);font-size:13px;margin-top:2px}
.badge{font-size:13px;padding:6px 12px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.badge.ok{color:var(--ok);border-color:#166534}
.badge.bad{color:#fca5a5;border-color:#7f1d1d}
main{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(300px,1fr);gap:20px;padding:20px 24px;max-width:1300px;margin:0 auto}
@media(max-width:900px){main{grid-template-columns:1fr;padding:14px}}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:16px}
h2{margin:0 0 10px;font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
select{width:100%;padding:10px;border-radius:10px;border:1px solid var(--line);background:#0b1324;color:var(--text);font-size:15px}
.prod{display:flex;justify-content:space-between;align-items:center;gap:8px;width:100%;text-align:left;padding:11px 12px;margin-bottom:8px;border-radius:10px;border:1px solid var(--line);background:#0b1324;color:var(--text);font-size:15px;cursor:pointer}
.prod:hover{border-color:var(--accent)}
.prod.active{border-color:var(--accent);background:#0c2a3d}
.prod small{color:var(--muted)}
button.replay{margin-top:10px;padding:8px 14px;border-radius:10px;border:1px solid var(--line);background:#0b1324;color:var(--text);cursor:pointer;font-size:14px}
#map{width:100%;height:auto;display:block}
.floor{fill:#0b1324;stroke:#334155;stroke-dasharray:6 6}
.edge{stroke:#475569;stroke-width:3;stroke-linecap:round}
.node{fill:#64748b;stroke:#0b1324;stroke-width:2}
.lbl{fill:#94a3b8;font-size:12px}
.route{fill:none;stroke:var(--accent);stroke-width:6;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:12 9;animation:dash .8s linear infinite}
@keyframes dash{to{stroke-dashoffset:-21}}
.ring{fill:none;stroke:var(--warn);stroke-width:3}
.shelf{fill:var(--warn);font-size:13px;font-weight:600}
.halo{fill:rgba(74,222,128,.25)}
.dot{fill:var(--ok);stroke:#0b1324;stroke-width:3}
.steps{list-style:none;margin:10px 0 0;padding:0}
.steps li{display:flex;gap:10px;padding:9px 0;border-bottom:1px solid var(--line);font-size:15px}
.steps li:last-child{border:0}
.ic{width:26px;text-align:center}
.sum{margin-top:8px;color:var(--muted);font-size:14px}
.pos{margin-top:10px;font-size:14px;color:var(--ok)}
.err{color:#fca5a5;margin-top:8px;font-size:14px}
footer{text-align:center;color:var(--muted);font-size:12px;padding:6px 0 22px}
</style>
</head>
<body>
<header>
  <div>
    <h1><span>digibookgo</span> &middot; Indoor Navigation</h1>
    <div class="sub" id="storeName">Loading store...</div>
  </div>
  <div class="badge" id="status">Connecting...</div>
</header>
<main>
  <section class="card">
    <h2>Store map</h2>
    <svg id="map" viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg"></svg>
  </section>
  <section>
    <div class="card">
      <h2>1 &middot; Scan a QR code (your position)</h2>
      <select id="marker"></select>
      <div class="pos" id="pos"></div>
    </div>
    <div class="card">
      <h2>2 &middot; What are you looking for?</h2>
      <div id="products"></div>
    </div>
    <div class="card">
      <h2>3 &middot; Directions</h2>
      <div id="summary" class="sum">Pick a product to see the route.</div>
      <ol class="steps" id="steps"></ol>
      <div class="err" id="err"></div>
      <button class="replay" id="replay" style="display:none">Replay walk</button>
    </div>
  </section>
</main>
<footer id="foot"></footer>

<script>
const S = 44, PAD = 56;
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {store:null, nodes:[], edges:[], byId:{}, edgeLen:{}, products:[], markers:[], start:null, anim:null, lastPts:null, px:null, py:null};

async function get(url){
  const r = await fetch(url);
  if(!r.ok) throw new Error(url + ' returned ' + r.status);
  return r.json();
}
const nodeLabel = id => (state.byId[id] && state.byId[id].label) ? state.byId[id].label : ('Node ' + id);
const fmt = n => Number.isInteger(n) ? n : n.toFixed(1);

async function init(){
  try{
    const params = new URLSearchParams(location.search);
    const [stores, nodes, edges, products, locs, markers] = await Promise.all([
      get('/api/stores/'), get('/api/map/nodes'), get('/api/map/edges'),
      get('/api/products/'), get('/api/products/locations'), get('/api/markers/')
    ]);
    let store = params.get('store') ? stores.find(s => String(s.id) === params.get('store'))
                                    : stores.find(s => s.name === 'Lidl Demo Store');
    if(!store) store = stores[stores.length - 1];
    if(!store) throw new Error('No store found. Run seed_demo_store.py first.');
    state.store = store;
    state.nodes = nodes.filter(n => n.store_id === store.id);
    state.edges = edges.filter(e => e.store_id === store.id);
    if(!state.nodes.length) throw new Error('This store has no map nodes yet.');
    state.nodes.forEach(n => state.byId[n.id] = n);
    state.edges.forEach(e => state.edgeLen[Math.min(e.node_a_id, e.node_b_id) + '-' + Math.max(e.node_a_id, e.node_b_id)] = e.distance);
    const prodById = {}; products.forEach(p => prodById[p.id] = p);
    state.products = locs.filter(l => l.store_id === store.id && prodById[l.product_id])
                         .map(l => ({id:l.product_id, name:prodById[l.product_id].name, shelf:l.shelf_label, node:l.nearest_node_id}));
    state.markers = markers.filter(m => m.store_id === store.id);

    $('#storeName').textContent = store.name + ' \u00b7 ' + store.city;
    $('#status').textContent = '\u25cf Live API connected';
    $('#status').className = 'badge ok';
    $('#foot').textContent = 'Data served live from ' + location.host;

    drawMap();
    renderMarkers(params.get('code'));
    renderProducts();
    if(state.markers.length){ await setPosition($('#marker').value); }
    if(params.get('product')) goTo(Number(params.get('product')));
  }catch(e){
    $('#status').textContent = '\u25cf API error';
    $('#status').className = 'badge bad';
    $('#storeName').textContent = '';
    $('#err').textContent = e.message;
  }
}

function drawMap(){
  const xs = state.nodes.map(n => n.x), ys = state.nodes.map(n => n.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const W = (maxX - minX) * S + PAD * 2, H = (maxY - minY) * S + PAD * 2;
  const px = x => PAD + (x - minX) * S, py = y => PAD + (y - minY) * S;
  state.px = px; state.py = py;
  let h = '<rect class="floor" x="' + (PAD - 26) + '" y="' + (PAD - 26) + '" width="' + (W - 2 * PAD + 52) + '" height="' + (H - 2 * PAD + 52) + '" rx="18"/>';
  state.edges.forEach(e => {
    const a = state.byId[e.node_a_id], b = state.byId[e.node_b_id];
    if(a && b) h += '<line class="edge" x1="' + px(a.x) + '" y1="' + py(a.y) + '" x2="' + px(b.x) + '" y2="' + py(b.y) + '"/>';
  });
  h += '<polyline id="route" class="route" points="" style="display:none"/>';
  state.nodes.forEach(n => {
    h += '<circle class="node" cx="' + px(n.x) + '" cy="' + py(n.y) + '" r="7"/>';
    h += '<text class="lbl" x="' + px(n.x) + '" y="' + (py(n.y) + 25) + '" text-anchor="middle">' + esc(n.label || ('Node ' + n.id)) + '</text>';
  });
  h += '<g id="dest" style="display:none"><circle class="ring" r="15"/><text class="shelf" y="-24" text-anchor="middle"></text></g>';
  h += '<g id="you" style="display:none"><circle class="halo" r="17"/><circle class="dot" r="8"/></g>';
  const svg = $('#map');
  svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
  svg.innerHTML = h;
}

function renderMarkers(preferCode){
  const sel = $('#marker');
  sel.innerHTML = state.markers.map(m => '<option value="' + esc(m.code) + '">' + esc(m.code) + ' \u00b7 ' + esc(nodeLabel(m.node_id)) + '</option>').join('');
  if(preferCode && state.markers.some(m => m.code === preferCode)) sel.value = preferCode;
  sel.onchange = () => setPosition(sel.value);
}

function renderProducts(){
  $('#products').innerHTML = state.products.map(p =>
    '<button class="prod" data-id="' + p.id + '"><span>' + esc(p.name) + '</span><small>' + esc(p.shelf || '') + '</small></button>').join('')
    || '<div class="sum">No products placed in this store yet.</div>';
  document.querySelectorAll('.prod').forEach(b => b.onclick = () => goTo(Number(b.dataset.id)));
}

function moveYou(nodeId){
  const n = state.byId[nodeId]; if(!n) return;
  const g = $('#you'); g.style.display = '';
  g.setAttribute('transform', 'translate(' + state.px(n.x) + ',' + state.py(n.y) + ')');
}

function clearRoute(){
  cancelAnimationFrame(state.anim);
  $('#route').style.display = 'none';
  $('#dest').style.display = 'none';
  $('#steps').innerHTML = '';
  $('#summary').textContent = 'Pick a product to see the route.';
  $('#err').textContent = '';
  $('#replay').style.display = 'none';
  document.querySelectorAll('.prod').forEach(b => b.classList.remove('active'));
}

async function setPosition(code){
  clearRoute();
  try{
    const m = await get('/api/markers/scan/' + encodeURIComponent(code));
    state.start = m.node_id;
    moveYou(m.node_id);
    $('#pos').textContent = '\ud83d\udccd Position found: ' + nodeLabel(m.node_id);
  }catch(e){
    $('#pos').textContent = '';
    $('#err').textContent = 'QR code not recognised.';
  }
}

async function goTo(pid){
  if(state.start == null){ $('#err').textContent = 'Scan a QR code first to set your position.'; return; }
  const prod = state.products.find(p => p.id === pid);
  document.querySelectorAll('.prod').forEach(b => b.classList.toggle('active', Number(b.dataset.id) === pid));
  $('#err').textContent = '';
  try{
    const r = await fetch('/api/navigation/route?store_id=' + state.store.id + '&from_node=' + state.start + '&to_product_id=' + pid);
    if(!r.ok){ const e = await r.json().catch(() => ({})); throw new Error(e.detail || 'Route failed'); }
    const data = await r.json();
    showRoute(data, prod);
  }catch(e){
    $('#err').textContent = e.message;
  }
}

function showRoute(data, prod){
  const pts = data.coordinates.map(c => [state.px(c.x), state.py(c.y)]);
  state.lastPts = pts;
  const route = $('#route');
  route.setAttribute('points', pts.map(p => p.join(',')).join(' '));
  route.style.display = '';
  const last = pts[pts.length - 1];
  const d = $('#dest'); d.style.display = '';
  d.setAttribute('transform', 'translate(' + last[0] + ',' + last[1] + ')');
  d.querySelector('text').textContent = data.shelf_label || '';
  if(pts.length < 2){
    $('#summary').textContent = 'You are already at ' + (data.shelf_label || 'the shelf') + '.';
    $('#steps').innerHTML = '';
    return;
  }
  const secs = Math.round(data.distance / 1.4);
  $('#summary').textContent = fmt(data.distance) + ' m \u00b7 about ' + secs + ' s walk \u00b7 ' + (data.shelf_label || '');
  const steps = buildSteps(data.path_node_ids, data.coordinates, prod ? prod.name : 'Product', data.shelf_label);
  $('#steps').innerHTML = steps.map(s => '<li><span class="ic">' + s.ic + '</span><span>' + esc(s.txt) + '</span></li>').join('');
  $('#replay').style.display = '';
  animate(pts);
}

function buildSteps(path, coords, name, shelf){
  const segs = [];
  for(let i = 0; i < coords.length - 1; i++){
    const dx = coords[i+1].x - coords[i].x, dy = coords[i+1].y - coords[i].y;
    const key = Math.min(path[i], path[i+1]) + '-' + Math.max(path[i], path[i+1]);
    const len = (state.edgeLen[key] !== undefined) ? state.edgeLen[key] : Math.hypot(dx, dy);
    segs.push({dx:dx, dy:dy, len:len, to:path[i+1]});
  }
  const merged = [];
  segs.forEach(s => {
    const l = merged[merged.length - 1];
    if(l && Math.abs(l.dx * s.dy - l.dy * s.dx) < 1e-9 && (l.dx * s.dx + l.dy * s.dy) > 0){
      l.len += s.len; l.to = s.to; l.dx += s.dx; l.dy += s.dy;
    } else merged.push({dx:s.dx, dy:s.dy, len:s.len, to:s.to});
  });
  const out = [];
  merged.forEach((s, i) => {
    const dest = nodeLabel(s.to), m = fmt(s.len);
    if(i === 0){ out.push({ic:'\u2b06\ufe0f', txt:'Walk ' + m + ' m to ' + dest}); return; }
    const p = merged[i-1], cross = p.dx * s.dy - p.dy * s.dx, dot = p.dx * s.dx + p.dy * s.dy;
    if(Math.abs(cross) < 1e-9 && dot < 0) out.push({ic:'\ud83d\udd04', txt:'Turn around, walk ' + m + ' m to ' + dest});
    else if(cross > 0) out.push({ic:'\u21b1', txt:'Turn right, walk ' + m + ' m to ' + dest});
    else out.push({ic:'\u21b0', txt:'Turn left, walk ' + m + ' m to ' + dest});
  });
  out.push({ic:'\ud83c\udfc1', txt:'Arrive: ' + name + ' is at ' + (shelf || 'the marked shelf')});
  return out;
}

function animate(pts){
  cancelAnimationFrame(state.anim);
  const segs = []; let total = 0;
  for(let i = 0; i < pts.length - 1; i++){
    const d = Math.hypot(pts[i+1][0] - pts[i][0], pts[i+1][1] - pts[i][1]);
    segs.push(d); total += d;
  }
  const dur = Math.max(2500, total * 9), t0 = performance.now(), you = $('#you');
  you.style.display = '';
  function frame(t){
    const k = Math.min(1, (t - t0) / dur);
    let dist = k * total, i = 0;
    while(i < segs.length - 1 && dist > segs[i]){ dist -= segs[i]; i++; }
    const f = segs[i] ? dist / segs[i] : 1;
    const x = pts[i][0] + (pts[i+1][0] - pts[i][0]) * f;
    const y = pts[i][1] + (pts[i+1][1] - pts[i][1]) * f;
    you.setAttribute('transform', 'translate(' + x + ',' + y + ')');
    if(k < 1) state.anim = requestAnimationFrame(frame);
  }
  state.anim = requestAnimationFrame(frame);
}

$('#replay').onclick = () => { if(state.lastPts) animate(state.lastPts); };
init();
</script>
</body>
</html>
"""


@router.get("/demo", response_class=HTMLResponse, include_in_schema=False)
def demo_page():
    return PAGE
