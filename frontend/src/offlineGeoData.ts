/**
 * Sovereign Defense Air-Gapped Tactical Vector Basemap
 * 100% Client-Side Geometry for Indian Ocean / Arabian Sea / Bay of Bengal AOR
 * ZERO external network calls. ZERO CDN dependencies.
 * Designed for air-gapped FOBs, submarines, and disconnected military command posts.
 */

// Peninsular India & Littoral Coastlines [lat, lon]
export const INDIA_COASTLINE: [number, number][] = [
  // Sir Creek & Gujarat
  [23.85, 68.10], [23.50, 68.30], [23.10, 68.70], [22.80, 69.10], [22.50, 69.80],
  [22.40, 70.30], [22.90, 70.60], [22.50, 70.90], [21.80, 70.20], [21.10, 70.80],
  [20.75, 71.50], [21.50, 72.20], [21.75, 72.50], [21.20, 72.85],
  // Maharashtra & Mumbai Coastline
  [20.50, 72.75], [19.80, 72.70], [19.35, 72.80], [18.95, 72.82], [18.50, 72.95],
  [17.80, 73.10], [17.00, 73.25], [16.50, 73.35],
  // Goa & Karnataka (Karwar / Mangalore)
  [15.80, 73.65], [15.25, 73.90], [14.80, 74.12], [14.20, 74.35], [13.60, 74.65],
  [13.00, 74.80], [12.50, 74.95],
  // Kerala Coast (Kochi / Trivandrum)
  [11.80, 75.30], [11.20, 75.80], [10.50, 76.00], [9.95, 76.25], [9.30, 76.50],
  [8.80, 76.65], [8.40, 76.95],
  // Kanyakumari (Southernmost tip)
  [8.08, 77.55],
  // Tamil Nadu & Coromandel Coast
  [8.40, 78.10], [8.80, 78.15], [9.20, 79.15], [9.45, 79.30], [9.90, 79.20],
  [10.30, 79.85], [10.80, 79.85], [11.50, 79.80], [12.20, 80.00], [13.08, 80.28],
  [13.50, 80.20],
  // Andhra Pradesh Coast (Vizag)
  [14.20, 80.10], [15.20, 80.05], [15.80, 80.40], [16.30, 81.30], [16.80, 82.20],
  [17.20, 82.70], [17.70, 83.30], [18.30, 84.00], [19.00, 84.80],
  // Odisha & Bengal (Paradeep / Sundarbans)
  [19.70, 85.80], [20.20, 86.70], [20.80, 87.00], [21.50, 87.40], [21.80, 88.00],
  [21.60, 88.80], [21.80, 89.20]
];

// Sri Lanka Coastline [lat, lon]
export const SRI_LANKA_COASTLINE: [number, number][] = [
  [9.80, 80.20], [9.30, 79.90], [8.80, 79.80], [8.20, 79.80], [7.50, 79.85],
  [6.95, 79.85], [6.40, 80.00], [5.92, 80.45], [5.95, 80.60], [6.25, 81.10],
  [6.80, 81.85], [7.70, 81.70], [8.55, 81.25], [9.20, 80.90], [9.60, 80.40],
  [9.80, 80.20]
];

// Andaman & Nicobar Archipelago [lat, lon]
export const ANDAMAN_CHAIN: [number, number][] = [
  [13.60, 93.00], [13.20, 92.95], [12.80, 92.85], [12.30, 92.80],
  [11.90, 92.70], [11.60, 92.75], [11.45, 92.70]
];

export const NICOBAR_CHAIN: [number, number][] = [
  [9.20, 92.80], [8.50, 93.50], [7.80, 93.70], [7.20, 93.75],
  [6.85, 93.85], [7.00, 93.95], [7.50, 93.80], [8.20, 93.60],
  [9.20, 92.80]
];

export const LAKSHADWEEP_ISLANDS: [number, number][] = [
  [11.85, 72.80], // Chetlat
  [11.20, 72.75], // Amini
  [10.85, 72.20], // Agatti
  [10.57, 72.63], // Kavaratti
  [10.05, 73.65], // Androth
  [8.30, 73.05]   // Minicoy (Eight Degree Channel)
];

// 200 Nautical Mile Sovereign Exclusive Economic Zone (EEZ) Boundary Polygon
export const INDIAN_EEZ_BOUNDARY: [number, number][] = [
  // Arabian Sea EEZ Outer Perimeter (approx 200nm from baseline)
  [22.80, 65.50], [21.50, 65.80], [20.00, 66.20], [18.50, 67.00],
  [16.80, 68.20], [15.20, 69.50], [13.50, 70.80], [11.50, 71.20],
  [9.50, 71.00],  [7.50, 71.80],  [6.50, 74.00],  [6.00, 76.50],
  // Southern Maritime Boundary / Gulf of Mannar Treaty Line
  [6.20, 78.50],  [7.20, 80.50],  [8.00, 82.50],  [9.50, 83.80],
  // Bay of Bengal EEZ Outer Perimeter
  [11.00, 85.00], [13.00, 86.50], [15.00, 87.80], [17.50, 88.50],
  [19.20, 89.20], [20.50, 89.50]
];

