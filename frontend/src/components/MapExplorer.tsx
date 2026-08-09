import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';

import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl,
  iconRetinaUrl,
  shadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

// ─── types ────────────────────────────────────────────────────────────────────
export type PropertyPageType = 'land' | 'house' | 'rental';

export interface MapExplorerProps {
  pageType?: PropertyPageType;
}

/** Compact land record (keys minified to save bytes) */
interface LandRec {
  a: number;   // lat
  o: number;   // lon
  l: string;   // location
  di: string;  // district
  p: number;   // price_per_perch
  s: number;   // land_size_perches
  t: string;   // land_type
  dt: string;  // date_listed
  ds: string;  // dataset_source
  ar: string;  // access_road
  b: string;   // badge
}

/** Compact house record */
interface HouseRec {
  a: number;   // lat
  o: number;   // lon
  l: string;   // location
  di: string;  // district
  p: number;   // price_lkr
  ps: number | null;  // price_per_sqft
  sq: number;  // house_sqft
  lp: number | null;  // land_perches
  bd: number;  // bedrooms
  bt: number;  // bathrooms
  fu: string;  // furnishing
  dt: string;  // date_listed
  b: string;   // badge
}

/** Compact rental record */
interface RentalRec {
  a: number;   // lat
  o: number;   // lon
  l: string;   // location
  di: string;  // district
  p: number;   // monthly_rent_lkr
  pt: string;  // property_type
  sq: number | null;  // floor_area_sqft
  bd: number;  // bedrooms
  bt: number;  // bathrooms
  lt: string;  // lease_term
  dt: string;  // date_listed
  b: string;   // badge
}

type AnyRec = LandRec | HouseRec | RentalRec;

// ─── nearest-point lookup (Euclidean on lat/lon) ──────────────────────────────
function nearestRecord<T extends { a: number; o: number }>(
  records: T[],
  lat: number,
  lon: number,
): T | null {
  if (!records.length) return null;
  let best = records[0];
  let bestD = Infinity;
  for (const r of records) {
    const d = (r.a - lat) ** 2 + (r.o - lon) ** 2;
    if (d < bestD) { bestD = d; best = r; }
  }
  return best;
}

// ─── format helpers ───────────────────────────────────────────────────────────
function fmtLKR(v: number): string {
  if (v >= 1_000_000) return `LKR ${(v / 1_000_000).toFixed(2)}M`;
  if (v >= 1_000)     return `LKR ${(v / 1_000).toFixed(0)}K`;
  return `LKR ${v.toLocaleString()}`;
}

function bedBath(bd: number, bt: number): string {
  const parts: string[] = [];
  if (bd > 0) parts.push(`${bd} Bed${bd > 1 ? 's' : ''}`);
  if (bt > 0) parts.push(`${bt} Bath${bt > 1 ? 's' : ''}`);
  return parts.join(' \u2022 ') || '--';
}

function locLabel(l: string, di: string): string {
  const loc = (l || '').trim().toUpperCase();
  const dist = (di || '').trim().toUpperCase();
  return loc === dist || !dist ? loc : `${loc}, ${dist}`;
}

// ─── display shape ────────────────────────────────────────────────────────────
interface DisplayData {
  location: string;
  price: string;
  unit: string;
  badge: string;
  fields: { label: string; value: string }[];
  image: string;
  isLoaded: boolean;
}

const EMPTY: Record<PropertyPageType, DisplayData> = {
  land: {
    location: 'SELECT A LOCATION',
    price: '--',
    unit: '/ perch',
    badge: '',
    image: '/img/lands.png',
    isLoaded: false,
    fields: [
      { label: 'Date Listed',    value: '--' },
      { label: 'Dataset Source', value: '--' },
      { label: 'Land Type',      value: '--' },
      { label: 'Access Road',    value: '--' },
    ],
  },
  house: {
    location: 'SELECT A LOCATION',
    price: '--',
    unit: '/ sale',
    badge: '',
    image: '/img/housing.png',
    isLoaded: false,
    fields: [
      { label: 'House Size',  value: '--' },
      { label: 'Beds & Baths', value: '--' },
      { label: 'Land Area',   value: '--' },
      { label: 'Furnishing',  value: '--' },
    ],
  },
  rental: {
    location: 'SELECT A LOCATION',
    price: '--',
    unit: '/ month',
    badge: '',
    image: '/img/rentals.png',
    isLoaded: false,
    fields: [
      { label: 'Property Type', value: '--' },
      { label: 'Floor Area',    value: '--' },
      { label: 'Beds & Baths',  value: '--' },
      { label: 'Lease Term',    value: '--' },
    ],
  },
};

