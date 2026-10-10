"""Local Sovereign Air-Gapped Tactical Tile Service for Project Rakshak 2.0.

Provides 100% offline, zero-network-egress map tiles for Leaflet.
Generates dynamic 256x256 C4ISR graticule and littoral vector basemap tiles
with coordinate watermarks, landmass contours, and tactical sensor grids.
Zero external network calls (no ArcGIS, no OSM, no Mapbox).
"""
from __future__ import annotations
import io
import math
from typing import Dict, Tuple, List
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

# ── Approximate Simplified Landmass Polygons for Indian Littoral & Key Sectors ─
# (lon, lat) points defining rough continental landmass outlines in WGS84
_SIMPLIFIED_LANDMASSES: List[List[Tuple[float, float]]] = [
    # Indian Subcontinent & South Asia
    [
        (68.0, 24.0), (70.0, 22.0), (72.8, 19.0), (74.0, 15.0), (76.0, 10.0),
        (77.5, 8.1), (79.8, 9.5), (80.3, 13.0), (82.5, 17.0), (85.8, 20.0),
        (88.0, 22.0), (91.5, 22.5), (92.5, 21.0), (94.0, 26.0), (97.0, 28.0),
        (96.0, 29.5), (88.0, 28.0), (81.0, 30.5), (78.0, 32.0), (74.0, 36.5),
        (72.0, 36.0), (69.0, 32.0), (66.5, 29.0), (68.0, 24.0)
    ],
    # Arabian Peninsula (West)
    [
        (35.0, 28.0), (43.0, 13.0), (51.0, 12.0), (59.0, 22.5), (56.0, 26.0),
        (50.0, 27.0), (48.0, 30.0), (35.0, 28.0)
    ],
    # Southeast Asia / Indochina (East)
    [
        (98.0, 10.0), (101.0, 3.0), (104.0, 1.3), (105.0, 10.0), (108.0, 12.0),
        (106.0, 20.0), (99.0, 20.0), (98.0, 10.0)
    ],
    # Sri Lanka
    [
        (79.7, 9.0), (81.8, 8.5), (81.9, 6.9), (80.5, 5.9), (79.8, 7.0), (79.7, 9.0)
    ]
]


def _tile_to_bbox(z: int, x: int, y: int) -> Tuple[float, float, float, float]:
    """Convert Web Mercator tile (z, x, y) to (lon_min, lat_min, lon_max, lat_max)."""
    n = 2.0 ** z
    lon_min = (x / n) * 360.0 - 180.0
    lon_max = ((x + 1) / n) * 360.0 - 180.0

    lat_rad_top = math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / n)))
    lat_max = math.degrees(lat_rad_top)

    lat_rad_bot = math.atan(math.sinh(math.pi * (1.0 - 2.0 * (y + 1) / n)))
    lat_min = math.degrees(lat_rad_bot)

    return (lon_min, lat_min, lon_max, lat_max)


def _coord_to_pixel(lon: float, lat: float, bbox: Tuple[float, float, float, float], size: int = 256) -> Tuple[float, float]:
    """Project (lon, lat) to tile pixel coordinates (px, py)."""
    lon_min, lat_min, lon_max, lat_max = bbox
    px = ((lon - lon_min) / (lon_max - lon_min)) * size if lon_max > lon_min else 0.0
    py = ((lat_max - lat) / (lat_max - lat_min)) * size if lat_max > lat_min else 0.0
    return (px, py)


# In-memory LRU cache holding pre-rendered PNG tiles
_TILE_CACHE: Dict[Tuple[str, int, int, int], bytes] = {}
_MAX_CACHE_SIZE = 4096


