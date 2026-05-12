/* GeoToxGraph Browser — D3 force layout + filtering + detail panel.
   No build step. Loads CSVs directly. State held in memory only. */

(function () {
  'use strict';

  // ----- Static config -----
  const LAYERS = {
    geotox: {
      label: 'GeoToxGraph strain map',
      nodesUrl: 'geotoxgraph/geotoxgraph_nodes_enriched.csv',
      edgesUrl: 'geotoxgraph/geotoxgraph_edges_enriched.csv',
    },
    contrast: {
      label: 'Human contrast map',
      nodesUrl: 'geotoxgraph/evolutionary_contrast_nodes.csv',
      edgesUrl: 'geotoxgraph/evolutionary_contrast_edges.csv',
    },
  };

  // Display labels for known categorical values
  const NODE_TYPE_LABEL = {
    strain:   'Strain',
    module:   'Module',
    gene:     'Gene / locus',
    system:   'System',
    compound: 'Compound',
    pathway:  'Pathway',
    microbe:  'Microbial mechanism',
    human:    'Human mechanism',
    process:  'Process',
    contrast: 'Contrast class',
    tissue:   'Tissue context',
  };
  const NODE_TYPE_ORDER = ['strain', 'module', 'microbe', 'human', 'tissue', 'process', 'contrast', 'gene', 'system', 'compound', 'pathway'];

  const STRAIN_LABEL = {
    gmet_gs15: 'G. metallireducens GS-15',
    gsu_pca:   'G. sulfurreducens PCA',
    glov_sz:   'G. lovleyi SZ',
    geo_iae:   'Geobacter sp. strain IAE',
    geobacter: 'Geobacter mechanisms',
    environmental_microbes: 'Environmental microbes',
    human_host:'Human cells',
    shared:    'Shared compounds/processes',
  };
  const MODULE_LABEL = {
    gmet_aromatics:        'GS-15 aromatics',
    gmet_arsenic:          'GS-15 arsenic',
    gsu_arsenic:           'PCA arsenic',
    gsu_metal_redox:       'PCA metal redox',
    glov_organochlorine:   'lovleyi organohalide',
    geo_iae_organochlorine:'IAE organohalide',
    contrast_arsenic:      'Arsenic contrast',
    contrast_aromatics:    'Aromatics contrast',
    contrast_metals:       'Metal redox contrast',
    contrast_uranium:      'Uranium contrast',
    contrast_organochlorine:'Organohalide contrast',
    contrast_pah:           'PAH contrast',
    contrast_aromatic_amines:'Aromatic amine contrast',
    contrast_nitrosamines:  'Nitrosamine contrast',
    contrast_aflatoxin:     'Aflatoxin contrast',
    contrast_aldehydes:     'Aldehyde contrast',
    tissue_context:         'Human tissue context',
  };

  const TIER_LABEL = {
    '1': 'T1 · Strong experimental',
    '2': 'T2 · Supported inference',
    '3': 'T3 · Homology prediction',
    '4': 'T4 · Redox/background',
  };

  // ----- Filter state -----
  const state = {
    nodes: [],
    edges: [],
    nodeIndex: new Map(),       // id -> node
    edgesByNode: new Map(),     // id -> [edge,...]
    filters: {
      q: '',
      strains: new Set(),       // empty means: include all
      modules: new Set(),
      tiers: new Set(['1', '2', '3', '4']),
      types: new Set(NODE_TYPE_ORDER),
    },
    layer: 'geotox',
    selectedId: null,
    pinnedId: null,
    sim: null,
    zoomBehavior: null,
    transform: null,
  };

  // ----- Helpers -----
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function el(tag, attrs = {}, children = []) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') n.className = v;
      else if (k === 'dataset') Object.assign(n.dataset, v);
      else if (k.startsWith('on') && typeof v === 'function') n.addEventListener(k.slice(2), v);
      else if (v === true) n.setAttribute(k, '');
      else if (v === false || v == null) {}
      else n.setAttribute(k, v);
    }
    for (const c of [].concat(children)) {
      if (c == null) continue;
      n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }
    return n;
  }
  function splitList(s) {
    return String(s || '')
      .split(/[;,]/)
      .map((x) => x.trim())
      .filter(Boolean);
  }
  function displayLabel(d) {
    const label = String(d.label || d.id || '');
    const locus = String(d.identifier || '');
    let cleaned = label;
    if (locus && cleaned.startsWith(`${locus} ${locus}`)) {
      cleaned = `${locus}${cleaned.slice((`${locus} ${locus}`).length)}`;
    }
    if (cleaned.length > 34) return `${cleaned.slice(0, 31)}…`;
    return cleaned;
  }
  function safeUrl(u) {
    if (!u) return null;
    try {
      const url = new URL(u);
      return (url.protocol === 'http:' || url.protocol === 'https:') ? url.toString() : null;
    } catch { return null; }
  }
  function selectedNodeUrl(id = state.selectedId) {
    const url = new URL(window.location.href);
    if (id) url.searchParams.set('node', id);
    else url.searchParams.delete('node');
    if (state.layer && state.layer !== 'geotox') url.searchParams.set('layer', state.layer);
    else url.searchParams.delete('layer');
    url.hash = '';
    return url.toString();
  }
  function getUrlNodeId() {
    const params = new URLSearchParams(window.location.search);
    return params.get('node') || null;
  }
  function getUrlLayer() {
    const params = new URLSearchParams(window.location.search);
    const layer = params.get('layer');
    return LAYERS[layer] ? layer : 'geotox';
  }
  function setPinnedUrl(id) {
    window.history.replaceState({}, '', selectedNodeUrl(id));
  }
  function renderShareControls(message = '') {
    const pinBtn = $('#btn-pin-node');
    const shareBtn = $('#btn-share-node');
    const status = $('#share-status');
    const hasSelection = Boolean(state.selectedId);
    if (pinBtn) {
      pinBtn.disabled = !hasSelection;
      pinBtn.classList.toggle('active', hasSelection && state.pinnedId === state.selectedId);
      pinBtn.setAttribute('aria-pressed', String(hasSelection && state.pinnedId === state.selectedId));
      const label = pinBtn.querySelector('.optional-label');
      if (label) label.textContent = hasSelection && state.pinnedId === state.selectedId ? 'Pinned' : 'Pin node';
    }
    if (shareBtn) shareBtn.disabled = !hasSelection;
    if (status) status.textContent = message;
    if (message) setTimeout(() => { if ($('#share-status')?.textContent === message) $('#share-status').textContent = ''; }, 2200);
  }

  // ----- Load + parse -----
  async function loadData() {
    const layer = LAYERS[state.layer] || LAYERS.geotox;
    const [nodesRaw, edgesRaw] = await Promise.all([
      d3.csv(layer.nodesUrl),
      d3.csv(layer.edgesUrl),
    ]);

    const nodes = nodesRaw.map((r) => ({
      id: r.id,
      label: r.label || r.id,
      node_type: r.node_type || 'unknown',
      strain_id: r.strain_id || '',
      module_id: r.module_id || '',
      module_ids: splitList(r.module_id), // multi-module support
      entity_class: r.entity_class || '',
      identifier: r.identifier || '',
      description: r.description || '',
      source_url: r.source_url || '',
      kegg_gene_ids: r.kegg_gene_ids || '',
      ko_ids: r.ko_ids || '',
      ec_numbers: r.ec_numbers || '',
      kegg_pathways: r.kegg_pathways || '',
      kegg_modules: r.kegg_modules || '',
      ncbi_protein_ids: r.ncbi_protein_ids || '',
      uniprot_ids: r.uniprot_ids || '',
      pubchem_cid: r.pubchem_cid || '',
      kegg_compound: r.kegg_compound || '',
      chebi_id: r.chebi_id || '',
      metacyc_candidate: r.metacyc_candidate || '',
      metacyc_status: r.metacyc_status || '',
      annotation_status: r.annotation_status || '',
    }));

    // Pre-compute searchable haystack
    for (const n of nodes) {
      n._search = [
        n.id, n.label, n.identifier,
        n.kegg_gene_ids, n.ko_ids, n.ec_numbers,
        n.kegg_pathways, n.kegg_modules,
        n.ncbi_protein_ids, n.uniprot_ids,
        n.pubchem_cid, n.kegg_compound, n.chebi_id,
        n.description, n.entity_class, n.annotation_status, n.strain_id, n.module_id,
      ].join(' ').toLowerCase();
    }

    const edges = edgesRaw.map((r) => ({
      edge_id: r.edge_id,
      source: r.source_id,
      target: r.target_id,
      predicate: r.predicate || '',
      enzyme_or_system: r.enzyme_or_system || '',
      strain_id: r.strain_id || '',
      module_id: r.module_id || '',
      module_ids: splitList(r.module_id),
      evidence_tier: (r.evidence_tier || '').trim(),
      evidence_type: r.evidence_type || '',
      effect: r.effect || '',
      source_url: r.source_url || '',
      notes: r.notes || '',
    }));

    state.nodes = nodes;
    state.edges = edges;
    state.nodeIndex = new Map(nodes.map((n) => [n.id, n]));
    state.edgesByNode = new Map();
    for (const e of edges) {
      if (!state.edgesByNode.has(e.source)) state.edgesByNode.set(e.source, []);
      if (!state.edgesByNode.has(e.target)) state.edgesByNode.set(e.target, []);
      state.edgesByNode.get(e.source).push(e);
      state.edgesByNode.get(e.target).push(e);
    }
  }

  function resetFiltersForLayer() {
    const types = new Set(state.nodes.map((n) => n.node_type).filter(Boolean));
    const tiers = new Set(state.edges.map((e) => e.evidence_tier).filter(Boolean));
    state.filters.q = '';
    state.filters.strains.clear();
    state.filters.modules.clear();
    state.filters.tiers = tiers.size ? tiers : new Set(['1', '2', '3', '4']);
    state.filters.types = types.size ? types : new Set(NODE_TYPE_ORDER);
    const search = $('#q-search');
    if (search) search.value = '';
  }

  // ----- Filter logic -----
  function matchesFilters(node) {
    const f = state.filters;
    if (!f.types.has(node.node_type)) return false;

    if (f.strains.size > 0) {
      // strain match: node has strain_id in selected OR is a strain node selected
      if (!node.strain_id || !f.strains.has(node.strain_id)) {
        // Allow strain nodes themselves to pass if their own strain is selected
        if (!(node.node_type === 'strain' && f.strains.has(node.id.replace(/^strain:/, '')))) {
          // compounds/pathways with no strain still pass when no strain filter constrains them?
          // Decision: strict — if user selects strains, only include strain-tagged nodes.
          return false;
        }
      }
    }

    if (f.modules.size > 0) {
      const has = node.module_ids.some((m) => f.modules.has(m))
               || (node.node_type === 'module' && f.modules.has(node.id.replace(/^module:/, '')));
      if (!has) return false;
    }

    if (f.q) {
      if (!node._search.includes(f.q)) return false;
    }
    return true;
  }

  function computeFiltered() {
    const visibleNodes = new Set();
    for (const n of state.nodes) {
      if (matchesFilters(n)) visibleNodes.add(n.id);
    }

    // Edges visible if both endpoints visible AND tier passes
    const tiers = state.filters.tiers;
    const visibleEdges = state.edges.filter((e) =>
      visibleNodes.has(e.source.id || e.source) &&
      visibleNodes.has(e.target.id || e.target) &&
      tiers.has(e.evidence_tier)
    );

    return { visibleNodes, visibleEdges };
  }

  // ----- Render: filters UI -----
  function uniqueValues(arr, key) {
    const m = new Map();
    for (const x of arr) {
      const v = x[key];
      if (!v) continue;
      m.set(v, (m.get(v) || 0) + 1);
    }
    return Array.from(m.entries()).sort((a, b) => b[1] - a[1]);
  }

  function buildCheckGroup(container, items, getLabel, getColor, set, onChange) {
    container.innerHTML = '';
    for (const [val, count] of items) {
      const cb = el('input', { type: 'checkbox', checked: set.has(val) });
      cb.addEventListener('change', () => {
        if (cb.checked) set.add(val); else set.delete(val);
        onChange();
      });
      const children = [
        cb,
        getColor ? el('span', { class: 'swatch', style: `color: ${getColor(val)}; background: ${getColor(val)};` }) : null,
        el('span', {}, getLabel(val)),
      ];
      if (count !== '' && count != null) children.push(el('span', { class: 'count' }, String(count)));
      const label = el('label', { class: 'chk' }, children);
      container.appendChild(label);
    }
  }

  function buildChipGroup(container, items, getLabel, set, onChange) {
    container.innerHTML = '';
    for (const [val, count] of items) {
      const isActive = set.has(val);
      const cb = el('input', { type: 'checkbox', checked: isActive });
      const chip = el('label', { class: 'chk', dataset: { active: String(isActive) } }, [
        cb,
        el('span', {}, `${getLabel(val)}`),
        el('span', { class: 'count' }, String(count)),
      ]);
      cb.addEventListener('change', () => {
        if (cb.checked) set.add(val); else set.delete(val);
        chip.dataset.active = String(cb.checked);
        onChange();
      });
      container.appendChild(chip);
    }
  }

  function nodeColor(node) {
    const css = getComputedStyle(document.documentElement);
    const map = {
      strain:   css.getPropertyValue('--n-strain'),
      module:   css.getPropertyValue('--n-module'),
      gene:     css.getPropertyValue('--n-gene'),
      system:   css.getPropertyValue('--n-system'),
      compound: css.getPropertyValue('--n-compound'),
      pathway:  css.getPropertyValue('--n-pathway'),
      microbe:  css.getPropertyValue('--n-microbe'),
      human:    css.getPropertyValue('--n-human'),
      process:  css.getPropertyValue('--n-process'),
      contrast: css.getPropertyValue('--n-contrast'),
      tissue:   css.getPropertyValue('--n-tissue'),
    };
    return (map[node.node_type] || '#9aa').trim();
  }

  function nodeRadius(node) {
    return ({
      strain: 11, module: 9, gene: 5.5, system: 7,
      compound: 6.5, pathway: 7, microbe: 9, human: 9,
      tissue: 7, process: 7.5, contrast: 8,
    })[node.node_type] || 5;
  }

  function renderFilters() {
    // Strains
    const strainCounts = uniqueValues(state.nodes.filter((n) => n.strain_id), 'strain_id');
    buildCheckGroup(
      $('#filter-strains'),
      strainCounts,
      (v) => STRAIN_LABEL[v] || v,
      null,
      state.filters.strains,
      onFilterChange,
    );

    // Modules
    const modCounts = new Map();
    for (const n of state.nodes) for (const m of n.module_ids) {
      modCounts.set(m, (modCounts.get(m) || 0) + 1);
    }
    const modItems = Array.from(modCounts.keys()).sort().map((m) => [m, '']);
    buildCheckGroup(
      $('#filter-modules'),
      modItems,
      (v) => MODULE_LABEL[v] || v,
      null,
      state.filters.modules,
      onFilterChange,
    );

    // Tiers (chips)
    const tierCounts = uniqueValues(state.edges, 'evidence_tier');
    const tierOrder = ['1', '2', '3', '4'];
    const tierItems = tierOrder
      .map((t) => [t, (tierCounts.find(([v]) => v === t) || [, 0])[1]])
      .filter(([, c]) => c > 0 || ['1','2','3','4'].includes(state.filters.tiers.has));
    buildChipGroup(
      $('#filter-tiers'),
      tierItems,
      (v) => `T${v}`,
      state.filters.tiers,
      onFilterChange,
    );

    // Types
    const typeCounts = uniqueValues(state.nodes, 'node_type');
    typeCounts.sort((a, b) => NODE_TYPE_ORDER.indexOf(a[0]) - NODE_TYPE_ORDER.indexOf(b[0]));
    buildCheckGroup(
      $('#filter-types'),
      typeCounts,
      (v) => NODE_TYPE_LABEL[v] || v,
      (v) => {
        const css = getComputedStyle(document.documentElement);
        return css.getPropertyValue(`--n-${v}`).trim() || '#999';
      },
      state.filters.types,
      onFilterChange,
    );
    renderCompoundCompareControl();
  }

  function renderCompoundCompareControl() {
    const select = $('#compound-compare');
    const help = $('#compare-help');
    if (!select) return;
    select.innerHTML = '';
    select.appendChild(el('option', { value: '' }, 'Choose a compound…'));
    const compounds = state.nodes
      .filter((n) => n.node_type === 'compound')
      .sort((a, b) => a.label.localeCompare(b.label));
    for (const n of compounds) {
      select.appendChild(el('option', { value: n.id }, n.label));
    }
    const enabled = state.layer === 'contrast' && compounds.length > 0;
    select.disabled = !enabled;
    if (help) {
      help.textContent = enabled
        ? 'Choose an exposure to compare microbial transformation with human exposure handling.'
        : 'Switch to the Human contrast map to enable compound-centered comparison.';
    }
    if (state.selectedId && state.nodeIndex.get(state.selectedId)?.node_type === 'compound') {
      select.value = state.selectedId;
    }
  }

  function renderLegend() {
    // Node types
    const ul = $('#legend-types');
    ul.innerHTML = '';
    const presentTypes = new Set(state.nodes.map((n) => n.node_type));
    for (const t of NODE_TYPE_ORDER.filter((type) => presentTypes.has(type))) {
      const c = getComputedStyle(document.documentElement).getPropertyValue(`--n-${t}`).trim();
      ul.appendChild(el('li', {}, [
        el('span', { class: 'swatch', style: `color: ${c}; background: ${c};` }),
        el('span', {}, NODE_TYPE_LABEL[t]),
      ]));
    }
    // Tiers
    const ulT = $('#legend-tiers');
    ulT.innerHTML = '';
    const presentTiers = new Set(state.edges.map((e) => e.evidence_tier).filter(Boolean));
    for (const t of ['1', '2', '3', '4'].filter((tier) => presentTiers.has(tier))) {
      const c = getComputedStyle(document.documentElement).getPropertyValue(`--t-${t}`).trim();
      const stroke = el('span', { class: 'stroke', style: `color: ${c};` });
      if (t === '4') stroke.style.backgroundImage = `repeating-linear-gradient(90deg, ${c} 0 3px, transparent 3px 6px)`;
      ulT.appendChild(el('li', {}, [
        stroke,
        el('span', {}, TIER_LABEL[t]),
      ]));
    }
  }

  function updateCounts({ visibleNodes, visibleEdges }) {
    const c = $('#counts');
    if (c) c.textContent = `${visibleNodes.size}/${state.nodes.length} nodes · ${visibleEdges.length}/${state.edges.length} edges`;
    const sn = $('#stat-nodes'); if (sn) sn.textContent = state.nodes.length;
    const se = $('#stat-edges'); if (se) se.textContent = state.edges.length;
    const ss = $('#stat-strains');
    if (ss) ss.textContent = new Set(state.nodes.filter(n => n.strain_id).map(n => n.strain_id)).size;
    const sm = $('#stat-modules');
    if (sm) {
      const allMods = new Set();
      for (const n of state.nodes) for (const m of n.module_ids) allMods.add(m);
      sm.textContent = allMods.size;
    }
  }

  // ----- Graph rendering -----
  const svgState = {
    svg: null,
    root: null,
    linkSel: null,
    nodeSel: null,
    labelSel: null,
    arrowMarker: null,
  };

  function setupSvg() {
    const svg = d3.select('#graph-svg');
    svgState.svg = svg;

    // Arrowhead markers per tier
    const defs = svg.append('defs');
    for (const t of ['1', '2', '3', '4']) {
      defs.append('marker')
        .attr('id', `arrow-t${t}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 12)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-4L8,0L0,4')
        .attr('class', `arrow-fill t-${t}`)
        .attr('fill', getComputedStyle(document.documentElement).getPropertyValue(`--t-${t}`).trim());
    }

    const root = svg.append('g').attr('class', 'graph-root');
    svgState.root = root;

    const zoom = d3.zoom()
      .scaleExtent([0.2, 6])
      .on('zoom', (ev) => {
        root.attr('transform', ev.transform);
        state.transform = ev.transform;
        updateLabelVisibility();
      });
    state.zoomBehavior = zoom;
    svg.call(zoom);

    // Click empty space deselects
    svg.on('click', (ev) => {
      if (ev.target.closest('.node')) return;
      selectNode(null);
    });
  }

  function buildSim() {
    const { width, height } = $('#graph-svg').getBoundingClientRect();
    const largeGraph = state.nodes.length > 80;
    state.sim = d3.forceSimulation(state.nodes)
      .force('charge', d3.forceManyBody().strength((d) => {
        if (largeGraph) return d.node_type === 'strain' ? -240 : d.node_type === 'module' ? -140 : -55;
        return d.node_type === 'strain' ? -360 : d.node_type === 'module' ? -230 : -110;
      }))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius((d) => nodeRadius(d) + (largeGraph ? 3 : 5)))
      .force('link', d3.forceLink(state.edges)
        .id((d) => d.id)
        .distance((d) => {
          const t = d.evidence_tier;
          if (d.predicate === 'has_module' || d.predicate === 'member_of') return largeGraph ? 36 : 50;
          if (d.predicate === 'participates_in') return largeGraph ? 48 : 70;
          return largeGraph ? 62 : 90;
        })
        .strength((d) => d.predicate === 'has_module' ? 0.75 : largeGraph ? 0.55 : 0.4))
      .force('x', d3.forceX(width / 2).strength(largeGraph ? 0.075 : 0.04))
      .force('y', d3.forceY(height / 2).strength(largeGraph ? 0.075 : 0.04))
      .on('tick', tick);
  }

  function drawGraph() {
    const root = svgState.root;

    // Links
    const links = root.selectAll('path.link').data(state.edges, (d) => d.edge_id);
    links.exit().remove();
    const linksEnter = links.enter().append('path')
      .attr('class', (d) => `link t-${d.evidence_tier}`)
      .attr('stroke-width', (d) => d.evidence_tier === '1' ? 1.6 : d.evidence_tier === '2' ? 1.2 : 1.0)
      .attr('marker-end', (d) => `url(#arrow-t${d.evidence_tier})`);
    svgState.linkSel = linksEnter.merge(links);

    // Node groups
    const nodes = root.selectAll('g.node').data(state.nodes, (d) => d.id);
    nodes.exit().remove();
    const nodesEnter = nodes.enter().append('g')
      .attr('class', 'node')
      .attr('tabindex', 0)
      .on('click', (ev, d) => { ev.stopPropagation(); selectNode(d.id); })
      .on('keydown', (ev, d) => {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); selectNode(d.id); }
      })
      .call(d3.drag()
        .on('start', (ev, d) => { if (!ev.active) state.sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag',  (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
        .on('end',   (ev, d) => { if (!ev.active) state.sim.alphaTarget(0); d.fx = null; d.fy = null; }));

    nodesEnter.append('circle')
      .attr('class', 'body')
      .attr('r', (d) => nodeRadius(d))
      .attr('fill', (d) => nodeColor(d));

    nodesEnter.append('title')
      .text((d) => `${d.label} (${NODE_TYPE_LABEL[d.node_type] || d.node_type})`);

    nodesEnter.append('text')
      .attr('class', 'node-label')
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => -nodeRadius(d) - 4)
      .text((d) => displayLabel(d));

    svgState.nodeSel = nodesEnter.merge(nodes);
  }

  function tick() {
    if (!svgState.linkSel) return;
    const { width, height } = $('#graph-svg').getBoundingClientRect();
    const pad = state.nodes.length > 80 ? 42 : 28;
    for (const d of state.nodes) {
      d.x = Math.max(pad, Math.min(width - pad, d.x || width / 2));
      d.y = Math.max(pad, Math.min(height - pad, d.y || height / 2));
    }
    svgState.linkSel.attr('d', (d) => {
      const s = d.source, t = d.target;
      // straight path with arrow offset implicit via marker refX
      return `M${s.x},${s.y}L${t.x},${t.y}`;
    });
    svgState.nodeSel.attr('transform', (d) => `translate(${d.x},${d.y})`);
    updateLabelVisibility();
  }

  function applyVisibility({ visibleNodes, visibleEdges }) {
    if (!svgState.nodeSel) return;
    const visibleEdgeIds = new Set(visibleEdges.map((e) => e.edge_id));
    svgState.nodeSel.classed('dim', (d) => !visibleNodes.has(d.id));
    svgState.linkSel.classed('dim', (d) => !visibleEdgeIds.has(d.edge_id));
    updateLabelVisibility(visibleNodes);
  }

  function updateLabelVisibility(visibleNodes = null) {
    if (!svgState.nodeSel) return;
    const qActive = Boolean(state.filters.q);
    const visible = visibleNodes || computeFiltered().visibleNodes;
    const bounds = $('#graph-svg').getBoundingClientRect();
    const transform = state.transform || d3.zoomIdentity;
    svgState.nodeSel.select('.node-label')
      .style('display', (d) => {
        const highLevel = false;
        const selected = d.id === state.selectedId;
        const searchHit = qActive && visible.has(d.id);
        const sx = transform.applyX(d.x || 0);
        const sy = transform.applyY(d.y || 0);
        const labelPad = 72;
        const labelTopPad = 28;
        const insideViewport =
          sx > labelPad &&
          sx < bounds.width - labelPad &&
          sy > labelTopPad &&
          sy < bounds.height - labelTopPad;
        return ((highLevel || selected || searchHit) && insideViewport) ? null : 'none';
      });
  }

  // ----- Selection / detail panel -----
  function selectNode(id) {
    state.selectedId = id;
    if (!id && state.pinnedId) {
      state.pinnedId = null;
      setPinnedUrl(null);
    }
    svgState.nodeSel.attr('data-selected', (d) => (d.id === id ? 'true' : null));
    updateLabelVisibility();
    renderDetail();
    const compare = $('#compound-compare');
    if (compare) compare.value = id && state.nodeIndex.get(id)?.node_type === 'compound' ? id : '';
    renderShareControls();
    if (id && window.matchMedia('(max-width: 1100px)').matches) openMobileSheet();
  }

  function pinSelectedNode() {
    if (!state.selectedId) return;
    if (state.pinnedId === state.selectedId) {
      state.pinnedId = null;
      setPinnedUrl(null);
      renderShareControls('Node unpinned');
      return;
    }
    state.pinnedId = state.selectedId;
    setPinnedUrl(state.selectedId);
    renderShareControls('Node pinned in URL');
  }

  async function shareSelectedNode() {
    if (!state.selectedId) return;
    const url = selectedNodeUrl(state.selectedId);
    state.pinnedId = state.selectedId;
    setPinnedUrl(state.selectedId);
    try {
      if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(url);
      else throw new Error('clipboard unavailable');
      renderShareControls('Node URL copied');
    } catch {
      const box = el('textarea', { style: 'position:fixed;left:-9999px;top:0;' }, url);
      document.body.appendChild(box);
      box.focus();
      box.select();
      let copied = false;
      try { copied = document.execCommand('copy'); } catch {}
      box.remove();
      renderShareControls(copied ? 'Node URL copied' : 'Copy URL from address bar');
    }
  }

  function renderDetail() {
    const panel = $('#detail');
    panel.innerHTML = '';
    const mobilePanel = $('#mobile-detail');
    if (mobilePanel) mobilePanel.innerHTML = '';
    const id = state.selectedId;
    if (!id || !state.nodeIndex.has(id)) {
      panel.appendChild(renderEmptyDetail());
      if (mobilePanel) mobilePanel.appendChild(renderEmptyDetail());
      closeMobileSheet(false);
      return;
    }
    const n = state.nodeIndex.get(id);
    const isCompoundComparison = state.layer === 'contrast' && n.node_type === 'compound';
    const content = isCompoundComparison ? renderCompoundComparisonContent(n) : renderNodeDetailContent(n);
    panel.appendChild(content);
    if (mobilePanel) mobilePanel.appendChild(isCompoundComparison ? renderCompoundComparisonContent(n) : renderNodeDetailContent(n));
    const mobileTitle = $('#mobile-sheet-title');
    if (mobileTitle) mobileTitle.textContent = n.label;
  }

  function selectCompoundComparison(id) {
    if (!id || !state.nodeIndex.has(id)) {
      selectNode(null);
      return;
    }
    selectNode(id);
  }

  function renderNodeDetailContent(n) {
    const panel = el('div', { class: 'detail-content' });
    const color = nodeColor(n);

    const head = el('div', { class: 'detail-head' }, [
      el('div', { class: 'type-pill', style: `color: ${color};` }, [
        el('span', { class: 'swatch' }),
        NODE_TYPE_LABEL[n.node_type] || n.node_type,
      ]),
      el('h3', { style: 'margin-top: 8px;' }, n.label),
      el('div', { class: 'muted', style: 'font-family: var(--font-mono); font-size: 11px; word-break: break-all;' }, n.id),
    ]);
    panel.appendChild(head);

    if (n.description) {
      panel.appendChild(el('p', { style: 'margin: 10px 0; color: var(--c-text-soft);' }, n.description));
    }

    // Meta grid
    const meta = el('dl', { class: 'meta-grid' });
    function pushMeta(k, v) {
      if (!v) return;
      meta.appendChild(el('dt', {}, k));
      meta.appendChild(el('dd', {}, v));
    }
    pushMeta('Strain', STRAIN_LABEL[n.strain_id] || n.strain_id);
    if (n.module_ids.length) {
      meta.appendChild(el('dt', {}, 'Module'));
      meta.appendChild(el('dd', {}, n.module_ids.map((m) => MODULE_LABEL[m] || m).join(', ')));
    }
    pushMeta('Class', n.entity_class);
    pushMeta('Annotation', n.annotation_status);
    if (n.source_url) {
      const url = safeUrl(n.source_url);
      if (url) {
        meta.appendChild(el('dt', {}, 'Source'));
        meta.appendChild(el('dd', {}, el('a', { href: url, target: '_blank', rel: 'noopener noreferrer' }, url.replace(/^https?:\/\//, ''))));
      }
    }
    if (meta.children.length) {
      const sec = el('section', { class: 'detail-section' }, [el('h4', {}, 'Metadata'), meta]);
      panel.appendChild(sec);
    }

    // Identifiers
    const ids = el('ul', { class: 'identifier-list' });
    function pushId(k, v) {
      if (!v) return;
      ids.appendChild(el('li', {}, [
        el('span', { class: 'k' }, k),
        el('span', {}, v),
      ]));
    }
    pushId('Identifier', n.identifier);
    pushId('KO', n.ko_ids);
    pushId('EC', n.ec_numbers);
    pushId('KEGG gene', n.kegg_gene_ids);
    pushId('Pathway', n.kegg_pathways);
    pushId('Module', n.kegg_modules);
    pushId('NCBI', n.ncbi_protein_ids);
    pushId('UniProt', n.uniprot_ids);
    pushId('PubChem', n.pubchem_cid);
    pushId('KEGG cpd', n.kegg_compound);
    pushId('ChEBI', n.chebi_id);
    if (n.metacyc_candidate) pushId('MetaCyc', `${n.metacyc_candidate}${n.metacyc_status ? ' · ' + n.metacyc_status : ''}`);

    if (ids.children.length) {
      panel.appendChild(el('section', { class: 'detail-section' }, [
        el('h4', {}, 'Identifiers'),
        ids,
      ]));
    }

    // Connected edges
    const myEdges = state.edgesByNode.get(n.id) || [];
    const inEdges = myEdges.filter((e) => (e.target.id || e.target) === n.id);
    const outEdges = myEdges.filter((e) => (e.source.id || e.source) === n.id);

    const edgesSec = el('section', { class: 'detail-section' });
    edgesSec.appendChild(el('h4', {}, `Edges (${myEdges.length})`));
    if (!myEdges.length) {
      edgesSec.appendChild(el('p', { class: 'muted', style: 'font-size: 12px;' }, 'No connected edges.'));
    } else {
      const ul = el('ul', { class: 'edge-list' });
      // Outgoing first
      for (const e of outEdges) ul.appendChild(renderEdgeCard(e, 'out', n.id));
      for (const e of inEdges) ul.appendChild(renderEdgeCard(e, 'in', n.id));
      edgesSec.appendChild(ul);
    }
    panel.appendChild(edgesSec);
    return panel;
  }

  function getOtherNode(edge, selfId) {
    const s = edge.source.id || edge.source;
    const t = edge.target.id || edge.target;
    return state.nodeIndex.get(s === selfId ? t : s);
  }

  function mechanismNeighborhood(mechanisms) {
    const out = { processes: new Map(), contrasts: new Map(), tissues: new Map(), edges: [] };
    for (const mech of mechanisms) {
      const edges = state.edgesByNode.get(mech.id) || [];
      for (const e of edges) {
        const other = getOtherNode(e, mech.id);
        if (!other) continue;
        out.edges.push(e);
        if (other.node_type === 'process') out.processes.set(other.id, other);
        if (other.node_type === 'contrast') out.contrasts.set(other.id, other);
        if (other.node_type === 'tissue') out.tissues.set(other.id, other);
      }
    }
    return out;
  }

  function renderMiniNodeList(title, nodes, emptyText) {
    const card = el('div', { class: 'compare-card' }, [
      el('h4', {}, title),
    ]);
    if (!nodes.length) {
      card.appendChild(el('p', { class: 'muted' }, emptyText));
      return card;
    }
    const ul = el('ul', { class: 'compare-list' });
    for (const n of nodes) {
      ul.appendChild(el('li', {}, [
        el('button', {
          type: 'button',
          class: 'other',
          onclick: () => selectNode(n.id),
          title: `Open ${n.label}`,
        }, n.label),
        n.description ? el('span', {}, n.description) : null,
      ]));
    }
    card.appendChild(ul);
    return card;
  }

  function humanizeOutcome(effect) {
    const map = {
      detoxification: 'Detoxification',
      methylation_efflux: 'Methylation + efflux',
      catabolism: 'Catabolism',
      oxidation: 'Oxidation',
      conjugation_excretion: 'Conjugation + excretion',
      dearomatization: 'Dearomatization',
      extracellular_reduction: 'Extracellular reduction',
      genotoxicity: 'DNA damage / genotoxicity',
      redox_transformation: 'Redox transformation',
      bioactivation: 'Bioactivation',
      immobilization: 'Immobilization',
      nephrotoxicity_response: 'Renal stress response',
      chlororespiration: 'Chlororespiration',
      oxidation_conjugation_toxicity: 'Oxidation / GSH toxicity',
      detoxtification_route: 'Detoxification route',
      toxicity_prone_metabolism: 'Toxicity-prone metabolism',
      conserved_chemistry: 'Conserved chemistry',
      lost_catabolic_pathway: 'Lost catabolic pathway',
      excretion_not_catabolism: 'Excretion, not catabolism',
      toxic_inversion: 'Toxic inversion',
      stress_not_respiration: 'Stress response, not respiration',
      lost_respiration: 'Lost respiration',
    };
    return map[effect] || String(effect || 'Outcome not specified').replace(/_/g, ' ');
  }

  function outcomeKind(effect, nodeType) {
    const e = String(effect || '').toLowerCase();
    if (nodeType === 'microbe' && /catabolism|immobilization|chlororespiration|detox|extracellular|redox/.test(e)) return 'microbial-benefit';
    if (/genotoxic|bioactivation|toxicity|nephro|stress|damage/.test(e)) return 'human-risk';
    if (/conjugation|efflux|methylation|excretion/.test(e)) return 'human-handling';
    if (/lost|inversion/.test(e)) return 'contrast-warning';
    return 'neutral';
  }

  function routeSummaries(compound, mechanisms) {
    const direct = state.edgesByNode.get(compound.id) || [];
    return mechanisms.map((node) => {
      const edge = direct.find((e) => (e.source.id || e.source) === compound.id && (e.target.id || e.target) === node.id)
        || direct.find((e) => (e.target.id || e.target) === compound.id && (e.source.id || e.source) === node.id);
      return {
        node,
        effect: edge?.effect || '',
        outcome: humanizeOutcome(edge?.effect),
        kind: outcomeKind(edge?.effect, node.node_type),
        edge,
      };
    });
  }

  function renderOutcomeChip(text, kind = 'neutral') {
    return el('span', { class: `outcome-chip ${kind}` }, text);
  }

  function renderSankeyFlow(compound, microbial, human, contrasts) {
    const microRoutes = routeSummaries(compound, microbial);
    const humanRoutes = routeSummaries(compound, human);
    const contrastLabels = contrasts.map((n) => n.label);
    const card = el('div', { class: 'sankey-card' }, [
      el('div', { class: 'sankey-title' }, [
        el('span', {}, 'Outcome flow'),
        contrastLabels.length ? el('span', { class: 'sankey-subtitle' }, contrastLabels.join(' · ')) : null,
      ]),
    ]);

    function row(label, routes, side) {
      const route = routes[0];
      const nodeLabel = route?.node?.label || 'No linked route';
      const outcome = route?.outcome || 'Outcome not specified';
      const kind = route?.kind || 'neutral';
      return el('div', { class: `sankey-row ${side}` }, [
        el('div', { class: 'sankey-node exposure' }, [el('span', {}, compound.label), renderOutcomeChip('exposure', 'neutral')]),
        el('div', { class: 'sankey-band', 'aria-hidden': 'true' }),
        el('div', { class: `sankey-node mechanism ${side}` }, [
          el('span', { class: 'sankey-kicker' }, label),
          el('strong', {}, nodeLabel),
        ]),
        el('div', { class: 'sankey-band', 'aria-hidden': 'true' }),
        el('div', { class: `sankey-node outcome ${kind}` }, [
          el('span', { class: 'sankey-kicker' }, 'Outcome'),
          renderOutcomeChip(outcome, kind),
        ]),
      ]);
    }

    card.appendChild(row('Geobacter', microRoutes, 'microbe'));
    card.appendChild(row('Human cells', humanRoutes, 'human'));
    if (microRoutes.length + humanRoutes.length > 2) {
      const extras = el('div', { class: 'sankey-extra' });
      for (const r of microRoutes.slice(1)) extras.appendChild(renderOutcomeChip(`Geobacter: ${r.outcome}`, r.kind));
      for (const r of humanRoutes.slice(1)) extras.appendChild(renderOutcomeChip(`Human: ${r.outcome}`, r.kind));
      card.appendChild(extras);
    }
    return card;
  }

  function renderEvidenceList(edges) {
    const unique = [];
    const seen = new Set();
    for (const e of edges) {
      const key = `${e.edge_id}`;
      if (!seen.has(key)) {
        seen.add(key);
        unique.push(e);
      }
    }
    const card = el('div', { class: 'compare-card wide' }, [el('h4', {}, 'Evidence and interpretation')]);
    const ul = el('ul', { class: 'edge-list compact' });
    for (const e of unique.slice(0, 10)) {
      const source = state.nodeIndex.get(e.source.id || e.source);
      const target = state.nodeIndex.get(e.target.id || e.target);
      const url = safeUrl(e.source_url);
      ul.appendChild(el('li', { class: 'edge-card' }, [
        el('div', { class: 'row' }, [
          el('span', { class: 'pred' }, e.predicate || '—'),
          el('span', { class: 'arrow' }, '→'),
          el('span', { class: 'other' }, `${source?.label || e.source} → ${target?.label || e.target}`),
          el('span', { class: 'tier', style: `color: ${getComputedStyle(document.documentElement).getPropertyValue(`--t-${e.evidence_tier}`).trim()};` }, `T${e.evidence_tier || '?'}`),
        ]),
        el('div', { class: 'meta' }, [
          e.effect ? el('span', {}, e.effect) : null,
          e.evidence_type ? el('span', {}, e.evidence_type) : null,
          url ? el('a', { href: url, target: '_blank', rel: 'noopener noreferrer' }, 'source ↗') : null,
        ]),
        e.notes ? el('div', { class: 'meta', style: 'font-style: italic;' }, e.notes) : null,
      ]));
    }
    card.appendChild(ul);
    return card;
  }

  function renderCompoundComparisonContent(compound) {
    const panel = el('div', { class: 'detail-content comparison-mode' });
    const directEdges = state.edgesByNode.get(compound.id) || [];
    const directNodes = directEdges.map((e) => getOtherNode(e, compound.id)).filter(Boolean);
    const microbial = directNodes.filter((n) => n.node_type === 'microbe');
    const human = directNodes.filter((n) => n.node_type === 'human');
    const microbialNeighborhood = mechanismNeighborhood(microbial);
    const humanNeighborhood = mechanismNeighborhood(human);
    const contrastNodes = new Map([
      ...microbialNeighborhood.contrasts,
      ...humanNeighborhood.contrasts,
    ]);
    const processNodes = new Map([
      ...microbialNeighborhood.processes,
      ...humanNeighborhood.processes,
    ]);
    const tissueNodes = new Map([
      ...humanNeighborhood.tissues,
      ...microbialNeighborhood.tissues,
    ]);
    const evidenceEdges = [
      ...directEdges,
      ...microbialNeighborhood.edges,
      ...humanNeighborhood.edges,
    ];

    panel.appendChild(el('div', { class: 'compare-hero' }, [
      el('div', { class: 'type-pill', style: `color: ${nodeColor(compound)};` }, [
        el('span', { class: 'swatch' }),
        'Exposure comparison',
      ]),
      el('h3', {}, compound.label),
      el('p', { class: 'muted' }, compound.description || 'Compound-centered contrast between microbial transformation and human exposure handling.'),
    ]));

    panel.appendChild(renderSankeyFlow(compound, microbial, human, Array.from(contrastNodes.values())));

    panel.appendChild(el('div', { class: 'compare-grid' }, [
      renderMiniNodeList('Geobacter route', microbial, 'No microbial route linked for this compound.'),
      renderMiniNodeList('Human route', human, 'No human exposure-handling route linked for this compound.'),
      renderMiniNodeList('Contrast class', Array.from(contrastNodes.values()), 'No contrast class linked yet.'),
      renderMiniNodeList('Shared chemistry / process', Array.from(processNodes.values()), 'No shared process linked yet.'),
      renderMiniNodeList('Human tissue context', Array.from(tissueNodes.values()), 'No tissue context linked yet.'),
    ]));

    panel.appendChild(renderEvidenceList(evidenceEdges));
    return panel;
  }

  function openMobileSheet() {
    const sheet = $('#mobile-sheet');
    const backdrop = $('#mobile-sheet-backdrop');
    if (!sheet || !backdrop) return;
    sheet.hidden = false;
    backdrop.hidden = false;
    requestAnimationFrame(() => {
      sheet.dataset.open = 'true';
      backdrop.dataset.open = 'true';
    });
  }

  function closeMobileSheet(clearSelection = true) {
    const sheet = $('#mobile-sheet');
    const backdrop = $('#mobile-sheet-backdrop');
    if (!sheet || !backdrop) return;
    sheet.dataset.open = 'false';
    backdrop.dataset.open = 'false';
    if (clearSelection && state.selectedId) {
      state.selectedId = null;
      if (svgState.nodeSel) svgState.nodeSel.attr('data-selected', null);
      updateLabelVisibility();
      renderDetail();
      return;
    }
    setTimeout(() => {
      if (sheet.dataset.open !== 'true') sheet.hidden = true;
      if (backdrop.dataset.open !== 'true') backdrop.hidden = true;
    }, 180);
  }

  function renderEdgeCard(e, dir, selfId) {
    const otherId = dir === 'out' ? (e.target.id || e.target) : (e.source.id || e.source);
    const other = state.nodeIndex.get(otherId);
    const tier = e.evidence_tier || '?';
    const tierColor = getComputedStyle(document.documentElement).getPropertyValue(`--t-${tier}`).trim() || '#888';
    const arrow = dir === 'out' ? '→' : '←';
    const otherBtn = el('button', {
      type: 'button',
      class: 'other',
      onclick: () => selectNode(otherId),
      title: `View ${other ? other.label : otherId}`,
    }, other ? other.label : otherId);

    const row = el('div', { class: 'row' }, [
      el('span', { class: 'pred' }, e.predicate || '—'),
      el('span', { class: 'arrow' }, arrow),
      otherBtn,
      el('span', { class: 'tier', style: `color: ${tierColor};` }, `T${tier}`),
    ]);

    const meta = el('div', { class: 'meta' });
    if (e.effect) meta.appendChild(el('span', {}, e.effect));
    if (e.enzyme_or_system) meta.appendChild(el('span', {}, e.enzyme_or_system));
    if (e.evidence_type) meta.appendChild(el('span', {}, e.evidence_type));
    const url = safeUrl(e.source_url);
    if (url) meta.appendChild(el('a', { href: url, target: '_blank', rel: 'noopener noreferrer' }, 'source ↗'));

    const card = el('li', { class: 'edge-card' }, [row]);
    if (meta.children.length) card.appendChild(meta);
    if (e.notes) card.appendChild(el('div', { class: 'meta', style: 'font-style: italic;' }, e.notes));
    return card;
  }

  function renderEmptyDetail() {
    const mark = el('div', { class: 'detail-empty-mark' });
    mark.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" stroke-width="1.4"/><circle cx="4" cy="6" r="1.6" fill="currentColor" opacity="0.5"/><circle cx="20" cy="6" r="1.6" fill="currentColor" opacity="0.5"/><circle cx="4" cy="18" r="1.6" fill="currentColor" opacity="0.5"/><circle cx="20" cy="18" r="1.6" fill="currentColor" opacity="0.5"/><path d="M5.4 6.8L9.2 10.6 M18.6 6.8L14.8 10.6 M5.4 17.2L9.2 13.4 M18.6 17.2L14.8 13.4" stroke="currentColor" stroke-width="1" opacity="0.5"/></svg>';
    return el('div', { class: 'detail-empty' }, [
      mark,
      el('h3', {}, 'No selection'),
      el('p', {}, 'Click a node in the graph to view its details, identifiers, and connected edges.'),
      el('dl', { class: 'meta-grid' }, [
        el('dt', {}, 'Nodes'), el('dd', { id: 'stat-nodes' }, String(state.nodes.length)),
        el('dt', {}, 'Edges'), el('dd', { id: 'stat-edges' }, String(state.edges.length)),
        el('dt', {}, 'Strains'), el('dd', { id: 'stat-strains' }, String(new Set(state.nodes.filter(n => n.strain_id).map(n => n.strain_id)).size)),
        el('dt', {}, 'Modules'), el('dd', { id: 'stat-modules' }, String((() => { const s = new Set(); for (const n of state.nodes) for (const m of n.module_ids) s.add(m); return s.size; })())),
      ]),
      el('p', { class: 'muted' }, [
        'Schema: strain → module → mechanism → compound.',
      ]),
    ]);
  }

  // ----- Reset / clear -----
  function resetView() {
    if (state.zoomBehavior) {
      svgState.svg.transition().duration(500).call(state.zoomBehavior.transform, d3.zoomIdentity);
    }
    if (state.sim) {
      for (const n of state.nodes) { n.fx = null; n.fy = null; }
      state.sim.alpha(0.7).restart();
    }
  }

  function clearFilters() {
    state.filters.q = '';
    state.filters.strains.clear();
    state.filters.modules.clear();
    state.filters.tiers = new Set(['1', '2', '3', '4']);
    state.filters.types = new Set(NODE_TYPE_ORDER);
    $('#q-search').value = '';
    renderFilters();
    onFilterChange();
  }

  // ----- Filter change handler -----
  function onFilterChange() {
    const result = computeFiltered();
    applyVisibility(result);
    updateCounts(result);
  }

  // ----- Downloads -----
  function csvEscape(v) {
    if (v == null) return '';
    const s = String(v);
    if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  }

  function downloadFilteredCsv() {
    const { visibleNodes, visibleEdges } = computeFiltered();
    // Build node CSV using the original column order for compatibility
    const nodeCols = [
      'id','label','node_type','strain_id','module_id','entity_class','identifier','description','source_url',
      'kegg_gene_ids','ko_ids','ec_numbers','kegg_pathways','kegg_modules','ncbi_protein_ids','uniprot_ids',
      'pubchem_cid','kegg_compound','chebi_id','metacyc_candidate','metacyc_status','annotation_status'
    ];
    const edgeCols = [
      'edge_id','source_id','target_id','predicate','enzyme_or_system','strain_id','module_id',
      'evidence_tier','evidence_type','effect','source_url','notes'
    ];
    const nodesCsv = [nodeCols.join(',')]
      .concat(state.nodes.filter((n) => visibleNodes.has(n.id))
        .map((n) => nodeCols.map((c) => csvEscape(n[c])).join(',')))
      .join('\n');
    const edgesCsv = [edgeCols.join(',')]
      .concat(visibleEdges.map((e) => edgeCols.map((c) => {
        if (c === 'source_id') return csvEscape(e.source.id || e.source);
        if (c === 'target_id') return csvEscape(e.target.id || e.target);
        return csvEscape(e[c]);
      }).join(',')))
      .join('\n');

    triggerDownload('geotoxgraph_filtered_nodes.csv', nodesCsv, 'text/csv');
    setTimeout(() => triggerDownload('geotoxgraph_filtered_edges.csv', edgesCsv, 'text/csv'), 200);
  }

  function downloadFilteredJson() {
    const { visibleNodes, visibleEdges } = computeFiltered();
    const payload = {
      generated_at: new Date().toISOString(),
      filters: {
        search: state.filters.q,
        strains: [...state.filters.strains],
        modules: [...state.filters.modules],
        tiers: [...state.filters.tiers],
        node_types: [...state.filters.types],
      },
      nodes: state.nodes.filter((n) => visibleNodes.has(n.id)).map((n) => {
        const { _search, module_ids, ...clean } = n;
        return clean;
      }),
      edges: visibleEdges.map((e) => ({
        ...e,
        source_id: e.source.id || e.source,
        target_id: e.target.id || e.target,
        source: undefined,
        target: undefined,
        module_ids: undefined,
      })),
    };
    triggerDownload('geotoxgraph_filtered.json', JSON.stringify(payload, null, 2), 'application/json');
  }

  function triggerDownload(filename, content, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = el('a', { href: url, download: filename, style: 'display: none;' });
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 500);
  }

  function toggleFigureMode() {
    const on = !document.body.classList.contains('figure-mode');
    document.body.classList.toggle('figure-mode', on);
    $('#btn-figure-mode')?.setAttribute('aria-pressed', String(on));
    setTimeout(() => {
      if (!state.sim) return;
      const { width, height } = $('#graph-svg').getBoundingClientRect();
      state.sim.force('center', d3.forceCenter(width / 2, height / 2));
      state.sim.force('x', d3.forceX(width / 2).strength(0.04));
      state.sim.force('y', d3.forceY(height / 2).strength(0.04));
      state.sim.alpha(0.35).restart();
    }, 120);
  }

  function exportGraphSvg() {
    const svg = $('#graph-svg');
    if (!svg) return;
    const clone = svg.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    const { width, height } = svg.getBoundingClientRect();
    clone.setAttribute('width', String(Math.round(width)));
    clone.setAttribute('height', String(Math.round(height)));
    clone.setAttribute('viewBox', `0 0 ${Math.round(width)} ${Math.round(height)}`);
    const style = document.createElement('style');
    style.textContent = `
      .link{stroke-opacity:.55;fill:none}.node-label{font:11px sans-serif;paint-order:stroke;stroke:#fff;stroke-width:3px;stroke-linejoin:round}.body{stroke:#fff;stroke-width:1.5}
    `;
    clone.insertBefore(style, clone.firstChild);
    const xml = new XMLSerializer().serializeToString(clone);
    triggerDownload(`geotoxgraph-${state.layer}-figure.svg`, xml, 'image/svg+xml');
  }

  async function exportGraphPng() {
    const svg = $('#graph-svg');
    if (!svg) return;
    const { width, height } = svg.getBoundingClientRect();
    const clone = svg.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    clone.setAttribute('width', String(Math.round(width)));
    clone.setAttribute('height', String(Math.round(height)));
    clone.setAttribute('viewBox', `0 0 ${Math.round(width)} ${Math.round(height)}`);
    const xml = new XMLSerializer().serializeToString(clone);
    const blob = new Blob([xml], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.decoding = 'async';
    await new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = reject;
      img.src = url;
    }).catch(() => null);
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(width * 2));
    canvas.height = Math.max(1, Math.round(height * 2));
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = getComputedStyle(document.body).backgroundColor || '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    URL.revokeObjectURL(url);
    canvas.toBlob((png) => {
      if (!png) return;
      const pngUrl = URL.createObjectURL(png);
      const a = el('a', { href: pngUrl, download: `geotoxgraph-${state.layer}-figure.png`, style: 'display:none;' });
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { URL.revokeObjectURL(pngUrl); a.remove(); }, 500);
    }, 'image/png');
  }

  // ----- Theme toggle -----
  function setTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    $('#btn-theme').setAttribute('aria-pressed', String(t === 'dark'));
    // Re-render legend swatches and node fills (because CSS vars change)
    renderLegend();
    if (svgState.nodeSel) {
      svgState.nodeSel.select('circle.body').attr('fill', (d) => nodeColor(d));
      // Update arrow marker colors
      svgState.svg.selectAll('marker path').each(function () {
        const m = this.parentNode.id;
        const t = m.replace('arrow-t', '');
        d3.select(this).attr('fill', getComputedStyle(document.documentElement).getPropertyValue(`--t-${t}`).trim());
      });
    }
  }

  // ----- Initialize -----
  function bindUi() {
    const search = $('#q-search');
    let qTimer;
    search.addEventListener('input', () => {
      clearTimeout(qTimer);
      qTimer = setTimeout(() => {
        state.filters.q = search.value.trim().toLowerCase();
        onFilterChange();
      }, 80);
    });
    $('#graph-layer')?.addEventListener('change', async (ev) => {
      await switchLayer(ev.target.value);
    });
    $('#compound-compare')?.addEventListener('change', (ev) => {
      selectCompoundComparison(ev.target.value);
    });

    $('#btn-clear').addEventListener('click', clearFilters);
    $('#btn-reset').addEventListener('click', resetView);
    $('#btn-download-csv').addEventListener('click', downloadFilteredCsv);
    $('#btn-download-json').addEventListener('click', downloadFilteredJson);
    $('#btn-pin-node')?.addEventListener('click', pinSelectedNode);
    $('#btn-share-node')?.addEventListener('click', shareSelectedNode);
    $('#btn-figure-mode')?.addEventListener('click', toggleFigureMode);
    $('#btn-export-svg')?.addEventListener('click', exportGraphSvg);
    $('#btn-export-png')?.addEventListener('click', exportGraphPng);
    $('#btn-theme').addEventListener('click', () => {
      const cur = document.documentElement.getAttribute('data-theme');
      setTheme(cur === 'dark' ? 'light' : 'dark');
    });
    $('#btn-sheet-close')?.addEventListener('click', () => closeMobileSheet(true));
    $('#mobile-sheet-backdrop')?.addEventListener('click', () => closeMobileSheet(true));

    // Keyboard shortcuts
    document.addEventListener('keydown', (ev) => {
      if (ev.target.matches('input, textarea, select')) return;
      if (ev.key === '/') { ev.preventDefault(); search.focus(); }
      else if (ev.key === 'r' || ev.key === 'R') { resetView(); }
      else if (ev.key === 'Escape') { closeMobileSheet(true); selectNode(null); }
    });

    // Resize
    window.addEventListener('resize', () => {
      if (!state.sim) return;
      const { width, height } = $('#graph-svg').getBoundingClientRect();
      state.sim.force('center', d3.forceCenter(width / 2, height / 2));
      state.sim.force('x', d3.forceX(width / 2).strength(0.04));
      state.sim.force('y', d3.forceY(height / 2).strength(0.04));
      state.sim.alpha(0.3).restart();
    });

    // Initial system preference (no storage)
    const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
    if (prefersLight) setTheme('light');
  }

  function setRepoLink() {
    // Best-effort: derive from window.location if on github.io
    const a = $('#repo-link');
    const host = location.hostname;
    if (host.endsWith('github.io')) {
      const user = host.split('.')[0];
      const path = location.pathname.replace(/^\//, '').split('/')[0];
      if (user && path) {
        a.href = `https://github.com/${user}/${path}`;
      }
    }
  }

  async function renderActiveLayer({ restoreFromUrl = false } = {}) {
    const loading = $('#loading');
    if (loading) {
      loading.hidden = false;
      loading.textContent = `Loading ${LAYERS[state.layer].label}…`;
    }
    if (state.sim) state.sim.stop();
    state.selectedId = null;
    state.pinnedId = null;
    closeMobileSheet(false);
    if (svgState.root) svgState.root.selectAll('*').remove();
    try {
      await loadData();
    } catch (err) {
      console.error(err);
      if (loading) {
        loading.hidden = false;
        loading.textContent = 'Failed to load graph data. Open via a local web server (e.g. python -m http.server) — file:// blocks CSV fetch.';
      }
      return;
    }
    resetFiltersForLayer();
    if (loading) loading.hidden = true;
    renderFilters();
    renderLegend();
    buildSim();
    drawGraph();
    state.sim.alpha(1).restart();
    const r = computeFiltered();
    applyVisibility(r);
    updateCounts(r);
    renderDetail();
    const urlNode = restoreFromUrl ? getUrlNodeId() : null;
    if (urlNode && state.nodeIndex.has(urlNode)) {
      state.pinnedId = urlNode;
      setTimeout(() => {
        selectNode(urlNode);
        state.pinnedId = urlNode;
        renderShareControls('Shared node restored');
      }, 300);
    } else {
      renderShareControls();
    }
  }

  async function switchLayer(layerKey) {
    if (!LAYERS[layerKey]) return;
    state.layer = layerKey;
    const url = new URL(window.location.href);
    if (layerKey === 'geotox') url.searchParams.delete('layer');
    else url.searchParams.set('layer', layerKey);
    url.searchParams.delete('node');
    window.history.replaceState({}, '', url);
    const select = $('#graph-layer');
    if (select) select.value = layerKey;
    await renderActiveLayer({ restoreFromUrl: false });
  }

  async function init() {
    bindUi();
    setRepoLink();
    setupSvg();
    state.layer = getUrlLayer();
    const select = $('#graph-layer');
    if (select) select.value = state.layer;
    await renderActiveLayer({ restoreFromUrl: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