function toLandDisplay(r: LandRec): DisplayData {
  return {
    location: locLabel(r.l, r.di),
    price: fmtLKR(r.p),
    unit: '/ perch',
    badge: r.b,
    image: '/img/lands.png',
    isLoaded: true,
    fields: [
      { label: 'Date Listed',    value: r.dt || '--' },
      { label: 'Dataset Source', value: r.ds || 'Ikman.lk' },
      { label: 'Land Type',      value: r.t  || 'Residential' },
      { label: 'Access Road',    value: r.ar || '--' },
    ],
  };
}

function toHouseDisplay(r: HouseRec): DisplayData {
  return {
    location: locLabel(r.l, r.di),
    price: fmtLKR(r.p),
    unit: '/ sale',
    badge: r.b,
    image: '/img/housing.png',
    isLoaded: true,
    fields: [
      { label: 'House Size',   value: r.sq ? `${r.sq.toLocaleString()} sqft` : '--' },
      { label: 'Beds & Baths', value: bedBath(r.bd, r.bt) },
      { label: 'Land Area',    value: r.lp ? `${r.lp} perches` : '--' },
      { label: 'Furnishing',   value: r.fu || '--' },
    ],
  };
}

function toRentalDisplay(r: RentalRec): DisplayData {
  return {
    location: locLabel(r.l, r.di),
    price: fmtLKR(r.p),
    unit: '/ month',
    badge: r.b,
    image: '/img/rentals.png',
    isLoaded: true,
    fields: [
      { label: 'Property Type', value: r.pt || '--' },
      { label: 'Floor Area',    value: r.sq ? `${Number(r.sq).toLocaleString()} sqft` : '--' },
      { label: 'Beds & Baths',  value: bedBath(r.bd, r.bt) },
      { label: 'Lease Term',    value: r.lt || 'Monthly' },
    ],
  };
}