def get_offline_tile(style: str, z: int, x: int, y: int) -> bytes:
    """Generate or retrieve a cached 256x256 sovereign C4ISR tactical map tile."""
    style = style.lower().strip()
    cache_key = (style, z, x, y)
    if cache_key in _TILE_CACHE:
        return _TILE_CACHE[cache_key]

    # Validate coordinate boundaries
    max_idx = (2 ** z) - 1
    x = max(0, min(x, max_idx))
    y = max(0, min(y, max_idx))

    bbox = _tile_to_bbox(z, x, y)
    lon_min, lat_min, lon_max, lat_max = bbox

    # 1. Base palette by style
    if style == 'satellite':
        bg_color = (9, 20, 28)        # Dark multispectral charcoal
        grid_color = (24, 48, 64)     # Infrared graticule
        land_color = (18, 38, 52)     # Radar reflective land
        border_color = (32, 72, 98)   # Littoral coastline trace
        text_color = (70, 140, 180)
    elif style == 'terrain':
        bg_color = (6, 17, 24)        # Deep oceanic bathymetry
        grid_color = (20, 42, 56)     # Tactical coordinate mesh
        land_color = (14, 34, 46)     # Coastal topography
        border_color = (28, 80, 105)  # Sovereign maritime buffer
        text_color = (85, 170, 200)
    else:  # 'dark' / default C4ISR
        bg_color = (7, 16, 25)        # Sovereign Tactical Dark
        grid_color = (18, 36, 50)     # MGRS graticule line
        land_color = (15, 32, 45)     # Land silhouette
        border_color = (25, 60, 85)   # Coastal demarcation
        text_color = (60, 130, 165)

    img = Image.new('RGB', (256, 256), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 2. Draw Landmass Polygons if intersecting this tile
    for polygon in _SIMPLIFIED_LANDMASSES:
        poly_px = [_coord_to_pixel(p_lon, p_lat, bbox) for p_lon, p_lat in polygon]
        # Quick boundary check: if any points are reasonably near the tile
        xs = [p[0] for p in poly_px]
        ys = [p[1] for p in poly_px]
        if min(xs) < 256 and max(xs) > 0 and min(ys) < 256 and max(ys) > 0:
            if len(poly_px) >= 3:
                draw.polygon(poly_px, fill=land_color, outline=border_color)

    # 3. Draw Sub-Graticule Lines (Coordinate Grid)
    # Determine step in degrees based on zoom level
    if z <= 3:
        deg_step = 20.0
    elif z <= 6:
        deg_step = 5.0
    elif z <= 9:
        deg_step = 1.0
    elif z <= 12:
        deg_step = 0.2
    else:
        deg_step = 0.05

    # Longitude vertical grid lines
    first_lon = math.floor(lon_min / deg_step) * deg_step
    curr_lon = first_lon
    while curr_lon <= lon_max + deg_step:
        if lon_min <= curr_lon <= lon_max:
            px, _ = _coord_to_pixel(curr_lon, 0.0, bbox)
            draw.line([(px, 0), (px, 256)], fill=grid_color, width=1)
        curr_lon += deg_step

    # Latitude horizontal grid lines
    first_lat = math.floor(lat_min / deg_step) * deg_step
    curr_lat = first_lat
    while curr_lat <= lat_max + deg_step:
        if lat_min <= curr_lat <= lat_max:
            _, py = _coord_to_pixel(0.0, curr_lat, bbox)
            draw.line([(0, py), (256, py)], fill=grid_color, width=1)
        curr_lat += deg_step

    # 4. Outer Tile Boundary Demarcation (Subtle border)
    draw.rectangle([0, 0, 255, 255], outline=(15, 30, 42), width=1)

    # 5. Tactical Coordinate Watermark Label
    center_lat = (lat_min + lat_max) / 2.0
    center_lon = (lon_min + lon_max) / 2.0
    lat_card = "N" if center_lat >= 0 else "S"
    lon_card = "E" if center_lon >= 0 else "W"
    coord_label = f"{abs(center_lat):.2f}°{lat_card} {abs(center_lon):.2f}°{lon_card} [Z{z}]"

    # Draw coordinate watermark on lower left corner
    draw.text((6, 240), coord_label, fill=text_color)

    # 6. Encode to PNG buffer
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    tile_bytes = buf.getvalue()

    # Cache management
    if len(_TILE_CACHE) >= _MAX_CACHE_SIZE:
        # Clear oldest quarter
        to_del = list(_TILE_CACHE.keys())[:1024]
        for k in to_del:
            _TILE_CACHE.pop(k, None)

    _TILE_CACHE[cache_key] = tile_bytes
    return tile_bytes
