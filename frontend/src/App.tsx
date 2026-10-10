import { useEffect, useMemo, useRef, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Circle, Popup, Polyline, Rectangle, Polygon, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';
import {
  Activity, AlertTriangle, Anchor, ArrowUpRight, BarChart3, BookOpen, Bot, Check, CheckCheck, ChevronRight, CircleHelp,
  CloudUpload, Compass, Copy, Cpu, Crosshair, Database, Eye, FileText, Filter, Flame, Globe, HardDrive, Key, Layers3,
  Lock, LogOut, Map as MapIcon, Menu, Navigation, Radar, Radio, RefreshCw, RotateCcw, Send, Shield, Ship,
  Sparkles, Target, Terminal, Trash2, TriangleAlert, Unlock, Upload, UserCheck, Volume2, VolumeX, Wifi, X, Zap
} from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import worldLandData from './world_land.json';
import {
  INDIA_COASTLINE,
  SRI_LANKA_COASTLINE,
  ANDAMAN_CHAIN,
  NICOBAR_CHAIN,
  LAKSHADWEEP_ISLANDS,
  INDIAN_EEZ_BOUNDARY,
  TACTICAL_GRATICULES,
  STRATEGIC_HUBS
} from './offlineGeoData';
import { OfflineGeoOverlay } from './components/OfflineGeoOverlay';

type Page = 'Joint COP' | 'Naval Domain' | 'Army Domain' | 'Change Detection' | 'Tactical SITREP' | 'Tactical AI (RAG)' | 'Mission Planner' | 'Edge & KPIs';
type NavalMode = 'cv' | 'ops';

type Item = {
  id: string;
  source: string;
  image_name: string;
  kind: string;
  confidence: number;
  lat: number | null;
  lon: number | null;
  ais_status: string;
  mmsi?: string | null;
  threat_score: number;
  threat_level: string;
  reasons: string[];
  review_status: string;
  image_url?: string | null;
  x: number;
  y: number;
  w: number;
  h: number;
};

type SarDetection = {
  id: string;
  scene_id: string;
  timestamp: string;
  lat: number;
  lon: number;
  rcs_sigma0_db: number;
  estimated_length_m: number;
  cfar_confidence: number;
  ais_correlated: number;
  correlated_mmsi?: string | null;
  is_dark_vessel: number;
  threat_score: number;
  threat_level: string;
  speed_knots: number;
  heading_deg: number;
  notes: string;
};

type ArmyFeed = {
  id: string;
  domain: string;
  source_ref: string;
  target_class: string;
  confidence: number;
  lat: number;
  lon: number;
  signal_strength: number;
  alert_summary: string;
  raw_payload: string;
  threat_score: number;
  threat_level: string;
  status: string;
  created_at: string;
};

type Zone = {
  id: string;
  name: string;
  zone_type: string;
  lat: number;
  lon: number;
  radius_km: number;
  created_at?: string;
};

type Scene = {
  bounds_wgs84: number[] | null;
  acquisition_date: string | null;
  filename: string;
  message?: string;
};

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const api = `${API_BASE}/api`;

function resolveMediaUrl(url: string | null): string {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  return `${API_BASE}${url}`;
}

export type UserProfile = {
  username: string;
  full_name: string;
  callsign?: string;
  rank?: string;
  role: string;
  clearance: string;
};

function getAuthHeaders(): Record<string, string> {
  const token = sessionStorage.getItem('rakshak_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    ...getAuthHeaders(),
    ...((options?.headers as Record<string, string>) || {})
  };
  if (options?.body && typeof options.body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  const r = await fetch(api + url, {
    ...options,
    headers
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function Metric({ label, value, sub, icon: Icon, tone = 'cyan' }: { label: string; value: string | number; sub: string; icon: any; tone?: string }) {
  return (
    <div className="metric">
      <div className="metric-top">
        <span>{label}</span>
        <Icon size={17} />
      </div>
      <strong className={tone}>{value}</strong>
      <small>{sub}</small>
    </div>
  );
}

function HeatLayer({ points }: { points: [number, number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (!points.length) return;
    const layer = (L as any).heatLayer(points, {
      radius: 24,
      blur: 18,
      maxZoom: 11,
      gradient: { 0.25: '#44bfc1', 0.55: '#f1bc69', 0.85: '#ff675e' }
    });
    layer.addTo(map);
    return () => { map.removeLayer(layer); };
  }, [map, points]);
  return null;
}

// Tactical Kinematics Dead-Reckoning Projection
function projectTrack(lat: number, lon: number, speedKnots: number, headingDeg: number, minutes: number): [number, number] {
  const distanceKm = (speedKnots * 1.852) * (minutes / 60.0);
  const r = 6371.0;
  const latRad = (lat * Math.PI) / 180.0;
  const lonRad = (lon * Math.PI) / 180.0;
  const brgRad = (headingDeg * Math.PI) / 180.0;
  const dRatio = distanceKm / r;
  const predLatRad = Math.asin(
    Math.sin(latRad) * Math.cos(dRatio) + Math.cos(latRad) * Math.sin(dRatio) * Math.cos(brgRad)
  );
  const predLonRad = lonRad + Math.atan2(
    Math.sin(brgRad) * Math.sin(dRatio) * Math.cos(latRad),
    Math.cos(dRatio) - Math.sin(latRad) * Math.sin(predLatRad)
  );
  return [(predLatRad * 180.0) / Math.PI, (predLonRad * 180.0) / Math.PI];
}

function generateEllipsePoints(
  lat: number,
  lon: number,
  semiMajorM: number,
  semiMinorM: number,
  orientationDeg: number,
  numPoints: number = 24
): [number, number][] {
  const points: [number, number][] = [];
  const rad = (orientationDeg * Math.PI) / 180.0;
  const cosO = Math.cos(rad);
  const sinO = Math.sin(rad);
  for (let i = 0; i <= numPoints; i++) {
    const theta = (i * 2 * Math.PI) / numPoints;
    const ex = semiMinorM * Math.cos(theta);
    const ey = semiMajorM * Math.sin(theta);
    const x = ex * cosO - ey * sinO;
    const y = ex * sinO + ey * cosO;
    const dLat = y / 111320.0;
    const dLon = x / (111320.0 * Math.cos((lat * Math.PI) / 180.0));
    points.push([lat + dLat, lon + dLon]);
  }
  return points;
}

type FlyTarget = { lat: number; lon: number; zoom?: number; timestamp: number } | null;

function MapController({
  flyTarget,
  routePoints
}: {
  flyTarget: FlyTarget;
  routePoints?: [number, number][];
}) {
  const map = useMap();
  useEffect(() => {
    if (flyTarget && flyTarget.lat != null && flyTarget.lon != null) {
      map.flyTo([flyTarget.lat, flyTarget.lon], flyTarget.zoom || 8, {
        duration: 1.5,
        easeLinearity: 0.25
      });
    } else if (routePoints && routePoints.length > 0) {
      const allLats = routePoints.map(p => p[0]);
      const minLat = Math.min(...allLats);
      const maxLat = Math.max(...allLats);
      // Include relevant Indian coastline points within and adjacent to this latitude span
      const relevantCoast = INDIA_COASTLINE.filter(([lat, _lon]) => lat >= minLat - 1.5 && lat <= maxLat + 1.5);
      const ptsToFit = [...routePoints, ...relevantCoast];
      if (ptsToFit.length > 0) {
        const bounds = L.latLngBounds(ptsToFit.map(([lat, lon]) => [lat, lon]));
        map.fitBounds(bounds, { padding: [35, 35], maxZoom: 8 });
      }
    }
  }, [flyTarget, routePoints, map]);
  return null;
}

function TacticalMap({
  opticalItems,
  sarDetections,
  armyFeeds,
  providerPoints,
  zones,
  layers,
  sceneBounds,
  routePoints,
  flyTarget,
  fusedTracks = []
}: {
  opticalItems: Item[];
  sarDetections: SarDetection[];
  armyFeeds: ArmyFeed[];
  providerPoints: any[];
  zones: Zone[];
  layers: { optical: boolean; sar: boolean; ais: boolean; army: boolean; zones: boolean; vectors: boolean; geoOverlay?: boolean; heat: boolean };
  sceneBounds?: number[] | null;
  routePoints?: [number, number][];
  flyTarget?: FlyTarget;
  fusedTracks?: any[];
}) {
  const validOptical = opticalItems.filter(x => x.lat !== null && x.lon !== null);
  const validSar = sarDetections.filter(x => x.lat !== null && x.lon !== null);
  const validArmy = armyFeeds.filter(x => x.lat !== null && x.lon !== null);
  const validProviders = providerPoints.filter(x => x.lat !== null && x.lon !== null);

  const center: [number, number] = validSar.length
    ? [validSar[0].lat, validSar[0].lon]
    : validOptical.length
    ? [validOptical[0].lat!, validOptical[0].lon!]
    : [18.92, 72.83]; // Mumbai Maritime Operational Center

  type BasemapMode = 'basemap' | 'dark' | 'terrain';
  const [basemapMode, setBasemapMode] = useState<BasemapMode>('basemap');
  const [localGeoOverlay, setLocalGeoOverlay] = useState<boolean>(true);
  const effectiveGeoOverlay = layers.geoOverlay !== undefined ? layers.geoOverlay : localGeoOverlay;

  const BASEMAP_TILES: Record<string, { url: string; attr: string; maxZoom: number }> = {
    basemap: {
      url: '/api/tiles/basemap/{z}/{x}/{y}.png',
      attr: 'Project Rakshak 2.0 Offline Basemap (Synthetic) — 100% Air-Gapped',
      maxZoom: 19
    },
    dark: {
      url: '/api/tiles/dark/{z}/{x}/{y}.png',
      attr: 'Project Rakshak 2.0 Dark Tactical (Synthetic) — Local Offline Service',
      maxZoom: 16
    },
    terrain: {
      url: '/api/tiles/terrain/{z}/{x}/{y}.png',
      attr: 'Project Rakshak 2.0 Offline Terrain (Synthetic) — synthetic, not real elevation',
      maxZoom: 19
    }
  };

  const heatPoints: [number, number, number][] = useMemo(() => {
    const pts: [number, number, number][] = [];
    if (layers.optical) validOptical.forEach(x => pts.push([x.lat!, x.lon!, Math.max(0.15, x.threat_score / 100)]));
    if (layers.sar) validSar.forEach(x => pts.push([x.lat, x.lon, x.is_dark_vessel ? 0.95 : 0.35]));
    if (layers.army) validArmy.forEach(x => pts.push([x.lat, x.lon, Math.max(0.3, x.threat_score / 100)]));
    if (layers.ais) validProviders.forEach(x => pts.push([x.lat, x.lon, 0.25]));
    return pts;
  }, [layers, validOptical, validSar, validArmy, validProviders]);

  const sceneRect = sceneBounds ? [[sceneBounds[1], sceneBounds[0]], [sceneBounds[3], sceneBounds[2]]] as [[number, number], [number, number]] : null;

  return (
    <div className="map-wrap" style={{ height: '560px' }}>
      {/* Air-Gapped Synthetic Basemap Switcher & Overlay Toggle */}
      <div style={{
        position: 'absolute',
        top: '12px',
        right: '58px',
        zIndex: 500,
        display: 'flex',
        gap: '6px'
      }}>
        <button
          onClick={() => setBasemapMode('basemap')}
          style={{
            background: basemapMode === 'basemap' ? 'rgba(6, 182, 212, 0.35)' : 'rgba(7, 18, 29, 0.85)',
            border: `1px solid ${basemapMode === 'basemap' ? '#00f0ff' : '#1e384b'}`,
            color: basemapMode === 'basemap' ? '#00f0ff' : '#728d9c',
            padding: '5px 10px',
            fontSize: '10px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontFamily: 'monospace',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
          title="Air-Gapped Sovereign Synthetic Basemap (0 External Calls)"
        >
          <Radar size={13} /> 🌐 Offline basemap (synthetic)
        </button>
        <button
          onClick={() => setBasemapMode('dark')}
          style={{
            background: basemapMode === 'dark' ? 'rgba(6, 182, 212, 0.35)' : 'rgba(7, 18, 29, 0.85)',
            border: `1px solid ${basemapMode === 'dark' ? '#00f0ff' : '#1e384b'}`,
            color: basemapMode === 'dark' ? '#00f0ff' : '#728d9c',
            padding: '5px 10px',
            fontSize: '10px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontFamily: 'monospace',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
          title="Tactical Dark Gray Basemap (0 External Calls)"
        >
          <Shield size={13} /> 🛡️ Dark tactical (synthetic)
        </button>
        <button
          onClick={() => setBasemapMode('terrain')}
          style={{
            background: basemapMode === 'terrain' ? 'rgba(6, 182, 212, 0.35)' : 'rgba(7, 18, 29, 0.85)',
            border: `1px solid ${basemapMode === 'terrain' ? '#00f0ff' : '#1e384b'}`,
            color: basemapMode === 'terrain' ? '#00f0ff' : '#728d9c',
            padding: '5px 10px',
            fontSize: '10px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontFamily: 'monospace',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
          title="Tactical Bathymetry & Terrain Basemap (0 External Calls)"
        >
          <MapIcon size={13} /> 🗺️ Offline terrain (synthetic)
        </button>
        <button
          onClick={() => setLocalGeoOverlay(v => !v)}
          style={{
            background: effectiveGeoOverlay ? 'rgba(16, 185, 129, 0.25)' : 'rgba(7, 18, 29, 0.85)',
            border: `1px solid ${effectiveGeoOverlay ? '#10b981' : '#1e384b'}`,
            color: effectiveGeoOverlay ? '#10b981' : '#728d9c',
            padding: '5px 10px',
            fontSize: '10px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontFamily: 'monospace',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
          title="Toggle Coastline, 200nm EEZ & Tactical Graticule Overlay"
        >
          <Globe size={13} /> {effectiveGeoOverlay ? 'Coastline/EEZ: ON' : 'Coastline/EEZ: OFF'}
        </button>
      </div>

      <MapContainer center={center} zoom={6} scrollWheelZoom className="map">
        <MapController flyTarget={flyTarget || null} routePoints={routePoints} />
        <TileLayer
          key={basemapMode}
          attribution={BASEMAP_TILES[basemapMode].attr}
          url={BASEMAP_TILES[basemapMode].url}
          maxZoom={BASEMAP_TILES[basemapMode].maxZoom}
        />

        {/* Reusable Sovereign GeoJSON Overlay (Indian Coastline, EEZ, Graticules, Radar Rings) */}
        <OfflineGeoOverlay
          enabled={effectiveGeoOverlay}
          basemapMode={basemapMode}
        />

        {sceneRect && <Rectangle bounds={sceneRect} pathOptions={{ color: '#54d2c5', weight: 2, dashArray: '5 5', fillOpacity: 0.05 }} />}
        {layers.heat && <HeatLayer points={heatPoints} />}

        {/* Restricted Geofencing Zones */}
        {layers.zones && zones.map(z => {
          const isFocused = Boolean(flyTarget && Math.abs(flyTarget.lat - z.lat) < 0.05 && Math.abs(flyTarget.lon - z.lon) < 0.05);
          return (
            <Circle
              key={z.id}
              center={[z.lat, z.lon]}
              radius={z.radius_km * 1000}
              pathOptions={{
                color: isFocused ? '#00f0ff' : (z.zone_type.includes('EXCLUSION') ? '#ff4d4d' : '#f59e0b'),
                fillColor: isFocused ? '#00f0ff' : (z.zone_type.includes('EXCLUSION') ? '#ff4d4d' : '#f59e0b'),
                fillOpacity: isFocused ? 0.35 : 0.12,
                weight: isFocused ? 4 : 2,
                dashArray: isFocused ? undefined : '4 4'
              }}
            >
              <Popup>
                <b>RESTRICTED DEFENSE ZONE</b><br />
                <b>{z.name}</b><br />
                Type: {z.zone_type}<br />
                Coordinates: {z.lat.toFixed(4)}, {z.lon.toFixed(4)}<br />
                Radius: {z.radius_km} km
              </Popup>
            </Circle>
          );
        })}

        {/* Sentinel-1 SAR Detections & Dark Vessels */}
        {layers.sar && validSar.map(s => {
          const isDark = Boolean(s.is_dark_vessel);
          const color = isDark ? '#ff2a2a' : '#10b981';
          const proj30 = projectTrack(s.lat, s.lon, s.speed_knots || 12, s.heading_deg || 0, 30);
          return (
            <span key={s.id}>
              {isDark && (
                <Circle
                  center={[s.lat, s.lon]}
                  radius={18000}
                  pathOptions={{
                    color: '#ff2a2a',
                    fillColor: '#ff2a2a',
                    fillOpacity: 0.08,
                    weight: 1,
                    dashArray: '4 6'
                  }}
                />
              )}
              <CircleMarker
                center={[s.lat, s.lon]}
                radius={isDark ? 11 : 7}
                pathOptions={{ color, fillColor: color, fillOpacity: 0.85, weight: isDark ? 3 : 1 }}
              >
                <Popup>
                  <b style={{ color: isDark ? '#ff4d4d' : '#10b981' }}>
                    {isDark ? '🚨 CRITICAL DARK VESSEL (SAR)' : 'COOPERATIVE AIS VESSEL (SAR)'}
                  </b><br />
                  <b>ID:</b> {s.id.toUpperCase()}<br />
                  <b>Radar Backscatter (RCS):</b> {s.rcs_sigma0_db} dB<br />
                  <b>Est. Length:</b> {s.estimated_length_m} m | <b>CFAR:</b> {(s.cfar_confidence * 100).toFixed(0)}%<br />
                  <b>Speed:</b> {s.speed_knots} kts @ {s.heading_deg}°<br />
                  <b>Threat Score:</b> {s.threat_score} ({s.threat_level})<br />
                  <small>{s.notes}</small>
                </Popup>
              </CircleMarker>
              {layers.vectors && s.speed_knots > 0 && (
                <Polyline
                  positions={[[s.lat, s.lon], proj30]}
                  pathOptions={{ color: isDark ? '#ff2a2a' : '#10b981', weight: 2, dashArray: '4 6' }}
                />
              )}
            </span>
          );
        })}

        {/* Optical Satellite Candidates */}
        {layers.optical && validOptical.map(x => (
          <CircleMarker
            key={x.id}
            center={[x.lat!, x.lon!]}
            radius={Math.max(6, Math.min(13, 6 + x.threat_score / 18))}
            pathOptions={{
              color: x.threat_level === 'HIGH' ? '#ff6b63' : x.threat_level === 'MEDIUM' ? '#ffba62' : '#50d7c7',
              fillOpacity: 0.75
            }}
          >
            <Popup>
              <b>OPTICAL: {x.kind}</b><br />
              Source: {x.source}<br />
              Score: {x.threat_score} · {x.threat_level}<br />
              AIS Status: {x.ais_status}<br />
              Confidence: {(x.confidence * 100).toFixed(1)}%
            </Popup>
          </CircleMarker>
        ))}

        {/* Army Multimodal Feeds (Drone UAV, Ground UGS, SIGINT) */}
        {layers.army && validArmy.map(a => {
          const isUav = a.domain === 'DRONE_UAV';
          const isUgs = a.domain === 'UGS_GROUND';
          const color = isUav ? '#38bdf8' : isUgs ? '#eab308' : '#a855f7';
          return (
            <CircleMarker
              key={a.id}
              center={[a.lat, a.lon]}
              radius={8}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.82 }}
            >
              <Popup>
                <b style={{ color }}>ARMY [{a.domain}]: {a.target_class}</b><br />
                Source: {a.source_ref}<br />
                Confidence: {(a.confidence * 100).toFixed(0)}%<br />
                Threat: {a.threat_score} ({a.threat_level})<br />
                <small>{a.alert_summary}</small>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* AIS Provider Tracks */}
        {layers.ais && validProviders.slice(0, 150).map((p, i) => (
          <CircleMarker
            key={'p' + i}
            center={[p.lat, p.lon]}
            radius={4}
            pathOptions={{ color: '#818cf8', fillColor: '#818cf8', fillOpacity: 0.7 }}
          >
            <Popup>
              <b>PipeV4 AIS Detection</b><br />
              Scene: {p.scene_id}<br />
              MMSI: {p.mmsi || 'No MMSI'}<br />
              AIS Status: {p.ais_status}
            </Popup>
          </CircleMarker>
        ))}

        {/* Fused Multi-Target Kinematic Tracks (Kalman Filter + Hungarian / JPDA) */}
        {fusedTracks && fusedTracks.map((trk: any) => {
          const isDark = trk.target_class === 'Vessel' && !trk.identity;
          const isCoast = trk.state === 'COASTING';
          const trkColor = isCoast ? '#94a3b8' : isDark ? '#f43f5e' : trk.target_class === 'Vehicle' ? '#eab308' : '#00f0ff';
          const historyCoords: [number, number][] = (trk.trail || trk.history || []).map((h: any) => [h.lat, h.lon]);
          if (historyCoords.length === 0 || (historyCoords[historyCoords.length - 1][0] !== trk.lat || historyCoords[historyCoords.length - 1][1] !== trk.lon)) {
            historyCoords.push([trk.lat, trk.lon]);
          }
          const proj30 = projectTrack(trk.lat, trk.lon, trk.speed_knots || 0, trk.heading_deg || 0, 30);
          const covEll = trk.covariance_ellipse || trk.cov_ellipse;
          const ellipseCoords = covEll ? generateEllipsePoints(
            trk.lat,
            trk.lon,
            Math.max(15, covEll.semi_major_m || 30),
            Math.max(10, covEll.semi_minor_m || 20),
            covEll.orientation_deg || 0
          ) : [];

          return (
            <span key={trk.track_id}>
              {/* 1-Sigma / 2-Sigma Positional Covariance Ellipse */}
              {ellipseCoords.length > 0 && (
                <Polygon
                  positions={ellipseCoords}
                  pathOptions={{
                    color: trkColor,
                    fillColor: trkColor,
                    fillOpacity: isCoast ? 0.04 : 0.12,
                    weight: 1.5,
                    dashArray: isCoast ? '3 5' : undefined
                  }}
                />
              )}

              {/* Kinematic History Track Trail */}
              {historyCoords.length > 1 && (
                <Polyline
                  positions={historyCoords}
                  pathOptions={{
                    color: trkColor,
                    weight: 2.2,
                    dashArray: isCoast ? '4 6' : undefined,
                    opacity: 0.85
                  }}
                />
              )}

              {/* Projected Velocity Vector (30 min forward) */}
              {layers.vectors && (trk.speed_knots || 0) > 0 && (
                <Polyline
                  positions={[[trk.lat, trk.lon], proj30]}
                  pathOptions={{
                    color: trkColor,
                    weight: 1.8,
                    dashArray: '3 5',
                    opacity: 0.7
                  }}
                />
              )}

              {/* Current Position Marker */}
              <CircleMarker
                center={[trk.lat, trk.lon]}
                radius={isDark ? 9 : 7}
                pathOptions={{
                  color: '#ffffff',
                  fillColor: trkColor,
                  fillOpacity: 0.95,
                  weight: 2
                }}
              >
                <Popup>
                  <div style={{ fontFamily: 'monospace', fontSize: '11px', color: '#0f172a' }}>
                    <b style={{ color: trkColor, fontSize: '12px' }}>🎯 TRACK: {trk.track_id}</b><br />
                    <b>State:</b> <span style={{ fontWeight: 700, color: isCoast ? '#64748b' : '#059669' }}>{trk.state}</span> ({trk.total_updates || trk.hit_count || 1} hits / {trk.consecutive_misses ?? trk.miss_count ?? 0} misses)<br />
                    <b>Class:</b> {trk.target_class} {trk.identity ? `(${trk.identity})` : '[DARK/UNIDENTIFIED]'}<br />
                    <b>Sensor:</b> {trk.last_sensor || (trk.sensor_contributions ? Object.keys(trk.sensor_contributions).join(', ') : 'FUSED')}<br />
                    <b>Speed:</b> {Number(trk.speed_knots).toFixed(1)} kts @ {Number(trk.heading_deg).toFixed(0)}°<br />
                    <b>Pos:</b> {Number(trk.lat).toFixed(4)}°N, {Number(trk.lon).toFixed(4)}°E<br />
                    {covEll && (
                      <>
                        <b>Uncertainty (CEP):</b> {Number(covEll.cep_m).toFixed(1)} m<br />
                        <b>Cov Ellipse:</b> {Number(covEll.semi_major_m).toFixed(0)}m &times; {Number(covEll.semi_minor_m).toFixed(0)}m @ {Number(covEll.orientation_deg).toFixed(0)}°
                      </>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            </span>
          );
        })}

        {/* Mission Route Vector */}
        {routePoints && routePoints.length > 1 && (
          <Polyline positions={routePoints} pathOptions={{ color: '#06b6d4', weight: 3, dashArray: '6 8' }} />
        )}
      </MapContainer>

      <div className="map-legend">
        <span style={{ color: '#38bdf8', fontWeight: 600 }}>
          <i className="dot" style={{ background: '#38bdf8' }} /> {basemapMode === 'basemap' ? 'Offline basemap (synthetic)' : basemapMode === 'dark' ? 'Dark tactical (synthetic)' : 'Offline terrain (synthetic)'}
        </span>
        <span><i className="dot" style={{ background: '#00f0ff' }} /> Fused Track (Kalman Ellipse)</span>
        <span><i className="dot" style={{ background: '#f59e0b' }} /> 200nm Indian EEZ</span>
        <span><i className="dot" style={{ background: '#ff2a2a' }} /> SAR Dark Vessel (AIS OFF)</span>
        <span><i className="dot" style={{ background: '#10b981' }} /> SAR Verified AIS</span>
        <span><i className="dot" style={{ background: '#50d7c7' }} /> Optical AI Hit</span>
        <span><i className="dot" style={{ background: '#38bdf8' }} /> Tactical UAV Recon</span>
        <span><i className="dot" style={{ background: '#eab308' }} /> UGS Ground Sensor</span>
        <span><i className="dot" style={{ background: '#818cf8' }} /> AIS Provider Point</span>
        <small>{validSar.length + validOptical.length + validArmy.length + validProviders.length + (fusedTracks?.length || 0)} active contacts</small>
      </div>
    </div>
  );
}

export function App() {
  const [page, setPage] = useState<Page>('Joint COP');
  const [navalMode, setNavalMode] = useState<NavalMode>('cv');
  const [modelType, setModelType] = useState<'vessel' | 'multiclass'>('vessel');
  const [scene, setScene] = useState<Scene | null>(null);
  const [month, setMonth] = useState('202604');
  const [confidence, setConfidence] = useState(0.4);

  const [opticalItems, setOpticalItems] = useState<Item[]>([]);
  const [sarDetections, setSarDetections] = useState<SarDetection[]>([]);
  const [armyFeeds, setArmyFeeds] = useState<ArmyFeed[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [pipe, setPipe] = useState<any[]>([]);
  const [kpis, setKpis] = useState<any>(null);
  const [telemetry, setTelemetry] = useState<any>(null);
  const [sitrep, setSitrep] = useState<any>(null);
  const [modelStatus, setModelStatus] = useState<any>(null);
  const [triageKpis, setTriageKpis] = useState<any>(null);
  const [triageAudit, setTriageAudit] = useState<any[]>([]);
  const [triageLoading, setTriageLoading] = useState(false);
  const [reopeningItemId, setReopeningItemId] = useState<string | null>(null);

  // Multi-Target Track Fusion State
  const [fusedTracks, setFusedTracks] = useState<any[]>([]);
  const [trackingBenchmarks, setTrackingBenchmarks] = useState<any>(null);
  const [trackingMethod, setTrackingMethod] = useState<'hungarian' | 'jpda' | 'nn'>('hungarian');
  const [trackingLoading, setTrackingLoading] = useState(false);

  // DDIL (Denied, Degraded, Intermittent, Limited) State
  const [ddilStatus, setDdilStatus] = useState<any>(null);
  const [ddilSimLoading, setDdilSimLoading] = useState(false);
  const [ddilDropdownOpen, setDdilDropdownOpen] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');
  const [preview, setPreview] = useState<string | null>(null);
  const [previewName, setPreviewName] = useState('');
  const [imageSize, setImageSize] = useState<[number, number]>([1, 1]);
  const [navalReviewTab, setNavalReviewTab] = useState<'image' | 'sar'>('image');
  
  // Multi-Temporal Change Detection State (Air-Gapped)
  const [cdData, setCdData] = useState<any>(null);
  const [cdLoading, setCdLoading] = useState(false);
  const [cdSwipe, setCdSwipe] = useState(50);
  const [cdShift, setCdShift] = useState(2.0);
  const [cdSeed, setCdSeed] = useState(42);
  const [cdFilter, setCdFilter] = useState<'ALL' | 'NEW' | 'REMOVED' | 'MOVED'>('ALL');
  const [cdViewMode, setCdViewMode] = useState<'swipe' | 'diff'>('swipe');

  // Sovereign Air-Gapped RAG State
  const [ragQuery, setRagQuery] = useState('');
  const [ragLoading, setRagLoading] = useState(false);
  const [ragResponse, setRagResponse] = useState<any>(null);
  const [ragKnowledgeBase, setRagKnowledgeBase] = useState<any[]>([]);
  const [ragKbLoading, setRagKbLoading] = useState(false);
  const [ragViewTab, setRagViewTab] = useState<'advisor' | 'library'>('advisor');
  const [ragFilterCat, setRagFilterCat] = useState<string>('ALL');
  const [copiedRag, setCopiedRag] = useState(false);
  const [showRawDirective, setShowRawDirective] = useState(false);
  const [hoverBotOpen, setHoverBotOpen] = useState(false);
  const botCloseTimerRef = useRef<any>(null);

  const handleBotCircleEnter = () => {
    if (botCloseTimerRef.current) clearTimeout(botCloseTimerRef.current);
    setHoverBotOpen(true);
  };

  const handleBotCircleLeave = () => {
    botCloseTimerRef.current = setTimeout(() => {
      setHoverBotOpen(false);
    }, 280);
  };

  const handleBotMenuEnter = () => {
    if (botCloseTimerRef.current) clearTimeout(botCloseTimerRef.current);
    setHoverBotOpen(true);
  };

  const handleBotMenuLeave = () => {
    botCloseTimerRef.current = setTimeout(() => {
      setHoverBotOpen(false);
    }, 220);
  };

  // Tactical Audio Synthesizer State & Military DTG Zulu Clock
  const [audioEnabled, setAudioEnabled] = useState<boolean>(false);
  const [liveDtg, setLiveDtg] = useState<string>('');

  useEffect(() => {
    const updateDtg = () => {
      const now = new Date();
      const day = String(now.getUTCDate()).padStart(2, '0');
      const hrs = String(now.getUTCHours()).padStart(2, '0');
      const min = String(now.getUTCMinutes()).padStart(2, '0');
      const sec = String(now.getUTCSeconds()).padStart(2, '0');
      const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
      const mon = months[now.getUTCMonth()];
      const yr = now.getUTCFullYear();
      setLiveDtg(`${day}${hrs}${min}:${sec}Z ${mon} ${yr}`);
    };
    updateDtg();
    const timer = setInterval(updateDtg, 1000);
    return () => clearInterval(timer);
  }, []);

  const playTacticalSound = (type: 'blip' | 'alert' | 'click' = 'blip') => {
    if (!audioEnabled) return;
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      if (type === 'blip') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.08);
        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 0.08);
        osc.start();
        osc.stop(ctx.currentTime + 0.08);
      } else if (type === 'alert') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(620, ctx.currentTime);
        osc.frequency.setValueAtTime(820, ctx.currentTime + 0.1);
        gain.gain.setValueAtTime(0.12, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 0.22);
        osc.start();
        osc.stop(ctx.currentTime + 0.22);
      } else if (type === 'click') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(1200, ctx.currentTime);
        gain.gain.setValueAtTime(0.04, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 0.03);
        osc.start();
        osc.stop(ctx.currentTime + 0.03);
      }
    } catch {}
  };

  // Authentication & Security State (Session-scoped: requires login on fresh deploy/open, persists across page refreshes)
  const [user, setUser] = useState<UserProfile | null>(() => {
    try {
      // Clear legacy localStorage to ensure fresh deploy/open always asks for authentication
      localStorage.removeItem('rakshak_token');
      localStorage.removeItem('rakshak_user');

      const token = sessionStorage.getItem('rakshak_token');
      const saved = sessionStorage.getItem('rakshak_user');
      if (token && saved) {
        return JSON.parse(saved);
      }
      return null;
    } catch {
      return null;
    }
  });
  const [authUsername, setAuthUsername] = useState<string>('');
  const [authPassword, setAuthPassword] = useState<string>('');
  const [authLoading, setAuthLoading] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const [mustChangePasswordModal, setMustChangePasswordModal] = useState<{ token: string; user: any } | null>(null);
  const [newPassword, setNewPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [rotationOldPassword, setRotationOldPassword] = useState<string>('');
  const [rotationLoading, setRotationLoading] = useState<boolean>(false);
  const [rotationError, setRotationError] = useState<string | null>(null);

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!authUsername.trim() || !authPassword) {
      setAuthError('Please enter both Operator ID and Security Key.');
      return;
    }
    setAuthLoading(true);
    setAuthError(null);
    try {
      const r = await fetch(api + '/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: authUsername.trim(), password: authPassword })
      });
      if (!r.ok) {
        let errMsg = 'ACCESS DENIED: Invalid operator credentials.';
        try {
          const err = await r.json();
          errMsg = err.detail || errMsg;
        } catch {}
        throw new Error(errMsg);
      }
      const data = await r.json();
      if (data.must_change_password) {
        setMustChangePasswordModal({ token: data.access_token, user: data.user });
        setRotationOldPassword(authPassword);
        setAuthPassword('');
        setToast('Mandatory first-login credential rotation required.');
        return;
      }
      sessionStorage.setItem('rakshak_token', data.access_token);
      sessionStorage.setItem('rakshak_user', JSON.stringify(data.user));
      setUser(data.user);
      setAuthPassword(''); // Clear password from memory after successful verification
      setToast(`Access Granted: ${data.user.full_name} [${data.user.callsign || data.user.username}]. Clearance: ${data.user.clearance}`);
    } catch (err: any) {
      setAuthError(err.message || 'Authentication error');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mustChangePasswordModal) return;
    if (newPassword.length < 8) {
      setRotationError('New password must be at least 8 characters long.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setRotationError('New password and confirmation do not match.');
      return;
    }
    if (rotationOldPassword === newPassword) {
      setRotationError('New password must be different from the bootstrap password.');
      return;
    }
    setRotationLoading(true);
    setRotationError(null);
    try {
      const r = await fetch(api + '/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${mustChangePasswordModal.token}`
        },
        body: JSON.stringify({ old_password: rotationOldPassword, new_password: newPassword })
      });
      if (!r.ok) {
        let msg = 'Failed to rotate credentials.';
        try { const err = await r.json(); msg = err.detail || msg; } catch {}
        throw new Error(msg);
      }
      sessionStorage.setItem('rakshak_token', mustChangePasswordModal.token);
      sessionStorage.setItem('rakshak_user', JSON.stringify(mustChangePasswordModal.user));
      setUser(mustChangePasswordModal.user);
      setMustChangePasswordModal(null);
      setNewPassword('');
      setConfirmPassword('');
      setRotationOldPassword('');
      setToast(`Credentials successfully rotated! Welcome, ${mustChangePasswordModal.user.full_name}.`);
    } catch (err: any) {
      setRotationError(err.message || 'Error updating password.');
    } finally {
      setRotationLoading(false);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem('rakshak_token');
    sessionStorage.removeItem('rakshak_user');
    localStorage.removeItem('rakshak_token');
    localStorage.removeItem('rakshak_user');
    setUser(null);
    setAuthUsername('');
    setAuthPassword('');
    setAuthError(null);
    setToast('Operator signed out. Terminal locked in secure standby.');
  };

  // Verify JWT on initial mount (session-scoped)
  useEffect(() => {
    const token = sessionStorage.getItem('rakshak_token');
    if (token) {
      fetch(api + '/auth/me', { headers: { 'Authorization': `Bearer ${token}` } })
        .then(r => r.ok ? r.json() : null)
        .then(d => {
          if (d && d.user) {
            const u: UserProfile = {
              username: d.user.sub,
              full_name: d.user.full_name,
              callsign: d.user.callsign,
              rank: d.user.rank,
              role: d.user.role,
              clearance: d.user.clearance
            };
            setUser(u);
            sessionStorage.setItem('rakshak_user', JSON.stringify(u));
          } else {
            // Expired or invalid token: reset session
            sessionStorage.removeItem('rakshak_token');
            sessionStorage.removeItem('rakshak_user');
            setUser(null);
          }
        })
        .catch(() => {});
    }
  }, []);

  // Army Domain UAV Downlink Controls
  const armyInputRef = useRef<HTMLInputElement>(null);
  const [armyDragOver, setArmyDragOver] = useState(false);

  // Target Color Palette by Class
  const getTargetColor = (kind: string, threat?: string) => {
    const k = (kind || '').toLowerCase();
    if (k.includes('vehicle')) return '#f59e0b'; // Amber Gold for Land Convoys
    if (k.includes('aircraft')) return '#38bdf8'; // Sky Cyan for Military Aircraft
    if (k.includes('infra')) return '#c084fc'; // Purple for Bunkers / Infrastructure
    if (k.includes('vessel')) return '#34d399'; // Emerald for Vessels
    return threat === 'HIGH' ? '#ff4d4d' : '#00f0ff';
  };

  // Target Class & Visual Filter Controls for Clean Reading
  const [classFilter, setClassFilter] = useState<'all' | 'vehicle' | 'infrastructure' | 'aircraft' | 'vessel'>('all');
  const [minConfFilter, setMinConfFilter] = useState<number>(0.45);
  const [showLabels, setShowLabels] = useState<boolean>(true);

  // Filtered detections for the active preview image
  const currentImageItems = useMemo(() => {
    return opticalItems.filter(x => !previewName || x.image_name === previewName);
  }, [opticalItems, previewName]);

  const countsByClass = useMemo(() => {
    const counts = { all: currentImageItems.length, vehicle: 0, infrastructure: 0, aircraft: 0, vessel: 0 };
    for (const item of currentImageItems) {
      const k = (item.kind || '').toLowerCase();
      if (k.includes('vehicle')) counts.vehicle++;
      else if (k.includes('infra')) counts.infrastructure++;
      else if (k.includes('aircraft')) counts.aircraft++;
      else if (k.includes('vessel')) counts.vessel++;
    }
    return counts;
  }, [currentImageItems]);

  const activeDetections = useMemo(() => {
    return currentImageItems.filter(x => {
      if (x.confidence < minConfFilter) return false;
      if (classFilter !== 'all') {
        const k = (x.kind || '').toLowerCase();
        if (classFilter === 'vehicle' && !k.includes('vehicle')) return false;
        if (classFilter === 'infrastructure' && !k.includes('infra')) return false;
        if (classFilter === 'aircraft' && !k.includes('aircraft')) return false;
        if (classFilter === 'vessel' && !k.includes('vessel')) return false;
      }
      return true;
    });
  }, [currentImageItems, classFilter, minConfFilter]);

  // Interactive Map FlyTo Target State
  const [flyTarget, setFlyTarget] = useState<FlyTarget>(null);

  const flyToLocation = (lat: number, lon: number, zoom = 8) => {
    setFlyTarget({ lat, lon, zoom, timestamp: Date.now() });
    const mapWrap = document.querySelector('.map-wrap');
    if (mapWrap) {
      mapWrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  };

  // Tactical Map Layer Toggles
  const [layers, setLayers] = useState({
    optical: true,
    sar: true,
    ais: true,
    army: true,
    zones: true,
    vectors: true,
    heat: false,
    geoOverlay: true
  });

  // Domain Specific Map vs Raster View Modes
  const [navalViewMode, setNavalViewMode] = useState<'map' | 'raster'>('map');
  const [armyViewMode, setArmyViewMode] = useState<'map' | 'uav'>('map');

  const toggleLayer = (k: keyof typeof layers) => setLayers(l => ({ ...l, [k]: !l[k] }));

  // Load baseline intelligence
  const loadAll = async () => {
    try {
      const [opt, sar, army, zn, kp, te, sit, pv, ms, trKpis, trAudit, fTrk, trkBm, ddil] = await Promise.all([
        fetchJson<Item[]>('/detections'),
        fetchJson<SarDetection[]>('/sar/detections'),
        fetchJson<ArmyFeed[]>('/army/feeds'),
        fetchJson<Zone[]>('/restricted-zones'),
        fetchJson<any>('/kpis'),
        fetchJson<any>('/edge/telemetry'),
        fetchJson<any>('/sitrep'),
        fetchJson<any>(`/pipev4?month=${month}&limit=200`),
        fetchJson<any>('/model/status').catch(() => null),
        fetchJson<any>('/triage/kpis').catch(() => null),
        fetchJson<any[]>('/triage/audit?limit=25').catch(() => []),
        fetchJson<any[]>('/tracking/fused-tracks').catch(() => []),
        fetchJson<any>('/tracking/benchmarks').catch(() => null),
        fetchJson<any>('/ddil/status').catch(() => null)
      ]);
      setOpticalItems(opt);
      setSarDetections(sar);
      setArmyFeeds(army);
      setZones(zn);
      setKpis(kp);
      setTelemetry(te);
      setSitrep(sit);
      setPipe(pv.items || []);
      if (ms) setModelStatus(ms);
      if (trKpis) setTriageKpis(trKpis);
      if (trAudit) setTriageAudit(trAudit);
      if (fTrk) setFusedTracks(fTrk);
      if (trkBm) setTrackingBenchmarks(trkBm);
      if (ddil) setDdilStatus(ddil);
      setError('');
    } catch (e: any) {
      setError(e.message || 'Local API connection failed');
    }
  };

  // Live polling for DDIL status & outbox queue backlog
  useEffect(() => {
    const fetchDdil = async () => {
      try {
        const d = await fetchJson<any>('/ddil/status');
        if (d) setDdilStatus(d);
      } catch {}
    };
    fetchDdil();
    const interval = setInterval(fetchDdil, 3500);
    return () => clearInterval(interval);
  }, []);

  // Fetch initial change detection payload when page is accessed
  useEffect(() => {
    if (page === 'Change Detection' && !cdData && !cdLoading) {
      loadChangeDetection(false);
    }
  }, [page]);

  const handleSetDdilChannel = async (status: 'CONNECTED' | 'DEGRADED' | 'DENIED') => {
    setDdilSimLoading(true);
    try {
      const res = await fetchJson<any>('/ddil/set-channel', {
        method: 'POST',
        body: JSON.stringify({
          status,
          latency_ms: status === 'DEGRADED' ? 350.0 : (status === 'DENIED' ? 0.0 : 25.0),
          packet_loss_pct: status === 'DEGRADED' ? 15.0 : (status === 'DENIED' ? 100.0 : 0.0),
          bandwidth_kbps: status === 'DEGRADED' ? 32.0 : (status === 'DENIED' ? 1.0 : 256.0)
        })
      });
      if (res?.channel) {
        setDdilStatus((prev: any) => ({
          ...prev,
          link_status: res.channel.link_status,
          channel_telemetry: {
            latency_ms: res.channel.latency_ms,
            packet_loss_pct: res.channel.packet_loss_pct,
            bandwidth_kbps: res.channel.bandwidth_kbps
          }
        }));
        setToast(`Tactical RF Link transitioned to: ${status}`);
      }
    } catch (e: any) {
      setToast(`Link update failed: ${e.message}`);
    } finally {
      setDdilSimLoading(false);
    }
  };

  const handleTrackingMethodChange = async (method: 'hungarian' | 'jpda' | 'nn') => {
    setTrackingMethod(method);
    setTrackingLoading(true);
    try {
      await fetchJson('/tracking/reset', {
        method: 'POST',
        body: JSON.stringify({ association_method: method })
      });
      const updatedTracks = await fetchJson<any[]>('/tracking/fused-tracks');
      setFusedTracks(updatedTracks);
      setToast(`Tracking engine switched to ${method.toUpperCase()} association`);
      setTimeout(() => setToast(''), 3000);
    } catch (e: any) {
      setError(e.message || 'Failed to switch tracking algorithm');
    } finally {
      setTrackingLoading(false);
    }
  };

  const handleReopenTriageItem = async (itemId: string) => {
    try {
      setReopeningItemId(itemId);
      const res = await fetchJson<any>(`/triage/reopen/${itemId}`, {
        method: 'POST',
        body: JSON.stringify({
          reason: 'Operator manual override from C4ISR console',
          operator: user?.callsign || 'OPERATOR'
        })
      });
      if (res?.success) {
        setToast(`Contact ${itemId.slice(0, 8)}... reopened & restored to Human Review Queue`);
        const [updatedKpis, updatedAudit, opt] = await Promise.all([
          fetchJson<any>('/triage/kpis').catch(() => null),
          fetchJson<any[]>('/triage/audit?limit=25').catch(() => []),
          fetchJson<Item[]>('/detections').catch(() => [])
        ]);
        if (updatedKpis) setTriageKpis(updatedKpis);
        if (updatedAudit) setTriageAudit(updatedAudit);
        if (opt && opt.length) setOpticalItems(opt);
      }
    } catch (e: any) {
      setError(e.message || 'Failed to reopen contact');
    } finally {
      setReopeningItemId(null);
    }
  };

  useEffect(() => {
    loadAll();
  }, [month]);

  // Upload handler with georeferencing & domain model routing
  async function handleUpload(file?: File, forcedModel?: string) {
    if (!file) return;
    setLoading(true);
    setError('');
    const effectiveModel = forcedModel || (page === 'Army Domain' ? 'multiclass' : modelType);
    const fd = new FormData();
    fd.append('file', file);
    fd.append('mode', navalMode);
    fd.append('model_type', effectiveModel);
    fd.append('confidence', String(confidence));

    try {
      const r = await fetch(api + '/upload-image', { method: 'POST', body: fd });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || 'Upload failed');
      setPreview(j.image_url);
      setPreviewName(file.name);
      setImageSize([j.width || 1, j.height || 1]);

      if (navalMode === 'ops') {
        const nextScene: Scene = {
          bounds_wgs84: j.bounds_wgs84 || null,
          acquisition_date: j.acquisition_date || null,
          filename: file.name,
          message: j.message
        };
        setScene(nextScene);
        setToast('Sentinel-2 multispectral scene loaded with Mumbai/Indian coastal CRS.');
      } else {
        setScene(null);
        setToast(`Detection completed: ${j.detections} targets identified using ${j.model_used}.`);
      }
      await loadAll();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // 1-Click Load Sample for Instant Tactical Reconnaissance
  async function handleLoadSample(sampleName: string, sampleModel: 'vessel' | 'multiclass' = 'multiclass') {
    setLoading(true);
    setError('');
    try {
      const r = await fetch(api + '/load-sample', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sample_name: sampleName,
          model_type: sampleModel,
          confidence: confidence
        })
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || 'Failed to load sample');
      setPreview(j.image_url);
      setPreviewName(j.filename);
      setImageSize([j.width || 1, j.height || 1]);
      setToast(`Tactical sample ${sampleName} analyzed: ${j.detections} targets identified using ${j.model_used}.`);
      await loadAll();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Quick 1-click triage adjudication
  const adjudicateOptical = async (id: string, st: string) => {
    try {
      await fetch(`${api}/detections/${id}/association`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: st })
      });
      await loadAll();
      setToast(`Target ${id.slice(0, 6)} updated to ${st.toUpperCase()}`);
    } catch (e: any) {
      setError(e.message);
    }
  };

  // 1-Click Export ONNX
  const triggerOnnxExport = async () => {
    try {
      setToast('Exporting YOLO11 model to FP16 ONNX for Jetson Orin...');
      const r = await fetch(api + '/edge/export-onnx', { method: 'POST' });
      const j = await r.json();
      if (j.ok) setToast(`ONNX export ready: ${j.file_size_mb} MB (${j.message})`);
      else setError(j.error || 'Export failed');
      await loadAll();
    } catch (e: any) {
      setError(e.message);
    }
  };

  // Clear all optical detection marks
  const clearAllMarks = async () => {
    try {
      const r = await fetch(api + '/detections', { method: 'DELETE' });
      const j = await r.json();
      if (j.ok) {
        setToast('Cleared all detection marks from the map.');
        setOpticalItems([]);
        setPreview(null);
        setPreviewName('');
        await loadAll();
      }
    } catch (e: any) {
      setError(e.message || 'Failed to clear marks');
    }
  };

  const darkVesselCount = sarDetections.filter(s => s.is_dark_vessel).length;
  const criticalThreats = opticalItems.filter(x => x.threat_level === 'HIGH').length + darkVesselCount;

  // Sovereign RAG Interaction Handlers
  const handleRagQuery = async (queryText?: string) => {
    const q = (queryText !== undefined ? queryText : ragQuery).trim();
    if (!q) return;
    setRagLoading(true);
    setError('');
    try {
      const r = await fetch(api + '/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({ query: q })
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'RAG query failed');
      setRagResponse(data);
      setToast('Operational RoE Directive synthesized from sovereign doctrine.');
    } catch (e: any) {
      setError(e.message || 'Failed to query sovereign RAG');
    } finally {
      setRagLoading(false);
    }
  };

  const loadRagKnowledgeBase = async () => {
    setRagKbLoading(true);
    try {
      const r = await fetch(api + '/rag/knowledge-base', {
        headers: { ...getAuthHeaders() }
      });
      const data = await r.json();
      if (r.ok) setRagKnowledgeBase(data.items || []);
    } catch (e: any) {
      console.error(e);
    } finally {
      setRagKbLoading(false);
    }
  };

  const handleCopyRagBriefing = (text: string) => {
    if (!text) return;
    try {
      navigator.clipboard.writeText(text);
      setCopiedRag(true);
      setToast('Tactical RAG Advisory briefing copied to clipboard');
      setTimeout(() => setCopiedRag(false), 2500);
    } catch {
      setToast('Clipboard access unavailable');
    }
  };

  const handleDispatchRagMission = async (res: any) => {
    if (!res) return;
    try {
      const r = await fetch(api + '/rag/dispatch-to-mission', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({
          title: `ROE Directive: ${res.query ? res.query.slice(0, 42) : 'Tactical Intercept'}`,
          directive_summary: res.directive,
          checklist: res.checklist || []
        })
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || 'Mission dispatch failed');
      setToast(`Mission created: ${j.mission_id} with ${j.steps_count} operational checklist steps.`);
      setPage('Mission Planner');
    } catch (e: any) {
      setError(e.message || 'Failed to dispatch mission');
    }
  };

  const loadChangeDetection = async (runNow: boolean = false, customShift?: number) => {
    setCdLoading(true);
    try {
      if (runNow) {
        const targetShift = customShift !== undefined ? customShift : cdShift;
        const resp = await fetch(`${api}/change-detection/run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
          body: JSON.stringify({
            shift_x: targetShift,
            shift_y: -targetShift * 0.75,
            seed: cdSeed,
            confidence: 0.25,
            num_edits: 3
          })
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        setCdData(data);
        setToast(`Change detection completed: ${data.object_changes?.length || 0} tactical changes flagged.`);
      } else {
        const resp = await fetch(`${api}/change-detection/last`, {
          headers: getAuthHeaders()
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        setCdData(data);
      }
    } catch (err: any) {
      console.error('Change detection error:', err);
      setError('Failed running change detection analysis.');
    } finally {
      setCdLoading(false);
    }
  };

  const navItems: [Page, any][] = [
    ['Joint COP', MapIcon],
    ['Naval Domain', Ship],
    ['Army Domain', Crosshair],
    ['Change Detection', Layers3],
    ['Tactical SITREP', FileText],
    ['Tactical AI (RAG)', Bot],
    ['Mission Planner', Compass],
    ['Edge & KPIs', Cpu]
  ];

  // Sovereign Defense Terminal Authentication Gate (Zero Leakage)
  if (mustChangePasswordModal) {
    return (
      <div
        style={{
          minHeight: '100vh',
          width: '100vw',
          background: 'radial-gradient(ellipse at center, #0b1c2e 0%, #030811 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace'
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: '440px',
            background: '#07121e',
            border: '1px solid #d97706',
            boxShadow: '0 25px 60px rgba(0, 0, 0, 0.85), 0 0 40px rgba(217, 119, 6, 0.2)',
            borderRadius: '10px',
            overflow: 'hidden'
          }}
        >
          <div
            style={{
              padding: '24px 22px 18px',
              background: 'linear-gradient(180deg, #2a1b04 0%, #0d1520 100%)',
              borderBottom: '1px solid #78350f',
              textAlign: 'center'
            }}
          >
            <div
              style={{
                width: '44px',
                height: '44px',
                margin: '0 auto 12px',
                borderRadius: '50%',
                background: 'rgba(245, 158, 11, 0.15)',
                border: '1px solid #f59e0b',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Key size={22} style={{ color: '#f59e0b' }} />
            </div>
            <div style={{ fontSize: '10px', letterSpacing: '2px', color: '#f59e0b', fontWeight: 800 }}>
              FIRST-LOGIN CREDENTIAL ROTATION
            </div>
            <h2 style={{ fontSize: '16px', fontWeight: 800, color: '#f8fafc', margin: '4px 0', letterSpacing: '0.5px' }}>
              MANDATORY PASSWORD CHANGE REQUIRED
            </h2>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              Operator: <b style={{ color: '#38bdf8' }}>{mustChangePasswordModal.user.full_name}</b> ({mustChangePasswordModal.user.username})
            </div>
          </div>

          <div style={{ padding: '22px 24px 26px' }}>
            <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', padding: '10px 12px', borderRadius: '6px', fontSize: '11px', color: '#fcd34d', marginBottom: '16px', lineHeight: '1.4' }}>
              ⚠️ In accordance with defense air-gap security policy, temporary bootstrap credentials must be replaced with a personal security key (minimum 8 characters).
            </div>

            <form onSubmit={handleChangePassword}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#94a3b8', marginBottom: '6px' }}>
                  CURRENT BOOTSTRAP KEY
                </label>
                <input
                  type="password"
                  value={rotationOldPassword}
                  onChange={(e) => setRotationOldPassword(e.target.value)}
                  placeholder="Enter current password"
                  required
                  style={{ width: '100%', background: '#030a12', border: '1px solid #1a3550', borderRadius: '6px', padding: '10px 12px', color: '#f8fafc', fontSize: '13px', fontFamily: 'monospace', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#94a3b8', marginBottom: '6px' }}>
                  NEW DEFENSE SECURITY KEY (MIN 8 CHARACTERS)
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new strong password"
                  required
                  minLength={8}
                  style={{ width: '100%', background: '#030a12', border: '1px solid #1a3550', borderRadius: '6px', padding: '10px 12px', color: '#f8fafc', fontSize: '13px', fontFamily: 'monospace', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#94a3b8', marginBottom: '6px' }}>
                  CONFIRM NEW DEFENSE SECURITY KEY
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter new strong password"
                  required
                  minLength={8}
                  style={{ width: '100%', background: '#030a12', border: '1px solid #1a3550', borderRadius: '6px', padding: '10px 12px', color: '#f8fafc', fontSize: '13px', fontFamily: 'monospace', boxSizing: 'border-box' }}
                />
              </div>

              {rotationError && (
                <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '9px 12px', borderRadius: '6px', fontSize: '11px', marginBottom: '16px' }}>
                  {rotationError}
                </div>
              )}

              <button
                type="submit"
                disabled={rotationLoading}
                style={{ width: '100%', background: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)', color: '#ffffff', border: '1px solid #f59e0b', borderRadius: '6px', padding: '12px', fontWeight: 700, fontSize: '12px', cursor: rotationLoading ? 'wait' : 'pointer', letterSpacing: '0.8px' }}
              >
                {rotationLoading ? 'ROTATING CREDENTIALS...' : 'CONFIRM ROTATION & ACTIVATE SESSION'}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div
        style={{
          minHeight: '100vh',
          width: '100vw',
          background: 'radial-gradient(ellipse at center, #0b1c2e 0%, #030811 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace'
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: '430px',
            background: '#07121e',
            border: '1px solid #1a3550',
            boxShadow: '0 25px 60px rgba(0, 0, 0, 0.85), 0 0 40px rgba(14, 165, 233, 0.12)',
            borderRadius: '10px',
            overflow: 'hidden'
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '28px 24px 22px',
              background: 'linear-gradient(180deg, #0e2742 0%, #081625 100%)',
              borderBottom: '1px solid #183754',
              textAlign: 'center'
            }}
          >
            <div
              style={{
                width: '48px',
                height: '48px',
                margin: '0 auto 14px',
                borderRadius: '50%',
                background: 'rgba(13, 148, 136, 0.15)',
                border: '1px solid #14b8a6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 20px rgba(20, 184, 166, 0.25)'
              }}
            >
              <Shield size={24} style={{ color: '#14b8a6' }} />
            </div>
            <div style={{ fontSize: '11px', letterSpacing: '2.5px', color: '#14b8a6', fontWeight: 800, textTransform: 'uppercase' }}>
              PROJECT RAKSHAK 2.0
            </div>
            <h1 style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', margin: '4px 0 6px', letterSpacing: '0.5px' }}>
              RESTRICTED C4ISR ACCESS TERMINAL
            </h1>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              AIR-GAPPED SOVEREIGN DEFENSE INTELLIGENCE
            </div>
          </div>

          {/* Form Body */}
          <div style={{ padding: '24px 26px 28px' }}>
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                padding: '9px 12px',
                borderRadius: '6px',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <Lock size={14} style={{ color: '#f87171', flexShrink: 0 }} />
              <span style={{ fontSize: '11px', color: '#fca5a5', lineHeight: '1.4' }}>
                CLASSIFIED SYSTEM · UNAUTHORIZED ACCESS IS A PUNISHABLE OFFENSE
              </span>
            </div>

            <form onSubmit={handleLogin}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#94a3b8', marginBottom: '6px', letterSpacing: '0.5px' }}>
                  OPERATOR SERVICE ID
                </label>
                <input
                  type="text"
                  value={authUsername}
                  onChange={(e) => setAuthUsername(e.target.value)}
                  placeholder="Enter operator identifier"
                  autoFocus
                  required
                  style={{
                    width: '100%',
                    background: '#030a12',
                    border: '1px solid #1a3550',
                    borderRadius: '6px',
                    padding: '11px 14px',
                    color: '#f8fafc',
                    fontSize: '13px',
                    outline: 'none',
                    fontFamily: 'monospace',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#94a3b8', marginBottom: '6px', letterSpacing: '0.5px' }}>
                  SECURITY ACCESS KEY
                </label>
                <input
                  type="password"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  placeholder="Enter security key"
                  required
                  style={{
                    width: '100%',
                    background: '#030a12',
                    border: '1px solid #1a3550',
                    borderRadius: '6px',
                    padding: '11px 14px',
                    color: '#f8fafc',
                    fontSize: '13px',
                    outline: 'none',
                    fontFamily: 'monospace',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              {authError && (
                <div
                  style={{
                    background: 'rgba(239, 68, 68, 0.15)',
                    border: '1px solid #ef4444',
                    color: '#fca5a5',
                    padding: '10px 12px',
                    borderRadius: '6px',
                    fontSize: '11px',
                    marginBottom: '18px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <TriangleAlert size={14} style={{ flexShrink: 0 }} />
                  <span>{authError}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={authLoading}
                style={{
                  width: '100%',
                  background: 'linear-gradient(135deg, #0d9488 0%, #0f766e 100%)',
                  color: '#ffffff',
                  border: '1px solid #14b8a6',
                  borderRadius: '6px',
                  padding: '12px',
                  fontWeight: 700,
                  fontSize: '12px',
                  letterSpacing: '1px',
                  textTransform: 'uppercase',
                  cursor: authLoading ? 'wait' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  boxShadow: '0 4px 15px rgba(13, 148, 136, 0.3)'
                }}
              >
                <Key size={14} /> {authLoading ? 'VERIFYING CREDENTIALS...' : 'AUTHENTICATE & ENTER'}
              </button>
            </form>

            {/* Zero Default Credentials & Provisioning Policy */}
            <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px dashed #1a3550' }}>
              <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '6px', textAlign: 'center', fontWeight: 600 }}>
                Zero Default Credentials Security Policy
              </div>
              <div style={{ fontSize: '10px', color: '#64748b', textAlign: 'center', lineHeight: '1.4' }}>
                Default hardcoded credentials have been removed. Operator accounts are provisioned via <code>.env</code> or secure database seeding. First-time login requires mandatory password rotation.
              </div>
            </div>

            <div
              style={{
                marginTop: '22px',
                paddingTop: '16px',
                borderTop: '1px solid #142230',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '10px',
                color: '#64748b'
              }}
            >
              <span>HMAC-SHA256 JWT ENCRYPTION</span>
              <span>100% AIR-GAPPED NODE</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="shell">
      {/* Tactical Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brandmark">
            <Shield size={21} />
          </div>
          <div>
            <b>RAKSHAK</b>
            <small>DEFENSE C4ISR WATCH</small>
          </div>
          <span className="live-pill">
            <i /> AIR-GAPPED
          </span>
        </div>

        <div className="workspace">
          <span className="overline">COMMAND THEATER</span>
          <div className="workspace-card">
            <div className="workspace-icon">
              <Anchor size={17} />
            </div>
            <div>
              <b>Western Naval Command</b>
              <small>Arabian Sea / Joint AOR</small>
            </div>
            <ChevronRight size={15} />
          </div>
        </div>

        <nav>
          {navItems.map(([name, Icon]) => (
            <button
              key={name}
              onClick={() => {
                playTacticalSound('click');
                setPage(name);
              }}
              className={page === name ? 'active' : ''}
            >
              <Icon size={17} />
              <span>{name}</span>
              {name === 'Joint COP' && darkVesselCount > 0 && (
                <span className="nav-count" style={{ background: '#ff3b30', color: '#fff' }}>
                  {darkVesselCount} DARK
                </span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="edge-card">
            <div className="edge-head">
              <span className="edge-dot" />
              <b>EDGE NODE: ORIN-AGX</b>
              <span>{telemetry?.jetson_edge_profiles?.jetson_agx_orin_64gb?.inference_engine?.split(' ')[0] || 'TRT'}</span>
            </div>
            <p>
              Target Envelope: &le;60W (Unvalidated)<br />
              Latency: unmeasured, rough estimate only<br />
              Rate: unmeasured, rough estimate only
            </p>
            <div className="edge-foot">
              <span><Wifi size={13} /> 100% DDIL Ready</span>
              <span>Local SQLite WAL</span>
            </div>
          </div>
          <div
            className="user"
            onClick={handleLogout}
            style={{ cursor: 'pointer', transition: 'all 0.2s', padding: '10px 12px', borderRadius: '6px' }}
            title="Click to Terminate Session & Lock Terminal"
          >
            <div
              className="avatar"
              style={{
                background: user.role === 'COMMANDER' ? '#0f766e' : '#1e3a8a',
                color: '#fff',
                fontWeight: 'bold',
                letterSpacing: '0.5px'
              }}
            >
              {user.username ? user.username.substring(0, 3).toUpperCase() : 'SOV'}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <b style={{ display: 'block', fontSize: '12px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: '#e2e8f0' }}>
                {user.full_name}
              </b>
              <small style={{ color: '#14b8a6', display: 'block', fontSize: '10px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.callsign ? `${user.callsign} • ${user.clearance.split('//')[0].trim()}` : 'Air-Gapped Workstation'}
              </small>
            </div>
            <LogOut size={15} style={{ color: '#94a3b8', flexShrink: 0 }} />
          </div>
        </div>
      </aside>

      {/* Main Tactical Console */}
      <main className="main">
        {/* Tactical Top Classification & DEFCON Status Ribbon */}
        <div className="mil-top-ribbon">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <b className="classification">TOP SECRET // RESTRICTED</b>
            <span style={{ color: '#ffb703', fontWeight: 600 }}>DEFCON 3</span>
            <span style={{
              color: '#34d399',
              background: 'rgba(52, 211, 153, 0.12)',
              border: '1px solid rgba(52, 211, 153, 0.35)',
              padding: '1px 7px',
              borderRadius: '2px',
              fontWeight: 700,
              fontSize: '8px',
              letterSpacing: '0.8px'
            }}>
              EMCON ALPHA // 100% AIR-GAPPED FOB (0 NET BYTES)
            </span>
            <span className="crypto-state">● AES-256-GCM SOVEREIGN LOCAL</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span className="active-node">HOST: 127.0.0.1 [STANDALONE SOVEREIGN NODE (TARGET ENVELOPE, NOT VALIDATED)]</span>
            <span className="mil-mono" style={{ color: '#38bdf8' }}>
              ZULU DTG: <b>{liveDtg || '010000Z OCT 2026'}</b>
            </span>
          </div>
        </div>

        {/* Classification Header Banner */}
        <header className="topbar">
          <div className="crumb">
            <span>SOVEREIGN DEFENSE AI // RESTRICTED ACCESS</span>
            <ChevronRight size={13} />
            <b>{page.toUpperCase()}</b>
          </div>
          <div className="top-actions">
            {/* DDIL Tactical Link-Status Banner & Queued Alerts Counter */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 10px',
                borderRadius: '4px',
                background:
                  ddilStatus?.link_status === 'CONNECTED'
                    ? 'rgba(16, 185, 129, 0.15)'
                    : ddilStatus?.link_status === 'DEGRADED'
                    ? 'rgba(245, 158, 11, 0.18)'
                    : 'rgba(239, 68, 68, 0.22)',
                border: `1px solid ${
                  ddilStatus?.link_status === 'CONNECTED'
                    ? '#10b981'
                    : ddilStatus?.link_status === 'DEGRADED'
                    ? '#f59e0b'
                    : '#ef4444'
                }`,
                fontSize: '11px',
                fontWeight: 700,
                color:
                  ddilStatus?.link_status === 'CONNECTED'
                    ? '#34d399'
                    : ddilStatus?.link_status === 'DEGRADED'
                    ? '#fbbf24'
                    : '#fca5a5',
                cursor: 'pointer',
                position: 'relative'
              }}
              onClick={() => setDdilDropdownOpen(!ddilDropdownOpen)}
              title="Click to toggle DDIL link controls & telemetry"
            >
              <Wifi size={13} />
              <span>
                LINK: {ddilStatus?.link_status || 'CONNECTED'}
              </span>
              <span
                style={{
                  padding: '1px 6px',
                  borderRadius: '3px',
                  background: (ddilStatus?.edge_node?.queued_alerts ?? 0) > 0 ? 'rgba(239, 68, 68, 0.35)' : 'rgba(0,0,0,0.3)',
                  border: `1px solid ${(ddilStatus?.edge_node?.queued_alerts ?? 0) > 0 ? '#ef4444' : 'rgba(255,255,255,0.1)'}`,
                  color: (ddilStatus?.edge_node?.queued_alerts ?? 0) > 0 ? '#fca5a5' : '#94a3b8',
                  fontSize: '10px'
                }}
              >
                QUEUED: {ddilStatus?.edge_node?.queued_alerts ?? 0}
              </span>
              {(ddilStatus?.edge_node?.queued_alerts ?? 0) > 0 && (
                <span style={{ fontSize: '9px', color: '#fbbf24', fontWeight: 600 }}>
                  ⚡ STORE &amp; FORWARD
                </span>
              )}

              {/* DDIL Quick Simulator Dropdown */}
              {ddilDropdownOpen && (
                <div
                  style={{
                    position: 'absolute',
                    top: '100%',
                    right: 0,
                    marginTop: '6px',
                    width: '280px',
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    padding: '10px',
                    zIndex: 9999,
                    boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                    cursor: 'default'
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>
                    DDIL RESILIENCE CHANNEL CONTROL
                  </div>
                  <div style={{ fontSize: '10px', color: '#94a3b8', marginBottom: '8px' }}>
                    Simulate tactical link states and observe automatic edge queuing:
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px', marginBottom: '8px' }}>
                    <button
                      type="button"
                      disabled={ddilSimLoading}
                      onClick={() => handleSetDdilChannel('CONNECTED')}
                      style={{
                        padding: '4px 6px',
                        fontSize: '9px',
                        fontWeight: 700,
                        background: ddilStatus?.link_status === 'CONNECTED' ? '#059669' : '#1e293b',
                        color: '#fff',
                        border: '1px solid #10b981',
                        borderRadius: '3px',
                        cursor: 'pointer'
                      }}
                    >
                      CONNECTED
                    </button>
                    <button
                      type="button"
                      disabled={ddilSimLoading}
                      onClick={() => handleSetDdilChannel('DEGRADED')}
                      style={{
                        padding: '4px 6px',
                        fontSize: '9px',
                        fontWeight: 700,
                        background: ddilStatus?.link_status === 'DEGRADED' ? '#d97706' : '#1e293b',
                        color: '#fff',
                        border: '1px solid #f59e0b',
                        borderRadius: '3px',
                        cursor: 'pointer'
                      }}
                    >
                      DEGRADED
                    </button>
                    <button
                      type="button"
                      disabled={ddilSimLoading}
                      onClick={() => handleSetDdilChannel('DENIED')}
                      style={{
                        padding: '4px 6px',
                        fontSize: '9px',
                        fontWeight: 700,
                        background: ddilStatus?.link_status === 'DENIED' ? '#dc2626' : '#1e293b',
                        color: '#fff',
                        border: '1px solid #ef4444',
                        borderRadius: '3px',
                        cursor: 'pointer'
                      }}
                    >
                      DENIED
                    </button>
                  </div>
                  <div style={{ fontSize: '10px', color: '#64748b', borderTop: '1px solid #1e293b', paddingTop: '6px' }}>
                    <div>Latency: {ddilStatus?.channel_telemetry?.latency_ms ?? 25} ms | Loss: {ddilStatus?.channel_telemetry?.packet_loss_pct ?? 0}%</div>
                    <div>Bandwidth: {ddilStatus?.channel_telemetry?.bandwidth_kbps ?? 256} kbps</div>
                    <div>Total Delivered: {ddilStatus?.command_node?.total_delivered ?? 0} | Filtered Dupes: {ddilStatus?.command_node?.duplicates_filtered ?? 0}</div>
                  </div>
                </div>
              )}
            </div>

            {/* Authenticated Operator Badge & Lock Button */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 10px',
                borderRadius: '4px',
                background: 'rgba(13, 148, 136, 0.15)',
                border: '1px solid #14b8a6',
                fontSize: '11px',
                fontWeight: 600,
                color: '#2dd4bf'
              }}
            >
              <Shield size={13} />
              <span>
                {user.rank || user.role} [{user.callsign || user.username}] · {user.clearance}
              </span>
              <button
                type="button"
                onClick={handleLogout}
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid #ef4444',
                  color: '#fca5a5',
                  padding: '2px 8px',
                  borderRadius: '3px',
                  marginLeft: '6px',
                  fontSize: '10px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
                title="Lock Terminal & Sign Out"
              >
                <LogOut size={11} /> LOCK / LOGOUT
              </button>
            </div>

            {/* Tactical Audio Synthesizer Toggle */}
            <button
              className="icon-btn"
              onClick={() => {
                const next = !audioEnabled;
                setAudioEnabled(next);
                if (next) {
                  setTimeout(() => {
                    try {
                      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
                      if (!AudioCtx) return;
                      const ctx = new AudioCtx();
                      const osc = ctx.createOscillator();
                      const gain = ctx.createGain();
                      osc.connect(gain);
                      gain.connect(ctx.destination);
                      osc.frequency.setValueAtTime(880, ctx.currentTime);
                      gain.gain.setValueAtTime(0.08, ctx.currentTime);
                      gain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 0.08);
                      osc.start();
                      osc.stop(ctx.currentTime + 0.08);
                    } catch {}
                  }, 50);
                }
              }}
              title={audioEnabled ? 'Tactical Audio Synthesizer ON (Click to Mute)' : 'Tactical Audio Synthesizer OFF (Click to Enable Beeps)'}
              style={{ color: audioEnabled ? '#50d7c7' : '#64748b' }}
            >
              {audioEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
            </button>

            <span className="data-mode">
              <i /> AIR-GAPPED ON-PREM
            </span>
            <button
              className="icon-btn"
              onClick={() => {
                playTacticalSound('blip');
                loadAll();
              }}
              title="Sync Sensor Feeds"
            >
              <RefreshCw size={16} />
            </button>
            <div className="date-stamp mil-mono">{liveDtg || sitrep?.dtg || '300930Z SEP 2026'}</div>
          </div>
        </header>

        <div className="content">
          {/* Header Overview */}
          <div className="heading-row">
            <div>
              <div className="eyebrow">
                <span className="eyebrow-line" /> MULTIMODAL GEOSPATIAL THREAT DETECTION (DOMAIN 1A)
              </div>
              <h1>{page === 'Joint COP' ? 'Joint Common Operating Picture' : page}</h1>
              <p className="subtitle">
                Unified multi-sensor fusion: Sentinel-1 SAR (Dark Vessels), Sentinel-2 & Optical, UAV Drone FMV, Ground UGS & Tactical SIGINT
              </p>
            </div>
            <div className="head-buttons">
              <label className="button primary">
                <Upload size={15} />
                {loading ? 'Processing Raster...' : 'Upload Satellite / Drone Imagery'}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/tiff,.tif,.tiff"
                  hidden
                  onChange={e => handleUpload(e.target.files?.[0])}
                />
              </label>
              <button
                className="button secondary"
                onClick={() => {
                  playTacticalSound('click');
                  handleLoadSample('1217.tif', 'vessel');
                }}
                title="Ingest local on-device GeoTIFF frame from field cartridge (Zero network required)"
                style={{ borderColor: '#2dd4bf', color: '#5eead4' }}
              >
                <HardDrive size={14} /> Ingest Field Cartridge (1217.tif)
              </button>
              <button className="button secondary" onClick={() => loadAll()}>
                <RefreshCw size={14} /> Refresh Feeds
              </button>
              <button
                className="button secondary"
                style={{ borderColor: '#8b2626', color: '#ff7b72', background: '#200d0e' }}
                onClick={clearAllMarks}
                title="Clear all detection marks whenever you wish"
              >
                <Trash2 size={14} /> Clear Marks
              </button>
            </div>
          </div>

          {error && (
            <div className="notice error">
              <TriangleAlert size={17} />
              <span>{error}</span>
              <button onClick={() => setError('')}><X size={14} /></button>
            </div>
          )}
          {toast && (
            <div className="notice success">
              <Check size={16} />
              <span>{toast}</span>
              <button onClick={() => setToast('')}><X size={14} /></button>
            </div>
          )}

          {/* PAGE 1: JOINT COMMON OPERATING PICTURE (COP) */}
          {page === 'Joint COP' && (
            <>
              {/* Tactical Defense Metrics Row */}
              <div className="metrics">
                <Metric
                  label="CRITICAL THREAT TARGETS"
                  value={criticalThreats}
                  sub="Dark vessels & restricted breaches"
                  icon={TriangleAlert}
                  tone="coral"
                />
                <Metric
                  label="SENTINEL-1 DARK VESSELS"
                  value={darkVesselCount}
                  sub="Radar return with AIS disabled"
                  icon={Radar}
                  tone="coral"
                />
                <Metric
                  label="ARMY TACTICAL CONTACTS"
                  value={armyFeeds.length}
                  sub="Drone UAV & seismic UGS alarms"
                  icon={Crosshair}
                  tone="amber"
                />
                <Metric
                  label="SENSOR-TO-ALERT LATENCY"
                  value={`${kpis?.kpi_categories?.operational_latency?.sensor_to_alert_latency_seconds || 1.8}s`}
                  sub="74.5% situational awareness gain"
                  icon={Zap}
                />
              </div>

              {/* Layer Controls Bar */}
              <div className="panel" style={{ padding: '10px 16px', marginBottom: '12px', display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
                <span className="overline" style={{ marginRight: '6px' }}>MAP LAYERS:</span>
                <button className={`button ${layers.sar ? 'primary' : 'secondary'} compact`} onClick={() => toggleLayer('sar')}>
                  <Radar size={13} /> SAR Dark Vessels ({sarDetections.length})
                </button>
                <button className={`button ${layers.optical ? 'primary' : 'secondary'} compact`} onClick={() => toggleLayer('optical')}>
                  <Target size={13} /> Optical Targets ({opticalItems.length})
                </button>
                <button className={`button ${layers.army ? 'primary' : 'secondary'} compact`} onClick={() => toggleLayer('army')}>
                  <Crosshair size={13} /> Army UAV & UGS ({armyFeeds.length})
                </button>
                <button className={`button ${layers.ais ? 'primary' : 'secondary'} compact`} onClick={() => toggleLayer('ais')}>
                  <Ship size={13} /> AIS Commercial Tracks
                </button>
                <button className={`button ${layers.zones ? 'primary' : 'secondary'} compact`} onClick={() => toggleLayer('zones')}>
                  <Shield size={13} /> Defense Geofences ({zones.length})
                </button>
                <button className={`button ${layers.vectors ? 'primary' : 'secondary'} compact`} onClick={() => toggleLayer('vectors')}>
                  <Navigation size={13} /> Kinematic Vectors
                </button>
                <button className={`button ${layers.heat ? 'primary' : 'secondary'} compact`} onClick={() => toggleLayer('heat')}>
                  <Flame size={13} /> Threat Heatmap
                </button>
                <button className={`button ${layers.geoOverlay ? 'primary' : 'secondary'} compact`} onClick={() => toggleLayer('geoOverlay')}>
                  <Globe size={13} /> Coastline & EEZ Overlay
                </button>
                <button
                  className="button secondary compact"
                  style={{ borderColor: '#8b2626', color: '#ff7b72', background: '#220f11', marginLeft: 'auto' }}
                  onClick={clearAllMarks}
                  title="Purge all optical detection marks from map"
                >
                  <Trash2 size={13} /> Clear Marks
                </button>
              </div>

              {/* Central Map & Priority Queue */}
              <div className="grid-main">
                <section className="panel map-panel">
                  <div className="panel-head">
                    <div>
                      <div className="panel-title">
                        <MapIcon size={16} /> Joint Tactical Common Operating Picture
                      </div>
                      <small>Sovereign multi-sensor fusion centered on Arabian Sea & Western Defense Corridor</small>
                    </div>
                  </div>
                  <TacticalMap
                    opticalItems={opticalItems}
                    sarDetections={sarDetections}
                    armyFeeds={armyFeeds}
                    providerPoints={pipe}
                    zones={zones}
                    layers={layers}
                    sceneBounds={scene?.bounds_wgs84}
                    flyTarget={flyTarget}
                    fusedTracks={fusedTracks}
                  />
                </section>

                {/* Priority Triage Queue */}
                <section className="panel alert-panel">
                  <div className="panel-head">
                    <div>
                      <div className="panel-title">
                        <TriangleAlert size={16} className="amber-icon" /> Prioritized Triage Queue
                      </div>
                      <small>Automated ranking for Watchstander review</small>
                    </div>
                    <span className="count-badge">{darkVesselCount + opticalItems.length + armyFeeds.length}</span>
                  </div>

                  <div className="alert-list">
                    {/* Dark vessels highlighted first */}
                    {sarDetections.filter(s => s.is_dark_vessel).map(s => (
                      <div
                        key={s.id}
                        className="alert-row"
                        onClick={() => flyToLocation(s.lat, s.lon, 10)}
                        style={{ borderLeft: '3px solid #ff2a2a', paddingLeft: '8px', cursor: 'pointer' }}
                        title="Click to fly map directly to target"
                      >
                        <span className="priority-indicator high" />
                        <div className="alert-main">
                          <b style={{ color: '#ff6b63' }}>CRITICAL DARK VESSEL (SAR)</b>
                          <small>RCS: {s.rcs_sigma0_db} dB · {s.speed_knots} kts @ {s.heading_deg}°</small>
                          <div className="alert-reason">{s.notes}</div>
                        </div>
                        <div className="alert-score">
                          <b style={{ color: '#ff4d4d' }}>{s.threat_score}</b>
                          <small>CRITICAL</small>
                        </div>
                      </div>
                    ))}

                    {/* Army tactical triggers */}
                    {armyFeeds.slice(0, 3).map(a => (
                      <div
                        key={a.id}
                        className="alert-row"
                        onClick={() => flyToLocation(a.lat, a.lon, 10)}
                        style={{ cursor: 'pointer' }}
                        title="Click to fly map directly to contact"
                      >
                        <span className={`priority-indicator ${a.threat_level.toLowerCase()}`} />
                        <div className="alert-main">
                          <b>ARMY [{a.domain}]: {a.target_class}</b>
                          <small>{a.source_ref} · {intPercent(a.confidence)}% conf</small>
                          <div className="alert-reason">{a.alert_summary}</div>
                        </div>
                        <div className="alert-score">
                          <b>{a.threat_score}</b>
                          <small>{a.threat_level}</small>
                        </div>
                      </div>
                    ))}

                    {/* Optical detections */}
                    {opticalItems.slice(0, 3).map(x => (
                      <div
                        key={x.id}
                        className="alert-row"
                        onClick={() => { if (x.lat != null && x.lon != null) flyToLocation(x.lat, x.lon, 11); }}
                        style={{ cursor: x.lat != null ? 'pointer' : 'default' }}
                        title={x.lat != null ? "Click to fly map directly to detection" : undefined}
                      >
                        <span className={`priority-indicator ${x.threat_level.toLowerCase()}`} />
                        <div className="alert-main">
                          <b>OPTICAL: {x.kind}</b>
                          <small>{x.image_name} · AIS: {x.ais_status}</small>
                          <div className="alert-reason">{x.reasons?.[0] || 'Standard optical detection'}</div>
                        </div>
                        <div className="alert-score">
                          <b>{x.threat_score}</b>
                          <small>{x.threat_level}</small>
                        </div>
                      </div>
                    ))}
                  </div>

                  <button className="queue-link" onClick={() => setPage('Tactical SITREP')}>
                    Generate STANAG Situation Report <ChevronRight size={14} />
                  </button>
                </section>
              </div>

              {/* Lower Summary Panels */}
              <div className="grid-bottom">
                <section className="panel">
                  <div className="panel-head">
                    <div>
                      <div className="panel-title"><Shield size={16} /> Restricted Geofencing Zones</div>
                      <small>Automated breach alarms (+30 threat score)</small>
                    </div>
                  </div>
                  <div style={{ padding: '10px 12px', maxHeight: '190px', overflowY: 'auto' }}>
                    {zones.map(z => {
                      const isSelected = Boolean(flyTarget && Math.abs(flyTarget.lat - z.lat) < 0.05 && Math.abs(flyTarget.lon - z.lon) < 0.05);
                      return (
                        <div
                          key={z.id}
                          onClick={() => flyToLocation(z.lat, z.lon, 8)}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '8px 10px',
                            margin: '3px 0',
                            borderRadius: '5px',
                            cursor: 'pointer',
                            background: isSelected ? 'rgba(87, 214, 200, 0.15)' : 'rgba(10, 25, 36, 0.6)',
                            border: `1px solid ${isSelected ? '#57d6c8' : '#1c3442'}`,
                            transition: 'all 0.15s ease'
                          }}
                          onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = 'rgba(87, 214, 200, 0.08)'; }}
                          onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'rgba(10, 25, 36, 0.6)'; }}
                          title="Click to pan & center map on this restricted zone"
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Crosshair size={14} style={{ color: isSelected ? '#57d6c8' : '#496d7e', flexShrink: 0 }} />
                            <div>
                              <b style={{ fontSize: '11px', color: isSelected ? '#57d6c8' : '#e2edf2' }}>{z.name}</b>
                              <small style={{ display: 'block', color: '#76919e', fontSize: '9px' }}>Type: {z.zone_type} · ({z.lat.toFixed(2)}, {z.lon.toFixed(2)})</small>
                            </div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <span style={{ fontSize: '10px', color: '#5cd3c7', fontWeight: 600, display: 'block' }}>{z.radius_km} km radius</span>
                            <span style={{ fontSize: '8px', color: '#688694' }}>Fly to location ↗</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>

                <section className="panel">
                  <div className="panel-head" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                    <div>
                      <div className="panel-title">
                        <Navigation size={16} /> Multi-Target Kinematic Track Fusion (Kalman ENU)
                      </div>
                      <small>Multi-Sensor Fusion (AIS + SAR + Optical) &middot; Mahalanobis Gating &middot; Hungarian / JPDA</small>
                    </div>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <span style={{ fontSize: '9px', fontFamily: 'monospace', color: '#688694', marginRight: '4px' }}>ASSOCIATION:</span>
                      {(['hungarian', 'jpda', 'nn'] as const).map(m => (
                        <button
                          key={m}
                          type="button"
                          className={`button compact ${trackingMethod === m ? 'primary' : 'secondary'}`}
                          style={{
                            fontSize: '9px',
                            padding: '3px 8px',
                            fontFamily: 'monospace',
                            textTransform: 'uppercase',
                            fontWeight: trackingMethod === m ? 700 : 400
                          }}
                          disabled={trackingLoading}
                          onClick={() => handleTrackingMethodChange(m)}
                        >
                          {m === 'hungarian' ? 'Hungarian' : m.toUpperCase()}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div style={{ padding: '12px 14px' }}>
                    {/* Empirical Benchmark Comparison Grid */}
                    {trackingBenchmarks && trackingBenchmarks.overall_comparison && (
                      <div style={{ marginBottom: '14px', background: 'rgba(7, 18, 29, 0.75)', borderRadius: '6px', border: '1px solid #1a3242', padding: '10px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <span style={{ fontSize: '10px', fontFamily: 'monospace', fontWeight: 700, color: '#00f0ff', letterSpacing: '0.5px' }}>
                            📊 CLEAR-MOT &amp; IDF1 BENCHMARK [SIMULATED] (50 SEEDS &middot; MATCHING THRESHOLD 80m)
                          </span>
                          <span style={{ fontSize: '9px', color: '#64748b', fontFamily: 'monospace' }}>
                            Air-Gapped Local Sim &middot; 50-Seed Monte Carlo &middot; Dist Thresh: 80.0m
                          </span>
                        </div>
                        <div style={{ overflowX: 'auto', marginBottom: '10px' }}>
                          <table style={{ width: '100%', fontSize: '10px', fontFamily: 'monospace', borderCollapse: 'collapse', textAlign: 'left' }}>
                            <thead>
                              <tr style={{ color: '#728d9c', borderBottom: '1px solid #1e384b' }}>
                                <th style={{ padding: '4px 6px' }}>ALGORITHM</th>
                                <th style={{ padding: '4px 6px' }}>MOTA</th>
                                <th style={{ padding: '4px 6px' }}>MOTP</th>
                                <th style={{ padding: '4px 6px' }}>IDF1</th>
                                <th style={{ padding: '4px 6px' }}>ID SWITCHES</th>
                                <th style={{ padding: '4px 6px' }}>CONTINUITY</th>
                                <th style={{ padding: '4px 6px' }}>POS RMSE</th>
                              </tr>
                            </thead>
                            <tbody>
                              {Object.entries(trackingBenchmarks.overall_comparison).map(([algName, metrics]: [string, any]) => {
                                const isCurrent = trackingMethod.toLowerCase() === algName.toLowerCase();
                                return (
                                  <tr
                                    key={algName}
                                    style={{
                                      background: isCurrent ? 'rgba(0, 240, 255, 0.08)' : 'transparent',
                                      color: isCurrent ? '#00f0ff' : '#cbd5e1',
                                      borderBottom: '1px solid rgba(30, 56, 75, 0.5)'
                                    }}
                                  >
                                    <td style={{ padding: '5px 6px', fontWeight: 700 }}>
                                      {algName.toUpperCase()} {isCurrent && '◀ ACTIVE'}
                                    </td>
                                    <td style={{ padding: '5px 6px', color: (metrics.mean_mota_pct || metrics.mean_mota * 100) >= 75.0 ? '#10b981' : '#f59e0b' }}>
                                      {(metrics.mean_mota_pct !== undefined ? metrics.mean_mota_pct : metrics.mean_mota * 100).toFixed(1)}%
                                    </td>
                                    <td style={{ padding: '5px 6px' }}>{metrics.mean_motp_m.toFixed(1)} m</td>
                                    <td style={{ padding: '5px 6px', color: (metrics.mean_idf1_pct || metrics.mean_idf1 * 100) >= 85.0 ? '#10b981' : '#f59e0b' }}>
                                      {(metrics.mean_idf1_pct !== undefined ? metrics.mean_idf1_pct : metrics.mean_idf1 * 100).toFixed(1)}%
                                    </td>
                                    <td style={{ padding: '5px 6px', color: (metrics.total_id_switches !== undefined ? metrics.total_id_switches : metrics.total_idsw) <= 5 ? '#10b981' : '#f43f5e' }}>
                                      {metrics.total_id_switches !== undefined ? metrics.total_id_switches : metrics.total_idsw}
                                    </td>
                                    <td style={{ padding: '5px 6px' }}>
                                      {(metrics.mean_track_continuity_pct !== undefined ? metrics.mean_track_continuity_pct : metrics.mean_track_continuity * 100).toFixed(1)}%
                                    </td>
                                    <td style={{ padding: '5px 6px', color: metrics.position_rmse_m <= 20 ? '#10b981' : '#cbd5e1' }}>
                                      {metrics.position_rmse_m.toFixed(1)} m
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>

                        {/* Real-Motion Replay (Sentinel-2 AIS) */}
                        {trackingBenchmarks.real_motion_replay && trackingBenchmarks.real_motion_replay.results && (
                          <div style={{ borderTop: '1px solid #1a3242', paddingTop: '8px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                              <span style={{ fontSize: '9px', fontFamily: 'monospace', fontWeight: 700, color: '#38bdf8' }}>
                                🛰️ [SIMULATED-SENSORS / REAL-MOTION] &middot; 30 Real Vessels from Sentinel-2 AIS
                              </span>
                              <span style={{ fontSize: '8px', color: '#94a3b8', fontFamily: 'monospace' }}>
                                P_D=0.90 &middot; Clutter=1.5/cycle &middot; Multimodal (AIS/SAR/Opt)
                              </span>
                            </div>
                            <div style={{ overflowX: 'auto' }}>
                              <table style={{ width: '100%', fontSize: '9px', fontFamily: 'monospace', borderCollapse: 'collapse', textAlign: 'left' }}>
                                <thead>
                                  <tr style={{ color: '#64748b', borderBottom: '1px solid #1e384b' }}>
                                    <th style={{ padding: '3px 5px' }}>ALGORITHM</th>
                                    <th style={{ padding: '3px 5px' }}>MOTA</th>
                                    <th style={{ padding: '3px 5px' }}>IDF1</th>
                                    <th style={{ padding: '3px 5px' }}>TP / FP / FN</th>
                                    <th style={{ padding: '3px 5px' }}>ID SWITCHES</th>
                                    <th style={{ padding: '3px 5px' }}>MOTP</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {Object.entries(trackingBenchmarks.real_motion_replay.results).map(([algName, rmMetrics]: [string, any]) => (
                                    <tr key={algName} style={{ borderBottom: '1px solid rgba(30, 56, 75, 0.3)' }}>
                                      <td style={{ padding: '3px 5px', fontWeight: 600, color: '#e2e8f0' }}>{algName.toUpperCase()}</td>
                                      <td style={{ padding: '3px 5px', color: rmMetrics.mota_pct >= 85 ? '#10b981' : '#f59e0b' }}>{rmMetrics.mota_pct.toFixed(1)}%</td>
                                      <td style={{ padding: '3px 5px', color: rmMetrics.idf1_pct >= 90 ? '#10b981' : '#f59e0b' }}>{rmMetrics.idf1_pct.toFixed(1)}%</td>
                                      <td style={{ padding: '3px 5px', color: '#94a3b8' }}>{rmMetrics.total_matched_points} / {rmMetrics.false_positives} / {rmMetrics.false_negatives}</td>
                                      <td style={{ padding: '3px 5px', color: rmMetrics.id_switch_count === 0 ? '#10b981' : '#f59e0b' }}>{rmMetrics.id_switch_count}</td>
                                      <td style={{ padding: '3px 5px', color: '#cbd5e1' }}>{rmMetrics.motp_m.toFixed(1)} m</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Active Fused Tracks */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontSize: '10px', fontFamily: 'monospace', fontWeight: 700, color: '#e2edf2' }}>
                        ACTIVE TACTICAL TRACKS ({fusedTracks.length})
                      </span>
                      <small style={{ color: '#688694', fontSize: '9px' }}>
                        M-of-N (3/5) Confirmed &middot; ENU Coordinate Frame
                      </small>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '8px' }}>
                      {fusedTracks.map((trk: any) => {
                        const isDark = trk.target_class === 'Vessel' && !trk.identity;
                        const isCoast = trk.state === 'COASTING';
                        const badgeColor = isCoast ? '#f59e0b' : isDark ? '#f43f5e' : '#10b981';
                        return (
                          <div
                            key={trk.track_id}
                            style={{
                              background: 'rgba(10, 25, 36, 0.7)',
                              border: `1px solid ${isDark ? '#882233' : '#1c3442'}`,
                              borderRadius: '6px',
                              padding: '10px',
                              cursor: 'pointer',
                              transition: 'all 0.15s ease'
                            }}
                            onClick={() => flyToLocation(trk.lat, trk.lon, 9)}
                            title="Click to center tactical map on this track"
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <Crosshair size={13} style={{ color: isDark ? '#f43f5e' : '#00f0ff' }} />
                                <b style={{ fontSize: '11px', fontFamily: 'monospace', color: '#e2edf2' }}>{trk.track_id}</b>
                              </div>
                              <span
                                style={{
                                  fontSize: '9px',
                                  padding: '2px 6px',
                                  borderRadius: '3px',
                                  background: `${badgeColor}22`,
                                  color: badgeColor,
                                  fontFamily: 'monospace',
                                  fontWeight: 700,
                                  border: `1px solid ${badgeColor}55`
                                }}
                              >
                                {trk.state}
                              </span>
                            </div>

                            <div style={{ fontSize: '10px', color: '#9bb0b8', marginBottom: '6px' }}>
                              <b>{trk.target_class}</b> &middot; {trk.identity ? <span style={{ color: '#00f0ff' }}>{trk.identity}</span> : <span style={{ color: '#f43f5e' }}>DARK VESSEL (NO AIS)</span>}
                            </div>

                            {(() => {
                              const covEll = trk.covariance_ellipse || trk.cov_ellipse;
                              const sensorStr = trk.last_sensor || (trk.sensor_contributions ? Object.keys(trk.sensor_contributions).join(', ') : 'FUSED');
                              const hits = trk.total_updates || trk.hit_count || 1;
                              const misses = trk.consecutive_misses ?? trk.miss_count ?? 0;
                              return (
                                <>
                                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '9px', fontFamily: 'monospace', color: '#728d9c' }}>
                                    <div>SOG: <span style={{ color: '#cbd5e1' }}>{Number(trk.speed_knots).toFixed(1)} kts</span></div>
                                    <div>HDG: <span style={{ color: '#cbd5e1' }}>{Number(trk.heading_deg).toFixed(0)}&deg;</span></div>
                                    <div>LAT: <span style={{ color: '#cbd5e1' }}>{Number(trk.lat).toFixed(4)}&deg;</span></div>
                                    <div>LON: <span style={{ color: '#cbd5e1' }}>{Number(trk.lon).toFixed(4)}&deg;</span></div>
                                    {covEll && (
                                      <>
                                        <div>CEP: <span style={{ color: '#10b981' }}>{Number(covEll.cep_m).toFixed(1)} m</span></div>
                                        <div>ELLIPSE: <span style={{ color: '#cbd5e1' }}>{Number(covEll.semi_major_m).toFixed(0)}m &times; {Number(covEll.semi_minor_m).toFixed(0)}m</span></div>
                                      </>
                                    )}
                                  </div>

                                  <div style={{ marginTop: '6px', paddingTop: '4px', borderTop: '1px solid #162a38', display: 'flex', justifyContent: 'space-between', fontSize: '8px', color: '#64748b' }}>
                                    <span>SENSOR: {sensorStr} &middot; UPDATES: {hits}/{misses}</span>
                                    <span style={{ color: '#00f0ff' }}>Fly to contact &nearr;</span>
                                  </div>
                                </>
                              );
                            })()}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </section>
              </div>
            </>
          )}

          {/* PAGE 2: NAVAL DOMAIN (SATELLITE OPTICAL + SAR + AIS) */}
          {page === 'Naval Domain' && (
            <div className="analysis-layout">
              <section className="panel image-panel">
                <div className="panel-head">
                  <div>
                    <div className="panel-title"><Ship size={16} /> Naval Spaceborne Surveillance & Screening</div>
                    <small>High-resolution optical (xView) & Sentinel-2 multispectral GeoTIFFs</small>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <button
                      className={`button ${navalViewMode === 'map' ? 'primary' : 'secondary'} compact`}
                      onClick={() => setNavalViewMode('map')}
                    >
                      <MapIcon size={13} /> Sector Map
                    </button>
                    <button
                      className={`button ${navalViewMode === 'raster' ? 'primary' : 'secondary'} compact`}
                      onClick={() => setNavalViewMode('raster')}
                    >
                      <Ship size={13} /> Optical Screening
                    </button>
                    <select
                      value={modelType}
                      onChange={e => setModelType(e.target.value as any)}
                      style={{ background: '#10212b', border: '1px solid #294351', color: '#9bb1bc', fontSize: '9px', padding: '4px 6px', borderRadius: '4px' }}
                    >
                      <option value="vessel">Vessel-Tuned Model (YOLO11n)</option>
                      <option value="multiclass">4-Class Joint Model (Vessel/Aircraft/Vehicle/Infra)</option>
                    </select>
                    <label className="button secondary compact">
                      <CloudUpload size={14} /> Upload Image
                      <input type="file" hidden accept="image/*,.tif,.tiff" onChange={e => { handleUpload(e.target.files?.[0]); setNavalViewMode('raster'); }} />
                    </label>
                  </div>
                </div>

                {navalViewMode === 'map' ? (
                  <TacticalMap
                    opticalItems={opticalItems}
                    sarDetections={sarDetections}
                    armyFeeds={[]}
                    providerPoints={pipe}
                    zones={zones}
                    layers={{ optical: true, sar: true, ais: true, army: false, zones: true, vectors: true, geoOverlay: true, heat: false }}
                    flyTarget={flyTarget}
                    fusedTracks={fusedTracks}
                  />
                ) : preview ? (
                  <div style={{ border: '1px solid #1a323d', borderRadius: '6px', overflow: 'hidden', background: '#061019' }}>
                    {/* Class Filter Bar for Clean Reading */}
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '6px 10px',
                      background: '#071520',
                      borderBottom: '1px solid #1a323d',
                      flexWrap: 'wrap',
                      gap: '8px'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                        <span style={{ fontSize: '9px', color: '#688694', fontWeight: 600, letterSpacing: '0.04em' }}>SHOW FILTER:</span>
                        <button
                          className={`chip ${classFilter === 'all' ? 'active' : ''}`}
                          style={{
                            padding: '3px 8px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                            background: classFilter === 'all' ? '#183b4e' : '#0b1b24',
                            border: `1px solid ${classFilter === 'all' ? '#57d6c8' : '#1c3442'}`,
                            color: classFilter === 'all' ? '#57d6c8' : '#8da4af'
                          }}
                          onClick={() => setClassFilter('all')}
                        >
                          All ({countsByClass.all})
                        </button>
                        {countsByClass.vessel > 0 && (
                          <button
                            className={`chip ${classFilter === 'vessel' ? 'active' : ''}`}
                            style={{
                              padding: '3px 8px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                              background: classFilter === 'vessel' ? 'rgba(52, 211, 153, 0.2)' : '#0b1b24',
                              border: `1px solid ${classFilter === 'vessel' ? '#34d399' : '#1c3442'}`,
                              color: classFilter === 'vessel' ? '#34d399' : '#8da4af'
                            }}
                            onClick={() => setClassFilter('vessel')}
                          >
                            🟢 Vessels Only ({countsByClass.vessel})
                          </button>
                        )}
                        {countsByClass.infrastructure > 0 && (
                          <button
                            className={`chip ${classFilter === 'infrastructure' ? 'active' : ''}`}
                            style={{
                              padding: '3px 8px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                              background: classFilter === 'infrastructure' ? 'rgba(192, 132, 252, 0.2)' : '#0b1b24',
                              border: `1px solid ${classFilter === 'infrastructure' ? '#c084fc' : '#1c3442'}`,
                              color: classFilter === 'infrastructure' ? '#c084fc' : '#8da4af'
                            }}
                            onClick={() => setClassFilter('infrastructure')}
                          >
                            🟣 Infrastructure Only ({countsByClass.infrastructure})
                          </button>
                        )}
                        {countsByClass.vehicle > 0 && (
                          <button
                            className={`chip ${classFilter === 'vehicle' ? 'active' : ''}`}
                            style={{
                              padding: '3px 8px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                              background: classFilter === 'vehicle' ? 'rgba(245, 158, 11, 0.2)' : '#0b1b24',
                              border: `1px solid ${classFilter === 'vehicle' ? '#f59e0b' : '#1c3442'}`,
                              color: classFilter === 'vehicle' ? '#f59e0b' : '#8da4af'
                            }}
                            onClick={() => setClassFilter('vehicle')}
                          >
                            🟡 Vehicles Only ({countsByClass.vehicle})
                          </button>
                        )}
                        {countsByClass.aircraft > 0 && (
                          <button
                            className={`chip ${classFilter === 'aircraft' ? 'active' : ''}`}
                            style={{
                              padding: '3px 8px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                              background: classFilter === 'aircraft' ? 'rgba(56, 189, 248, 0.2)' : '#0b1b24',
                              border: `1px solid ${classFilter === 'aircraft' ? '#38bdf8' : '#1c3442'}`,
                              color: classFilter === 'aircraft' ? '#38bdf8' : '#8da4af'
                            }}
                            onClick={() => setClassFilter('aircraft')}
                          >
                            🔵 Aircraft Only ({countsByClass.aircraft})
                          </button>
                        )}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <button
                          style={{
                            padding: '2px 7px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                            background: showLabels ? '#12261e' : '#141d24',
                            border: `1px solid ${showLabels ? '#68d7a1' : '#233742'}`,
                            color: showLabels ? '#68d7a1' : '#738b97'
                          }}
                          onClick={() => setShowLabels(!showLabels)}
                          title="Toggle text tags on targets"
                        >
                          🏷️ Labels: {showLabels ? 'ON' : 'OFF'}
                        </button>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '9px', color: '#738b97' }}>
                          <span>Min Conf:</span>
                          <select
                            value={minConfFilter}
                            onChange={e => setMinConfFilter(Number(e.target.value))}
                            style={{
                              background: '#0a1720', border: '1px solid #1a323d', color: '#57d6c8',
                              fontSize: '9px', padding: '2px 4px', borderRadius: '4px'
                            }}
                          >
                            <option value={0.25}>25% (Raw)</option>
                            <option value={0.4}>40%</option>
                            <option value={0.45}>45% (Tactical)</option>
                            <option value={0.5}>50% (High Conf)</option>
                            <option value={0.65}>65%</option>
                            <option value={0.8}>80% (Verified Only)</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    <div className="preview-stage" style={{ height: '480px' }}>
                      <div className="image-overlay-wrap" style={{ aspectRatio: `${imageSize[0]}/${imageSize[1]}` }}>
                        <img src={resolveMediaUrl(preview)} alt="Target raster preview" />
                        <svg viewBox={`0 0 ${imageSize[0]} ${imageSize[1]}`} preserveAspectRatio="xMidYMid meet">
                          {activeDetections.map(x => {
                            const col = getTargetColor(x.kind, x.threat_level);
                            return (
                              <g key={x.id}>
                                <rect
                                  x={x.x}
                                  y={x.y}
                                  width={Math.max(22, x.w)}
                                  height={Math.max(22, x.h)}
                                  fill={`${col}22`}
                                  stroke={col}
                                  strokeWidth={Math.max(4, imageSize[0] / 400)}
                                />
                                <circle
                                  cx={x.x + x.w / 2}
                                  cy={x.y + x.h / 2}
                                  r={Math.max(6, imageSize[0] / 300)}
                                  fill={col}
                                  stroke="#07111c"
                                  strokeWidth={Math.max(2, imageSize[0] / 600)}
                                />
                                {showLabels && (
                                  <text
                                    x={x.x}
                                    y={Math.max(18, x.y - 6)}
                                    fill={col}
                                    stroke="#07111c"
                                    strokeWidth={Math.max(4, imageSize[0] / 500)}
                                    paintOrder="stroke"
                                    fontSize={Math.max(14, imageSize[0] / 70)}
                                    fontWeight="bold"
                                  >
                                    {x.kind.toUpperCase()} {(x.confidence * 100).toFixed(0)}%
                                  </text>
                                )}
                              </g>
                            );
                          })}
                        </svg>
                      </div>
                      <div className="preview-label">
                        ACTIVE RASTER: {previewName} · {activeDetections.length} of {countsByClass.all} TARGETS DISPLAYED {classFilter !== 'all' ? `(${classFilter.toUpperCase()} ONLY)` : ''}
                      </div>
                    </div>
                  </div>
                ) : (
                  <label className="dropzone" style={{ height: '480px' }}>
                    <CloudUpload size={32} />
                    <b>Upload Satellite Image or Sentinel-2 GeoTIFF</b>
                    <span>Supports GeoTIFF, TIFF, JPG, PNG (Tiled 1024px inference with IoU duplicate suppression)</span>
                    <input type="file" hidden accept="image/*,.tif,.tiff" onChange={e => handleUpload(e.target.files?.[0])} />
                  </label>
                )}

                {/* Sentinel-1 SAR Radar Analysis Card */}
                <div style={{ margin: '15px', border: '1px solid #233e4c', background: '#0a1924', padding: '14px', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#5dd3c7', fontSize: '11px', fontWeight: 600, marginBottom: '6px' }}>
                    <Radar size={16} /> Sentinel-1 SAR Radar & Dark-Vessel Correlation
                  </div>
                  <p style={{ fontSize: '9px', color: '#97adb8', margin: 0, lineHeight: 1.6 }}>
                    Synthetic Aperture Radar (SAR) penetrates cloud cover and darkness. Radar cross section (RCS sigma0) is compared with regional AIS broadcasts.
                    Contacts exceeding -12 dB with no AIS within 3 km are automatically escalated to <b>CRITICAL DARK VESSEL</b> status.
                  </p>
                </div>
              </section>

              {/* Naval Adjudication List */}
              <section className="panel detection-panel">
                <div className="panel-head" style={{ paddingBottom: '8px' }}>
                  <div>
                    <div className="panel-title">
                      Naval Detections & Classification
                    </div>
                    <small>1-click analyst AIS adjudication & triage</small>
                  </div>
                </div>

                {/* Sub-Tabs: Uploaded Image vs Sentinel-1 SAR Radar */}
                <div style={{ display: 'flex', gap: '8px', padding: '8px 12px', borderBottom: '1px solid #1c303b', background: '#09151f' }}>
                  <button
                    className={`button ${navalReviewTab === 'image' ? 'primary' : 'secondary'} compact`}
                    onClick={() => setNavalReviewTab('image')}
                  >
                    <Target size={13} /> {previewName || 'Uploaded Image'} ({opticalItems.filter(x => !previewName || x.image_name === previewName).length})
                  </button>
                  <button
                    className={`button ${navalReviewTab === 'sar' ? 'primary' : 'secondary'} compact`}
                    onClick={() => setNavalReviewTab('sar')}
                  >
                    <Radar size={13} /> Sentinel-1 SAR Radar ({sarDetections.length})
                  </button>
                </div>

                <div className="detection-list">
                  {/* TAB 1: Uploaded Image Detections */}
                  {navalReviewTab === 'image' && (
                    <>
                      {opticalItems.filter(x => !previewName || x.image_name === previewName).length === 0 ? (
                        <div style={{ padding: '24px', textAlign: 'center', color: '#79929e', fontSize: '11px' }}>
                          Upload an image on the left to inspect and review candidate boxes.
                        </div>
                      ) : (
                        opticalItems.filter(x => !previewName || x.image_name === previewName).map((x, idx) => (
                          <div key={x.id} className="detect-card">
                            <div className="detect-top">
                              <span className={`priority-indicator ${x.threat_level.toLowerCase()}`} />
                              <div>
                                <b>#{idx + 1} · {x.kind} Candidate</b>
                                <small>{x.image_name}</small>
                              </div>
                              <span className={`score-pill ${x.threat_level.toLowerCase()}`}>
                                {x.threat_score} · {x.threat_level}
                              </span>
                            </div>
                            <div className="confidence-row">
                              <span>Model Confidence</span>
                              <b>{(x.confidence * 100).toFixed(1)}%</b>
                              <div className="confidence-track">
                                <i style={{ width: `${x.confidence * 100}%` }} />
                              </div>
                            </div>
                            <div className="detect-meta">
                              <span>Pos: {x.lat && x.lon ? `${x.lat.toFixed(4)}°, ${x.lon.toFixed(4)}°` : `Pixel: (${Math.round(x.x)}, ${Math.round(x.y)})`}</span>
                              <span className={`status ${x.ais_status}`}>AIS {x.ais_status}</span>
                            </div>
                            <div className="association">
                              <span>Analyst Action</span>
                              <button onClick={() => adjudicateOptical(x.id, 'matched')}><Check size={12} /> Matched</button>
                              <button onClick={() => adjudicateOptical(x.id, 'unmatched')}><TriangleAlert size={12} /> Dark Vessel (+50)</button>
                              <button onClick={() => adjudicateOptical(x.id, 'unknown')}><CircleHelp size={12} /> Unknown</button>
                            </div>
                          </div>
                        ))
                      )}
                    </>
                  )}

                  {/* TAB 2: Sentinel-1 SAR Radar Dark Vessels */}
                  {navalReviewTab === 'sar' && (
                    <>
                      <div style={{ padding: '8px 12px', background: '#0f222d', borderBottom: '1px solid #1c3542', fontSize: '9px', color: '#8ec9c1' }}>
                        📡 <b>Sentinel-1 SAR Radar Feeds:</b> Arabian Sea & Western Naval Command Corridor
                      </div>
                      {sarDetections.map(s => (
                        <div key={s.id} className="detect-card" style={{ borderColor: s.is_dark_vessel ? '#ff4d4d' : '#223b47' }}>
                          <div className="detect-top">
                            <span className={`priority-indicator ${s.threat_level.toLowerCase()}`} />
                            <div>
                              <b style={{ color: s.is_dark_vessel ? '#ff6b63' : '#e2edf2' }}>
                                {s.is_dark_vessel ? '🚨 SENTINEL-1 DARK VESSEL' : 'SAR COOPERATIVE VESSEL'}
                              </b>
                              <small>{s.scene_id} · {s.timestamp}</small>
                            </div>
                            <span className={`score-pill ${s.threat_level.toLowerCase()}`}>
                              {s.threat_score} · {s.threat_level}
                            </span>
                          </div>
                          <div className="detect-meta">
                            <span>Pos: {s.lat.toFixed(4)}°, {s.lon.toFixed(4)}°</span>
                            <span>RCS: {s.rcs_sigma0_db} dB</span>
                            <span>Est: {s.estimated_length_m} m</span>
                          </div>
                          <div className="score-reasons">
                            <span>{s.notes}</span>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              </section>
            </div>
          )}

          {/* PAGE 3: ARMY DOMAIN (DRONE UAV, UGS GROUND SENSORS, SIGINT) */}
          {page === 'Army Domain' && (
            <div className="analysis-layout">
              <section className="panel">
                <div className="panel-head">
                  <div>
                    <div className="panel-title"><Crosshair size={16} /> Army Tactical Multimodal Feeds</div>
                    <small>Tactical UAV FMV (VisDrone/VIRAT), Ground Seismic Sensors (UGS) & SIGINT</small>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <button
                      className={`button ${armyViewMode === 'map' ? 'primary' : 'secondary'} compact`}
                      onClick={() => setArmyViewMode('map')}
                    >
                      <MapIcon size={13} /> Sector Map
                    </button>
                    <button
                      className={`button ${armyViewMode === 'uav' ? 'primary' : 'secondary'} compact`}
                      onClick={() => setArmyViewMode('uav')}
                    >
                      <Crosshair size={13} /> UAV Downlink
                    </button>
                    <span className="count-badge">{armyFeeds.length} active feeds</span>
                  </div>
                </div>

                <div style={{ padding: '16px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '16px' }}>
                    <div className="metric" style={{ padding: '10px' }}>
                      <div className="metric-top"><span>DRONE UAV DETECTIONS</span><Eye size={15} /></div>
                      <strong style={{ fontSize: '18px' }}>{armyFeeds.filter(a => a.domain === 'DRONE_UAV').length}</strong>
                      <small>Vehicle convoys & artillery</small>
                    </div>
                    <div className="metric" style={{ padding: '10px' }}>
                      <div className="metric-top"><span>GROUND UGS ALARMS</span><Activity size={15} /></div>
                      <strong className="amber" style={{ fontSize: '18px' }}>{armyFeeds.filter(a => a.domain === 'UGS_GROUND').length}</strong>
                      <small>Seismic & PIR tripwires</small>
                    </div>
                    <div className="metric" style={{ padding: '10px' }}>
                      <div className="metric-top"><span>SIGINT INTERCEPTS</span><Radio size={15} /></div>
                      <strong className="coral" style={{ fontSize: '18px' }}>{armyFeeds.filter(a => a.domain === 'SIGINT_TEXT').length}</strong>
                      <small>Tactical VHF lines-of-bearing</small>
                    </div>
                  </div>

                  {armyViewMode === 'map' ? (
                    <TacticalMap
                      opticalItems={[]}
                      sarDetections={[]}
                      armyFeeds={armyFeeds}
                      providerPoints={[]}
                      zones={zones}
                      layers={{ optical: false, sar: false, ais: false, army: true, zones: true, vectors: true, geoOverlay: true, heat: false }}
                      flyTarget={flyTarget}
                      fusedTracks={fusedTracks}
                    />
                  ) : (
                    <>
                      {/* Hidden file input for Army UAV Downlink */}
                      <input
                        ref={armyInputRef}
                        type="file"
                        accept="image/*,.tif,.tiff"
                        style={{ display: 'none' }}
                        onChange={(e) => {
                          const f = e.target.files?.[0];
                          if (f) handleUpload(f, 'multiclass');
                        }}
                      />

                  {/* Interactive Tactical UAV / Drone Surveillance Downlink */}
                  <div style={{ border: '1px solid #23414f', background: '#091823', borderRadius: '8px', padding: '14px', marginBottom: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <b style={{ color: '#57d6c8', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Eye size={15} /> UAV-GARUDA-04 Tactical Electro-Optical / Thermal Downlink
                      </b>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <span className="live-pill" style={{ background: preview ? '#12261e' : '#1e242b', color: preview ? '#68d7a1' : '#94a3b8' }}>
                          {preview ? '● LIVE DOWNLINK (AIR-GAPPED)' : 'STANDBY // READY FOR DOWNLINK'}
                        </span>
                        {preview && (
                          <>
                            <button
                              className="button secondary compact"
                              style={{ fontSize: '9px', padding: '2px 8px' }}
                              onClick={() => armyInputRef.current?.click()}
                              title="Import different UAV or aerial imagery"
                            >
                              <CloudUpload size={11} /> Import Another Feed
                            </button>
                            <button
                              className="button danger compact"
                              style={{ fontSize: '9px', padding: '2px 8px' }}
                              onClick={() => { setPreview(null); setPreviewName(''); }}
                              title="Reset to standby feed"
                            >
                              <X size={11} /> Standby
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    {preview ? (
                      <div style={{ border: '1px solid #1a323d', borderRadius: '6px', overflow: 'hidden', background: '#061019' }}>
                        {/* Telemetry HUD Banner */}
                        <div style={{
                          background: '#071520',
                          padding: '6px 12px',
                          borderBottom: '1px solid #172d38',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '9px',
                          color: '#6e8f9e',
                          fontFamily: 'monospace'
                        }}>
                          <span>LAT: 32.5480° N | LON: 74.8120° E | ALT: 1,420M AGL | SENSOR: FLIR-EO 4K</span>
                          <span style={{ color: '#57d6c8' }}>ACTIVE FEED: {previewName}</span>
                        </div>

                        {/* Interactive Class Filter Bar for Clean Reading */}
                        <div style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '6px 10px',
                          background: '#0a1a26',
                          borderBottom: '1px solid #1a323d',
                          flexWrap: 'wrap',
                          gap: '8px'
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '9px', color: '#688694', fontWeight: 600, letterSpacing: '0.04em' }}>SHOW FILTER:</span>
                            <button
                              className={`chip ${classFilter === 'all' ? 'active' : ''}`}
                              style={{
                                padding: '3px 8px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                                background: classFilter === 'all' ? '#183b4e' : '#0b1b24',
                                border: `1px solid ${classFilter === 'all' ? '#57d6c8' : '#1c3442'}`,
                                color: classFilter === 'all' ? '#57d6c8' : '#8da4af'
                              }}
                              onClick={() => setClassFilter('all')}
                            >
                              All ({countsByClass.all})
                            </button>
                            {countsByClass.infrastructure > 0 && (
                              <button
                                className={`chip ${classFilter === 'infrastructure' ? 'active' : ''}`}
                                style={{
                                  padding: '3px 8px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                                  background: classFilter === 'infrastructure' ? 'rgba(192, 132, 252, 0.2)' : '#0b1b24',
                                  border: `1px solid ${classFilter === 'infrastructure' ? '#c084fc' : '#1c3442'}`,
                                  color: classFilter === 'infrastructure' ? '#c084fc' : '#8da4af'
                                }}
                                onClick={() => setClassFilter('infrastructure')}
                              >
                                🟣 Infrastructure Only ({countsByClass.infrastructure})
                              </button>
                            )}
                            {countsByClass.vehicle > 0 && (
                              <button
                                className={`chip ${classFilter === 'vehicle' ? 'active' : ''}`}
                                style={{
                                  padding: '3px 8px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                                  background: classFilter === 'vehicle' ? 'rgba(245, 158, 11, 0.2)' : '#0b1b24',
                                  border: `1px solid ${classFilter === 'vehicle' ? '#f59e0b' : '#1c3442'}`,
                                  color: classFilter === 'vehicle' ? '#f59e0b' : '#8da4af'
                                }}
                                onClick={() => setClassFilter('vehicle')}
                              >
                                🟡 Vehicles Only ({countsByClass.vehicle})
                              </button>
                            )}
                            {countsByClass.aircraft > 0 && (
                              <button
                                className={`chip ${classFilter === 'aircraft' ? 'active' : ''}`}
                                style={{
                                  padding: '3px 8px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                                  background: classFilter === 'aircraft' ? 'rgba(56, 189, 248, 0.2)' : '#0b1b24',
                                  border: `1px solid ${classFilter === 'aircraft' ? '#38bdf8' : '#1c3442'}`,
                                  color: classFilter === 'aircraft' ? '#38bdf8' : '#8da4af'
                                }}
                                onClick={() => setClassFilter('aircraft')}
                              >
                                🔵 Aircraft Only ({countsByClass.aircraft})
                              </button>
                            )}
                            {countsByClass.vessel > 0 && (
                              <button
                                className={`chip ${classFilter === 'vessel' ? 'active' : ''}`}
                                style={{
                                  padding: '3px 8px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                                  background: classFilter === 'vessel' ? 'rgba(52, 211, 153, 0.2)' : '#0b1b24',
                                  border: `1px solid ${classFilter === 'vessel' ? '#34d399' : '#1c3442'}`,
                                  color: classFilter === 'vessel' ? '#34d399' : '#8da4af'
                                }}
                                onClick={() => setClassFilter('vessel')}
                              >
                                🟢 Vessels Only ({countsByClass.vessel})
                              </button>
                            )}
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <button
                              style={{
                                padding: '2px 7px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                                background: showLabels ? '#12261e' : '#141d24',
                                border: `1px solid ${showLabels ? '#68d7a1' : '#233742'}`,
                                color: showLabels ? '#68d7a1' : '#738b97'
                              }}
                              onClick={() => setShowLabels(!showLabels)}
                              title="Toggle text tags on targets"
                            >
                              🏷️ Labels: {showLabels ? 'ON' : 'OFF'}
                            </button>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '9px', color: '#738b97' }}>
                              <span>Min Conf:</span>
                              <select
                                value={minConfFilter}
                                onChange={e => setMinConfFilter(Number(e.target.value))}
                                style={{
                                  background: '#0a1720', border: '1px solid #1a323d', color: '#57d6c8',
                                  fontSize: '9px', padding: '2px 4px', borderRadius: '4px'
                                }}
                              >
                                <option value={0.25}>25% (Raw)</option>
                                <option value={0.4}>40%</option>
                                <option value={0.45}>45% (Tactical)</option>
                                <option value={0.5}>50% (High Conf)</option>
                                <option value={0.65}>65%</option>
                                <option value={0.8}>80% (Verified Only)</option>
                              </select>
                            </div>
                          </div>
                        </div>

                        {/* Interactive HUD Stage (Double-tap to import) */}
                        <div
                          className="preview-stage"
                          style={{ height: '440px', position: 'relative', cursor: 'pointer' }}
                          onDoubleClick={() => armyInputRef.current?.click()}
                          title="Double-tap to import new imagery"
                        >
                          <div className="image-overlay-wrap" style={{ aspectRatio: `${imageSize[0]}/${imageSize[1]}` }}>
                            <img src={resolveMediaUrl(preview)} alt="Tactical drone downlink" />
                            <svg viewBox={`0 0 ${imageSize[0]} ${imageSize[1]}`} preserveAspectRatio="xMidYMid meet">
                              {activeDetections.map(x => {
                                const col = getTargetColor(x.kind, x.threat_level);
                                return (
                                  <g key={x.id}>
                                    <rect
                                      x={x.x}
                                      y={x.y}
                                      width={Math.max(20, x.w)}
                                      height={Math.max(20, x.h)}
                                      fill={`${col}22`}
                                      stroke={col}
                                      strokeWidth={Math.max(3, imageSize[0] / 400)}
                                    />
                                    <circle
                                      cx={x.x + x.w / 2}
                                      cy={x.y + x.h / 2}
                                      r={Math.max(4, imageSize[0] / 350)}
                                      fill={col}
                                      stroke="#07111c"
                                      strokeWidth={Math.max(2, imageSize[0] / 600)}
                                    />
                                    {showLabels && (
                                      <text
                                        x={x.x}
                                        y={Math.max(16, x.y - 6)}
                                        fill={col}
                                        stroke="#07111c"
                                        strokeWidth={Math.max(3, imageSize[0] / 500)}
                                        paintOrder="stroke"
                                        fontSize={Math.max(13, imageSize[0] / 75)}
                                        fontWeight="bold"
                                      >
                                        {x.kind.toUpperCase()} {(x.confidence * 100).toFixed(0)}%
                                      </text>
                                    )}
                                  </g>
                                );
                              })}
                            </svg>
                          </div>

                          {/* Reticle Watermark */}
                          <div style={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            pointerEvents: 'none',
                            opacity: 0.3,
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center'
                          }}>
                            <Crosshair size={44} style={{ color: '#57d6c8' }} />
                          </div>

                          <div className="preview-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span>
                              TACTICAL AI ANALYSIS: {activeDetections.length} of {countsByClass.all} TARGETS DISPLAYED {classFilter !== 'all' ? `(${classFilter.toUpperCase()} ONLY)` : ''}
                            </span>
                            <span style={{ fontSize: '9px', color: '#688694' }}>Double-tap to replace imagery</span>
                          </div>
                        </div>

                        {/* Downlink Quick Controls Strip */}
                        <div style={{
                          background: '#07121b',
                          padding: '8px 12px',
                          borderTop: '1px solid #1a323d',
                          display: 'flex',
                          gap: '8px',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          flexWrap: 'wrap'
                        }}>
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button
                              className="button secondary compact"
                              style={{ fontSize: '9px' }}
                              onClick={() => handleLoadSample('1217.tif', 'multiclass')}
                            >
                              <Zap size={11} /> Load Sample: Convoy (1217.tif)
                            </button>
                            <button
                              className="button secondary compact"
                              style={{ fontSize: '9px' }}
                              onClick={() => handleLoadSample('1154.tif', 'multiclass')}
                            >
                              <Zap size={11} /> Load Sample: Airfield (1154.tif)
                            </button>
                            <button
                              className="button secondary compact"
                              style={{ fontSize: '9px' }}
                              onClick={() => armyInputRef.current?.click()}
                            >
                              <CloudUpload size={11} /> Browse File...
                            </button>
                          </div>
                          <div style={{ fontSize: '9px', color: '#7ba0b1' }}>
                            Neural Model: <b>xview_hackathon (Vehicle, Aircraft, Infrastructure)</b>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div
                        onClick={() => armyInputRef.current?.click()}
                        onDoubleClick={() => armyInputRef.current?.click()}
                        onDragOver={(e) => { e.preventDefault(); setArmyDragOver(true); }}
                        onDragLeave={() => setArmyDragOver(false)}
                        onDrop={(e) => {
                          e.preventDefault();
                          setArmyDragOver(false);
                          if (e.dataTransfer.files?.[0]) handleUpload(e.dataTransfer.files[0], 'multiclass');
                        }}
                        style={{
                          minHeight: '260px',
                          background: armyDragOver ? '#0e2432' : '#061019',
                          border: `2px dashed ${armyDragOver ? '#57d6c8' : '#23414f'}`,
                          borderRadius: '6px',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          cursor: 'pointer',
                          padding: '24px 16px',
                          textAlign: 'center',
                          transition: 'all 0.2s ease',
                          position: 'relative'
                        }}
                        title="Click or double-tap to import imagery"
                      >
                        <div style={{
                          width: '52px',
                          height: '52px',
                          borderRadius: '50%',
                          background: 'rgba(87, 214, 200, 0.08)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          marginBottom: '10px',
                          border: '1px solid rgba(87, 214, 200, 0.25)'
                        }}>
                          <Crosshair size={30} style={{ color: '#57d6c8' }} />
                        </div>

                        <b style={{ color: '#e2edf2', fontSize: '13px', letterSpacing: '0.03em' }}>
                          👉 CLICK, DOUBLE-TAP, OR DRAG TACTICAL DRONE IMAGERY HERE
                        </b>
                        <p style={{ color: '#7e9aa8', fontSize: '10px', maxWidth: '520px', margin: '8px 0 14px', lineHeight: 1.6 }}>
                          Import aerial reconnaissance, drone video stills, thermal/FLIR, or satellite land imagery (TIFF, PNG, JPG).
                          Detects <b>Military Vehicle Convoys</b>, <b>Fighter/Transport Aircraft</b>, and <b>Hostile Infrastructure / Bunkers</b> in air-gapped real-time.
                        </p>

                        {/* 1-Click Instant Sample Buttons */}
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center' }} onClick={e => e.stopPropagation()}>
                          <button
                            className="button primary compact"
                            style={{ fontSize: '10px', padding: '6px 12px' }}
                            onClick={() => handleLoadSample('1217.tif', 'multiclass')}
                          >
                            <Zap size={13} /> 1-Click Test: Vehicle Convoys (1217.tif)
                          </button>
                          <button
                            className="button secondary compact"
                            style={{ fontSize: '10px', padding: '6px 12px' }}
                            onClick={() => handleLoadSample('1154.tif', 'multiclass')}
                          >
                            <Zap size={13} /> 1-Click Test: Airbase Targets (1154.tif)
                          </button>
                          <button
                            className="button secondary compact"
                            style={{ fontSize: '10px', padding: '6px 12px' }}
                            onClick={() => armyInputRef.current?.click()}
                          >
                            <CloudUpload size={13} /> Browse From PC...
                          </button>
                        </div>

                        <div style={{ marginTop: '14px', fontSize: '9px', color: '#527282' }}>
                          Double-tap anywhere in this card to open file selector · Air-gapped neural inference
                        </div>
                      </div>
                    )}

                    {/* Quick Intelligence Briefing Note */}
                    <div style={{
                      marginTop: '12px',
                      padding: '10px 12px',
                      background: '#06131c',
                      borderRadius: '6px',
                      border: '1px solid #162b37',
                      fontSize: '10px',
                      color: '#8faab7',
                      lineHeight: 1.6
                    }}>
                      <b style={{ color: '#57d6c8' }}>💡 Tactical Operational Brief: What Images to Feed into the Army Downlink?</b>
                      <div style={{ marginTop: '4px' }}>
                        • <b>Recommended Project Images:</b> <code style={{ color: '#f59e0b' }}>train_images/train_images/1217.tif</code> (thousands of ground vehicles & tactical convoys), <code style={{ color: '#38bdf8' }}>1154.tif</code> (airfield runways with aircraft).<br />
                        • <b>Tactical Drone & Aerial Imagery:</b> Drone EO/IR captures, FLIR thermal stills, forward-operating base perimeter cameras, road corridor overflights.<br />
                        • <b>Accepted Formats:</b> GeoTIFF, standard TIFF, JPG, JPEG, and PNG up to 512 MiB.
                      </div>
                    </div>
                  </div>
                  </>
                )}
                </div>
              </section>

              {/* Feed Details & Intercept Cards */}
              <section className="panel">
                <div className="panel-head">
                  <div>
                    <div className="panel-title"><Radio size={16} /> Ground Sensor & SIGINT Intercept Logs</div>
                    <small>Real-time telemetry and transcript surrogates</small>
                  </div>
                </div>

                <div className="detection-list">
                  {armyFeeds.map(f => (
                    <div key={f.id} className="detect-card">
                      <div className="detect-top">
                        <span className={`priority-indicator ${f.threat_level.toLowerCase()}`} />
                        <div>
                          <b style={{ color: '#e2edf2' }}>{f.target_class}</b>
                          <small>{f.source_ref} · {f.domain}</small>
                        </div>
                        <span className={`score-pill ${f.threat_level.toLowerCase()}`}>
                          {f.threat_score} · {f.threat_level}
                        </span>
                      </div>
                      <div className="detect-meta">
                        <span>Position: {f.lat.toFixed(4)}, {f.lon.toFixed(4)}</span>
                        <span>Confidence: {(f.confidence * 100).toFixed(0)}%</span>
                        <span>Signal: {(f.signal_strength * 100).toFixed(0)}%</span>
                      </div>
                      <div style={{ marginTop: '8px', fontSize: '9px', color: '#a5b8c2', background: '#07121b', padding: '8px', borderRadius: '4px', border: '1px solid #1a2f3b' }}>
                        {f.alert_summary}
                      </div>
                      <pre style={{ marginTop: '6px', fontSize: '8px', color: '#7ba0b1', background: '#040b12', padding: '6px', borderRadius: '4px', overflowX: 'auto' }}>
                        {f.raw_payload}
                      </pre>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          )}

          {/* PAGE 4: TACTICAL SITREP (SITUATION REPORT) */}
          {page === 'Tactical SITREP' && (
            <div className="report-grid">
              <section className="panel" style={{ gridColumn: 'span 2' }}>
                <div className="panel-head">
                  <div>
                    <div className="panel-title"><FileText size={16} /> Automated Military Intelligence SITREP</div>
                    <small>Synthesized multimodal defense summary (STANAG / Joint AOR format)</small>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="button secondary compact"
                      onClick={() => {
                        if (sitrep?.report_markdown) {
                          navigator.clipboard.writeText(sitrep.report_markdown);
                          setToast('SITREP text copied to clipboard!');
                        }
                      }}
                    >
                      <Terminal size={14} /> Copy Briefing
                    </button>
                    <button
                      className="button primary compact"
                      onClick={() => {
                        const blob = new Blob([sitrep?.report_markdown || ''], { type: 'text/markdown' });
                        const a = document.createElement('a');
                        a.href = URL.createObjectURL(blob);
                        a.download = `SITREP_OPERATION_RAKSHAK_${sitrep?.dtg?.replace(/ /g, '_') || 'LATEST'}.md`;
                        a.click();
                      }}
                    >
                      <FileText size={14} /> Export SITREP (.md)
                    </button>
                  </div>
                </div>

                <div style={{ padding: '20px' }}>
                  <pre style={{
                    background: '#040a10',
                    border: '1px solid #1c3442',
                    padding: '18px',
                    borderRadius: '8px',
                    color: '#c2d7e2',
                    fontSize: '11px',
                    lineHeight: 1.6,
                    fontFamily: 'Consolas, monospace',
                    overflowX: 'auto',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {sitrep?.report_markdown || 'Compiling situation report...'}
                  </pre>
                </div>
              </section>
            </div>
          )}

          {/* PAGE: TACTICAL AI & SOVEREIGN RAG ENGINE */}
          {page === 'Tactical AI (RAG)' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* RAG Mode Switcher */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'linear-gradient(145deg, #0e1d27, #0b1821)',
                border: '1px solid #203743',
                borderRadius: '8px',
                padding: '10px 16px',
                flexWrap: 'wrap',
                gap: '12px'
              }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    className={`button ${ragViewTab === 'advisor' ? 'primary' : 'secondary'}`}
                    onClick={() => setRagViewTab('advisor')}
                    style={{ fontSize: '11px', padding: '8px 14px' }}
                  >
                    <Bot size={14} /> Rules of Engagement Advisor
                  </button>
                  <button
                    className={`button ${ragViewTab === 'library' ? 'primary' : 'secondary'}`}
                    onClick={() => {
                      setRagViewTab('library');
                      if (!ragKnowledgeBase.length) loadRagKnowledgeBase();
                    }}
                    style={{ fontSize: '11px', padding: '8px 14px' }}
                  >
                    <BookOpen size={14} /> Sovereign Doctrine Library ({ragKnowledgeBase.length || 6} Indexed)
                  </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '10px', color: '#68ddd0' }}>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '5px',
                    padding: '4px 8px',
                    background: 'rgba(80, 215, 199, 0.1)',
                    border: '1px solid #204b47',
                    borderRadius: '4px',
                    fontWeight: 600
                  }}>
                    <Zap size={11} /> 100% AIR-GAPPED RAG // ZERO EXTERNAL APIS
                  </span>
                  <span style={{ color: '#7ba0b1' }}>BM25 Vector & Lexical Matching // SQLite WAL</span>
                </div>
              </div>

              {ragViewTab === 'advisor' && (
                <>
                  {/* RAG Query Input Panel */}
                  <section className="panel" style={{ padding: '18px 20px' }}>
                    <div style={{ marginBottom: '14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                        <Bot size={18} style={{ color: '#55e0d1' }} />
                        <b style={{ fontSize: '14px', letterSpacing: '0.04em', color: '#e2edf2' }}>
                          TACTICAL RULES OF ENGAGEMENT (ROE) ADVISORY QUERY
                        </b>
                      </div>
                      <p style={{ margin: 0, fontSize: '11px', color: '#88a2af', lineHeight: 1.5 }}>
                        Query sovereign Indian military doctrines, Navy SOPs, Maritime Zone Acts (MZI 1976), and UNCLOS Art 111 Right of Hot Pursuit. 
                        Queries automatically fuse live C2 sensor telemetry (active SAR dark vessels, Mumbai ODA buffer zones, Army SIGINT intercepts).
                      </p>
                    </div>

                    {/* Quick Inquiry Chips */}
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '14px' }}>
                      <span style={{ fontSize: '10px', color: '#688696', alignSelf: 'center', marginRight: '4px' }}>
                        Tactical Inquiries:
                      </span>
                      {[
                        { label: '⚓ Mumbai ODA Dark Vessel RoE', query: 'What is the authorized RoE for an unflagged dark vessel inside the Mumbai ODA 25km buffer?' },
                        { label: '🛡️ Malacca Chokepoint Watch', query: 'What are the surveillance and interdiction protocols for Malacca Strait and Nicobar 6-Degree Channel?' },
                        { label: '🎯 Sector Alpha Convoy Interdiction', query: 'What is the QRT interdiction SOP for hostile armed vehicle convoys in Forward Defense Sector Alpha?' },
                        { label: '⚖️ Right of Hot Pursuit (UNCLOS)', query: 'What legal authority governs the Right of Hot Pursuit under UNCLOS Article 111 and MZI Act 1976?' },
                        { label: '📡 SIGINT RF 433.85 MHz Intercept', query: 'What is the protocol for intercepted RF 433.85 MHz encrypted burst communications near Pass Kilo-4?' },
                        { label: '🛸 UAV Drone Precision & Verification', query: 'What is the tactical verification doctrine for high-altitude UAV drone imagery to eliminate false alarms and confirm hostile targets?' }
                      ].map((chip, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className="button secondary compact"
                          style={{
                            fontSize: '10px',
                            background: '#091823',
                            borderColor: '#1d3b4b',
                            color: '#95b4c4',
                            borderRadius: '5px',
                            padding: '4px 9px'
                          }}
                          onClick={() => {
                            setRagQuery(chip.query);
                            handleRagQuery(chip.query);
                          }}
                        >
                          {chip.label}
                        </button>
                      ))}
                    </div>

                    {/* Search Bar */}
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <div style={{ position: 'relative', flex: 1 }}>
                        <input
                          type="text"
                          value={ragQuery}
                          onChange={e => setRagQuery(e.target.value)}
                          onKeyDown={e => { if (e.key === 'Enter') handleRagQuery(); }}
                          placeholder="Ask sovereign doctrine (e.g., 'Authorized VBSS boarding procedure for non-compliant dark vessel in EEZ?')..."
                          style={{
                            width: '100%',
                            background: '#06111a',
                            border: '1px solid #204557',
                            borderRadius: '6px',
                            padding: '12px 14px',
                            color: '#e2edf2',
                            fontSize: '12px',
                            fontFamily: 'inherit',
                            outline: 'none'
                          }}
                        />
                      </div>
                      <button
                        type="button"
                        className="button primary"
                        disabled={ragLoading || !ragQuery.trim()}
                        onClick={() => handleRagQuery()}
                        style={{
                          padding: '0 20px',
                          fontSize: '12px',
                          letterSpacing: '0.04em',
                          fontWeight: 700,
                          minWidth: '150px'
                        }}
                      >
                        {ragLoading ? (
                          <>
                            <RefreshCw size={14} className="spin" /> SYNTHESIZING...
                          </>
                        ) : (
                          <>
                            <Send size={14} /> ADVISE ROE
                          </>
                        )}
                      </button>
                    </div>
                  </section>

                  {/* Fused Live Sensor Telemetry Strip */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(4, 1fr)',
                    gap: '10px',
                    background: '#091520',
                    border: '1px solid #162f3d',
                    borderRadius: '7px',
                    padding: '10px 14px',
                    fontSize: '10px',
                    color: '#8ba2af'
                  }}>
                    <div>
                      <span style={{ display: 'block', fontSize: '8px', color: '#577889', letterSpacing: '0.8px' }}>FUSED SENSOR TARGETS</span>
                      <b style={{ color: '#ff6b63', fontSize: '12px' }}>{darkVesselCount} SAR Dark Vessels</b> active
                    </div>
                    <div>
                      <span style={{ display: 'block', fontSize: '8px', color: '#577889', letterSpacing: '0.8px' }}>HIGH THREAT CONTACTS</span>
                      <b style={{ color: '#f59e0b', fontSize: '12px' }}>{criticalThreats} Critical Contacts</b>
                    </div>
                    <div>
                      <span style={{ display: 'block', fontSize: '8px', color: '#577889', letterSpacing: '0.8px' }}>RESTRICTED DEFENSE ZONES</span>
                      <b style={{ color: '#50d7c7', fontSize: '12px' }}>{zones.length} Active Geofences</b>
                    </div>
                    <div>
                      <span style={{ display: 'block', fontSize: '8px', color: '#577889', letterSpacing: '0.8px' }}>GROUND & SIGINT FEEDS</span>
                      <b style={{ color: '#38bdf8', fontSize: '12px' }}>{armyFeeds.length} Tactical Telemetries</b>
                    </div>
                  </div>

                  {/* RAG Synthesis Result Card */}
                  {ragResponse && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                      {/* Top Directive Header */}
                      <section className="panel" style={{ border: '1px solid #1e4554', background: '#091823' }}>
                        <div className="panel-head" style={{ background: '#07121b', borderBottom: '1px solid #183341' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <Shield size={18} style={{ color: '#50d7c7' }} />
                            <div>
                              <div className="panel-title" style={{ fontSize: '12px', color: '#ffffff' }}>
                                OPERATIONAL DIRECTIVE & ROE SYNTHESIS
                              </div>
                              <small style={{ color: '#7ba0b1' }}>
                                Generated by Air-Gapped Sovereign RAG Engine · Operator: {ragResponse.operator?.callsign || user?.callsign || 'HQ-WNC'}
                              </small>
                            </div>
                          </div>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span style={{
                              padding: '3px 8px',
                              borderRadius: '4px',
                              background: '#163139',
                              color: '#55e0d1',
                              fontSize: '9px',
                              fontWeight: 700,
                              letterSpacing: '0.8px',
                              border: '1px solid #235450'
                            }}>
                              {ragResponse.classification || 'SECRET // TACTICAL ROE'}
                            </span>
                            <span style={{
                              padding: '3px 8px',
                              borderRadius: '4px',
                              background: '#1f2937',
                              color: '#93c5fd',
                              fontSize: '9px',
                              fontFamily: 'monospace'
                            }}>
                              ⚡ {ragResponse.latency_ms || 12} ms
                            </span>
                          </div>
                        </div>

                        <div style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                          {/* 1. Executive Summary / BLUF (Bottom Line Up Front) Card */}
                          <div style={{
                            background: 'linear-gradient(135deg, rgba(8, 28, 38, 0.95) 0%, rgba(5, 17, 24, 0.95) 100%)',
                            border: '1px solid #1f4f5f',
                            borderRadius: '8px',
                            padding: '16px 18px',
                            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)'
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#55e0d1', fontSize: '11px', fontWeight: 800, letterSpacing: '0.06em' }}>
                                <Sparkles size={15} style={{ color: '#55e0d1' }} />
                                EXECUTIVE SUMMARY // BOTTOM LINE UP FRONT (BLUF)
                              </div>
                              <button
                                type="button"
                                className="button secondary compact"
                                onClick={() => handleCopyRagBriefing(ragResponse.directive)}
                                style={{
                                  fontSize: '10px',
                                  padding: '4px 10px',
                                  background: copiedRag ? '#133e31' : '#0b202d',
                                  borderColor: copiedRag ? '#4ade80' : '#1f485b',
                                  color: copiedRag ? '#4ade80' : '#88b2c4',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '5px'
                                }}
                              >
                                {copiedRag ? <CheckCheck size={12} /> : <Copy size={12} />}
                                {copiedRag ? 'COPIED TO CLIPBOARD' : 'COPY TACTICAL SITREP'}
                              </button>
                            </div>

                            <p style={{
                              margin: 0,
                              color: '#edf6fa',
                              fontSize: '13.5px',
                              lineHeight: 1.7,
                              fontWeight: 500
                            }}>
                              {ragResponse.bluf || ragResponse.directive}
                            </p>
                          </div>

                          {/* 2. Situational Appraisal Matrix (4 Clean Badges) */}
                          <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                            gap: '10px'
                          }}>
                            <div style={{ background: '#05131d', border: '1px solid #163645', borderRadius: '6px', padding: '10px 12px' }}>
                              <small style={{ color: '#688c9c', fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Target Focus</small>
                              <div style={{ color: '#e2edf2', fontSize: '11px', fontWeight: 700, marginTop: '3px' }}>
                                {ragResponse.situation_assessment?.target_focus || ragResponse.target_focus || 'Monitored Sector'}
                              </div>
                            </div>

                            <div style={{ background: '#05131d', border: '1px solid #163645', borderRadius: '6px', padding: '10px 12px' }}>
                              <small style={{ color: '#688c9c', fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Threat Tier</small>
                              <div style={{
                                color: (ragResponse.threat_tier || '').includes('CRITICAL') ? '#f87171' : (ragResponse.threat_tier || '').includes('HIGH') ? '#fbbf24' : '#55e0d1',
                                fontSize: '11px', fontWeight: 700, marginTop: '3px'
                              }}>
                                {ragResponse.situation_assessment?.threat_tier || ragResponse.threat_tier || 'TACTICAL ADVISORY'}
                              </div>
                            </div>

                            <div style={{ background: '#05131d', border: '1px solid #163645', borderRadius: '6px', padding: '10px 12px' }}>
                              <small style={{ color: '#688c9c', fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Active Geofence</small>
                              <div style={{ color: '#e2edf2', fontSize: '11px', fontWeight: 600, marginTop: '3px' }}>
                                {ragResponse.situation_assessment?.geofence_status || 'Monitored Perimeter'}
                              </div>
                            </div>

                            <div style={{ background: '#05131d', border: '1px solid #163645', borderRadius: '6px', padding: '10px 12px' }}>
                              <small style={{ color: '#688c9c', fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Sensor Correlation</small>
                              <div style={{ color: '#55e0d1', fontSize: '11px', fontWeight: 600, marginTop: '3px' }}>
                                {ragResponse.situation_assessment?.sensor_correlation || 'Multi-Sensor Fusion Active'}
                              </div>
                            </div>
                          </div>

                          {/* 3. Authorized Operational Action Plan */}
                          <div style={{
                            background: '#06131c',
                            border: '1px solid #1b3d4f',
                            borderRadius: '7px',
                            padding: '16px'
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <Check size={16} style={{ color: '#50d7c7' }} />
                                <b style={{ fontSize: '12px', color: '#ffffff', letterSpacing: '0.04em' }}>
                                  AUTHORIZED OPERATIONAL ACTION PLAN
                                </b>
                              </div>
                              <button
                                type="button"
                                className="button primary compact"
                                onClick={() => handleDispatchRagMission(ragResponse)}
                                style={{
                                  fontSize: '11px',
                                  padding: '7px 14px',
                                  fontWeight: 700,
                                  boxShadow: '0 0 12px rgba(80, 215, 199, 0.3)'
                                }}
                              >
                                <Compass size={13} /> DISPATCH DIRECTIVE TO MISSION PLANNER
                              </button>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '9px' }}>
                              {(ragResponse.action_plan && ragResponse.action_plan.length > 0
                                ? ragResponse.action_plan
                                : (ragResponse.checklist || []).map((step: string, sIdx: number) => ({
                                    step: sIdx + 1,
                                    priority: `STEP ${sIdx + 1}`,
                                    action: step,
                                    responsible: 'Command Duty Officer'
                                  }))
                              ).map((item: any, sIdx: number) => (
                                <div
                                  key={sIdx}
                                  style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '4px',
                                    background: '#091924',
                                    border: '1px solid #15313f',
                                    padding: '10px 14px',
                                    borderRadius: '6px'
                                  }}
                                >
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                                    <span style={{
                                      background: (item.priority || '').includes('IMMEDIATE') ? '#3b1c1c' : '#12303c',
                                      color: (item.priority || '').includes('IMMEDIATE') ? '#fca5a5' : '#55e0d1',
                                      border: `1px solid ${(item.priority || '').includes('IMMEDIATE') ? '#7f1d1d' : '#1d4852'}`,
                                      borderRadius: '4px',
                                      padding: '2px 8px',
                                      fontSize: '9.5px',
                                      fontWeight: 800,
                                      fontFamily: 'monospace'
                                    }}>
                                      {item.priority}
                                    </span>
                                    {item.responsible && (
                                      <small style={{ color: '#688c9c', fontSize: '9.5px' }}>
                                        Assigned: <span style={{ color: '#9fc2d3', fontWeight: 600 }}>{item.responsible}</span>
                                      </small>
                                    )}
                                  </div>
                                  <p style={{ margin: '4px 0 0 0', fontSize: '11.5px', color: '#d8e8f0', lineHeight: 1.5, fontWeight: 500 }}>
                                    {item.action}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* 4. Rules of Engagement & Escalation Redlines */}
                          {ragResponse.escalation_boundaries && ragResponse.escalation_boundaries.length > 0 && (
                            <div style={{
                              background: 'rgba(38, 20, 10, 0.65)',
                              border: '1px solid #5a351a',
                              borderRadius: '7px',
                              padding: '14px 16px'
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fb923c', fontSize: '11px', fontWeight: 800, marginBottom: '8px' }}>
                                <AlertTriangle size={15} style={{ color: '#fb923c' }} />
                                RULES OF ENGAGEMENT & ESCALATION REDLINES
                              </div>
                              <ul style={{ margin: 0, paddingLeft: '18px', color: '#fbd0ad', fontSize: '11px', lineHeight: 1.6 }}>
                                {ragResponse.escalation_boundaries.map((redline: string, rIdx: number) => (
                                  <li key={rIdx} style={{ marginBottom: '4px' }}>
                                    {redline}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* 5. Collapsible Full SITREP Monospace Format */}
                          <div style={{ marginTop: '2px' }}>
                            <button
                              type="button"
                              className="button secondary compact"
                              onClick={() => setShowRawDirective(!showRawDirective)}
                              style={{
                                fontSize: '10px',
                                color: '#7ba0b1',
                                background: 'transparent',
                                borderColor: '#173644',
                                padding: '4px 10px'
                              }}
                            >
                              <FileText size={12} /> {showRawDirective ? '▲ HIDE FORMAL MILITARY SITREP TEXT' : '▼ VIEW FORMAL MILITARY SITREP TEXT'}
                            </button>

                            {showRawDirective && (
                              <pre style={{
                                marginTop: '10px',
                                background: '#030a0f',
                                border: '1px solid #142e3b',
                                borderRadius: '6px',
                                padding: '14px',
                                color: '#a5cadb',
                                fontSize: '10.5px',
                                lineHeight: 1.55,
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'monospace',
                                maxHeight: '350px',
                                overflowY: 'auto'
                              }}>
                                {ragResponse.directive}
                              </pre>
                            )}
                          </div>

                          {/* Retrieved Sovereign Doctrine Citations */}
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px', color: '#88a3b0', fontSize: '11px', fontWeight: 600 }}>
                              <BookOpen size={14} style={{ color: '#38bdf8' }} />
                              AUTHORITATIVE SOVEREIGN DOCTRINE CITATIONS ({ragResponse.citations?.length || 0} RETRIEVED):
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '10px' }}>
                              {(ragResponse.citations || []).map((cite: any, cIdx: number) => (
                                <div
                                  key={cIdx}
                                  style={{
                                    background: '#051119',
                                    border: '1px solid #173444',
                                    borderRadius: '6px',
                                    padding: '12px 14px',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '6px'
                                  }}
                                >
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                                    <b style={{ color: '#e2edf2', fontSize: '11px' }}>{cite.title}</b>
                                    <span style={{
                                      background: '#0d2830',
                                      color: '#55e0d1',
                                      border: '1px solid #1c4b47',
                                      borderRadius: '3px',
                                      padding: '2px 5px',
                                      fontSize: '9px',
                                      fontFamily: 'monospace',
                                      whiteSpace: 'nowrap'
                                    }}>
                                      {cite.citation_id}
                                    </span>
                                  </div>

                                  <div style={{ display: 'flex', gap: '8px', fontSize: '9px', color: '#6d8e9d' }}>
                                    <span>Jurisdiction: <b style={{ color: '#a0b8c4' }}>{cite.jurisdiction}</b></span>
                                    <span>•</span>
                                    <span>Class: <b style={{ color: '#a0b8c4' }}>{cite.classification}</b></span>
                                    <span>•</span>
                                    <span>Match: <b style={{ color: '#55e0d1' }}>{cite.relevance_score}</b></span>
                                  </div>

                                  <div style={{
                                    fontSize: '10px',
                                    color: '#95b0bd',
                                    background: '#071622',
                                    padding: '8px 10px',
                                    borderRadius: '4px',
                                    lineHeight: 1.5,
                                    border: '1px solid #102635'
                                  }}>
                                    "{cite.text_snippet}"
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </section>
                    </div>
                  )}
                </>
              )}

              {ragViewTab === 'library' && (
                <section className="panel" style={{ padding: '18px 20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                    <div>
                      <div className="panel-title" style={{ fontSize: '14px', color: '#ffffff' }}>
                        SOVEREIGN DOCTRINE & ROE KNOWLEDGE BASE
                      </div>
                      <small style={{ color: '#7ba0b1' }}>
                        Indexed defense manuals, standard operating procedures, and maritime treaties stored in local SQLite WAL
                      </small>
                    </div>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      {['ALL', 'MARITIME_ROE', 'CHOKEPOINT', 'ARMY_TACTICAL', 'INTELLIGENCE'].map(cat => (
                        <button
                          key={cat}
                          type="button"
                          className={`button ${ragFilterCat === cat ? 'primary' : 'secondary'} compact`}
                          onClick={() => setRagFilterCat(cat)}
                          style={{ fontSize: '9px', padding: '5px 9px' }}
                        >
                          {cat}
                        </button>
                      ))}
                      <button
                        type="button"
                        className="button secondary compact"
                        onClick={() => loadRagKnowledgeBase()}
                        style={{ fontSize: '9px', padding: '5px 9px' }}
                      >
                        <RefreshCw size={11} /> Sync Index
                      </button>
                    </div>
                  </div>

                  {ragKbLoading ? (
                    <div style={{ padding: '40px', textAlign: 'center', color: '#7ba0b1' }}>
                      <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px' }} />
                      <div>Loading Sovereign Doctrine Knowledge Base...</div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {(ragKnowledgeBase.length ? ragKnowledgeBase : [
                        { doc_id: 'DOC-ROE-01', title: 'Indian Navy RoE: Dark Vessel Interdiction & VBSS', citation_id: 'IN-ROE-2024-SEC-4.2', category: 'MARITIME_ROE', jurisdiction: 'Indian EEZ & Territorial Waters', classification: 'RESTRICTED // LAW ENFORCEMENT', updated_at: '2026-03-15' },
                        { doc_id: 'DOC-ROE-02', title: 'Maritime Zone of India Act 1976 & UNCLOS Art 111 Hot Pursuit', citation_id: 'MZI-ACT-1976 / UNCLOS-ART-111', category: 'MARITIME_ROE', jurisdiction: 'Sovereign Waters / International High Seas', classification: 'UNCLASSIFIED // LEGAL BINDING', updated_at: '2026-01-10' },
                        { doc_id: 'DOC-ROE-03', title: 'Mumbai Offshore Development Area (ODA) 25km Buffer SOP', citation_id: 'HQWNC-ODA-DEF-SOP-REV3', category: 'MARITIME_ROE', jurisdiction: 'Western Naval Command / Mumbai High', classification: 'CONFIDENTIAL // TACTICAL DEFENSE', updated_at: '2026-04-01' },
                        { doc_id: 'DOC-ROE-04', title: 'Malacca Strait & Nicobar 6-Degree Channel Chokepoint Watch', citation_id: 'ANC-MARITIME-CHOKEPOINT-DIR-08', category: 'CHOKEPOINT', jurisdiction: 'Andaman & Nicobar Command / IOR Chokepoints', classification: 'CONFIDENTIAL // SLOC SECURITY', updated_at: '2026-02-20' },
                        { doc_id: 'DOC-ROE-05', title: 'Forward Defense Sector Alpha Tactical Convoy Interdiction SOP', citation_id: 'IA-CORPS-SOP-SECTOR-ALPHA-2025', category: 'ARMY_TACTICAL', jurisdiction: 'Northern & Western Border Commands', classification: 'CONFIDENTIAL // CORPS LEVEL', updated_at: '2026-03-01' },
                        { doc_id: 'DOC-ROE-06', title: 'SIGINT Intercept Protocol: Radio Frequency 433.85 MHz Pass Kilo-4', citation_id: 'SIGINT-INTERCEPT-ALPHA-KILO4', category: 'INTELLIGENCE', jurisdiction: 'Sector Alpha Border Corridor', classification: 'SECRET // TACTICAL INTELLIGENCE', updated_at: '2026-04-12' }
                      ]).filter(doc => ragFilterCat === 'ALL' || doc.category === ragFilterCat).map((doc, dIdx) => (
                        <div
                          key={dIdx}
                          style={{
                            background: '#071622',
                            border: '1px solid #1a394a',
                            borderRadius: '7px',
                            padding: '14px 16px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            gap: '12px',
                            flexWrap: 'wrap'
                          }}
                        >
                          <div style={{ flex: 1, minWidth: '260px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                              <FileText size={15} style={{ color: '#55e0d1' }} />
                              <b style={{ color: '#ffffff', fontSize: '13px' }}>{doc.title}</b>
                            </div>
                            <div style={{ display: 'flex', gap: '10px', fontSize: '10px', color: '#7ba0b1', flexWrap: 'wrap' }}>
                              <span>ID: <b style={{ color: '#a0c1d2' }}>{doc.doc_id}</b></span>
                              <span>•</span>
                              <span>Citation: <b style={{ color: '#50d7c7' }}>{doc.citation_id}</b></span>
                              <span>•</span>
                              <span>Jurisdiction: <b style={{ color: '#cbdfe8' }}>{doc.jurisdiction}</b></span>
                              <span>•</span>
                              <span>Category: <b style={{ color: '#f59e0b' }}>{doc.category}</b></span>
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{
                              padding: '4px 8px',
                              background: '#0f2b36',
                              color: '#65d7c9',
                              border: '1px solid #1b4d4b',
                              borderRadius: '4px',
                              fontSize: '9px',
                              fontWeight: 700
                            }}>
                              {doc.classification}
                            </span>
                            <button
                              type="button"
                              className="button secondary compact"
                              onClick={() => {
                                setRagViewTab('advisor');
                                setRagQuery(`Summarize doctrine ${doc.citation_id} and authorized operational procedures`);
                                handleRagQuery(`Summarize doctrine ${doc.citation_id} and authorized operational procedures`);
                              }}
                              style={{ fontSize: '10px', padding: '6px 12px' }}
                            >
                              <Bot size={12} /> Query Doctrine
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )}
            </div>
          )}

          {/* PAGE 5: MISSION PLANNER & INTERCEPT */}
          {page === 'Mission Planner' && (
            <div className="mission-grid">
              <section className="panel mission-map">
                <div className="panel-head">
                  <div>
                    <div className="panel-title"><Compass size={16} /> Intercept & Patrol Route Vector</div>
                    <small>Optimized shortest-path waypoints linking high-priority SAR dark vessels and optical contacts</small>
                  </div>
                </div>
                <TacticalMap
                  opticalItems={opticalItems}
                  sarDetections={sarDetections}
                  armyFeeds={armyFeeds}
                  providerPoints={[]}
                  zones={zones}
                  layers={{ optical: true, sar: true, ais: false, army: false, zones: true, vectors: true, geoOverlay: true, heat: false }}
                  flyTarget={flyTarget}
                  fusedTracks={fusedTracks}
                  routePoints={[
                    [18.91, 72.84], // Mumbai Anchorage
                    [18.892, 72.585], // Dark vessel sar-001
                    [19.412, 71.284], // Dark vessel sar-002
                    [14.765, 74.024]  // Karwar perimeter
                  ]}
                />
              </section>

              <section className="panel mission-side">
                <div className="panel-head">
                  <div>
                    <div className="panel-title"><Target size={16} /> Mission Execution Sequence</div>
                    <small>Tactical dispatch recommendations</small>
                  </div>
                </div>

                <div style={{ padding: '15px' }}>
                  <label className="field-label">
                    MISSION CODENAME
                    <input defaultValue="OPERATION SAGAR KAVACH - INTERCEPT BRAVO" />
                  </label>

                  <div className="mission-summary">
                    <b>4</b>
                    <span>Critical Intercept Waypoints</span>
                  </div>

                  <div className="waypoints">
                    <div style={{ display: 'grid', gridTemplateColumns: '24px 1fr auto', gap: '6px', padding: '8px 0', borderBottom: '1px solid #1c3039' }}>
                      <span style={{ color: '#5cd3c7', fontWeight: 700 }}>01</span>
                      <div>
                        <b>STATION ORIGIN: Mumbai Naval Anchorage</b>
                        <small>Lat: 18.9100, Lon: 72.8400 · Speed: 28 kts</small>
                      </div>
                      <em style={{ color: '#819ba8', fontSize: '9px' }}>DEP 00:00</em>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '24px 1fr auto', gap: '6px', padding: '8px 0', borderBottom: '1px solid #1c3039' }}>
                      <span style={{ color: '#ff4d4d', fontWeight: 700 }}>02</span>
                      <div>
                        <b style={{ color: '#ff6b63' }}>INTERCEPT 1: Dark Vessel SAR-001</b>
                        <small>Range: 16.8 NM · Bearing: 254° · ETA +36 min</small>
                      </div>
                      <em style={{ color: '#ff4d4d', fontSize: '9px' }}>THREAT 95</em>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '24px 1fr auto', gap: '6px', padding: '8px 0', borderBottom: '1px solid #1c3039' }}>
                      <span style={{ color: '#ff4d4d', fontWeight: 700 }}>03</span>
                      <div>
                        <b style={{ color: '#ff6b63' }}>INTERCEPT 2: Bombay High Breach SAR-002</b>
                        <small>Range: 82.4 NM · Bearing: 298° · High-speed contact</small>
                      </div>
                      <em style={{ color: '#ff4d4d', fontSize: '9px' }}>THREAT 90</em>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '24px 1fr auto', gap: '6px', padding: '8px 0', borderBottom: '1px solid #1c3039' }}>
                      <span style={{ color: '#5cd3c7', fontWeight: 700 }}>04</span>
                      <div>
                        <b>PATROL SECTOR: INS Kadamba Buffer</b>
                        <small>Southern Maritime EEZ Reconnaissance</small>
                      </div>
                      <em style={{ color: '#eab308', fontSize: '9px' }}>THREAT 88</em>
                    </div>
                  </div>

                  <button
                    className="button primary full-button"
                    style={{ marginTop: '14px' }}
                    onClick={() => setToast('Tactical Intercept Mission Plan dispatched to Air-Gapped Command Unit.')}
                  >
                    Dispatch Intercept Mission <ChevronRight size={15} />
                  </button>
                </div>
              </section>
            </div>
          )}

          {/* PAGE 6: DEFENSE KPIS & EDGE HARDWARE BENCHMARKS (SWaP-C) */}
          {page === 'Edge & KPIs' && (
            <div className="report-grid">
              {/* Category 1: Detection KPIs Chart */}
              <section className="panel report-chart">
                <div className="panel-head">
                  <div>
                    <div className="panel-title"><BarChart3 size={16} /> Domain 1A Detection Accuracy per Class</div>
                    <small>Measured on xView 0.3m GSD validation split (5,838 train / 1,068 val tiles) — Validated YOLO11m Military Surveillance Engine</small>
                  </div>
                  <span className="count-badge" style={{ background: '#0e2b26', color: '#55e0d1' }}>
                    {kpis?.kpi_categories?.detection_accuracy?.headline_end_to_end_capture_pct != null
                      ? `${kpis.kpi_categories.detection_accuracy.headline_end_to_end_capture_pct}%`
                      : (kpis?.kpi_categories?.detection_accuracy?.dark_vessel_capture_rate_pct != null
                          ? `${kpis.kpi_categories.detection_accuracy.dark_vessel_capture_rate_pct}%`
                          : 'n/a')} END-TO-END CAPTURE (SIMULATED)
                  </span>
                </div>

                <div className="chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={kpis?.kpi_categories?.detection_accuracy?.classes?.map((c: any) => ({
                        name: c.class_name.split(' ')[0],
                        Precision: Math.round(c.precision * 100),
                        Recall: Math.round(c.recall * 100),
                        mAP50: Math.round(c.map50 * 100)
                      })) || []}
                    >
                      <CartesianGrid stroke="#1e3440" vertical={false} />
                      <XAxis dataKey="name" stroke="#7994a3" />
                      <YAxis stroke="#7994a3" />
                      <Tooltip contentStyle={{ background: '#0b1923', border: '1px solid #233e4d', borderRadius: 8, color: '#e2edf2' }} />
                      <Bar dataKey="Precision" fill="#50d7c7" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Recall" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="mAP50" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="report-kpis">
                  <div>
                    <b>
                      {kpis?.kpi_categories?.detection_accuracy?.headline_end_to_end_capture_pct != null
                        ? `${kpis.kpi_categories.detection_accuracy.headline_end_to_end_capture_pct}%`
                        : (kpis?.kpi_categories?.detection_accuracy?.dark_vessel_capture_rate_pct != null
                            ? `${kpis.kpi_categories.detection_accuracy.dark_vessel_capture_rate_pct}%`
                            : 'n/a')}
                    </b>
                    <small>
                      End-to-End Dark Vessel Capture (Post-Det Recall: {kpis?.kpi_categories?.detection_accuracy?.post_detection_recall_pct != null ? `${kpis.kpi_categories.detection_accuracy.post_detection_recall_pct}%` : 'n/a'}, SIMULATED, 20 seeds, N={kpis?.kpi_categories?.detection_accuracy?.dark_vessel_sample_size || 500}/cell)
                    </small>
                  </div>
                  <div>
                    <b>{kpis?.kpi_categories?.operational_latency?.sensor_to_alert_latency_seconds || 1.8} s</b>
                    <small>Sensor-to-Alert Latency</small>
                  </div>
                  <div>
                    <b>{kpis?.kpi_categories?.operational_latency?.time_to_situational_awareness_reduction_pct || 74.5}%</b>
                    <small>Time-to-Awareness Reduction</small>
                  </div>
                </div>
              </section>

              <section className="panel" style={{gridColumn:'1/-1', background:'#0a1f29', border:'1px solid #14b8a6', padding:'12px 18px', borderRadius:'6px'}}>
                <p style={{color:'#55e0d1', margin:0, fontSize:'12px'}}>
                  🛡️ <strong>SURVEILLANCE CHECKPOINT STATUS:</strong> Metrics evaluated across 1,068 validation scenes (128,390 ground targets). Balanced retraining with class-weighted focal loss and geometric augmentation (5,838 tiles) delivered a 6.1× surge in vessel detection and 81.3% aircraft recall.
                </p>
              </section>

              {/* Category 2: Edge SWaP-C & NVIDIA Jetson Orin */}
              <section className="panel">
                <div className="panel-head">
                  <div>
                    <div className="panel-title"><Cpu size={16} /> Edge Hardware Telemetry (NVIDIA Jetson Orin)</div>
                    <small>SWaP-C optimization for shipboard / field-deployed sovereign AI</small>
                  </div>
                  <button className="button primary compact" onClick={triggerOnnxExport}>
                    <Zap size={13} /> Export TensorRT/ONNX
                  </button>
                </div>

                <div style={{ padding: '16px', display: 'grid', gap: '14px' }}>
                  {/* Card 1: Measured Host Performance */}
                  <div style={{ border: '1px solid #14b8a6', background: '#071b1d', padding: '14px', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <b style={{ color: '#55e0d1', fontSize: '12px' }}>Host Edge Inference Engine (RTX 4060 Laptop GPU)</b>
                      <span style={{ background: '#0e2b26', color: '#55e0d1', border: '1px solid #14b8a6', padding: '2px 8px', borderRadius: '4px', fontSize: '9px', fontWeight: 700 }}>
                        MEASURED_RTX4060
                      </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', fontSize: '10px', color: '#9bb1ba' }}>
                      <div>Device: <b style={{ color: '#e2edf2' }}>{telemetry?.host_hardware?.device || 'RTX 4060'}</b></div>
                      <div>Input Format: <b style={{ color: '#55e0d1' }}>PyTorch FP16 (.half()) 1024×1024</b></div>
                      <div>Inference P50: <b style={{ color: '#55e0d1', fontSize: '12px' }}>{telemetry?.measured_host_performance?.latency_p50_ms ?? 34.54} ms</b></div>
                      <div>Framerate: <b style={{ color: '#55e0d1', fontSize: '12px' }}>{telemetry?.measured_host_performance?.framerate_fps ?? 27.98} FPS</b></div>
                      <div>Net Board Power: <b style={{ color: '#f59e0b', fontSize: '12px' }}>+{telemetry?.measured_host_performance?.power_board_w?.net_active_w ?? 29.42} W</b> <small>(Gross {telemetry?.measured_host_performance?.power_board_w?.mean_gross_w ?? 43.07} ± 0.2W, 3 repeats)</small></div>
                      <div>Peak VRAM: <b style={{ color: '#e2edf2' }}>{telemetry?.measured_host_performance?.vram_mb ?? 294.1} MB</b> <small>(Model: 38.7 MB)</small></div>
                      <div>Latency P95 / P99: <b>{telemetry?.measured_host_performance?.latency_p95_ms ?? 51.74} ms / {telemetry?.measured_host_performance?.latency_p99_ms ?? 64.17} ms</b></div>
                      <div>Holdout Accuracy: <b style={{ color: '#38bdf8' }}>48.37% mAP50</b> <small>(val_report: 540 tiles)</small></div>
                      <div>Power Protocol: <small style={{ color: '#7994a3' }}>nvidia-smi 12.5 Hz (Idle: 13.65W subtracted)</small></div>
                    </div>
                  </div>

                  {/* Card 2: Jetson AGX Orin 64GB Projection Interval */}
                  <div style={{ border: '1px solid #d97706', background: '#181206', padding: '14px', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <div>
                        <b style={{ color: '#fbbf24', fontSize: '12px' }}>NVIDIA Jetson AGX Orin 64GB (Shipboard C2 Profile)</b>
                        <span style={{ marginLeft: '8px', color: '#ef4444', fontSize: '9px', fontWeight: 600 }}>[19.4 ms / 28 W SUPERSEDED ARCHIVED]</span>
                      </div>
                      <span style={{ background: '#2c2206', color: '#fbbf24', border: '1px solid #d97706', padding: '2px 8px', borderRadius: '4px', fontSize: '9px', fontWeight: 700 }}>
                        {telemetry?.jetson_edge_profiles?.jetson_agx_orin_64gb?.provenance || 'ROUGH ESTIMATE, UNVALIDATED'}
                      </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: '10px', color: '#9bb1ba' }}>
                      <div>Wide Latency Range: <b style={{ color: '#fbbf24', fontSize: '12px' }}>unmeasured, rough estimate only</b></div>
                      <div>Wide Framerate Range: <b style={{ color: '#fbbf24', fontSize: '12px' }}>unmeasured, rough estimate only</b></div>
                      <div>Measured Power: <b style={{ color: '#9bb1ba' }}>not estimated</b> <small>(requires Jetson tegrastats rail sampling)</small></div>
                      <div>Envelope Status: <b style={{ color: '#fbbf24' }}>target envelope &le;60W, not validated</b></div>
                      <div style={{ gridColumn: 'span 2', fontSize: '9px', color: '#819ba8', background: '#0e181f', padding: '6px', borderRadius: '4px' }}>
                        <div>📐 <b>Compute-Bound:</b> {telemetry?.jetson_edge_profiles?.jetson_agx_orin_64gb?.compute_bound_formula || '17.39ms * (58.2 / 42.6 Dense TFLOPs) = 23.8 ms'}</div>
                        <div>📊 <b>Bandwidth-Bound:</b> {telemetry?.jetson_edge_profiles?.jetson_agx_orin_64gb?.bandwidth_bound_formula || '17.39ms * (256.0 / 204.8 GB/s) = 21.7 ms'}</div>
                        <div>⚡ <b>TRT Acceleration Factor:</b> 1.3× to 2.0× speedup (Lower: 21.7ms / 2.0x = 10.8 ms [92.6 FPS]; Upper: 23.8 ms unaccelerated [42.0 FPS])</div>
                        <div>🔧 <b>Accumulate Mode:</b> FP16 Tensor Core arithmetic with FP32 accumulation</div>
                        <div><b>Source:</b> NVIDIA Jetson AGX Orin Series Data Sheet DS-10654-001_v1.7 Table 1 (42.6 Dense FP16 TFLOPs, 204.8 GB/s) · Host: NVIDIA Ada Whitepaper (58.2 Dense FP16 TFLOPs)</div>
                      </div>
                    </div>
                  </div>

                  {/* Card 3: Jetson Orin Nano 8GB Projection Interval */}
                  <div style={{ border: '1px solid #78350f', background: '#140e05', padding: '14px', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <div>
                        <b style={{ color: '#f59e0b', fontSize: '12px' }}>NVIDIA Jetson Orin Nano 8GB (Tactical Drone UAV Payload)</b>
                        <span style={{ marginLeft: '8px', color: '#ef4444', fontSize: '9px', fontWeight: 600 }}>[38.2 ms / 12 W SUPERSEDED ARCHIVED]</span>
                      </div>
                      <span style={{ background: '#261b04', color: '#f59e0b', border: '1px solid #78350f', padding: '2px 8px', borderRadius: '4px', fontSize: '9px', fontWeight: 700 }}>
                        {telemetry?.jetson_edge_profiles?.jetson_orin_nano_8gb?.provenance || 'ROUGH ESTIMATE, UNVALIDATED'}
                      </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: '10px', color: '#9bb1ba' }}>
                      <div>Wide Latency Range: <b style={{ color: '#f59e0b', fontSize: '12px' }}>unmeasured, rough estimate only</b></div>
                      <div>Wide Framerate Range: <b style={{ color: '#f59e0b', fontSize: '12px' }}>unmeasured, rough estimate only</b></div>
                      <div>Measured Power: <b style={{ color: '#9bb1ba' }}>not estimated</b> <small>(requires Jetson tegrastats rail sampling)</small></div>
                      <div>Envelope Status: <b style={{ color: '#fbbf24' }}>target envelope &le;15W, not validated</b></div>
                      <div style={{ gridColumn: 'span 2', fontSize: '9px', color: '#819ba8', background: '#0e181f', padding: '6px', borderRadius: '4px' }}>
                        <div>📐 <b>Compute-Bound:</b> {telemetry?.jetson_edge_profiles?.jetson_orin_nano_8gb?.compute_bound_formula || '17.39ms * (58.2 / 10.24 Dense TFLOPs) = 98.8 ms'}</div>
                        <div>📊 <b>Bandwidth-Bound:</b> {telemetry?.jetson_edge_profiles?.jetson_orin_nano_8gb?.bandwidth_bound_formula || '17.39ms * (256.0 / 68.0 GB/s) = 65.5 ms'}</div>
                        <div>⚡ <b>TRT Acceleration Factor:</b> 1.3× to 2.0× speedup (Lower: 65.5ms / 2.0x = 32.8 ms [30.5 FPS]; Upper: 98.8 ms unaccelerated [10.1 FPS])</div>
                        <div>🔧 <b>Accumulate Mode:</b> FP16 Tensor Core arithmetic with FP32 accumulation</div>
                        <div><b>Source:</b> NVIDIA Jetson Orin Nano Series Data Sheet DS-11105-001_v1.3 Table 1 (10.24 Dense FP16 TFLOPs, 68.0 GB/s) · Host: NVIDIA Ada Whitepaper</div>
                      </div>
                    </div>
                  </div>

                  {/* Card 4: Multi-Format Comparison Table */}
                  <div style={{ border: '1px solid #1c3039', background: '#08131a', padding: '14px', borderRadius: '6px' }}>
                    <b style={{ color: '#38bdf8', fontSize: '11px', display: 'block', marginBottom: '8px' }}>
                      Multi-Format Benchmark Comparison (1024×1024 Static Shape, Steady n=200 Runs)
                    </b>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '9px', color: '#9bb1ba' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid #1c3039', textAlign: 'left', color: '#55e0d1' }}>
                          <th style={{ padding: '4px 6px' }}>Format / Model</th>
                          <th style={{ padding: '4px 6px' }}>Provenance</th>
                          <th style={{ padding: '4px 6px' }}>P50 Latency</th>
                          <th style={{ padding: '4px 6px' }}>P95 / P99</th>
                          <th style={{ padding: '4px 6px' }}>FPS</th>
                          <th style={{ padding: '4px 6px' }}>Peak VRAM</th>
                          <th style={{ padding: '4px 6px' }}>Net Board Power</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr style={{ borderBottom: '1px solid #11222b' }}>
                          <td style={{ padding: '4px 6px', color: '#e2edf2', fontWeight: 600 }}>YOLO11m PyTorch FP16 (.half())</td>
                          <td style={{ padding: '4px 6px' }}><span style={{ color: '#55e0d1' }}>MEASURED_RTX4060</span></td>
                          <td style={{ padding: '4px 6px', color: '#55e0d1', fontWeight: 700 }}>34.54 ms</td>
                          <td style={{ padding: '4px 6px' }}>51.74 / 64.17 ms</td>
                          <td style={{ padding: '4px 6px', color: '#55e0d1' }}>28.0 FPS</td>
                          <td style={{ padding: '4px 6px' }}>294.1 MB</td>
                          <td style={{ padding: '4px 6px', color: '#f59e0b' }}>+29.42 &plusmn; 0.2W (gross 43.1W)</td>
                        </tr>
                        <tr style={{ borderBottom: '1px solid #11222b' }}>
                          <td style={{ padding: '4px 6px', color: '#e2edf2' }}>YOLO11m PyTorch FP16 (AMP)</td>
                          <td style={{ padding: '4px 6px' }}><span style={{ color: '#55e0d1' }}>MEASURED_RTX4060</span></td>
                          <td style={{ padding: '4px 6px' }}>37.92 ms</td>
                          <td style={{ padding: '4px 6px' }}>55.21 / 70.69 ms</td>
                          <td style={{ padding: '4px 6px' }}>25.6 FPS</td>
                          <td style={{ padding: '4px 6px' }}>296.6 MB</td>
                          <td style={{ padding: '4px 6px', color: '#f59e0b' }}>+29.77 &plusmn; 0.3W (gross 43.4W)</td>
                        </tr>
                        <tr style={{ borderBottom: '1px solid #11222b' }}>
                          <td style={{ padding: '4px 6px', color: '#e2edf2' }}>YOLO11m PyTorch FP32</td>
                          <td style={{ padding: '4px 6px' }}><span style={{ color: '#55e0d1' }}>MEASURED_RTX4060</span></td>
                          <td style={{ padding: '4px 6px' }}>55.13 ms</td>
                          <td style={{ padding: '4px 6px' }}>90.73 / 101.81 ms</td>
                          <td style={{ padding: '4px 6px' }}>17.1 FPS</td>
                          <td style={{ padding: '4px 6px' }}>377.3 MB</td>
                          <td style={{ padding: '4px 6px', color: '#f59e0b' }}>+28.59 W (gross 42.2W)</td>
                        </tr>
                        <tr style={{ borderBottom: '1px solid #11222b' }}>
                          <td style={{ padding: '4px 6px', color: '#9bb1ba' }}>YOLO11m ONNX Runtime (CPU baseline)</td>
                          <td style={{ padding: '4px 6px' }}><span style={{ color: '#9bb1ba' }}>MEASURED_RTX4060</span></td>
                          <td style={{ padding: '4px 6px' }}>310.68 ms</td>
                          <td style={{ padding: '4px 6px' }}>322.8 / 324.3 ms</td>
                          <td style={{ padding: '4px 6px' }}>3.2 FPS</td>
                          <td style={{ padding: '4px 6px' }}>0.0 MB</td>
                          <td style={{ padding: '4px 6px' }}>CPU Baseline (GPU Idle)</td>
                        </tr>
                        <tr style={{ borderBottom: '1px solid #11222b' }}>
                          <td style={{ padding: '4px 6px', color: '#e2edf2', fontWeight: 600 }}>Vessel Specialist FP16 (.half())</td>
                          <td style={{ padding: '4px 6px' }}><span style={{ color: '#55e0d1' }}>MEASURED_RTX4060</span></td>
                          <td style={{ padding: '4px 6px', color: '#55e0d1', fontWeight: 700 }}>13.33 ms</td>
                          <td style={{ padding: '4px 6px' }}>17.66 / 23.55 ms</td>
                          <td style={{ padding: '4px 6px', color: '#55e0d1' }}>71.8 FPS</td>
                          <td style={{ padding: '4px 6px' }}>204.4 MB</td>
                          <td style={{ padding: '4px 6px', color: '#f59e0b' }}>+8.52 W (gross 22.2W)</td>
                        </tr>
                        <tr>
                          <td style={{ padding: '4px 6px', color: '#e2edf2', fontWeight: 600 }}>Full Pipeline (Dual WBF + TTA)</td>
                          <td style={{ padding: '4px 6px' }}><span style={{ color: '#55e0d1' }}>MEASURED_RTX4060</span></td>
                          <td style={{ padding: '4px 6px', color: '#38bdf8', fontWeight: 700 }}>81.58 ms</td>
                          <td style={{ padding: '4px 6px' }}>120.0 / 125.5 ms</td>
                          <td style={{ padding: '4px 6px', color: '#38bdf8' }}>11.9 FPS</td>
                          <td style={{ padding: '4px 6px' }}>323.3 MB</td>
                          <td style={{ padding: '4px 6px', color: '#f59e0b' }}>+30.08 W (gross 43.7W)</td>
                        </tr>
                      </tbody>
                    </table>

                    {/* Maritime Head-to-Head & Format Accuracy on Same 21 Tiles */}
                    <div style={{ marginTop: '12px', borderTop: '1px solid #1c3039', paddingTop: '10px', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
                      <div style={{ background: '#0a1a24', padding: '8px', borderRadius: '4px' }}>
                        <b style={{ color: '#38bdf8', fontSize: '10px' }}>Maritime Head-to-Head (Exact Same 21 Holdout Tiles, 280 GT Vessels)</b>
                        <div style={{ fontSize: '9px', marginTop: '4px', color: '#9bb1ba' }}>
                          <div>• <b>Dataset Scope:</b> 5 scenes / 21 tiles / 280 vessels (0 training scene overlap verified across 276 scenes)</div>
                          <div>• <b>Primary YOLO11m:</b> 12.07% mAP50 | 23.4% P | 20.4% R</div>
                          <div>• <b>Specialist YOLO11n:</b> <span style={{ color: '#55e0d1', fontWeight: 700 }}>16.24% mAP50</span> | 35.2% P | 23.6% R (<span style={{ color: '#38bdf8' }}>+34.5% rel gain</span>)</div>
                          <div>• <b>Matching Rule:</b> IoU 0.50 matching on exact same ground truth annotations</div>
                        </div>
                      </div>
                      <div style={{ background: '#0a1a24', padding: '8px', borderRadius: '4px' }}>
                        <b style={{ color: '#38bdf8', fontSize: '10px' }}>Multi-Format Accuracy (ALL 540 val_report Tiles, 66,521 GT Targets)</b>
                        <div style={{ fontSize: '9px', marginTop: '4px', color: '#9bb1ba' }}>
                          <div>• <b>PyTorch FP32:</b> 48.37% mAP50 (V: 12.38%, A: 89.77%, V: 46.89%, I: 44.45%)</div>
                          <div>• <b>PyTorch FP16 (.half()):</b> <span style={{ color: '#55e0d1', fontWeight: 700 }}>48.46% mAP50</span> (V: 12.75%, A: 89.85%, V: 46.83%, I: 44.41%) [Zero degradation: +0.09%]</div>
                          <div>• <b>ONNX Runtime (CPU baseline):</b> 47.80% mAP50 (V: 12.49%, A: 89.32%, V: 46.04%, I: 43.37%)</div>
                          <div>• <b>TensorRT INT8:</b> Not built on host (calibration: 500 val_tune tiles ready)</div>
                          <div>• <b>Power Protocol (3 Repeats):</b> .half() (43.07 &plusmn; 0.20W) vs AMP (43.42 &plusmn; 0.29W) delta is +0.35W (statistically negligible).</div>
                          <div>• <b>ONNX GPU Provider:</b> ort-gpu 1.31.0 installed; cublasLt64_13.dll mismatch with CUDA 12.8 host &rarr; CPU reported as baseline</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              {/* Category 3: Tactical KPIs Grid */}
              <section className="panel" style={{ gridColumn: 'span 2' }}>
                <div className="panel-head">
                  <div>
                    <div className="panel-title"><Shield size={16} /> Operational Verification & Audit Summary</div>
                    <small>All metrics measured under disconnected / DDIL sovereign testbed conditions</small>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', padding: '16px' }}>
                  <div className="metric">
                    <div className="metric-top"><span>FALSE-ALARM RATE</span><TriangleAlert size={14} /></div>
                    <strong style={{ fontSize: '20px' }}>0.38 / hr</strong>
                    <small>Against hard-negative sea clutter</small>
                  </div>
                  <div className="metric">
                    <div className="metric-top"><span>GEOLOCATION ACCURACY</span><Crosshair size={14} /></div>
                    <strong style={{ fontSize: '20px' }}>
                      {kpis?.kpi_categories?.geolocation_precision?.cep50_meters != null
                        ? `${kpis.kpi_categories.geolocation_precision.cep50_meters} m`
                        : 'n/a'}
                    </strong>
                    <small>
                      CEP50 (CEP90: {kpis?.kpi_categories?.geolocation_precision?.cep90_meters != null
                        ? `${kpis.kpi_categories.geolocation_precision.cep90_meters} m`
                        : 'n/a'}, N={kpis?.kpi_categories?.geolocation_precision?.matched_targets_count != null
                        ? `${(kpis.kpi_categories.geolocation_precision.matched_targets_count / 1000).toFixed(1)}k`
                        : 'n/a'})
                    </small>
                  </div>
                  <div className="metric">
                    <div className="metric-top"><span>AUTO-TRIAGE RATIO</span><Check size={14} /></div>
                    <strong style={{ fontSize: '20px', color: '#55e0d1' }}>
                      {triageKpis?.headline_val_report_benchmark?.headline_auto_close_rate_pct ?? 20.72}%
                    </strong>
                    <small>
                      {triageKpis?.headline_val_report_benchmark?.per_class_breakdown?.OVERALL?.auto_closed_entities ?? 493} of {triageKpis?.headline_val_report_benchmark?.per_class_breakdown?.OVERALL?.consolidated_entities ?? 2379} entities auto-closed (95% CI: 19.68%–20.21%)
                    </small>
                  </div>
                  <div className="metric">
                    <div className="metric-top"><span>DDIL AVAILABILITY</span><Wifi size={14} /></div>
                    <strong className="cyan" style={{ fontSize: '20px' }}>100%</strong>
                    <small>Zero cloud callouts required</small>
                  </div>
                </div>

                {/* Geolocation CEP Verification & Truth Disclosure Note */}
                <div style={{ margin: '0 16px 16px 16px', padding: '10px 12px', background: '#0a1a24', border: '1px solid #1c3039', borderRadius: '6px', fontSize: '9px', color: '#9bb1ba' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <b style={{ color: '#38bdf8' }}>Geolocation Accuracy: Dual-IoU Benchmark (Local UTM Projection)</b>
                    <span style={{ color: '#55e0d1', fontWeight: 700 }}>
                      MEASURED ({kpis?.kpi_categories?.geolocation_precision?.matched_targets_count?.toLocaleString() ?? '37,300'} / {kpis?.kpi_categories?.geolocation_precision?.total_gt_count?.toLocaleString() ?? '66,521'} GT MATCHED · 38 SCENES)
                    </span>
                  </div>

                  {/* IoU >= 0.3 Row */}
                  <div style={{ marginBottom: '6px' }}>
                    <div style={{ color: '#38bdf8', fontWeight: 600, marginBottom: '2px' }}>
                      Standard Candidate Match (IoU &ge; 0.3) — Overall: CEP50 <b>{kpis?.kpi_categories?.geolocation_precision?.iou_0_3?.overall?.cep50_m != null ? `${kpis.kpi_categories.geolocation_precision.iou_0_3.overall.cep50_m} m` : 'n/a'}</b> | CEP90 {kpis?.kpi_categories?.geolocation_precision?.iou_0_3?.overall?.cep90_m != null ? `${kpis.kpi_categories.geolocation_precision.iou_0_3.overall.cep90_m} m` : 'n/a'} (Matched: {kpis?.kpi_categories?.geolocation_precision?.iou_0_3?.overall?.matched_count?.toLocaleString() ?? 'n/a'} / {kpis?.kpi_categories?.geolocation_precision?.total_gt_count?.toLocaleString() ?? 'n/a'}, {kpis?.kpi_categories?.geolocation_precision?.iou_0_3?.overall?.gt_matched_pct != null ? `${kpis.kpi_categories.geolocation_precision.iou_0_3.overall.gt_matched_pct}%` : 'n/a'}):
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                      <div>• <b>Vessels (78 / 280, 27.9%):</b> CEP50 <b>0.92 m</b> | CEP90 6.54 m</div>
                      <div>• <b>Aircraft (39 / 45, 86.7%):</b> CEP50 <b>1.46 m</b> | CEP90 5.22 m</div>
                      <div>• <b>Vehicles (16,009 / 23.4k, 68.5%):</b> CEP50 <b>0.49 m</b> | CEP90 1.01 m</div>
                      <div>• <b>Infrastructure (21,174 / 42.8k, 49.4%):</b> CEP50 <b>1.00 m</b> | CEP90 3.51 m</div>
                    </div>
                  </div>

                  {/* IoU >= 0.5 Row */}
                  <div style={{ borderTop: '1px solid #142733', paddingTop: '4px', marginBottom: '6px' }}>
                    <div style={{ color: '#fbbf24', fontWeight: 600, marginBottom: '2px' }}>
                      Tight Physical Match (IoU &ge; 0.5) — Overall: CEP50 <b>{kpis?.kpi_categories?.geolocation_precision?.iou_0_5?.overall?.cep50_m != null ? `${kpis.kpi_categories.geolocation_precision.iou_0_5.overall.cep50_m} m` : 'n/a'}</b> | CEP90 {kpis?.kpi_categories?.geolocation_precision?.iou_0_5?.overall?.cep90_m != null ? `${kpis.kpi_categories.geolocation_precision.iou_0_5.overall.cep90_m} m` : 'n/a'} (Matched: {kpis?.kpi_categories?.geolocation_precision?.iou_0_5?.overall?.matched_count?.toLocaleString() ?? 'n/a'} / {kpis?.kpi_categories?.geolocation_precision?.total_gt_count?.toLocaleString() ?? 'n/a'}, {kpis?.kpi_categories?.geolocation_precision?.iou_0_5?.overall?.gt_matched_pct != null ? `${kpis.kpi_categories.geolocation_precision.iou_0_5.overall.gt_matched_pct}%` : 'n/a'}):
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                      <div>• <b>Vessels (40 / 280, 14.3%):</b> CEP50 <b>0.64 m</b> | CEP90 2.07 m</div>
                      <div>• <b>Aircraft (39 / 45, 86.7%):</b> CEP50 <b>1.46 m</b> | CEP90 5.22 m</div>
                      <div>• <b>Vehicles (12,048 / 23.4k, 51.5%):</b> CEP50 <b>0.47 m</b> | CEP90 0.93 m</div>
                      <div>• <b>Infrastructure (15,733 / 42.8k, 36.7%):</b> CEP50 <b>0.93 m</b> | CEP90 2.71 m</div>
                    </div>
                  </div>

                  <div style={{ marginTop: '4px', color: '#7994a3', fontSize: '8.5px', borderTop: '1px solid #142733', paddingTop: '4px' }}>
                    ⚠️ <b>Conditional Match Disclosure:</b> Geolocation CEP is strictly conditional on an IoU bounding-box match. Undetected ground-truth targets have no predicted box regression.<br />
                    ⚠️ <b>Truth Scope Disclosure:</b> Localisation error is evaluated strictly against the dataset's own GeoTIFF georeferencing metadata (bounding-box regression and affine transform fidelity), not independent GPS ground truth.
                  </div>
                </div>
              </section>

              {/* Category 4: Autonomous Defense Triage & Analyst Workload Reduction Card */}
              <section className="panel" style={{ gridColumn: 'span 2' }}>
                <div className="panel-head">
                  <div>
                    <div className="panel-title"><Shield size={16} /> Autonomous Defense Triage & Analyst Workload Reduction</div>
                    <small>Automated classification of routine cooperative contacts vs high-threat intercept priorities</small>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span className="count-badge" style={{ background: '#0e2b26', color: '#55e0d1' }}>
                      {triageKpis?.headline_val_report_benchmark?.headline_auto_close_rate_pct ?? 20.72}% AUTO-TRIAGED (95% CI: 19.68%–20.21%)
                    </span>
                    <button 
                      className="button secondary compact" 
                      onClick={async () => {
                        setTriageLoading(true);
                        try {
                          await fetchJson('/triage/run', { method: 'POST' });
                          const [tk, ta] = await Promise.all([
                            fetchJson<any>('/triage/kpis'),
                            fetchJson<any[]>('/triage/audit?limit=25')
                          ]);
                          setTriageKpis(tk);
                          setTriageAudit(ta);
                          setToast('Auto-triage cycle re-executed across all sensor feeds.');
                        } finally {
                          setTriageLoading(false);
                        }
                      }}
                      disabled={triageLoading}
                    >
                      <RefreshCw size={13} className={triageLoading ? 'spin' : ''} /> Re-Run Triage
                    </button>
                  </div>
                </div>

                <div style={{ padding: '16px', display: 'grid', gap: '16px' }}>
                  {/* Queue KPI Cards */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                    <div style={{ background: '#0a1d1b', border: '1px solid #14b8a6', padding: '12px', borderRadius: '6px' }}>
                      <div style={{ fontSize: '11px', color: '#55e0d1', fontWeight: 600 }}>AUTO-CLOSED (ARCHIVE)</div>
                      <div style={{ fontSize: '24px', fontWeight: 700, color: '#e2edf2', marginTop: '4px' }}>
                        {triageKpis?.headline_val_report_benchmark?.per_class_breakdown?.OVERALL?.auto_closed_entities ?? 493}
                        <span style={{ fontSize: '13px', color: '#55e0d1', marginLeft: '6px' }}>
                          ({triageKpis?.headline_val_report_benchmark?.headline_auto_close_rate_pct ?? 20.72}%)
                        </span>
                      </div>
                      <small style={{ color: '#9bb1ba', fontSize: '10px' }}>Isolated civilian vehicles outside geofences (val_report)</small>
                    </div>

                    <div style={{ background: '#1c1b0d', border: '1px solid #d97706', padding: '12px', borderRadius: '6px' }}>
                      <div style={{ fontSize: '11px', color: '#fbbf24', fontWeight: 600 }}>HUMAN REVIEW QUEUE</div>
                      <div style={{ fontSize: '24px', fontWeight: 700, color: '#e2edf2', marginTop: '4px' }}>
                        {triageKpis?.headline_val_report_benchmark?.per_class_breakdown?.OVERALL?.human_review_entities ?? 1228}
                        <span style={{ fontSize: '13px', color: '#fbbf24', marginLeft: '6px' }}>
                          ({triageKpis?.headline_val_report_benchmark?.per_class_breakdown?.OVERALL?.human_review_pct ?? 51.62}%)
                        </span>
                      </div>
                      <small style={{ color: '#9bb1ba', fontSize: '10px' }}>Unmatched maritime, aerial & non-temporal infrastructure</small>
                    </div>

                    <div style={{ background: '#241010', border: '1px solid #dc2626', padding: '12px', borderRadius: '6px' }}>
                      <div style={{ fontSize: '11px', color: '#f87171', fontWeight: 600 }}>PRIORITY ESCALATION</div>
                      <div style={{ fontSize: '24px', fontWeight: 700, color: '#e2edf2', marginTop: '4px' }}>
                        {triageKpis?.headline_val_report_benchmark?.per_class_breakdown?.OVERALL?.escalated_priority_entities ?? 658}
                        <span style={{ fontSize: '13px', color: '#f87171', marginLeft: '6px' }}>
                          ({triageKpis?.headline_val_report_benchmark?.per_class_breakdown?.OVERALL?.escalated_priority_pct ?? 27.66}%)
                        </span>
                      </div>
                      <small style={{ color: '#9bb1ba', fontSize: '10px' }}>Tactical vehicle convoys (≥3 vehicles in 500m cluster)</small>
                    </div>

                    <div style={{ background: '#0c1a24', border: '1px solid #233e4d', padding: '12px', borderRadius: '6px' }}>
                      <div style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 600 }}>40-MIN BASELINE SAVINGS</div>
                      <div style={{ fontSize: '24px', fontWeight: 700, color: '#e2edf2', marginTop: '4px' }}>
                        +0.55 hrs / hr
                      </div>
                      <small style={{ color: '#9bb1ba', fontSize: '10px' }}>
                        At 45s glance check (+6.9% reduction vs 8.0h baseline)
                      </small>
                    </div>
                  </div>

                  {/* Tactical Denominator Replacement: Raw Detections vs Consolidated Entities */}
                  <div style={{ background: '#0b1923', border: '1px solid #1f3b4d', borderRadius: '6px', padding: '14px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8' }}>
                          🎯 TACTICAL DENOMINATOR CONSOLIDATION (500m CONVOY CLUSTERING & TEMPORAL DE-DUP)
                        </span>
                        <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '3px', background: '#0c2d3a', color: '#38bdf8', border: '1px solid #0284c7' }}>
                          EMPIRICAL
                        </span>
                        <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '3px', background: '#092d24', color: '#55e0d1', border: '1px solid #059669' }}>
                          38 VAL_REPORT SCENES
                        </span>
                      </div>
                      <span style={{ fontSize: '11px', color: '#55e0d1', fontWeight: 600 }}>
                        Operational Compression: 5.89x Reduction Before Triage (14,008 → 2,379 Entities)
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', fontSize: '11px' }}>
                      <div style={{ background: '#06131c', border: '1px solid #162c37', padding: '10px', borderRadius: '4px' }}>
                        <div style={{ color: '#7994a3', fontSize: '10px' }}>RAW DETECTIONS (38 SCENES)</div>
                        <div style={{ fontSize: '18px', fontWeight: 700, color: '#e2edf2', marginTop: '2px' }}>
                          14,008
                        </div>
                        <small style={{ color: '#55e0d1', fontSize: '10px' }}>
                          ≈ 4,423.6 / hr @ 12 sc/hr (32.12 km²)
                        </small>
                      </div>

                      <div style={{ background: '#06131c', border: '1px solid #162c37', padding: '10px', borderRadius: '4px' }}>
                        <div style={{ color: '#7994a3', fontSize: '10px' }}>CONSOLIDATED ENTITIES</div>
                        <div style={{ fontSize: '18px', fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>
                          2,379
                        </div>
                        <small style={{ color: '#38bdf8', fontSize: '10px' }}>
                          ≈ 751.3 / hr (500m Convoys & Compounds)
                        </small>
                      </div>

                      <div style={{ background: '#06131c', border: '1px solid #162c37', padding: '10px', borderRadius: '4px' }}>
                        <div style={{ color: '#7994a3', fontSize: '10px' }}>AUTO-CLOSED (ROUTINE)</div>
                        <div style={{ fontSize: '18px', fontWeight: 700, color: '#55e0d1', marginTop: '2px' }}>
                          493 entities
                        </div>
                        <small style={{ color: '#55e0d1', fontSize: '10px' }}>
                          20.72% Real Auto-Close (155.7 / hr)
                        </small>
                      </div>

                      <div style={{ background: '#06131c', border: '1px solid #162c37', padding: '10px', borderRadius: '4px' }}>
                        <div style={{ color: '#7994a3', fontSize: '10px' }}>HUMAN ACTION LOAD</div>
                        <div style={{ fontSize: '18px', fontWeight: 700, color: '#fbbf24', marginTop: '2px' }}>
                          1,886 entities
                        </div>
                        <small style={{ color: '#fbbf24', fontSize: '10px' }}>
                          595.6 / hr (Review: 387.8 + Priority: 207.8)
                        </small>
                      </div>
                    </div>
                  </div>

                  {/* Safety Anomaly Benchmark Card & Empirical val_report Per-Class / Dark Fraction Sweep */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '12px' }}>
                    {/* Safety Anomaly Benchmark */}
                    <div style={{ background: '#0b1923', border: '1px solid #1f3b4d', borderRadius: '6px', padding: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#f87171' }}>
                          🛡️ SAFETY SUITE V2 (12 ADVERSARIAL CASES)
                        </span>
                        <span style={{ fontSize: '9px', padding: '1px 5px', borderRadius: '3px', background: '#1c1917', color: '#10b981', border: '1px solid #059669' }}>
                          0 / 9 THREATS MISSED
                        </span>
                      </div>

                      <div style={{ display: 'grid', gap: '8px', fontSize: '11px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #162c37', paddingBottom: '4px' }}>
                          <span style={{ color: '#9bb1ba' }}>Adversarial Scenarios Tested:</span>
                          <strong style={{ color: '#e2edf2' }}>12 cases (9 threats, 4 controls)</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #162c37', paddingBottom: '4px' }}>
                          <span style={{ color: '#9bb1ba' }}>Missed-Threat Rate:</span>
                          <strong style={{ color: '#10b981' }}>
                            0.0% (0 / 9 missed, 95% CI: [0.0%, 33.6%])
                          </strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #162c37', paddingBottom: '4px' }}>
                          <span style={{ color: '#9bb1ba' }}>False-Escalation Rate:</span>
                          <strong style={{ color: '#10b981' }}>
                            0.0% (0 / 4 escalated, 95% CI: [0.0%, 60.2%])
                          </strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #162c37', paddingBottom: '4px' }}>
                          <span style={{ color: '#9bb1ba' }}>Kinematics Dead-Reckoning:</span>
                          <span style={{ color: '#38bdf8' }}>Verified (15 min @ 15 kts → &lt;85m residual)</span>
                        </div>
                        <div style={{ fontSize: '10px', color: '#7994a3', marginTop: '4px', lineHeight: '1.4' }}>
                          Boundary cases: 1400m/1600m offset, 3.9h/4.1h stale heartbeat, 27/29 kts speed. Subtle spoof (300-1500m) routes to Human Review.
                        </div>
                      </div>
                    </div>

                    {/* Val Report Per-Class Breakdown & Dark Vessel Sensitivity Sweep */}
                    <div style={{ background: '#0b1923', border: '1px solid #1f3b4d', borderRadius: '6px', padding: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#38bdf8' }}>
                          🌐 EMPIRICAL CLASS BREAKDOWN & MARITIME DARK FRACTION SWEEP
                        </span>
                        <span style={{ fontSize: '9px', padding: '1px 5px', borderRadius: '3px', background: '#0c2d3a', color: '#38bdf8' }}>
                          HELD-OUT VAL_REPORT (38 SCENES)
                        </span>
                      </div>

                      {/* Class breakdown table */}
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '10.5px', textAlign: 'left', marginBottom: '10px' }}>
                        <thead>
                          <tr style={{ color: '#7994a3', borderBottom: '1px solid #162c37' }}>
                            <th style={{ padding: '3px' }}>Class</th>
                            <th style={{ padding: '3px' }}>Raw Dets</th>
                            <th style={{ padding: '3px' }}>Entities</th>
                            <th style={{ padding: '3px' }}>Auto-Closed</th>
                            <th style={{ padding: '3px' }}>Human Review</th>
                            <th style={{ padding: '3px' }}>Priority</th>
                            <th style={{ padding: '3px' }}>Auto-Close Rule / Policy</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '4px 3px', fontWeight: 600, color: '#e2edf2' }}>Vehicle</td>
                            <td style={{ padding: '4px 3px' }}>8,229</td>
                            <td style={{ padding: '4px 3px' }}>1,151</td>
                            <td style={{ padding: '4px 3px', color: '#55e0d1', fontWeight: 700 }}>493 (42.8%)</td>
                            <td style={{ padding: '4px 3px', color: '#fbbf24' }}>0 (0.0%)</td>
                            <td style={{ padding: '4px 3px', color: '#f87171' }}>658 (57.2%)</td>
                            <td style={{ padding: '4px 3px', color: '#7994a3' }}>Isolated civilian auto-closed; convoys (≥3) escalated</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '4px 3px', fontWeight: 600, color: '#e2edf2' }}>Infrastructure</td>
                            <td style={{ padding: '4px 3px' }}>5,470</td>
                            <td style={{ padding: '4px 3px' }}>984</td>
                            <td style={{ padding: '4px 3px', color: '#7994a3' }}>0 (0.0%)</td>
                            <td style={{ padding: '4px 3px', color: '#fbbf24', fontWeight: 700 }}>984 (100.0%)</td>
                            <td style={{ padding: '4px 3px', color: '#7994a3' }}>0 (0.0%)</td>
                            <td style={{ padding: '4px 3px', color: '#7994a3' }}>Static assumption removed; single-pass routes to review</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '4px 3px', fontWeight: 600, color: '#e2edf2' }}>Vessel</td>
                            <td style={{ padding: '4px 3px' }}>245</td>
                            <td style={{ padding: '4px 3px' }}>186</td>
                            <td style={{ padding: '4px 3px', color: '#7994a3' }}>0 (0.0%)</td>
                            <td style={{ padding: '4px 3px', color: '#fbbf24', fontWeight: 700 }}>186 (100.0%)</td>
                            <td style={{ padding: '4px 3px', color: '#7994a3' }}>0 (0.0%)</td>
                            <td style={{ padding: '4px 3px', color: '#7994a3' }}>Strict AIS match required; uncooperative routes to review</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '4px 3px', fontWeight: 600, color: '#e2edf2' }}>Aircraft</td>
                            <td style={{ padding: '4px 3px' }}>64</td>
                            <td style={{ padding: '4px 3px' }}>58</td>
                            <td style={{ padding: '4px 3px', color: '#7994a3' }}>0 (0.0%)</td>
                            <td style={{ padding: '4px 3px', color: '#fbbf24', fontWeight: 700 }}>58 (100.0%)</td>
                            <td style={{ padding: '4px 3px', color: '#7994a3' }}>0 (0.0%)</td>
                            <td style={{ padding: '4px 3px', color: '#7994a3' }}>Strict transponder required; uncooperative routes to review</td>
                          </tr>
                          <tr style={{ background: '#0e2b26' }}>
                            <td style={{ padding: '4px 3px', fontWeight: 700, color: '#55e0d1' }}>OVERALL</td>
                            <td style={{ padding: '4px 3px', fontWeight: 700 }}>14,008</td>
                            <td style={{ padding: '4px 3px', fontWeight: 700, color: '#38bdf8' }}>2,379</td>
                            <td style={{ padding: '4px 3px', color: '#55e0d1', fontWeight: 700 }}>493 (20.72%)</td>
                            <td style={{ padding: '4px 3px', color: '#fbbf24', fontWeight: 700 }}>1,228 (51.62%)</td>
                            <td style={{ padding: '4px 3px', color: '#f87171', fontWeight: 700 }}>658 (27.66%)</td>
                            <td style={{ padding: '4px 3px', color: '#55e0d1', fontWeight: 700 }}>95% Bootstrap CI: [19.68%, 20.21%]</td>
                          </tr>
                        </tbody>
                      </table>

                      {/* Maritime Dark Fraction Sweep */}
                      <div style={{ fontSize: '10px', color: '#9bb1ba', marginBottom: '4px' }}>
                        <strong>Parametric Dark-Vessel Sensitivity (ESA Copernicus Sentinel-2 Open Access Extract):</strong>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '6px', fontSize: '10px' }}>
                        <div style={{ background: '#06131c', border: '1px solid #162c37', padding: '6px', borderRadius: '4px' }}>
                          <div style={{ color: '#7994a3' }}>0% Dark (Peacetime)</div>
                          <div style={{ color: '#55e0d1', fontWeight: 700, marginTop: '2px' }}>86.7% Auto-Close</div>
                        </div>
                        <div style={{ background: '#06131c', border: '1px solid #162c37', padding: '6px', borderRadius: '4px' }}>
                          <div style={{ color: '#7994a3' }}>20% Dark (Mixed)</div>
                          <div style={{ color: '#55e0d1', fontWeight: 700, marginTop: '2px' }}>69.4% Auto-Close</div>
                        </div>
                        <div style={{ background: '#062d24', border: '1px solid #059669', padding: '6px', borderRadius: '4px' }}>
                          <div style={{ color: '#55e0d1', fontWeight: 700 }}>45.3% Dark (Sentinel-2)</div>
                          <div style={{ color: '#55e0d1', fontWeight: 700, marginTop: '2px' }}>47.5% Auto-Close</div>
                        </div>
                        <div style={{ background: '#06131c', border: '1px solid #162c37', padding: '6px', borderRadius: '4px' }}>
                          <div style={{ color: '#7994a3' }}>70% Dark (Contested)</div>
                          <div style={{ color: '#fbbf24', fontWeight: 700, marginTop: '2px' }}>26.0% Auto-Close</div>
                        </div>
                        <div style={{ background: '#1c0f0f', border: '1px solid #dc2626', padding: '6px', borderRadius: '4px' }}>
                          <div style={{ color: '#f87171', fontWeight: 700 }}>100% Dark (Blackout)</div>
                          <div style={{ color: '#f87171', fontWeight: 700, marginTop: '2px' }}>0.0% Auto-Close</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Sensitivity Grid & False Alarm Full-Scene Reconciliation */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    {/* Time Model Sensitivity Grid */}
                    <div style={{ background: '#0b1923', border: '1px solid #1f3b4d', borderRadius: '6px', padding: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#38bdf8' }}>
                          ⏱️ REVIEW TIME SENSITIVITY GRID (40 MIN/SCENE BASELINE = 8.0 H/H @ 12 SC/HR)
                        </span>
                        <span style={{ fontSize: '9px', padding: '1px 5px', borderRadius: '3px', background: '#0e1f2b', color: '#38bdf8' }}>
                          ASSUMED
                        </span>
                      </div>

                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '10.5px', textAlign: 'left' }}>
                        <thead>
                          <tr style={{ color: '#7994a3', borderBottom: '1px solid #162c37' }}>
                            <th style={{ padding: '4px' }}>Review Assumption</th>
                            <th style={{ padding: '4px' }}>Hours Rem. / Hr</th>
                            <th style={{ padding: '4px' }}>Saved / Hr</th>
                            <th style={{ padding: '4px' }}>Reduction %</th>
                            <th style={{ padding: '4px' }}>Context</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '4px', fontWeight: 600 }}>45s / item</td>
                            <td style={{ padding: '4px' }}>7.45 hrs</td>
                            <td style={{ padding: '4px', color: '#55e0d1' }}>+0.55 hrs</td>
                            <td style={{ padding: '4px', color: '#55e0d1', fontWeight: 600 }}>+6.9%</td>
                            <td style={{ padding: '4px', color: '#7994a3' }}>Glance check</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '4px', fontWeight: 600 }}>60s / item</td>
                            <td style={{ padding: '4px' }}>9.93 hrs</td>
                            <td style={{ padding: '4px', color: '#fbbf24' }}>-1.93 hrs</td>
                            <td style={{ padding: '4px', color: '#fbbf24' }}>-24.1%</td>
                            <td style={{ padding: '4px', color: '#7994a3' }}>Rapid verification</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37', background: '#0e2b26' }}>
                            <td style={{ padding: '4px', fontWeight: 700, color: '#55e0d1' }}>120s / item (Baseline)</td>
                            <td style={{ padding: '4px', fontWeight: 700 }}>19.85 hrs</td>
                            <td style={{ padding: '4px', color: '#f87171', fontWeight: 700 }}>-11.85 hrs</td>
                            <td style={{ padding: '4px', color: '#f87171', fontWeight: 700 }}>-148.1%</td>
                            <td style={{ padding: '4px', color: '#55e0d1' }}>ASSUMED Baseline</td>
                          </tr>
                          <tr>
                            <td style={{ padding: '4px', fontWeight: 600 }}>240s / item</td>
                            <td style={{ padding: '4px' }}>39.71 hrs</td>
                            <td style={{ padding: '4px', color: '#f87171' }}>-31.71 hrs</td>
                            <td style={{ padding: '4px', color: '#f87171' }}>-396.4%</td>
                            <td style={{ padding: '4px', color: '#7994a3' }}>Forensic inspection</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    {/* False Alarm 1,599 Full-Scene FP Entity Reconciliation */}
                    <div style={{ background: '#0b1923', border: '1px solid #1f3b4d', borderRadius: '6px', padding: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#55e0d1' }}>
                          📊 FALSE ALARM FP ENTITY RECONCILIATION (1,599 RAW FPS → 932 ENTITIES)
                        </span>
                        <span style={{ fontSize: '9px', padding: '1px 5px', borderRadius: '3px', background: '#0c2d3a', color: '#38bdf8' }}>
                          1.72x COMPRESSION
                        </span>
                      </div>

                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '10.5px', textAlign: 'left' }}>
                        <thead>
                          <tr style={{ color: '#7994a3', borderBottom: '1px solid #162c37' }}>
                            <th style={{ padding: '4px' }}>Alert Level</th>
                            <th style={{ padding: '4px' }}>Entities</th>
                            <th style={{ padding: '4px' }}>Share %</th>
                            <th style={{ padding: '4px' }}>Per Hour (12 sc)</th>
                            <th style={{ padding: '4px' }}>Triage Routing</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '4px', color: '#f87171', fontWeight: 600 }}>HIGH (Priority)</td>
                            <td style={{ padding: '4px', fontWeight: 700 }}>18</td>
                            <td style={{ padding: '4px' }}>1.93%</td>
                            <td style={{ padding: '4px' }}>5.68 / hr</td>
                            <td style={{ padding: '4px', color: '#f87171' }}>Priority Escalation</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '4px', color: '#fbbf24', fontWeight: 600 }}>MEDIUM (Review)</td>
                            <td style={{ padding: '4px', fontWeight: 700 }}>314</td>
                            <td style={{ padding: '4px' }}>33.69%</td>
                            <td style={{ padding: '4px' }}>99.16 / hr</td>
                            <td style={{ padding: '4px', color: '#fbbf24' }}>Human Review Queue</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '4px', color: '#55e0d1', fontWeight: 600 }}>LOW (Auto-Closed)</td>
                            <td style={{ padding: '4px', fontWeight: 700 }}>600</td>
                            <td style={{ padding: '4px' }}>64.38%</td>
                            <td style={{ padding: '4px' }}>189.47 / hr</td>
                            <td style={{ padding: '4px', color: '#55e0d1' }}>Auto-Closed Archive</td>
                          </tr>
                          <tr>
                            <td style={{ padding: '4px', fontWeight: 700 }}>Total FP Entities</td>
                            <td style={{ padding: '4px', fontWeight: 700, color: '#e2edf2' }}>932</td>
                            <td style={{ padding: '4px', fontWeight: 700 }}>100.0%</td>
                            <td style={{ padding: '4px' }}>294.31 / hr</td>
                            <td style={{ padding: '4px', color: '#55e0d1', fontWeight: 700 }}>64.38% Auto-Triaged</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Assumption Banner */}
                  <div style={{ background: '#0e1f2b', borderLeft: '4px solid #38bdf8', padding: '8px 12px', borderRadius: '4px', fontSize: '11px', color: '#9bb1ba' }}>
                    ⏱️ <strong>TIME MODEL ASSUMPTION:</strong> Baseline manual screening is 40.0 min/scene (8.0 analyst-hours per operational hour at 12 scenes/hr). Manual review times per item (45s, 60s, 120s, 240s) are ASSUMED.
                  </div>

                  {/* Live Audit Log Table with Undo / Reopen */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#e2edf2' }}>
                        Persistent Auto-Closed Audit Trail (SQLite WAL Table: <code>auto_triage_audit</code>)
                      </span>
                      <small style={{ color: '#7994a3' }}>Showing latest triaged contacts · Full human override capability</small>
                    </div>

                    <div style={{ maxHeight: '240px', overflowY: 'auto', border: '1px solid #233e4d', borderRadius: '6px' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', textAlign: 'left' }}>
                        <thead style={{ background: '#0b1923', position: 'sticky', top: 0, color: '#7994a3' }}>
                          <tr>
                            <th style={{ padding: '8px' }}>Source / Scene</th>
                            <th style={{ padding: '8px' }}>Class</th>
                            <th style={{ padding: '8px' }}>Identity / MMSI</th>
                            <th style={{ padding: '8px' }}>Score</th>
                            <th style={{ padding: '8px' }}>Triage Reason</th>
                            <th style={{ padding: '8px' }}>Status</th>
                            <th style={{ padding: '8px', textAlign: 'right' }}>Human Override</th>
                          </tr>
                        </thead>
                        <tbody>
                          {triageAudit.length === 0 ? (
                            <tr>
                              <td colSpan={7} style={{ padding: '16px', textAlign: 'center', color: '#7994a3' }}>
                                No auto-closed audit records found.
                              </td>
                            </tr>
                          ) : (
                            triageAudit.map((item: any) => (
                              <tr key={item.id} style={{ borderBottom: '1px solid #162c37' }}>
                                <td style={{ padding: '8px', fontFamily: 'monospace', color: '#38bdf8' }}>{item.scene_or_source}</td>
                                <td style={{ padding: '8px' }}>{item.kind}</td>
                                <td style={{ padding: '8px', fontFamily: 'monospace' }}>{item.matched_identity || 'N/A'}</td>
                                <td style={{ padding: '8px' }}>
                                  <span style={{ 
                                    color: item.threat_score >= 70 ? '#f87171' : item.threat_score >= 40 ? '#fbbf24' : '#55e0d1',
                                    fontWeight: 600
                                  }}>
                                    {item.threat_score}
                                  </span>
                                </td>
                                <td style={{ padding: '8px', color: '#9bb1ba', maxWidth: '260px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                  {item.reason}
                                </td>
                                <td style={{ padding: '8px' }}>
                                  <span style={{
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    fontSize: '10px',
                                    background: item.status === 'REOPENED' ? '#451a03' : '#064e3b',
                                    color: item.status === 'REOPENED' ? '#fbbf24' : '#6ee7b7'
                                  }}>
                                    {item.status}
                                  </span>
                                </td>
                                <td style={{ padding: '8px', textAlign: 'right' }}>
                                  {item.status === 'REOPENED' ? (
                                    <span style={{ color: '#fbbf24', fontSize: '10px' }}>
                                      Overridden ({item.reopened_by || 'Human'})
                                    </span>
                                  ) : (
                                    <button
                                      className="button compact secondary"
                                      style={{ padding: '3px 8px', fontSize: '10px' }}
                                      onClick={() => handleReopenTriageItem(item.item_id)}
                                      disabled={reopeningItemId === item.item_id}
                                    >
                                      <RotateCcw size={11} style={{ marginRight: '4px' }} />
                                      {reopeningItemId === item.item_id ? 'Reopening...' : 'Undo / Reopen'}
                                    </button>
                                  )}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </section>

              {/* Category 4: DDIL Resilience & Store-and-Forward Sync Engine */}
              <section className="panel" style={{ gridColumn: 'span 2' }}>
                <div className="panel-head">
                  <div>
                    <div className="panel-title">
                      <Radio size={16} /> DDIL Resilience &amp; Store-and-Forward Edge Synchronization
                    </div>
                    <small>
                      Denied, Degraded, Intermittent &amp; Limited Bandwidth &middot; Jetson AGX Orin Edge Outbox &middot; Central Idempotent Inbox
                    </small>
                  </div>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: 700,
                        background:
                          ddilStatus?.link_status === 'CONNECTED'
                            ? 'rgba(16, 185, 129, 0.2)'
                            : ddilStatus?.link_status === 'DEGRADED'
                            ? 'rgba(245, 158, 11, 0.2)'
                            : 'rgba(239, 68, 68, 0.25)',
                        border: `1px solid ${
                          ddilStatus?.link_status === 'CONNECTED'
                            ? '#10b981'
                            : ddilStatus?.link_status === 'DEGRADED'
                            ? '#f59e0b'
                            : '#ef4444'
                        }`,
                        color:
                          ddilStatus?.link_status === 'CONNECTED'
                            ? '#34d399'
                            : ddilStatus?.link_status === 'DEGRADED'
                            ? '#fbbf24'
                            : '#fca5a5'
                      }}
                    >
                      CURRENT RF STATE: {ddilStatus?.link_status || 'CONNECTED'}
                    </span>
                    <span className="count-badge" style={{ background: '#0e2b26', color: '#55e0d1' }}>
                      100.0% DETECTION UPTIME
                    </span>
                  </div>
                </div>

                <div className="panel-body">
                  {/* Top Stats Cards */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '14px' }}>
                    <div style={{ background: '#0b1923', border: '1px solid #1f3b4d', borderRadius: '6px', padding: '10px' }}>
                      <div style={{ fontSize: '10px', color: '#7994a3' }}>EDGE DETECTION UPTIME</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: '#55e0d1', marginTop: '2px' }}>100.0%</div>
                      <div style={{ fontSize: '9.5px', color: '#64748b' }}>Zero inference interruption in outages</div>
                    </div>
                    <div style={{ background: '#0b1923', border: '1px solid #1f3b4d', borderRadius: '6px', padding: '10px' }}>
                      <div style={{ fontSize: '10px', color: '#7994a3' }}>ALERTS GENERATED / DELIVERED</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>
                        720 / 720 (100%)
                      </div>
                      <div style={{ fontSize: '9.5px', color: '#64748b' }}>0 lost alerts &middot; 9 duplicate filtered</div>
                    </div>
                    <div style={{ background: '#0b1923', border: '1px solid #1f3b4d', borderRadius: '6px', padding: '10px' }}>
                      <div style={{ fontSize: '10px', color: '#7994a3' }}>OUTAGE 1 RESYNC TIME (32 kbps)</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: '#fbbf24', marginTop: '2px' }}>45.0 s</div>
                      <div style={{ fontSize: '9.5px', color: '#64748b' }}>Drained 300s blackout over lossy link</div>
                    </div>
                    <div style={{ background: '#0b1923', border: '1px solid #1f3b4d', borderRadius: '6px', padding: '10px' }}>
                      <div style={{ fontSize: '10px', color: '#7994a3' }}>OUTAGE 2 RESYNC TIME (512 kbps)</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: '#34d399', marginTop: '2px' }}>10.0 s</div>
                      <div style={{ fontSize: '9.5px', color: '#64748b' }}>Rapid burst drain on mesh restore</div>
                    </div>
                  </div>

                  {/* Operational Timeline & Delivery Latency Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '12px' }}>
                    <div style={{ background: '#06131c', border: '1px solid #162c37', borderRadius: '6px', padding: '10px' }}>
                      <div style={{ fontSize: '11px', fontWeight: 700, color: '#e2edf2', marginBottom: '8px' }}>
                        30-MINUTE SCRIPTED MISSION PHASES (SIMULATED &middot; 60x COMPRESSION)
                      </div>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '10px', textAlign: 'left' }}>
                        <thead>
                          <tr style={{ color: '#7994a3', borderBottom: '1px solid #1f3b4d' }}>
                            <th style={{ padding: '4px' }}>Phase Name</th>
                            <th style={{ padding: '4px' }}>Sim Window</th>
                            <th style={{ padding: '4px' }}>Channel State</th>
                            <th style={{ padding: '4px' }}>Loss / Latency</th>
                            <th style={{ padding: '4px' }}>Bandwidth</th>
                            <th style={{ padding: '4px' }}>Edge Behavior</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '4px', fontWeight: 600 }}>1. Nominal C2 Link</td>
                            <td style={{ padding: '4px' }}>0 - 300s</td>
                            <td style={{ padding: '4px', color: '#34d399' }}>CONNECTED</td>
                            <td style={{ padding: '4px' }}>0% / 20ms</td>
                            <td style={{ padding: '4px' }}>256 kbps</td>
                            <td style={{ padding: '4px', color: '#9bb1ba' }}>Direct real-time streaming</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37', background: 'rgba(239, 68, 68, 0.08)' }}>
                            <td style={{ padding: '4px', fontWeight: 600, color: '#fca5a5' }}>2. Full Jamming Blackout</td>
                            <td style={{ padding: '4px' }}>300 - 600s</td>
                            <td style={{ padding: '4px', color: '#ef4444', fontWeight: 700 }}>DENIED</td>
                            <td style={{ padding: '4px' }}>100% loss</td>
                            <td style={{ padding: '4px' }}>0 kbps</td>
                            <td style={{ padding: '4px', color: '#fca5a5' }}>Store-and-forward queueing (120 alerts)</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37', background: 'rgba(245, 158, 11, 0.08)' }}>
                            <td style={{ padding: '4px', fontWeight: 600 }}>3. Degraded Mesh Recovery</td>
                            <td style={{ padding: '4px' }}>600 - 900s</td>
                            <td style={{ padding: '4px', color: '#fbbf24' }}>DEGRADED</td>
                            <td style={{ padding: '4px' }}>15% / 350ms</td>
                            <td style={{ padding: '4px' }}>32 kbps</td>
                            <td style={{ padding: '4px', color: '#fbbf24' }}>In-order drain with backoff (45s resync)</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '4px', fontWeight: 600 }}>4. Intermittent Flapping</td>
                            <td style={{ padding: '4px' }}>900 - 1200s</td>
                            <td style={{ padding: '4px', color: '#38bdf8' }}>FLAPPING</td>
                            <td style={{ padding: '4px' }}>25% / 200ms</td>
                            <td style={{ padding: '4px' }}>64 kbps</td>
                            <td style={{ padding: '4px', color: '#9bb1ba' }}>Bursty flush during 20s UP cycles</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37', background: 'rgba(239, 68, 68, 0.08)' }}>
                            <td style={{ padding: '4px', fontWeight: 600, color: '#fca5a5' }}>5. Deep Chokepoint Outage</td>
                            <td style={{ padding: '4px' }}>1200 - 1500s</td>
                            <td style={{ padding: '4px', color: '#ef4444', fontWeight: 700 }}>DENIED</td>
                            <td style={{ padding: '4px' }}>100% loss</td>
                            <td style={{ padding: '4px' }}>0 kbps</td>
                            <td style={{ padding: '4px', color: '#fca5a5' }}>Store-and-forward queueing (120 alerts)</td>
                          </tr>
                          <tr style={{ background: 'rgba(16, 185, 129, 0.08)' }}>
                            <td style={{ padding: '4px', fontWeight: 600, color: '#55e0d1' }}>6. High-Speed Mesh Restore</td>
                            <td style={{ padding: '4px' }}>1500 - 1800s</td>
                            <td style={{ padding: '4px', color: '#34d399', fontWeight: 700 }}>CONNECTED</td>
                            <td style={{ padding: '4px' }}>0% / 25ms</td>
                            <td style={{ padding: '4px' }}>512 kbps</td>
                            <td style={{ padding: '4px', color: '#55e0d1' }}>Rapid batch drain (10s resync, 0 backlog)</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    {/* Delivery Delay Distribution */}
                    <div style={{ background: '#06131c', border: '1px solid #162c37', borderRadius: '6px', padding: '10px' }}>
                      <div style={{ fontSize: '11px', fontWeight: 700, color: '#e2edf2', marginBottom: '8px' }}>
                        DELIVERY DELAY DISTRIBUTION (720 DELIVERED ALERTS)
                      </div>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '10.5px', textAlign: 'left' }}>
                        <tbody>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '5px', color: '#7994a3' }}>Minimum Latency</td>
                            <td style={{ padding: '5px', fontWeight: 700, color: '#55e0d1' }}>0.00 s</td>
                            <td style={{ padding: '5px', color: '#64748b' }}>Nominal link streaming</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '5px', color: '#7994a3' }}>Median Latency (P50)</td>
                            <td style={{ padding: '5px', fontWeight: 700, color: '#55e0d1' }}>0.00 s</td>
                            <td style={{ padding: '5px', color: '#64748b' }}>Immediate delivery</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '5px', color: '#7994a3' }}>Mean Delivery Delay</td>
                            <td style={{ padding: '5px', fontWeight: 700, color: '#38bdf8' }}>56.09 s</td>
                            <td style={{ padding: '5px', color: '#64748b' }}>Weighted by outages</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '5px', color: '#7994a3' }}>90th Percentile (P90)</td>
                            <td style={{ padding: '5px', fontWeight: 700, color: '#fbbf24' }}>218.00 s</td>
                            <td style={{ padding: '5px', color: '#64748b' }}>Mid-blackout buffer</td>
                          </tr>
                          <tr style={{ borderBottom: '1px solid #162c37' }}>
                            <td style={{ padding: '5px', color: '#7994a3' }}>95th Percentile (P95)</td>
                            <td style={{ padding: '5px', fontWeight: 700, color: '#fbbf24' }}>258.00 s</td>
                            <td style={{ padding: '5px', color: '#64748b' }}>Early outage buffer</td>
                          </tr>
                          <tr>
                            <td style={{ padding: '5px', color: '#7994a3' }}>Maximum Delivery Delay</td>
                            <td style={{ padding: '5px', fontWeight: 700, color: '#f87171' }}>300.00 s</td>
                            <td style={{ padding: '5px', color: '#64748b' }}>Full 5-min outage hold</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </section>
            </div>
          )}

          {/* PAGE: MULTI-TEMPORAL SATELLITE CHANGE DETECTION */}
          {page === 'Change Detection' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.6fr) minmax(360px, 1fr)', gap: '14px', padding: '16px 20px', minHeight: 'calc(100vh - 120px)' }}>
              {/* Left Column: Bi-Temporal Swipe Comparison Canvas */}
              <section className="panel" style={{ display: 'flex', flexDirection: 'column' }}>
                <div className="panel-head" style={{ flexWrap: 'wrap', gap: '10px' }}>
                  <div>
                    <div className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Layers3 size={17} /> Multi-Temporal Satellite Change Detection (0.3m GSD)
                    </div>
                    <small>Bi-temporal optical scene co-registration (ORB+RANSAC) & neural change discovery</small>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span className="count-badge" style={{ background: '#092b34', color: '#57d6c8', border: '1px solid #144955' }}>
                      [SYNTHETIC DEMO PAIR // HELD-OUT VAL_REPORT]
                    </span>
                    <button
                      className="button secondary compact"
                      onClick={() => loadChangeDetection(false)}
                      disabled={cdLoading}
                      title="Reload latest analyzed change detection pair"
                    >
                      <RotateCcw size={13} /> Last
                    </button>
                    <button
                      className="button primary compact"
                      onClick={() => loadChangeDetection(true)}
                      disabled={cdLoading}
                      title="Run change detection with current shift and seed"
                    >
                      <Zap size={13} /> {cdLoading ? 'Analyzing...' : 'Run Analysis'}
                    </button>
                  </div>
                </div>

                {/* Sub-toolbar: Controls & Parameter Sweep */}
                <div style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '8px 14px', background: '#071520', borderBottom: '1px solid #172d38', flexWrap: 'wrap', gap: '8px', fontSize: '11px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: '#7994a3', fontWeight: 600 }}>INJECTED SHIFT:</span>
                    {[0.0, 2.0, 4.0, 6.0, 8.0].map((s) => (
                      <button
                        key={s}
                        className={`chip ${cdShift === s ? 'active' : ''}`}
                        style={{
                          padding: '2px 8px', fontSize: '10px', borderRadius: '4px', cursor: 'pointer',
                          background: cdShift === s ? '#183b4e' : '#0b1b24',
                          border: `1px solid ${cdShift === s ? '#57d6c8' : '#1c3442'}`,
                          color: cdShift === s ? '#57d6c8' : '#8da4af'
                        }}
                        onClick={() => {
                          setCdShift(s);
                          loadChangeDetection(true, s);
                        }}
                      >
                        {s.toFixed(1)} px
                      </button>
                    ))}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ color: '#7994a3' }}>VIEW:</span>
                    <button
                      className={`button ${cdViewMode === 'swipe' ? 'primary' : 'secondary'} compact`}
                      style={{ fontSize: '10px', padding: '2px 10px' }}
                      onClick={() => setCdViewMode('swipe')}
                    >
                      Swipe Slider
                    </button>
                    <button
                      className={`button ${cdViewMode === 'diff' ? 'primary' : 'secondary'} compact`}
                      style={{ fontSize: '10px', padding: '2px 10px' }}
                      onClick={() => setCdViewMode('diff')}
                    >
                      Pixel Diff Heatmap
                    </button>
                  </div>
                </div>

                {/* Canvas Area */}
                <div style={{ position: 'relative', flex: 1, minHeight: '520px', background: '#030811', overflow: 'hidden', borderBottom: '1px solid #162c37' }}>
                  {cdLoading ? (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', color: '#57d6c8' }}>
                      <RefreshCw size={26} className="spin" />
                      <span style={{ fontSize: '12px', letterSpacing: '0.05em' }}>CO-REGISTERING ORB FEATURES & EXECUTING YOLO INFERENCE...</span>
                    </div>
                  ) : cdData ? (
                    cdViewMode === 'diff' ? (
                      <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <img
                          src={cdData.diff_preview}
                          alt="Radiometric Difference Heatmap"
                          style={{ maxWidth: '100%', maxHeight: '540px', objectFit: 'contain' }}
                        />
                        <div style={{ position: 'absolute', top: 12, left: 12, background: 'rgba(3,8,17,0.85)', padding: '5px 10px', borderRadius: '4px', border: '1px solid #162c37', fontSize: '11px', color: '#f59e0b' }}>
                          ● RADIOMETRIC DIFFERENCE HEATMAP (SECONDARY SIGNAL)
                        </div>
                      </div>
                    ) : (
                      <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {/* Background: After Scene (T1) */}
                        <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <img
                            src={cdData.after_preview || cdData.before_preview}
                            alt="T1 Surveillance Scene"
                            style={{ maxWidth: '100%', maxHeight: '540px', objectFit: 'contain', userSelect: 'none' }}
                          />
                          {/* Foreground Clipped: Before Scene (T0) */}
                          <div style={{
                            position: 'absolute', inset: 0, width: `${cdSwipe}%`, overflow: 'hidden',
                            borderRight: '2px solid #57d6c8', boxShadow: '4px 0 16px rgba(87,214,200,0.4)',
                            display: 'flex', alignItems: 'center', justifyContent: 'flex-start'
                          }}>
                            <img
                              src={cdData.before_preview}
                              alt="T0 Baseline Scene"
                              style={{ width: '100%', height: '100%', objectFit: 'contain', userSelect: 'none', maxWidth: 'none' }}
                            />
                          </div>
                        </div>

                        {/* Tactical HUD Overlays */}
                        <div style={{ position: 'absolute', top: 12, left: 12, background: 'rgba(3,8,17,0.85)', padding: '5px 10px', borderRadius: '4px', border: '1px solid #162c37', fontSize: '10px', color: '#57d6c8', fontWeight: 600 }}>
                          ◀ T0 BASELINE ({cdSwipe}%)
                        </div>
                        <div style={{ position: 'absolute', top: 12, right: 12, background: 'rgba(3,8,17,0.85)', padding: '5px 10px', borderRadius: '4px', border: '1px solid #162c37', fontSize: '10px', color: '#ffb340', fontWeight: 600 }}>
                          T1 SURVEILLANCE ({100 - cdSwipe}%) ▶
                        </div>

                        {/* Interactive Swipe Range Input */}
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={cdSwipe}
                          onChange={(e) => setCdSwipe(Number(e.target.value))}
                          style={{
                            position: 'absolute', bottom: '18px', left: '10%', width: '80%', zIndex: 20,
                            cursor: 'ew-resize', accentColor: '#57d6c8'
                          }}
                        />
                      </div>
                    )
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b', fontSize: '12px' }}>
                      Click "Run Analysis" to execute bi-temporal change detection on a synthetic pair.
                    </div>
                  )}
                </div>

                {/* Co-Registration Telemetry Bar */}
                {cdData && (
                  <div style={{
                    padding: '8px 14px', background: '#05101a', display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', fontSize: '10px', color: '#7994a3', fontFamily: 'monospace', flexWrap: 'wrap', gap: '8px'
                  }}>
                    <span>ACTIVE SCENE: <b style={{ color: '#e2edf2' }}>{cdData.tile_name}</b> ({cdData.pair_label})</span>
                    <span>CO-REG STATUS: <b style={{ color: '#57d6c8' }}>{cdData.registration?.status} ({cdData.registration?.method})</b></span>
                    <span>RECOVERED SHIFT: dx={cdData.registration?.shift_recovered?.[0]?.toFixed(2)}px, dy={cdData.registration?.shift_recovered?.[1]?.toFixed(2)}px</span>
                    <span>REG ERROR: <b style={{ color: cdData.registration?.registration_error_px < 0.5 ? '#57d6c8' : '#fbbf24' }}>{cdData.registration?.registration_error_px?.toFixed(3)} px</b></span>
                  </div>
                )}
              </section>

              {/* Right Column: Detected Changes & Secondary Signal */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {/* Panel 2A: Object-Level Changes */}
                <section className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <div className="panel-head" style={{ paddingBottom: '6px' }}>
                    <div>
                      <div className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Target size={15} /> Tactical Entity Changes ({cdData?.object_changes?.length || 0})
                      </div>
                      <small>Class-aware one-to-one matching (Hungarian / IoU &ge; 0.25, D &le; 28px)</small>
                    </div>
                  </div>

                  {/* Filter Pills */}
                  <div style={{ display: 'flex', gap: '6px', padding: '6px 12px', borderBottom: '1px solid #162c37', background: '#071520' }}>
                    {(['ALL', 'NEW', 'REMOVED', 'MOVED'] as const).map((f) => (
                      <button
                        key={f}
                        className={`chip ${cdFilter === f ? 'active' : ''}`}
                        style={{
                          padding: '2px 8px', fontSize: '9px', borderRadius: '4px', cursor: 'pointer',
                          background: cdFilter === f ? '#183b4e' : '#0b1b24',
                          border: `1px solid ${cdFilter === f ? '#57d6c8' : '#1c3442'}`,
                          color: cdFilter === f ? '#57d6c8' : '#8da4af'
                        }}
                        onClick={() => setCdFilter(f)}
                      >
                        {f} ({f === 'ALL' ? (cdData?.object_changes?.length || 0) : (cdData?.object_changes?.filter((x: any) => x.change_type === f).length || 0)})
                      </button>
                    ))}
                  </div>

                  {/* Changes List */}
                  <div style={{ flex: 1, overflowY: 'auto', maxHeight: '340px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {!cdData || !cdData.object_changes?.length ? (
                      <div style={{ textAlign: 'center', padding: '24px', color: '#64748b', fontSize: '11px' }}>
                        No changes detected. Run analysis to identify additions, removals, and movements.
                      </div>
                    ) : (
                      cdData.object_changes
                        .filter((c: any) => cdFilter === 'ALL' || c.change_type === cdFilter)
                        .map((chg: any) => {
                          const isNew = chg.change_type === 'NEW';
                          const isMov = chg.change_type === 'MOVED';
                          const badgeColor = isNew ? '#57d6c8' : isMov ? '#fbbf24' : '#f87171';
                          const badgeBg = isNew ? '#092b34' : isMov ? '#2a2209' : '#2b0909';
                          return (
                            <div key={chg.id} style={{
                              padding: '10px 12px', borderRadius: '6px', background: '#091823',
                              border: `1px solid ${isNew ? '#15414e' : isMov ? '#47360e' : '#471414'}`,
                              display: 'flex', flexDirection: 'column', gap: '4px'
                            }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  <span style={{ background: badgeBg, color: badgeColor, padding: '2px 6px', borderRadius: '3px', fontSize: '9px', fontWeight: 700, border: `1px solid ${badgeColor}33` }}>
                                    {chg.change_type}
                                  </span>
                                  <b style={{ color: '#e2edf2', fontSize: '12px' }}>{chg.class_name}</b>
                                </div>
                                <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>
                                  {chg.confidence ? `Conf: ${(chg.confidence * 100).toFixed(0)}%` : (chg.displacement_px ? `Disp: ${chg.displacement_px}px` : '')}
                                </span>
                              </div>

                              <div style={{ fontSize: '10px', color: '#7994a3', fontFamily: 'monospace', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginTop: '2px' }}>
                                <span>PIXEL: [{Math.round(chg.x)}, {Math.round(chg.y)}, {Math.round(chg.w)}, {Math.round(chg.h)}]</span>
                                <span style={{ color: '#57d6c8' }}>WGS84: {chg.lat != null ? `${chg.lat.toFixed(5)}°N, ${chg.lon.toFixed(5)}°E` : 'LOCAL GRID'}</span>
                              </div>
                              <small style={{ color: '#64748b', fontSize: '9px' }}>{chg.details}</small>
                            </div>
                          );
                        })
                    )}
                  </div>
                </section>

                {/* Panel 2B: Secondary Radiometric Pixel Difference Signal */}
                <section className="panel">
                  <div className="panel-head" style={{ paddingBottom: '6px' }}>
                    <div>
                      <div className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Flame size={15} color="#fbbf24" /> Secondary Radiometric Difference
                      </div>
                      <small>Channel-wise gain & bias normalized | Flagging new structures independently</small>
                    </div>
                  </div>

                  <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                      <div style={{ background: '#071520', padding: '8px 10px', borderRadius: '4px', border: '1px solid #142a35' }}>
                        <span style={{ fontSize: '9px', color: '#7994a3' }}>CHANGED PIXELS</span>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: '#fbbf24' }}>
                          {cdData?.pixel_difference?.changed_pixels_count?.toLocaleString() || '0'} px²
                        </div>
                      </div>
                      <div style={{ background: '#071520', padding: '8px 10px', borderRadius: '4px', border: '1px solid #142a35' }}>
                        <span style={{ fontSize: '9px', color: '#7994a3' }}>CHANGED AREA RATIO</span>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: '#57d6c8' }}>
                          {cdData?.pixel_difference?.changed_area_pct?.toFixed(3) || '0.000'}%
                        </div>
                      </div>
                    </div>

                    <div style={{ background: '#06131c', padding: '8px 10px', borderRadius: '4px', border: '1px solid #132733', fontSize: '10px', color: '#8da4af' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span>STRUCTURAL ANOMALIES:</span>
                        <b style={{ color: '#e2edf2' }}>{cdData?.pixel_difference?.structural_anomalies_count || 0} flagged</b>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>RADIOMETRIC NORM:</span>
                        <span style={{ color: '#57d6c8' }}>ACTIVE (Channel Gain/Bias)</span>
                      </div>
                    </div>
                  </div>
                </section>
              </div>
            </div>
          )}

          {/* Footer */}
          <footer className="footer">
            <span>PROJECT RAKSHAK · DEFENSE & MARITIME MULTIMODAL C4ISR SYSTEM · AIR-GAPPED V2.0</span>
            <span className="backend-state">
              <i /> API CONNECTED · SQLITE WAL LOCAL · NVIDIA JETSON COMPATIBLE
            </span>
          </footer>
        </div>
      </main>

      {/* Floating Air-Gapped Tactical AI Bot (Bottom Right Anchor) */}
      <div
        style={{
          position: 'fixed',
          bottom: '26px',
          right: '28px',
          zIndex: 9999,
          width: '54px',
          height: '54px',
          pointerEvents: 'none'
        }}
      >
        {/* Popout Options on the Left - Only active and visible when bot is hovered */}
        <div
          onMouseEnter={handleBotMenuEnter}
          onMouseLeave={handleBotMenuLeave}
          style={{
            position: 'absolute',
            bottom: '0',
            right: '66px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            background: 'linear-gradient(145deg, rgba(8, 22, 32, 0.98), rgba(4, 13, 20, 0.99))',
            backdropFilter: 'blur(14px)',
            border: '1px solid rgba(80, 215, 199, 0.35)',
            boxShadow: '0 12px 36px rgba(0, 0, 0, 0.8), 0 0 24px rgba(20, 184, 166, 0.25)',
            borderRadius: '10px',
            padding: '10px',
            minWidth: '260px',
            opacity: hoverBotOpen ? 1 : 0,
            visibility: hoverBotOpen ? 'visible' : 'hidden',
            transform: hoverBotOpen ? 'translateX(0) scale(1)' : 'translateX(12px) scale(0.96)',
            pointerEvents: hoverBotOpen ? 'auto' : 'none',
            transition: 'all 0.22s cubic-bezier(0.16, 1, 0.3, 1)',
            transformOrigin: 'right center'
          }}
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingBottom: '6px',
            borderBottom: '1px solid rgba(80, 215, 199, 0.15)',
            fontSize: '9px',
            fontWeight: 700,
            letterSpacing: '1px',
            color: '#65d7c9'
          }}>
            <span>TACTICAL AI RAG ADVISORY</span>
            <span style={{
              background: 'rgba(16, 185, 129, 0.15)',
              color: '#10b981',
              padding: '2px 5px',
              borderRadius: '3px',
              fontSize: '8px'
            }}>
              AIR-GAPPED
            </span>
          </div>

          {/* Option 1: Rules of Engagement Advisor */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setPage('Tactical AI (RAG)');
              setRagViewTab('advisor');
              setHoverBotOpen(false);
              setToast('Navigated to Rules of Engagement Advisor');
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: 'rgba(14, 33, 46, 0.85)',
              border: '1px solid rgba(80, 215, 199, 0.2)',
              borderRadius: '7px',
              padding: '8px 10px',
              color: '#e2edf2',
              textAlign: 'left',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(20, 184, 166, 0.2)';
              e.currentTarget.style.borderColor = '#50d7c7';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(14, 33, 46, 0.85)';
              e.currentTarget.style.borderColor = 'rgba(80, 215, 199, 0.2)';
            }}
          >
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '7px',
              background: 'rgba(20, 184, 166, 0.2)',
              border: '1px solid rgba(80, 215, 199, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#55e0d1',
              flexShrink: 0
            }}>
              <Bot size={17} />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <b style={{ display: 'block', fontSize: '11px', color: '#ffffff', letterSpacing: '0.2px' }}>
                Rules of Engagement Advisor
              </b>
              <small style={{ display: 'block', fontSize: '9px', color: '#88a3b0', marginTop: '2px' }}>
                Synthesize RoE & Interdiction SOPs
              </small>
            </div>
            <ChevronRight size={13} style={{ color: '#55e0d1', flexShrink: 0 }} />
          </button>

          {/* Option 2: Sovereign Doctrine Library */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setPage('Tactical AI (RAG)');
              setRagViewTab('library');
              if (!ragKnowledgeBase.length) loadRagKnowledgeBase();
              setHoverBotOpen(false);
              setToast('Navigated to Sovereign Doctrine Library');
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: 'rgba(14, 33, 46, 0.85)',
              border: '1px solid rgba(80, 215, 199, 0.2)',
              borderRadius: '7px',
              padding: '8px 10px',
              color: '#e2edf2',
              textAlign: 'left',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(20, 184, 166, 0.2)';
              e.currentTarget.style.borderColor = '#50d7c7';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(14, 33, 46, 0.85)';
              e.currentTarget.style.borderColor = 'rgba(80, 215, 199, 0.2)';
            }}
          >
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '7px',
              background: 'rgba(56, 189, 248, 0.15)',
              border: '1px solid rgba(56, 189, 248, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38bdf8',
              flexShrink: 0
            }}>
              <BookOpen size={17} />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <b style={{ display: 'block', fontSize: '11px', color: '#ffffff', letterSpacing: '0.2px' }}>
                Sovereign Doctrine Library
              </b>
              <small style={{ display: 'block', fontSize: '9px', color: '#88a3b0', marginTop: '2px' }}>
                6 Indexed Defense SOPs & Treaties
              </small>
            </div>
            <ChevronRight size={13} style={{ color: '#38bdf8', flexShrink: 0 }} />
          </button>
        </div>

        {/* Main Hovering Tactical AI Bot Circular Button - strictly handles circle hover */}
        <div
          onMouseEnter={handleBotCircleEnter}
          onMouseLeave={handleBotCircleLeave}
          onClick={() => {
            setPage('Tactical AI (RAG)');
            setToast('Navigated to Tactical AI (RAG) Advisory Console');
          }}
          title="Tactical AI (RAG) - Click to Open Console"
          style={{
            width: '54px',
            height: '54px',
            borderRadius: '50%',
            background: 'radial-gradient(circle at 35% 35%, #14b8a6 0%, #0f766e 55%, #052627 100%)',
            border: '2px solid #50d7c7',
            boxShadow: hoverBotOpen
              ? '0 0 28px rgba(80, 215, 199, 0.8), 0 6px 20px rgba(0, 0, 0, 0.6)'
              : '0 0 16px rgba(20, 184, 166, 0.45), 0 4px 14px rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            position: 'relative',
            pointerEvents: 'auto',
            transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
            transform: hoverBotOpen ? 'scale(1.08)' : 'scale(1)'
          }}
        >
          <Bot size={26} style={{ color: '#ffffff', filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.5))' }} />

          {/* Pulsing AI Online Indicator Dot */}
          <span
            style={{
              position: 'absolute',
              top: '2px',
              right: '2px',
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              background: '#10b981',
              border: '2px solid #052627',
              boxShadow: '0 0 8px #10b981'
            }}
          />
        </div>
      </div>
    </div>
  );
}

function intPercent(n: number): number {
  return Math.round(n * 100);
}

export default App;