// ─── component ────────────────────────────────────────────────────────────────
const MapExplorer: React.FC<MapExplorerProps> = ({ pageType = 'land' }) => {
  const mapRef     = useRef<HTMLDivElement>(null);
  const mapInst    = useRef<L.Map | null>(null);
  const markerRef  = useRef<L.Marker | null>(null);
  const recordsRef = useRef<AnyRec[]>([]);

  const [data,     setData]     = useState<DisplayData>(EMPTY[pageType]);
  const [loading,  setLoading]  = useState(false);
  const [dbStatus, setDbStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');

  // ── fetch dataset on pageType change ────────────────────────────────────────
  useEffect(() => {
    setData(EMPTY[pageType]);
    recordsRef.current = [];
    setDbStatus('loading');

    const urls: Record<PropertyPageType, string> = {
      land:   '/data/market_land.json',
      house:  '/data/market_house.json',
      rental: '/data/market_rental.json',
    };

    fetch(urls[pageType])
      .then(r => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); })
      .then((rows: AnyRec[]) => {
        recordsRef.current = rows;
        setDbStatus('ready');
      })
      .catch(() => setDbStatus('error'));
  }, [pageType]);

  // ── init Leaflet (once) ──────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || mapInst.current) return;

    const map = L.map(mapRef.current, { zoomControl: false })
      .setView([7.8731, 80.7718], 8);
    mapInst.current = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    return () => { mapInst.current?.remove(); mapInst.current = null; };
  }, []);

  // ── click handler — re-registers whenever dbStatus or pageType changes ──────
  const pageTypeRef = useRef(pageType);
  pageTypeRef.current = pageType;

  useEffect(() => {
    const map = mapInst.current;
    if (!map) return;

    const onClick = (e: L.LeafletMouseEvent) => {
      const { lat, lng } = e.latlng;

      if (markerRef.current) map.removeLayer(markerRef.current);
      markerRef.current = L.marker([lat, lng]).addTo(map);

      if (!recordsRef.current.length) {
        setData({ ...EMPTY[pageTypeRef.current], location: 'DATA NOT LOADED' });
        return;
      }

      setLoading(true);
      // Defer to allow spinner to paint
      setTimeout(() => {
        const rec = nearestRecord(recordsRef.current, lat, lng);
        if (!rec) { setLoading(false); return; }

        const pt = pageTypeRef.current;
        let display: DisplayData;
        if (pt === 'land')        display = toLandDisplay(rec as LandRec);
        else if (pt === 'house')  display = toHouseDisplay(rec as HouseRec);
        else                      display = toRentalDisplay(rec as RentalRec);

        setData(display);
        setLoading(false);
      }, 0);
    };

    map.on('click', onClick);
    return () => { map.off('click', onClick); };
  }, [dbStatus, pageType]);

  // ── render ───────────────────────────────────────────────────────────────────
  return (
    <div className="map-grid">

      {/* ── Map panel ── */}
      <div className="map-visual" style={{ position: 'relative' }}>
        <div ref={mapRef} style={{ width: '100%', height: '100%' }} />

        {dbStatus === 'loading' && (
          <div style={{
            position: 'absolute', top: 14, left: '50%', transform: 'translateX(-50%)',
            background: 'rgba(17,17,34,0.72)', backdropFilter: 'blur(6px)',
            color: '#e0e4ff', padding: '7px 20px', borderRadius: 24,
            fontSize: 13, fontWeight: 600, zIndex: 1000, pointerEvents: 'none',
            letterSpacing: '0.4px',
          }}>
            Loading market data&hellip;
          </div>
        )}

        {dbStatus === 'error' && (
          <div style={{
            position: 'absolute', top: 14, left: '50%', transform: 'translateX(-50%)',
            background: 'rgba(180,40,40,0.82)', backdropFilter: 'blur(6px)',
            color: '#fff', padding: '7px 20px', borderRadius: 24,
            fontSize: 13, fontWeight: 600, zIndex: 1000, pointerEvents: 'none',
          }}>
            Market data unavailable
          </div>
        )}

        {dbStatus === 'ready' && !data.isLoaded && (
          <div style={{
            position: 'absolute', bottom: 14, left: '50%', transform: 'translateX(-50%)',
            background: 'rgba(17,17,34,0.65)', backdropFilter: 'blur(6px)',
            color: '#c8d0ff', padding: '7px 20px', borderRadius: 24,
            fontSize: 13, zIndex: 1000, pointerEvents: 'none', whiteSpace: 'nowrap',
          }}>
            Click anywhere on the map
          </div>
        )}
      </div>

      {/* ── Sidebar ── */}
      <div
        className="details-card"
        style={{ opacity: loading ? 0.6 : 1, transition: 'opacity 0.25s ease' }}
      >
        <div className="detail-header">
          <div className="detail-location">{data.location}</div>
          <div className="detail-price">
            {data.price}
            {data.unit && <span className="detail-unit"> {data.unit}</span>}
          </div>
        </div>

        <div className="detail-grid">
          {data.fields.map((f, i) => (
            <div className="detail-item" key={i}>
              <label>{f.label}</label>
              <span>{f.value}</span>
            </div>
          ))}
        </div>

        <div className="detail-image">
          <div
            className="detail-badge"
            style={{ opacity: data.isLoaded && data.badge ? 1 : 0, transition: 'opacity 0.3s' }}
          >
            {data.badge}
          </div>
          <img
            src={data.image}
            alt="Property illustration"
            style={{ opacity: data.isLoaded ? 0.38 : 0.18, transition: 'opacity 0.4s' }}
          />
        </div>
      </div>

    </div>
  );
};

export default MapExplorer;