// Tactical Graticule Lines (MGRS / Geodetic Grid for Navigation)
export const TACTICAL_GRATICULES: { id: string; name: string; points: [number, number][] }[] = [
  // Latitude parallels
  { id: 'lat-25', name: '25°00\'N', points: [[25.0, 45.0], [25.0, 105.0]] },
  { id: 'lat-20', name: '20°00\'N', points: [[20.0, 45.0], [20.0, 105.0]] },
  { id: 'lat-15', name: '15°00\'N', points: [[15.0, 45.0], [15.0, 105.0]] },
  { id: 'lat-10', name: '10°00\'N (Ten Degree Channel)', points: [[10.0, 45.0], [10.0, 105.0]] },
  { id: 'lat-5',  name: '05°00\'N', points: [[5.0, 45.0], [5.0, 105.0]] },

  // Longitude meridians
  { id: 'lon-50', name: '50°00\'E', points: [[0.0, 50.0], [32.0, 50.0]] },
  { id: 'lon-60', name: '60°00\'E', points: [[0.0, 60.0], [32.0, 60.0]] },
  { id: 'lon-70', name: '70°00\'E', points: [[0.0, 70.0], [32.0, 70.0]] },
  { id: 'lon-80', name: '80°00\'E', points: [[0.0, 80.0], [32.0, 80.0]] },
  { id: 'lon-90', name: '90°00\'E', points: [[0.0, 90.0], [32.0, 90.0]] },
  { id: 'lon-100', name: '100°00\'E', points: [[0.0, 100.0], [32.0, 100.0]] }
];

// Strategic Strategic Naval Commands, Operational FOBs & Chokepoints
export interface StrategicHub {
  id: string;
  name: string;
  code: string;
  lat: number;
  lon: number;
  type: 'COMMAND_HQ' | 'NAVAL_BASE' | 'CHOKEPOINT' | 'ISLAND_OUTPOST';
  radarRangeKm: number;
}

export const STRATEGIC_HUBS: StrategicHub[] = [
  { id: 'wnc-hq', name: 'Western Naval Command (HQ)', code: 'WNC-BOM', lat: 18.922, lon: 72.834, type: 'COMMAND_HQ', radarRangeKm: 85 },
  { id: 'kadamba', name: 'INS Kadamba (Project Seabird)', code: 'KRW-SEABIRD', lat: 14.819, lon: 74.133, type: 'NAVAL_BASE', radarRangeKm: 75 },
  { id: 'snc-hq', name: 'Southern Naval Command (INS Garuda)', code: 'SNC-COK', lat: 9.931, lon: 76.267, type: 'COMMAND_HQ', radarRangeKm: 75 },
  { id: 'enc-hq', name: 'Eastern Naval Command (INS Circars)', code: 'ENC-VTZ', lat: 17.686, lon: 83.218, type: 'COMMAND_HQ', radarRangeKm: 85 },
  { id: 'anc-hq', name: 'INS Jarawa / Port Blair (Andaman Command)', code: 'ANC-IXZ', lat: 11.623, lon: 92.726, type: 'COMMAND_HQ', radarRangeKm: 90 },
  { id: 'baaz', name: 'INS Baaz (Great Nicobar / 6° Channel)', code: 'BAAZ-NCP', lat: 6.990, lon: 93.850, type: 'ISLAND_OUTPOST', radarRangeKm: 110 },
  { id: 'dwee-rakshak', name: 'INS Dweeprakshak (Kavaratti / Lakshadweep)', code: 'DWEEP-LAK', lat: 10.570, lon: 72.630, type: 'ISLAND_OUTPOST', radarRangeKm: 70 },
  // Critical International Chokepoints Under Surveillance
  { id: 'malacca', name: 'Strait of Malacca Western Funnel', code: 'CHOKE-MALACCA', lat: 5.500, lon: 96.500, type: 'CHOKEPOINT', radarRangeKm: 60 },
  { id: 'nine-deg', name: 'Nine Degree Channel (Minicoy / SLOC)', code: 'CHOKE-9DEG', lat: 9.000, lon: 73.000, type: 'CHOKEPOINT', radarRangeKm: 50 },
  { id: 'six-deg', name: 'Six Degree Channel (Indira Point Gateway)', code: 'CHOKE-6DEG', lat: 6.000, lon: 94.000, type: 'CHOKEPOINT', radarRangeKm: 55 }
];
