import json
import re

with open('/tmp/prepared_fallback_nodes.json') as f:
    fallback_nodes = json.load(f)

fallback_js = json.dumps(fallback_nodes, indent=2)

with open('frontend/threat-map.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Ensure viewport CSS has clean light background by default and cyber dark mode when toggled
viewport_css = """/* Interactive Map Workspace */
.map-workspace-grid {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(54, 207, 255, 0.22);
}

.map-viewport-wrapper {
  position: relative;
  height: 720px;
  width: 100%;
  background: #eef2f6;
}

#threatMap {
  width: 100%;
  height: 100%;
  background: #eef2f6;
  font-family: inherit;
}

.cyber-dark-mode#threatMap,
.cyber-dark-mode #threatMap {
  background: #050a12 !important;
}

/* Ultra-smooth Leaflet zooming transitions */
.leaflet-zoom-animated {
  transition: transform 0.28s cubic-bezier(0.25, 0.1, 0.25, 1) !important;
}

.leaflet-tile {
  transition: opacity 0.25s linear, filter 0.3s ease !important;
}

/* Default standard light OSM cartography: crisp and clear */
.leaflet-tile-pane {
  filter: none;
}

/* Cyber Dark Mode: Converts pure OpenStreetMap tiles into a high-contrast cyber dark SOC map */
/* 100% standard OpenStreetMap, zero external API keys required, zero watermarks! */
.cyber-dark-mode .leaflet-tile-pane {
  filter: invert(1) hue-rotate(180deg) brightness(0.68) contrast(1.75) saturate(0.4) !important;
}"""

# Replace between .map-workspace-grid and .leaflet-control-attribution
vp_match = re.search(r'/\* Interactive Map Workspace \*/.*?/\* Custom Attribution Styling \*/', html, re.DOTALL)
if vp_match:
    html = html[:vp_match.start()] + viewport_css + "\n\n/* Custom Attribution Styling */" + html[vp_match.end() - len('/* Custom Attribution Styling */'):]
    print("[+] Viewport and base map CSS updated")

# 2. Update marker & popup CSS
markers_popups_css = """/* Custom Attacker Map Markers - High Contrast 38x38px */
.attacker-div-icon {
  background: transparent !important;
  border: none !important;
  z-index: 1000 !important;
}

.marker-pin-wrap {
  position: relative;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transform: translate(-19px, -19px);
  transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.5));
  z-index: 1000;
}

.marker-pin-wrap:hover {
  transform: translate(-19px, -19px) scale(1.28);
  z-index: 9999 !important;
}

.marker-pin-wrap.selected {
  transform: translate(-19px, -19px) scale(1.35);
  z-index: 10000 !important;
}

/* Glowing Pulsing Rings */
.marker-radar-ring {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 2px solid var(--marker-color, #e63946);
  opacity: 0.85;
  animation: radarWave 2s cubic-bezier(0.2, 0.8, 0.2, 1) infinite;
  pointer-events: none;
}

.marker-radar-ring.pulse-fast {
  animation-duration: 1.1s;
}

@keyframes radarWave {
  0% { transform: scale(0.6); opacity: 0.95; }
  100% { transform: scale(2.4); opacity: 0; }
}

.marker-core-badge {
  position: relative;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #0f1c30, #050b14);
  border: 2.5px solid var(--marker-color, #e63946);
  box-shadow: 0 0 10px var(--marker-color, #e63946), inset 0 0 6px rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  z-index: 2;
  transition: all 0.2s ease;
}

.marker-core-badge svg {
  width: 19px;
  height: 19px;
  fill: #ffffff;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.8));
}

.marker-status-dot {
  position: absolute;
  top: -1px;
  right: -1px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--marker-color, #e63946);
  border: 2px solid #ffffff;
  box-shadow: 0 0 6px var(--marker-color, #e63946);
  z-index: 3;
}

.marker-blocked-badge {
  position: absolute;
  bottom: -4px;
  right: -4px;
  background: #00c853;
  color: #fff;
  font-size: 8px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 4px;
  border: 1px solid #fff;
  letter-spacing: 0.3px;
  z-index: 4;
}

/* Custom Leaflet Tooltip */
.leaflet-tooltip.cyber-marker-tooltip {
  background: rgba(8, 16, 28, 0.94);
  border: 1px solid rgba(54, 207, 255, 0.35);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7);
  border-radius: 8px;
  padding: 8px 12px;
  color: var(--text);
  font-size: 11.5px;
  backdrop-filter: blur(8px);
}

.leaflet-tooltip-top:before {
  border-top-color: rgba(54, 207, 255, 0.35) !important;
}

/* Custom Leaflet Popup */
.cyber-marker-popup .leaflet-popup-content-wrapper {
  background: rgba(8, 16, 28, 0.96) !important;
  border: 1px solid rgba(54, 207, 255, 0.45) !important;
  border-radius: 10px !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.85) !important;
  backdrop-filter: blur(12px) !important;
  padding: 4px !important;
}

.cyber-marker-popup .leaflet-popup-tip {
  background: rgba(8, 16, 28, 0.96) !important;
  border: 1px solid rgba(54, 207, 255, 0.45) !important;
}

.cyber-marker-popup .leaflet-popup-close-button {
  color: var(--neon-cyan) !important;
  padding: 6px !important;
  font-size: 16px !important;
}

/* Marker Popup Card */
.marker-popup-card {
  padding: 8px 10px;
  min-width: 240px;
  max-width: 320px;
  font-family: var(--font-mono);
}

.marker-popup-card .popup-ip {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
  font-family: var(--font-heading);
}

.marker-popup-card .popup-sev {
  font-size: 9.5px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  font-family: var(--font-mono);
}

.marker-popup-card .popup-sev.CRITICAL {
  background: rgba(230, 57, 70, 0.2);
  color: #e63946;
  border: 1px solid rgba(230, 57, 70, 0.6);
}

.marker-popup-card .popup-sev.HIGH {
  background: rgba(255, 107, 53, 0.2);
  color: #ff6b35;
  border: 1px solid rgba(255, 107, 53, 0.6);
}

.marker-popup-card .popup-sev.MEDIUM {
  background: rgba(247, 127, 0, 0.2);
  color: #f77f00;
  border: 1px solid rgba(247, 127, 0, 0.6);
}

.marker-popup-card .popup-sev.LOW {
  background: rgba(0, 119, 182, 0.2);
  color: #0077b6;
  border: 1px solid rgba(0, 119, 182, 0.6);
}

.marker-popup-card .popup-loc {
  font-size: 11.5px;
  color: var(--neon-cyan);
  margin-bottom: 4px;
}

.marker-popup-card .popup-type {
  font-size: 11px;
  color: #9cb2c7;
  margin-bottom: 10px;
}

.marker-popup-card .popup-actions {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}

.marker-popup-card .popup-btn-case {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 7px 12px;
  background: linear-gradient(135deg, #0077b6, #0096c7);
  color: #ffffff !important;
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: 12px;
  border-radius: 6px;
  text-decoration: none;
  box-shadow: 0 4px 12px rgba(0, 119, 182, 0.4);
  transition: all 0.2s ease;
}

.marker-popup-card .popup-btn-case:hover {
  background: linear-gradient(135deg, #0096c7, #48cae4);
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(0, 119, 182, 0.6);
  color: #ffffff !important;
}

/* Drawer Case Banner & Chips */
.drawer-case-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 14px;
  background: linear-gradient(135deg, rgba(0, 119, 182, 0.35), rgba(54, 207, 255, 0.25));
  border: 1px solid var(--neon-cyan);
  border-radius: 8px;
  color: #ffffff !important;
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: 12.5px;
  text-decoration: none;
  box-shadow: 0 4px 16px rgba(54, 207, 255, 0.2);
  transition: all 0.2s ease;
}

.drawer-case-banner:hover {
  background: linear-gradient(135deg, rgba(0, 150, 199, 0.5), rgba(54, 207, 255, 0.4));
  border-color: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(54, 207, 255, 0.35);
  color: #ffffff !important;
}

.case-chip {
  background: rgba(54, 207, 255, 0.12);
  color: var(--neon-cyan) !important;
  border: 1px solid rgba(54, 207, 255, 0.35);
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 5px;
  text-decoration: none;
  font-family: var(--font-mono);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.18s ease;
}

.case-chip:hover {
  background: rgba(54, 207, 255, 0.25);
  border-color: var(--neon-cyan);
  color: #fff !important;
  transform: translateY(-1px);
}

.tt-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 4px;
  font-family: var(--font-mono);
  font-weight: 700;
  color: #fff;
}

.tt-type {
  font-size: 10px;
  font-weight: 600;
  color: var(--neon-cyan);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tt-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 11px;
  color: var(--muted);
}

.tt-row b {
  color: #eaf4ff;
}"""

mk_match = re.search(r'/\* Custom Attacker Map Markers.*?\*/.*?/\* Floating Threat Symbol Legend HUD \*/', html, re.DOTALL)
if mk_match:
    html = html[:mk_match.start()] + markers_popups_css + "\n\n/* Floating Threat Symbol Legend HUD */" + html[mk_match.end() - len('/* Floating Threat Symbol Legend HUD */'):]
    print("[+] Markers and popups CSS updated")

# 3. Ensure Layer switch button and default map HTML
html = html.replace('<div id="threatMap" class="cyber-dark-mode"></div>', '<div id="threatMap"></div>')

# 4. Ensure drawer has primary case banner
if '<a id="drawerPrimaryCaseBtn"' not in html:
    old_db = '<div class="drawer-body">\n          <!-- Status & Badges -->'
    new_db = """<div class="drawer-body">
          <!-- Prominent Primary Investigation Case Banner -->
          <a id="drawerPrimaryCaseBtn" href="investigation-workspace.html?case_id=1" class="drawer-case-banner">
            📂 Open Investigation Case CS-1024 &rarr;
          </a>

          <!-- Status & Badges -->"""
    html = html.replace(old_db, new_db)
    print("[+] Added drawerPrimaryCaseBtn to drawer")

# 5. Update JavaScript from const FALLBACK_ATTACKERS down to end of script
js_code = f"""// Static Standalone Fallback Dataset (Exact 26 database nodes from backend/cyberscope.db)
// Strictly authentic Indian cybercrime infrastructure nodes with verified postal codes.
// PRIVACY GUARANTEE: Attacker infrastructure only; zero victim IPs or victim personal records.
const FALLBACK_ATTACKERS = {fallback_js};

// In-memory blocked IPs set (initialized with known blocked nodes)
const localBlockedIps = new Set(["115.110.201.78", "183.82.112.55", "117.211.90.130", "117.240.18.99", "117.200.78.212"]);

// Color mapping for severities - High contrast vibrant pins
const SEVERITY_COLORS = {{
  CRITICAL: "#e63946",
  HIGH: "#ff6b35",
  MEDIUM: "#f77f00",
  LOW: "#0077b6"
}};

// Case ID Mapping Helper: Deterministic mapping of case numbers to integer case IDs
function getCaseId(caseNumber) {{
  if (!caseNumber) return 1;
  const s = String(caseNumber).trim();
  const KNOWN_MAP = {{
    'CS-1024': 1, 'CS-1025': 2, 'CS-1026': 3, 'CS-1027': 4,
    'CS-1028': 5, 'CS-1029': 6, 'CS-1030': 7, 'CS-1031': 8,
    'CS-1032': 9, 'CS-1033': 10, 'CS-1034': 11, 'CS-1035': 12
  }};
  if (KNOWN_MAP[s]) return KNOWN_MAP[s];
  if (s.startsWith('CS-')) {{
    const num = parseInt(s.replace('CS-', ''), 10);
    if (!isNaN(num)) return Math.max(1, num - 1023);
  }}
  if (/^\\d+$/.test(s)) return parseInt(s, 10);
  return 1;
}}

// SVG Icon definitions for 7 threat categories
const CATEGORY_SVGS = {{
  DDOS_BOTNET: '<svg viewBox="0 0 24 24"><path d="M13 2L3 14h7v8l11-13h-8l3-7z"/></svg>',
  PHISHING_HOST: '<svg viewBox="0 0 24 24"><path d="M18 2a3 3 0 0 0-3 3c0 .35.07.69.18 1L11.5 9.68A4.98 4.98 0 0 0 8 8C5.24 8 3 10.24 3 13c0 2.45 1.76 4.49 4.08 4.92l-1.79 1.79a1 1 0 1 0 1.42 1.42l3-3a1 1 0 0 0 0-1.42l-1.3-1.3C9.4 14.86 10 13.99 10 13a3 3 0 0 0-1.05-2.28L12.63 7c.43.6 1.13 1 1.92 1a2.45 2.45 0 0 0 2.45-2.45A2.45 2.45 0 0 0 14.55 3.1 3 3 0 0 0 18 2z"/></svg>',
  UPI_MULE_VECTOR: '<svg viewBox="0 0 24 24"><path d="M20 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2zM6 15h3v2H6v-2zm5 0h7v2h-7v-2z"/></svg>',
  SIM_BOX_RELAY: '<svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 0 0-7.07 17.07l1.41-1.41A8 8 0 1 1 12 20a7.96 7.96 0 0 1-5.66-2.34l-1.41 1.41A10 10 0 1 0 12 2zm0 4a6 6 0 0 0-4.24 10.24l1.41-1.41A4 4 0 1 1 12 16a3.98 3.98 0 0 1-2.83-1.17l-1.41 1.41A6 6 0 1 0 12 6zm0 4a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-1 8h2v4h-2v-4z"/></svg>',
  FAKE_KYC_GATEWAY: '<svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-1 6h2v6h-2V7zm0 8h2v2h-2v-2z"/></svg>',
  BRUTE_FORCE_STUFFER: '<svg viewBox="0 0 24 24"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zM9 6c0-1.66 1.34-3 3-3s3 1.34 3 3v2H9V6zm3 10.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm6 3.5H6V10h12v10z"/></svg>',
  MALWARE_C2: '<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12c0 3.84 2.16 7.18 5.34 8.87.27-.72.64-1.39 1.1-2C6.41 17.58 5 15.02 5 12c0-3.87 3.13-7 7-7s7 3.13 7 7c0 3.02-1.41 5.58-3.44 6.87.46.61.83 1.28 1.1 2C19.84 19.18 22 15.84 22 12c0-5.52-4.48-10-10-10zm-3 8a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3zm6 0a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3zm-6.5 5.5h7c-.5 1.79-2.02 3-3.5 3s-3-1.21-3.5-3z"/></svg>'
}};

// Global State
let map = null;
let currentLayerMode = 'standard'; // Default is Clean Light OpenStreetMap Standard
let osmStandardTileLayer = null;
let osmHotTileLayer = null;
let markersLayerGroup = null;
let allAttackers = [];
let activeFilteredAttackers = [];
let selectedAttacker = null;
let selectedMarkerElement = null;
let soundEnabled = false;
let audioCtx = null;
let streamPaused = false;
let streamInterval = null;
let legendActiveCategory = null;

// Audio Radar Synthesizer (Web Audio API)
function playRadarAudio(severity) {{
  if (!soundEnabled) return;
  try {{
    if (!audioCtx) {{
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }}
    if (audioCtx.state === 'suspended') {{
      audioCtx.resume();
    }}
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    let baseFreq = 580;
    if (severity === 'CRITICAL') baseFreq = 960;
    else if (severity === 'HIGH') baseFreq = 800;
    else if (severity === 'MEDIUM') baseFreq = 640;

    osc.type = 'sine';
    osc.frequency.setValueAtTime(baseFreq, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(baseFreq * 0.65, audioCtx.currentTime + 0.14);

    gain.gain.setValueAtTime(0.09, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.16);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + 0.16);
  }} catch (e) {{
    console.warn('Web Audio ping error:', e);
  }}
}}

function toggleRadarSound() {{
  soundEnabled = !soundEnabled;
  const icon = document.getElementById('soundIcon');
  const txt = document.getElementById('soundStatusText');
  const btn = document.getElementById('radarSoundBtn');

  if (soundEnabled) {{
    icon.textContent = '🔊';
    txt.textContent = 'ON';
    btn.classList.add('active');
    playRadarAudio('HIGH');
    showToast('Acoustic radar enabled: monitoring attacker telemetry');
  }} else {{
    icon.textContent = '🔇';
    txt.textContent = 'OFF';
    btn.classList.remove('active');
    showToast('Acoustic radar muted');
  }}
}}

// Map Initialization
function initThreatMap() {{
  // Strict India Bounds
  const indiaBounds = [
    [6.5, 68.0],   // Southwest corner (Kanyakumari / Lakshadweep / Gujarat)
    [37.5, 97.5]   // Northeast corner (Kashmir / Arunachal Pradesh)
  ];

  // Leaflet map instance with buttery-smooth zoom configuration
  map = L.map('threatMap', {{
    center: [22.5937, 78.9629],
    zoom: 5,
    minZoom: 4,
    maxZoom: 18,
    maxBounds: indiaBounds,
    maxBoundsViscosity: 1.0,  // Prevents dragging outside India
    zoomSnap: 0.25,           // Fluid fractional zooming
    zoomDelta: 0.5,           // Gentle step
    wheelPxPerZoomLevel: 120, // Butter-smooth mouse wheel
    wheelDebounceTime: 40,
    zoomAnimation: true,
    fadeAnimation: true,
    markerZoomAnimation: true,
    attributionControl: true
  }});

  // 100% Standard OpenStreetMap - Zero external API keys, zero watermarks
  osmStandardTileLayer = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
    maxZoom: 19
  }});

  // OSM Humanitarian Layer (HOT) - 100% OpenStreetMap community cartography
  osmHotTileLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.fr/hot/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors &copy; <a href="https://www.hotosm.org/" target="_blank">HOT</a>',
    subdomains: 'abc',
    maxZoom: 19
  }});

  // Add default base layer (Clean Light OpenStreetMap Standard)
  osmStandardTileLayer.addTo(map);

  markersLayerGroup = L.layerGroup().addTo(map);

  // Map click closes drawer if clicking empty space
  map.on('click', function(e) {{
    if (e.originalEvent && e.originalEvent.target && e.originalEvent.target.closest('.attacker-div-icon')) {{
      return;
    }}
    closeDrawer();
  }});

  // Render markers IMMEDIATELY in 0 milliseconds so points are guaranteed visible without waiting for network
  allAttackers = [...FALLBACK_ATTACKERS];
  activeFilteredAttackers = [...allAttackers];
  renderMarkers(activeFilteredAttackers);

  // Invalidate size immediately and after 100ms timeout to ensure Leaflet renders all panes and tiles correctly
  map.invalidateSize();
  setTimeout(() => {{
    if (map) map.invalidateSize();
  }}, 100);
}}

// Layer Switcher - Toggles between Standard Light (OSM), Cyber Dark (OSM), and OSM Humanitarian
function toggleMapLayer() {{
  const container = document.getElementById('threatMap');
  const btnText = document.getElementById('layerText');
  const btnIcon = document.getElementById('layerIcon');

  if (currentLayerMode === 'standard') {{
    // Switch to Cyber Dark (OSM with CSS filter)
    currentLayerMode = 'dark';
    if (map.hasLayer(osmHotTileLayer)) map.removeLayer(osmHotTileLayer);
    if (!map.hasLayer(osmStandardTileLayer)) osmStandardTileLayer.addTo(map);
    container.classList.add('cyber-dark-mode');
    btnText.textContent = 'Cyber Dark (OSM)';
    btnIcon.textContent = '🛰️';
    showToast('Switched to Cyber Dark Mode (OSM Inverse SOC Matrix)');
  }} else if (currentLayerMode === 'dark') {{
    // Switch to OSM Humanitarian
    currentLayerMode = 'hot';
    container.classList.remove('cyber-dark-mode');
    if (map.hasLayer(osmStandardTileLayer)) map.removeLayer(osmStandardTileLayer);
    osmHotTileLayer.addTo(map);
    btnText.textContent = 'OSM Humanitarian';
    btnIcon.textContent = '🌍';
    showToast('Switched to OSM Humanitarian Cartography');
  }} else {{
    // Switch back to Standard Light OSM (clear CSS filter)
    currentLayerMode = 'standard';
    container.classList.remove('cyber-dark-mode');
    if (map.hasLayer(osmHotTileLayer)) map.removeLayer(osmHotTileLayer);
    if (!map.hasLayer(osmStandardTileLayer)) osmStandardTileLayer.addTo(map);
    btnText.textContent = 'Standard Light (OSM)';
    btnIcon.textContent = '🗺️';
    showToast('Switched to OpenStreetMap Standard Light Cartography (Clean)');
  }}
}}

// Reset View Strictly to India
function resetIndiaView() {{
  if (!map) return;
  map.flyTo([22.5937, 78.9629], 5, {{
    duration: 1.1,
    easeLinearity: 0.25
  }});
  showToast('Centered on National Cyber Defense Perimeter (India)');
}}

// Marker Creation - High Contrast 38x38px with Interactive Popup
function createAttackerMarker(node) {{
  const color = SEVERITY_COLORS[node.severity] || SEVERITY_COLORS.MEDIUM;
  const svg = CATEGORY_SVGS[node.attack_type] || CATEGORY_SVGS.DDOS_BOTNET;
  const isBlocked = localBlockedIps.has(node.ip);
  const pulseSpeed = node.severity === 'CRITICAL' ? 'pulse-fast' : '';

  const primaryCaseNumber = node.primary_case_number || (node.linked_cases && node.linked_cases[0]) || 'CS-1024';
  const primaryCaseId = node.primary_case_id || getCaseId(primaryCaseNumber);

  const iconHtml = `
    <div class="marker-pin-wrap" id="marker-${{node.id}}" style="--marker-color:${{color}};" onclick="handleMarkerClick('${{node.id}}', event)">
      <div class="marker-radar-ring ${{pulseSpeed}}"></div>
      <div class="marker-core-badge">
        ${{svg}}
      </div>
      <div class="marker-status-dot" style="background:${{color}};"></div>
      ${{isBlocked ? '<div class="marker-blocked-badge" title="Perimeter Blocked">BLOCKED</div>' : ''}}
    </div>
  `;

  const customIcon = L.divIcon({{
    className: 'attacker-div-icon',
    html: iconHtml,
    iconSize: [38, 38],
    iconAnchor: [0, 0]
  }});

  const marker = L.marker([node.lat, node.lng], {{
    icon: customIcon,
    title: `${{node.ip}} · ${{node.city}}`,
    riseOnHover: true,
    zIndexOffset: 1000
  }});

  // Sleek cyber tooltip
  const tooltipContent = `
    <div class="tt-header">
      <span style="color:#fff;">${{node.ip}}</span>
      <span class="sev-badge ${{node.severity}}" style="font-size:9px; padding:1px 5px;">${{node.severity}}</span>
    </div>
    <div class="tt-type">${{(node.attack_type || '').replace(/_/g, ' ')}}</div>
    <div class="tt-row"><span>Location:</span><b>${{node.city}}, ${{node.state}}</b></div>
    <div class="tt-row"><span>Risk Score:</span><b style="color:${{color}};">${{node.risk_score}} / 100</b></div>
    <div class="tt-row"><span>ISP:</span><b>${{node.isp}}</b></div>
    ${{isBlocked ? '<div style="margin-top:4px; font-size:10px; color:#5dffb1; font-weight:700;">🛡️ BLOCKED AT EDGE</div>' : ''}}
  `;

  marker.bindTooltip(tooltipContent, {{
    className: 'cyber-marker-tooltip',
    direction: 'top',
    offset: [0, -20],
    opacity: 0.98
  }});

  // Interactive Leaflet Popup card with direct case investigation link
  const popupHtml = `
    <div class="marker-popup-card">
      <div class="popup-ip">${{node.ip}} <span class="popup-sev ${{node.severity}}">${{node.severity}}</span></div>
      <div class="popup-loc">📍 ${{node.city}}, ${{node.state}} (PIN: ${{node.pincode}})</div>
      <div class="popup-type">${{(node.attack_type || '').replace(/_/g, ' ')}} · ${{node.campaign}}</div>
      <div class="popup-actions">
        <a href="investigation-workspace.html?case_id=${{encodeURIComponent(primaryCaseId)}}" class="popup-btn-case" onclick="event.stopPropagation()">
          📂 Open Case ${{primaryCaseNumber}} →
        </a>
      </div>
    </div>
  `;

  marker.bindPopup(popupHtml, {{
    className: 'cyber-marker-popup',
    offset: [0, -18],
    closeButton: true,
    autoPan: true
  }});

  marker.on('click', function(e) {{
    L.DomEvent.stopPropagation(e);
    openAttackerDrawer(node);
    marker.openPopup();
  }});

  // Double-clicking directly redirects to the case workspace
  marker.on('dblclick', function(e) {{
    L.DomEvent.stopPropagation(e);
    window.location.href = `investigation-workspace.html?case_id=${{encodeURIComponent(primaryCaseId)}}`;
  }});

  return marker;
}}

// Render Markers
function renderMarkers(nodes) {{
  if (!markersLayerGroup) return;
  markersLayerGroup.clearLayers();

  nodes.forEach(node => {{
    const marker = createAttackerMarker(node);
    markersLayerGroup.addLayer(marker);
  }});
}}

// Marker Selection & Drawer
function handleMarkerClick(nodeId, e) {{
  if (e) e.stopPropagation();
  const node = allAttackers.find(n => String(n.id) === String(nodeId) || n.ip === String(nodeId));
  if (node) {{
    openAttackerDrawer(node);
  }}
}}

function openAttackerDrawer(node) {{
  selectedAttacker = node;
  playRadarAudio(node.severity);

  const primaryCaseNumber = node.primary_case_number || (node.linked_cases && node.linked_cases[0]) || 'CS-1024';
  const primaryCaseId = node.primary_case_id || getCaseId(primaryCaseNumber);

  // Update Drawer Primary Case Banner
  const bannerBtn = document.getElementById('drawerPrimaryCaseBtn');
  if (bannerBtn) {{
    bannerBtn.href = `investigation-workspace.html?case_id=${{encodeURIComponent(primaryCaseId)}}`;
    bannerBtn.innerHTML = `📂 Open Investigation Case ${{primaryCaseNumber}} &rarr;`;
    bannerBtn.title = `Investigate Case ${{primaryCaseNumber}} (ID: ${{primaryCaseId}}) in Investigation Workspace`;
  }}

  // Update Drawer UI
  document.getElementById('drawerIp').textContent = node.ip;
  document.getElementById('drawerHostname').textContent = node.hostname || 'unknown-host';

  const sevBadge = document.getElementById('drawerSeverityBadge');
  sevBadge.className = `sev-badge ${{node.severity}}`;
  sevBadge.textContent = node.severity;

  const typeBadge = document.getElementById('drawerTypeBadge');
  typeBadge.textContent = node.attack_type;

  const isBlocked = localBlockedIps.has(node.ip);
  const statusBadge = document.getElementById('drawerStatusBadge');
  const blockBtn = document.getElementById('drawerBlockBtn');
  const blockText = document.getElementById('drawerBlockText');
  const blockIcon = document.getElementById('drawerBlockIcon');

  if (isBlocked) {{
    statusBadge.className = 'status-badge-live blocked-threat';
    statusBadge.textContent = '🛡️ BLOCKED AT EDGE';
    blockBtn.className = 'block-toggle-btn blocked';
    blockText.textContent = 'Withdraw Firewall Block';
    blockIcon.textContent = '✓';
  }} else {{
    statusBadge.className = 'status-badge-live active-threat';
    statusBadge.textContent = '● ACTIVE MALICIOUS HIT';
    blockBtn.className = 'block-toggle-btn';
    blockText.textContent = 'Deploy Firewall IP Block';
    blockIcon.textContent = '🛡️';
  }}

  // Risk Score Gauge
  const gauge = document.getElementById('drawerGauge');
  gauge.style.setProperty('--gauge-pct', node.risk_score);
  const scoreColor = SEVERITY_COLORS[node.severity] || '#ff3366';
  gauge.style.setProperty('--gauge-color', scoreColor);
  document.getElementById('drawerScoreVal').textContent = node.risk_score;

  const riskLevelEl = document.getElementById('drawerRiskLevel');
  const riskSummaryEl = document.getElementById('drawerRiskSummary');
  if (node.risk_score >= 85) {{
    riskLevelEl.textContent = 'CRITICAL SYSTEM THREAT';
    riskSummaryEl.textContent = 'High-velocity hostile vector requiring immediate BGP null-route and bank gateway freeze.';
  }} else if (node.risk_score >= 65) {{
    riskLevelEl.textContent = 'HIGH SEVERITY ATTACKER';
    riskSummaryEl.textContent = 'Active phishing or mule vector attempting credentials drain and OTP evasion.';
  }} else {{
    riskLevelEl.textContent = 'ELEVATED RECONNAISSANCE THREAT';
    riskSummaryEl.textContent = 'Credential stuffer or vulnerability probe scanning perimeter gateways.';
  }}

  // Geolocation & Network
  document.getElementById('drawerCity').textContent = `${{node.city}}, ${{node.state}}`;
  document.getElementById('drawerPincode').textContent = node.pincode || 'N/A';
  document.getElementById('drawerCoords').textContent = `${{node.lat.toFixed(4)}}, ${{node.lng.toFixed(4)}}`;
  document.getElementById('drawerAsn').textContent = node.asn || 'AS-UNASSIGNED';
  document.getElementById('drawerIsp').textContent = node.isp || 'Telecom Entity';

  // Campaign & Cases
  const campaignLink = document.getElementById('drawerCampaignLink');
  campaignLink.textContent = `${{node.campaign}} →`;
  campaignLink.href = `campaign-explorer.html?campaign=${{encodeURIComponent(node.campaign)}}`;

  const casesContainer = document.getElementById('drawerCasesList');
  casesContainer.innerHTML = '';
  const linkedList = node.linked_cases || node.linked_case_numbers || [primaryCaseNumber];
  linkedList.forEach(cNum => {{
    const cId = getCaseId(cNum);
    const a = document.createElement('a');
    a.href = `investigation-workspace.html?case_id=${{encodeURIComponent(cId)}}`;
    a.className = 'case-chip';
    a.innerHTML = `📂 ${{cNum}}`;
    a.title = `Investigate Case ${{cNum}} in Workspace (ID: ${{cId}})`;
    casesContainer.appendChild(a);
  }});

  // Intercepted Malicious Request Sample
  const reqSample = node.request_sample || {{}};
  document.getElementById('drawerMethod').textContent = reqSample.method || 'POST';
  document.getElementById('drawerPath').textContent = reqSample.path || '/api/endpoint';
  document.getElementById('drawerHeaders').textContent = typeof reqSample.headers === 'string'
    ? reqSample.headers
    : JSON.stringify(reqSample.headers, null, 2) || 'N/A';
  document.getElementById('drawerPayload').textContent = typeof reqSample.payload === 'string'
    ? reqSample.payload
    : JSON.stringify(reqSample.payload, null, 2) || 'N/A';

  // Defense & Tactics
  document.getElementById('drawerTactics').textContent = node.tactics || 'Hostile traffic signature detected.';
  document.getElementById('drawerRec').textContent = `RECOMMENDED ACTION: ${{node.defense_recommendation || 'Block at edge firewall'}}`;

  // Timestamps
  document.getElementById('drawerFirstSeen').textContent = node.first_seen || '2026-09-20';
  document.getElementById('drawerLastActive').textContent = node.last_active || 'Just now';
  document.getElementById('drawerTotalRequests').textContent = Number(node.total_requests || 0).toLocaleString();

  // Slide Drawer Open
  document.getElementById('attackerDrawer').classList.add('open');

  // Smoothly pan map slightly to the left so drawer doesn't obstruct marker
  const targetLatLng = [node.lat, node.lng];
  map.panTo(targetLatLng, {{ animate: true, duration: 0.6 }});
}}

function closeDrawer() {{
  document.getElementById('attackerDrawer').classList.remove('open');
  selectedAttacker = null;
}}

function copyDrawerIp() {{
  if (!selectedAttacker) return;
  navigator.clipboard.writeText(selectedAttacker.ip).then(() => {{
    showToast(`IP ${{selectedAttacker.ip}} copied to clipboard`);
  }}).catch(() => {{
    showToast(`Copied: ${{selectedAttacker.ip}}`);
  }});
}}

// Toggle Firewall Block on Selected Attacker
async function toggleBlockSelectedAttacker() {{
  if (!selectedAttacker) return;
  const ip = selectedAttacker.ip;
  const isCurrentlyBlocked = localBlockedIps.has(ip);
  const newAction = isCurrentlyBlocked ? 'unblock' : 'block';

  // Optimistic local state update
  if (isCurrentlyBlocked) {{
    localBlockedIps.delete(ip);
    showToast(`[FIREWALL UPDATED] IP ${{ip}} removed from edge blocklist`, 'toast-unblocked');
  }} else {{
    localBlockedIps.add(ip);
    showToast(`[FIREWALL RULE ENFORCED] IP ${{ip}} null-routed across all gateways`, 'toast-blocked');
    playRadarAudio('CRITICAL');
  }}

  // Update Stats Strip
  document.getElementById('statBlocked').textContent = localBlockedIps.size;

  // Re-render markers to update blocked shield badge
  renderMarkers(activeFilteredAttackers);

  // Update Drawer UI
  openAttackerDrawer(selectedAttacker);

  // Synchronize with Backend API if online
  try {{
    const authHeaders = (window.CyberScopeAuth && typeof window.CyberScopeAuth.getAuthHeaders === 'function')
      ? window.CyberScopeAuth.getAuthHeaders()
      : {{}};
    authHeaders['Content-Type'] = 'application/json';

    await fetch('/api/threat-map/block', {{
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({{
        ip: ip,
        action: newAction,
        reason: 'Investigator action deployed from CyberScope Live Threat Map'
      }})
    }});
  }} catch (e) {{
    console.info('Backend block API offline, local state enforced.');
  }}
}}

// Filter and Search Logic
function applyAllFilters() {{
  const searchTerm = document.getElementById('mapSearchInput').value.trim().toLowerCase();
  const categoryFilter = document.getElementById('filterCategory').value;
  const severityFilter = document.getElementById('filterSeverity').value;
  const stateFilter = document.getElementById('filterState').value;

  activeFilteredAttackers = allAttackers.filter(node => {{
    // Search
    if (searchTerm) {{
      const matchIp = node.ip.toLowerCase().includes(searchTerm);
      const matchCity = node.city.toLowerCase().includes(searchTerm);
      const matchState = node.state.toLowerCase().includes(searchTerm);
      const matchPincode = (node.pincode || '').toLowerCase().includes(searchTerm);
      const matchAsn = (node.asn || '').toLowerCase().includes(searchTerm);
      const matchIsp = (node.isp || '').toLowerCase().includes(searchTerm);
      const matchCampaign = (node.campaign || '').toLowerCase().includes(searchTerm);
      if (!matchIp && !matchCity && !matchState && !matchPincode && !matchAsn && !matchIsp && !matchCampaign) {{
        return false;
      }}
    }}

    // Category
    if (categoryFilter && categoryFilter !== 'ALL') {{
      if (node.attack_type !== categoryFilter) return false;
    }}

    // Severity
    if (severityFilter && severityFilter !== 'ALL') {{
      if (node.severity !== severityFilter) return false;
    }}

    // State
    if (stateFilter && stateFilter !== 'ALL') {{
      if (!node.state.toLowerCase().includes(stateFilter.toLowerCase())) return false;
    }}

    return true;
  }});

  renderMarkers(activeFilteredAttackers);
  document.getElementById('statTotalAttackers').textContent = activeFilteredAttackers.length;

  if (activeFilteredAttackers.length === 0) {{
    showToast('No attacker nodes matching current filter criteria');
  }}
}}

function clearSearch() {{
  document.getElementById('mapSearchInput').value = '';
  applyAllFilters();
}}

function filterByLegend(category) {{
  const select = document.getElementById('filterCategory');
  if (legendActiveCategory === category) {{
    // Deselect
    legendActiveCategory = null;
    select.value = 'ALL';
    document.querySelectorAll('.legend-item').forEach(el => el.classList.remove('active'));
    showToast('Legend filter cleared: viewing all threat nodes');
  }} else {{
    legendActiveCategory = category;
    select.value = category;
    document.querySelectorAll('.legend-item').forEach(el => {{
      el.classList.toggle('active', el.dataset.category === category);
    }});
    showToast(`Filtering map by ${{category.replace(/_/g, ' ')}}`);
  }}
  applyAllFilters();
}}

function filterBySeverity(sev) {{
  const select = document.getElementById('filterSeverity');
  select.value = sev;
  applyAllFilters();
  showToast(`Filtering threat perimeter by severity: ${{sev}}`);
}}

function toggleLegendPanel() {{
  const legend = document.getElementById('hudLegend');
  const btn = document.getElementById('legendCollapseBtn');
  const isCollapsed = legend.classList.toggle('collapsed');
  btn.textContent = isCollapsed ? '▲' : '▼';
}}

// Live Simulation Stream (Realistic Cyber Defense Activity)
function initLiveStream() {{
  const streamEl = document.getElementById('liveStreamList');
  if (!streamEl) return;

  const CITIES = ['Jamtara', 'Nuh', 'Bharatpur', 'Gurugram', 'Kolkata', 'Surat', 'Bengaluru', 'Mumbai', 'Hyderabad', 'Patna', 'Pune', 'Jaipur', 'Alwar', 'Deoghar', 'Asansol', 'Delhi'];
  const TYPES = ['PHISHING_HOST', 'SIM_BOX_RELAY', 'UPI_MULE_VECTOR', 'MALWARE_C2', 'FAKE_KYC_GATEWAY'];

  streamInterval = setInterval(() => {{
    if (streamPaused) return;

    const city = CITIES[Math.floor(Math.random() * CITIES.length)];
    const type = TYPES[Math.floor(Math.random() * TYPES.length)];
    const node = allAttackers.find(n => n.city.includes(city) && n.attack_type === type) || allAttackers[Math.floor(Math.random() * allAttackers.length)];
    if (!node) return;

    const row = document.createElement('div');
    row.className = 'stream-row';
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];

    row.innerHTML = `
      <div class="stream-time">${{timeStr}}</div>
      <div class="stream-ip" onclick="handleMarkerClick('${{node.id}}')">${{node.ip}}</div>
      <div class="stream-type">${{node.attack_type.replace(/_/g, ' ')}}</div>
      <div class="stream-loc">${{node.city}}, ${{node.state}}</div>
      <div class="stream-sev"><span class="sev-badge ${{node.severity}}" style="font-size:9px; padding:1px 5px;">${{node.severity}}</span></div>
    `;

    streamEl.insertBefore(row, streamEl.firstChild);
    while (streamEl.children.length > 30) {{
      streamEl.removeChild(streamEl.lastChild);
    }}
  }}, 2400);
}}

function toggleStreamPause() {{
  streamPaused = !streamPaused;
  const btn = document.getElementById('streamPauseBtn');
  if (streamPaused) {{
    btn.textContent = '▶ Resume Feed';
    showToast('Telemetry stream paused');
  }} else {{
    btn.textContent = '⏸ Pause Feed';
    showToast('Telemetry stream resumed');
  }}
}}

// Toast Feedback Notification
let toastTimeout = null;
function showToast(msg, extraClass = '') {{
  const toast = document.getElementById('cyberToast');
  const msgEl = document.getElementById('toastMsg');
  msgEl.textContent = msg;
  toast.className = `cyber-toast show ${{extraClass}}`;
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {{
    toast.className = 'cyber-toast';
  }}, 3200);
}}

// Data Fetch & Hydration
async function loadThreatMapData() {{
  // If attackers array not populated, use FALLBACK_ATTACKERS
  if (!allAttackers || allAttackers.length === 0) {{
    allAttackers = [...FALLBACK_ATTACKERS];
    activeFilteredAttackers = [...allAttackers];
    renderMarkers(activeFilteredAttackers);
  }}

  // Try fetching from backend API if available
  try {{
    const authHeaders = (window.CyberScopeAuth && typeof window.CyberScopeAuth.getAuthHeaders === 'function')
      ? window.CyberScopeAuth.getAuthHeaders()
      : {{}};

    const [attackersRes, statsRes] = await Promise.all([
      fetch('/api/threat-map/attackers', {{ headers: authHeaders }}),
      fetch('/api/threat-map/stats', {{ headers: authHeaders }})
    ]);

    if (attackersRes.ok) {{
      const data = await attackersRes.json();
      if (Array.isArray(data) && data.length > 0) {{
        allAttackers = data;
      }} else if (Array.isArray(data.attackers) && data.attackers.length > 0) {{
        allAttackers = data.attackers;
      }}
    }}

    if (statsRes.ok) {{
      const stats = await statsRes.json();
      if (stats.blocked_ips && Array.isArray(stats.blocked_ips)) {{
        stats.blocked_ips.forEach(ip => localBlockedIps.add(ip));
      }}
      if (stats.total_attackers) {{
        document.getElementById('statTotalAttackers').textContent = stats.total_attackers;
      }}
      if (stats.critical_threats) {{
        document.getElementById('statCritical').textContent = stats.critical_threats;
      }}
      if (stats.active_attacks_per_min) {{
        document.getElementById('statVelocity').textContent = stats.active_attacks_per_min.toLocaleString();
      }}
    }}
  }} catch (err) {{
    console.info('Backend threat-map API offline, running in embedded SOC telemetry mode.');
  }}

  // Normalize attacker node fields for consistent UI representation
  allAttackers = allAttackers.map((node, idx) => {{
    const lat = Number(node.lat != null ? node.lat : (node.latitude != null ? node.latitude : 22.5937));
    const lng = Number(node.lng != null ? node.lng : (node.longitude != null ? node.longitude : 78.9629));
    const id = node.id != null ? String(node.id) : ('node-' + idx);
    const totalRequests = Number(node.total_requests || node.attack_count || 1420);
    const campaign = node.campaign || node.active_campaign || 'Operation Phantom KYC';
    const linkedCases = (Array.isArray(node.linked_cases) && node.linked_cases.length > 0)
      ? node.linked_cases
      : ((Array.isArray(node.linked_case_numbers) && node.linked_case_numbers.length > 0)
        ? node.linked_case_numbers
        : ['CS-1024']);
    const primaryCaseNum = node.primary_case_number || linkedCases[0] || 'CS-1024';
    const primaryCaseId = node.primary_case_id != null ? node.primary_case_id : getCaseId(primaryCaseNum);
    const linkedCaseIds = Array.isArray(node.linked_case_ids) && node.linked_case_ids.length > 0
      ? node.linked_case_ids
      : linkedCases.map(c => getCaseId(c));

    const pincode = node.pincode || (node.metadata && node.metadata.pincode) || '110001';

    let requestSample = node.request_sample;
    if (!requestSample && node.malicious_request_sample) {{
      const s = node.malicious_request_sample;
      let method = 'POST';
      let path = '/api/v1/intercept';
      let payload = s;
      const parts = s.split(' ');
      if (parts.length >= 2 && ['GET', 'POST', 'PUT', 'DELETE', 'HEAD'].includes(parts[0])) {{
        method = parts[0];
        path = parts[1];
      }}
      requestSample = {{
        method: method,
        path: path,
        headers: `Host: ${{node.hostname || node.ip}}\\nUser-Agent: AttackVector/2.4 (Simulated-In)\\nX-Attacker-IP: ${{node.ip}}\\nTarget-Sector: ${{node.target_sector || 'Banking & Financial'}}`,
        payload: payload
      }};
    }}

    if (node.status === 'BLOCKED_BY_FIREWALL' || node.status === 'BLOCKED') {{
      localBlockedIps.add(node.ip);
    }}

    return {{
      ...node,
      id: id,
      lat: lat,
      lng: lng,
      total_requests: totalRequests,
      campaign: campaign,
      primary_case_id: primaryCaseId,
      primary_case_number: primaryCaseNum,
      linked_case_ids: linkedCaseIds,
      linked_cases: linkedCases,
      linked_case_numbers: linkedCases,
      pincode: pincode,
      request_sample: requestSample
    }};
  }});

  // Update initial stats
  document.getElementById('statTotalAttackers').textContent = allAttackers.length;
  document.getElementById('statCritical').textContent = allAttackers.filter(n => n.severity === 'CRITICAL').length;
  document.getElementById('statBlocked').textContent = localBlockedIps.size;

  activeFilteredAttackers = [...allAttackers];
  renderMarkers(activeFilteredAttackers);
}}

// Authentication & Profile Setup
function checkAuthAndProfile() {{
  var user = (typeof cyberscopeUser === 'function') ? cyberscopeUser() : null;
  if (user) {{
    var name = (user.name || user.email || 'Investigator').trim();
    var role = user.role || 'Investigator';
    var pnameEl = document.getElementById('profileName');
    var avatarEl = document.getElementById('avatar');
    if (pnameEl) pnameEl.textContent = name;
    if (avatarEl && typeof cyberscopeInitials === 'function') avatarEl.textContent = cyberscopeInitials(name);
  }}
}}

// Lifecycle Boot
document.addEventListener('DOMContentLoaded', function() {{
  checkAuthAndProfile();
  initThreatMap();
  loadThreatMapData();
  initLiveStream();
}});
</script>
</body>
</html>
"""

# Replace from `// Static Standalone Fallback Dataset` to `</html>`
js_match = re.search(r'// Static Standalone Fallback Dataset.*', html, re.DOTALL)
if js_match:
    html = html[:js_match.start()] + js_code
    print("[+] Replaced entire JS logic block successfully")
else:
    print("[!] Warning: js_match not found")

with open('frontend/threat-map.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("[OK] frontend/threat-map.html updated cleanly without bash expansion issues!")
