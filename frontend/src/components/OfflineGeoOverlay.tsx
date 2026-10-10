import React, { useMemo } from 'react';
import { GeoJSON, Circle, CircleMarker, Popup } from 'react-leaflet';
import worldLandData from '../world_land.json';
import {
  INDIA_COASTLINE,
  SRI_LANKA_COASTLINE,
  ANDAMAN_CHAIN,
  NICOBAR_CHAIN,
  LAKSHADWEEP_ISLANDS,
  INDIAN_EEZ_BOUNDARY,
  TACTICAL_GRATICULES,
  STRATEGIC_HUBS
} from '../offlineGeoData';

export interface OfflineGeoOverlayProps {
  enabled?: boolean;
  basemapMode?: string;
  showStrategicHubs?: boolean;
}

/**
 * Reusable 100% Air-Gapped Sovereign Vector Overlay for Leaflet Maps.
 * Renders Peninsular India Coastline, Sri Lanka, Island Chains,
 * 200nm Sovereign EEZ, Tactical Graticules (MGRS), and Coastal Radar Rings.
 * ZERO external network calls. ZERO CDN dependencies.
 */
export const OfflineGeoOverlay: React.FC<OfflineGeoOverlayProps> = ({
  enabled = true,
  basemapMode = 'basemap',
  showStrategicHubs = true
}) => {
  if (!enabled) return null;

  const tacticalGeoJsonData = useMemo<any>(() => {
    const worldFeatures = ((worldLandData as any)?.features || []).map((f: any, idx: number) => ({
      ...f,
      id: f.id || `world-land-${idx}`,
      properties: {
        ...(f.properties || {}),
        type: 'LANDMASS'
      }
    }));

    const operationalFeatures = [
      {
        type: 'Feature',
        properties: { name: 'Indian Sovereign Littoral Coastline', type: 'COASTLINE' },
        geometry: {
          type: 'LineString',
          coordinates: INDIA_COASTLINE.map(([lat, lon]) => [lon, lat])
        }
      },
      {
        type: 'Feature',
        properties: { name: 'Sri Lanka Coastline', type: 'COASTLINE' },
        geometry: {
          type: 'LineString',
          coordinates: SRI_LANKA_COASTLINE.map(([lat, lon]) => [lon, lat])
        }
      },
      {
        type: 'Feature',
        properties: { name: 'Andaman Archipelago', type: 'COASTLINE' },
        geometry: {
          type: 'LineString',
          coordinates: ANDAMAN_CHAIN.map(([lat, lon]) => [lon, lat])
        }
      },
      {
        type: 'Feature',
        properties: { name: 'Nicobar Archipelago', type: 'COASTLINE' },
        geometry: {
          type: 'LineString',
          coordinates: NICOBAR_CHAIN.map(([lat, lon]) => [lon, lat])
        }
      },
      {
        type: 'Feature',
        properties: { name: 'Lakshadweep Archipelago', type: 'COASTLINE' },
        geometry: {
          type: 'LineString',
          coordinates: LAKSHADWEEP_ISLANDS.map(([lat, lon]) => [lon, lat])
        }
      },
      {
        type: 'Feature',
        properties: { name: 'Indian Sovereign EEZ Boundary (200nm)', type: 'EEZ' },
        geometry: {
          type: 'LineString',
          coordinates: INDIAN_EEZ_BOUNDARY.map(([lat, lon]) => [lon, lat])
        }
      },
      ...TACTICAL_GRATICULES.map(g => ({
        type: 'Feature',
        properties: { name: g.name, type: 'GRATICULE' },
        geometry: {
          type: 'LineString',
          coordinates: g.points.map(([lat, lon]) => [lon, lat])
        }
      }))
    ];

    return {
      type: 'FeatureCollection',
      features: [...worldFeatures, ...operationalFeatures]
    };
  }, []);

  const tacticalGeoJsonStyle = (feature: any) => {
    const fType = feature?.properties?.type;
    if (fType === 'LANDMASS') {
      return {
        fillColor: '#122637',
        fillOpacity: 0.95,
        color: 'rgba(56, 189, 248, 0.45)',
        weight: 1.0,
        opacity: 0.8
      };
    }
    if (fType === 'COASTLINE') {
      return {
        color: '#00f0ff',
        weight: 3.0,
        opacity: 1.0
      };
    }
    if (fType === 'EEZ') {
      return {
        color: '#f59e0b',
        weight: 2.2,
        dashArray: '6 6',
        opacity: 0.95
      };
    }
    if (fType === 'GRATICULE') {
      return {
        color: 'rgba(56, 189, 248, 0.25)',
        weight: 1,
        dashArray: '3 6',
        opacity: 0.6
      };
    }
    return { color: '#00f0ff', weight: 1.5 };
  };

  return (
    <>
      <GeoJSON
        key={`geo-overlay-${basemapMode}`}
        data={tacticalGeoJsonData}
        style={tacticalGeoJsonStyle}
      />

      {showStrategicHubs && STRATEGIC_HUBS.map(hub => (
        <span key={hub.id}>
          <Circle
            center={[hub.lat, hub.lon]}
            radius={hub.radarRangeKm * 1000}
            pathOptions={{
              color: hub.type === 'COMMAND_HQ' ? '#06b6d4' : '#64748b',
              fillColor: hub.type === 'COMMAND_HQ' ? '#06b6d4' : '#64748b',
              fillOpacity: 0.04,
              weight: 1,
              dashArray: '3 5'
            }}
          />
          <CircleMarker
            center={[hub.lat, hub.lon]}
            radius={hub.type === 'COMMAND_HQ' ? 6 : 4}
            pathOptions={{
              color: hub.type === 'COMMAND_HQ' ? '#00f0ff' : '#94a3b8',
              fillColor: '#071622',
              fillOpacity: 1,
              weight: 2
            }}
          >
            <Popup>
              <div style={{ fontSize: '11px', fontFamily: 'monospace' }}>
                <b style={{ color: '#00f0ff' }}>{hub.name}</b>
                <div style={{ color: '#94a3b8', fontSize: '9px' }}>
                  CALLSIGN: {hub.code} | TYPE: {hub.type}
                </div>
                <div style={{ color: '#f59e0b', fontSize: '9px', marginTop: '2px' }}>
                  COASTAL RADAR RANGE: {hub.radarRangeKm} KM
                </div>
              </div>
            </Popup>
          </CircleMarker>
        </span>
      ))}
    </>
  );
};

export default OfflineGeoOverlay;
