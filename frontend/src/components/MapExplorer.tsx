import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
// Leaflet CSS is already imported globally in main.tsx

// Fix for default Leaflet marker icons in React/Vite
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
    iconUrl: iconUrl,
    iconRetinaUrl: iconRetinaUrl,
    shadowUrl: shadowUrl,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// Define the shape of our property data
interface PropertyData {
  location: string;
  price: string;
  date: string;
  source: string;
  type: string;
  road: string;
  badge: string;
  isLoaded: boolean; // To handle the "Select a location" state
}

const MapExplorer: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);

  // State to hold the sidebar details
  const [data, setData] = useState<PropertyData>({
    location: "SELECT A LOCATION",
    price: "--",
    date: "--",
    source: "--",
    type: "--",
    road: "--",
    badge: "",
    isLoaded: false
  });

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return; // Map already initialized

    // 1. Initialize Map
    const map = L.map(mapContainerRef.current, { zoomControl: false }).setView([7.8731, 80.7718], 8);
    mapInstanceRef.current = map;

    // 2. Add Tile Layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // 3. Add Zoom Control
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // 4. Click Handler
    map.on('click', (e: L.LeafletMouseEvent) => {
        const { lat, lng } = e.latlng;

        // Remove previous marker
        if (markerRef.current) {
            map.removeLayer(markerRef.current);
        }

        // Add new marker
        markerRef.current = L.marker([lat, lng]).addTo(map);

        // Simulate Data Fetch
        simulateNearestRecord();
    });

    // Cleanup on unmount
    return () => {
        if (mapInstanceRef.current) {
            mapInstanceRef.current.remove();
            mapInstanceRef.current = null;
        }
    };
  }, []);

  // Logic from script.js translated to React
  const simulateNearestRecord = () => {
    setLoading(true);

    setTimeout(() => {
        const locations = ["COLOMBO", "GAMPAHA", "KANDY", "GALLE", "KURUNEGALA"];
        const sources = ["Prime Lands DB", "Ikman.lk Dataset", "Public Registry"];
        const types = ["Residential", "Agricultural", "Commercial"];
        const roads = ["Main Road", "20ft Carpet Road", "Concrete Access"];
        const badges = ["VERIFIED", "AVAILABLE", "NEW"];

        const randomPrice = (Math.random() * (4.5 - 0.8) + 0.8).toFixed(2) + "M";

        setData({
            location: locations[Math.floor(Math.random() * locations.length)],
            price: randomPrice,
            date: "2024-12",
            source: sources[Math.floor(Math.random() * sources.length)],
            type: types[Math.floor(Math.random() * types.length)],
            road: roads[Math.floor(Math.random() * roads.length)],
            badge: badges[Math.floor(Math.random() * badges.length)],
            isLoaded: true
        });

        setLoading(false);
    }, 300);
  };

  return (
    <div className="map-grid">
        {/* Map Container */}
        <div className="map-visual">
            <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }}></div>
        </div>

        {/* Details Sidebar */}
        <div className="details-card" style={{ opacity: loading ? 0.7 : 1, transition: 'opacity 0.3s' }}>
            <div className="detail-header">
                <div className="detail-location">{data.location}</div>
                <div className="detail-price">
                    {data.price} <span className="detail-unit">/ perch</span>
                </div>
            </div>

            <div className="detail-grid">
                <div className="detail-item">
                    <label>Date Listed</label>
                    <span>{data.date}</span>
                </div>
                <div className="detail-item">
                    <label>Dataset Source</label>
                    <span>{data.source}</span>
                </div>
                <div className="detail-item">
                    <label>Land Type</label>
                    <span>{data.type}</span>
                </div>
                <div className="detail-item">
                    <label>Access Road</label>
                    <span>{data.road}</span>
                </div>
            </div>

            <div className="detail-image">
                <div 
                    className="detail-badge" 
                    style={{ opacity: data.isLoaded ? 1 : 0 }}
                >
                    {data.badge}
                </div>
                {/* We use a static image for now, as per original code */}
                <img 
                    src="/img/lands.png" 
                    alt="Property" 
                    style={{ opacity: data.isLoaded ? 0.25 : 0.2 }} 
                />
            </div>
        </div>
    </div>
  );
};

export default MapExplorer;