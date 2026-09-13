import React, { useEffect, useRef, memo } from 'react';
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Circle,
  Polyline,
  Tooltip,
  useMap,
} from 'react-leaflet';
import { ZoomIn, ZoomOut, Maximize2, Compass } from 'lucide-react';

// Controller to smoothly animate map camera ONLY when station is explicitly selected via search/list
function MapController({ selectedStation, isMapClickRef }) {
  const map = useMap();
  const prevStationIdRef = useRef(null);

  useEffect(() => {
    // Invalidate map size on initial layout
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 200);
    return () => clearTimeout(timer);
  }, [map]);

  useEffect(() => {
    if (!selectedStation) return;

    // If selected station is unchanged, do not touch camera
    if (prevStationIdRef.current === selectedStation.station_id) return;
    prevStationIdRef.current = selectedStation.station_id;

    // If selection was triggered by clicking directly on the map marker, DO NOT hijack pan/zoom!
    if (isMapClickRef.current) {
      isMapClickRef.current = false;
      return;
    }

    // Otherwise smoothly pan to station while respecting user's current zoom level
    const currentZoom = map.getZoom();
    const targetZoom = Math.max(currentZoom, 6);
    map.flyTo([selectedStation.latitude, selectedStation.longitude], targetZoom, {
      duration: 0.8,
      easeLinearity: 0.25,
    });
  }, [selectedStation, map, isMapClickRef]);

  return null;
}

// Custom on-map zoom buttons (never hijacks user position)
function MapControls({ totalStations = 900 }) {
  const map = useMap();
  return (
    <div
      style={{
        position: 'absolute',
        top: '16px',
        left: '16px',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
      }}
    >
      <button
        className="glass-card map-ctrl-btn"
        onClick={() => map.zoomIn()}
        title="Zoom In (or use mouse scroll)"
      >
        <ZoomIn size={15} />
      </button>
      <button
        className="glass-card map-ctrl-btn"
        onClick={() => map.zoomOut()}
        title="Zoom Out (or use mouse scroll)"
      >
        <ZoomOut size={15} />
      </button>
      <button
        className="glass-card map-ctrl-btn"
        onClick={() => map.flyTo([22.5, 82.5], 4.8, { duration: 0.8 })}
        title="Fit All Indian AWS Stations (Reset Subcontinent View)"
        style={{ color: '#00f0ff' }}
      >
        <Maximize2 size={14} />
      </button>
    </div>
  );
}

// Memoized Canvas Stations Layer for instantaneous 60fps rendering without React DOM overhead
const StationsCanvasLayer = memo(function StationsCanvasLayer({
  stations,
  selectedStationId,
  onSelectStation,
  isMapClickRef,
}) {
  return (
    <>
      {stations.map((s) => {
        const isSelected = s.station_id === selectedStationId;
        let color = '#00e599'; // Emerald Nominal
        if (s.status === 'WARNING') color = '#ffb800'; // Amber Suspect
        if (s.status === 'CRITICAL') color = '#ff3366'; // Crimson Anomaly
        if (s.status === 'WEATHER') color = '#00f0ff'; // Cyan Extreme Weather

        return (
          <CircleMarker
            key={s.station_id}
            center={[s.latitude, s.longitude]}
            radius={isSelected ? 8 : 4.5}
            pathOptions={{
              color: isSelected ? '#ffffff' : color,
              fillColor: color,
              fillOpacity: isSelected ? 1.0 : 0.85,
              weight: isSelected ? 2.5 : 1.0,
            }}
            eventHandlers={{
              click: () => {
                isMapClickRef.current = true;
                onSelectStation(s);
              },
            }}
          >
            <Tooltip direction="top" offset={[0, -6]} opacity={0.95}>
              <div style={{ fontSize: '11px', lineHeight: '1.4', fontFamily: 'var(--font-body)', minWidth: '150px' }}>
                <strong style={{ color: '#00f0ff' }}>{s.station_name}</strong>
                <div style={{ color: '#94a3b8', fontSize: '10px' }}>
                  WMO: {s.station_id} • {s.elevation_m ?? 150}m
                </div>
                <div style={{ color: '#c9d1d9', fontSize: '10px' }}>
                  {s.state || 'India'}
                </div>
                <div style={{ marginTop: '3px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 700, color, fontSize: '10px' }}>{s.status}</span>
                  <span style={{ color: '#8b949e', fontSize: '10px' }}>Health: {Math.round(s.health_score ?? 98)}%</span>
                </div>
                <div style={{ marginTop: '3px', fontSize: '9px', color: '#58a6ff', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '2px' }}>
                  Click to inspect & run models →
                </div>
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </>
  );
});

export default function GisMap({
  stations,
  selectedStation,
  nearestNeighbors,
  onSelectStation,
  searchRadiusKm = 150,
}) {
  const isMapClickRef = useRef(false);
  const defaultCenter = [22.8, 79.5]; // Geographical center of India

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}>
      <MapContainer
        center={defaultCenter}
        zoom={5}
        minZoom={4}
        maxZoom={14}
        preferCanvas={true} // High-performance HTML5 Canvas renderer eliminates all marker lag
        scrollWheelZoom={true} // Allow free unrestricted zooming
        style={{ width: '100%', height: '100%', background: '#050811' }}
        zoomControl={false}
      >
        <MapController selectedStation={selectedStation} isMapClickRef={isMapClickRef} />
        <MapControls />

        {/* Esri World Dark Gray Base (Ultra-clean dark canvas without clutter or watermark) */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          attribution="&copy; Esri | IMD AWS National Mesonet"
          maxZoom={16}
        />

        {/* Esri Dark Boundaries and Reference Labels */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
          maxZoom={16}
          opacity={0.7}
        />

        {/* Spatial Correlation Vectors to Nearest Mesonet Neighbors */}
        {selectedStation && nearestNeighbors && nearestNeighbors.map((n) => (
          <Polyline
            key={n.station_id}
            positions={[
              [selectedStation.latitude, selectedStation.longitude],
              [n.latitude, n.longitude],
            ]}
            pathOptions={{
              color: '#00f0ff',
              weight: 1.5,
              dashArray: '4, 6',
              opacity: 0.7,
            }}
          />
        ))}

        {/* 150 km Regional Correlation Radius Buffer */}
        {selectedStation && (
          <Circle
            center={[selectedStation.latitude, selectedStation.longitude]}
            radius={searchRadiusKm * 1000}
            pathOptions={{
              color: '#00f0ff',
              fillColor: '#00f0ff',
              fillOpacity: 0.05,
              weight: 1.2,
              dashArray: '6, 6',
            }}
          />
        )}

        {/* High-Performance Canvas Stations Layer */}
        <StationsCanvasLayer
          stations={stations}
          selectedStationId={selectedStation?.station_id}
          onSelectStation={onSelectStation}
          isMapClickRef={isMapClickRef}
        />

        {/* Selected Station Glowing Radar Ring */}
        {selectedStation && (
          <CircleMarker
            center={[selectedStation.latitude, selectedStation.longitude]}
            radius={15}
            pathOptions={{
              color: '#00f0ff',
              fillColor: '#00f0ff',
              fillOpacity: 0.2,
              weight: 2.0,
              dashArray: '3, 4',
            }}
          />
        )}
      </MapContainer>

      {/* Top-Right Active AWS Observatories Counter Badge */}
      <div
        className="glass-panel"
        style={{
          position: 'absolute',
          top: '16px',
          right: '16px',
          padding: '6px 14px',
          zIndex: 1000,
          fontSize: '11px',
          display: 'flex',
          gap: '10px',
          alignItems: 'center',
          backdropFilter: 'blur(20px)',
          background: 'rgba(5, 5, 8, 0.92)',
          border: '1px solid rgba(255, 255, 255, 0.14)',
          borderRadius: '6px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.8)',
        }}
      >
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3fb950', boxShadow: '0 0 8px #3fb950' }} />
        <span style={{ color: '#f0f6fc', fontWeight: 600 }}>
          {stations.length} AWS Stations Rendered
        </span>
        <span style={{ color: '#8b949e', fontSize: '10px' }}>
          • IMD National Mesonet GIS
        </span>
      </div>

      {/* Mesonet Spatial Status Legend */}
      <div
        className="glass-panel"
        style={{
          position: 'absolute',
          bottom: '16px',
          right: '16px',
          padding: '8px 16px',
          zIndex: 1000,
          fontSize: '11px',
          display: 'flex',
          gap: '16px',
          alignItems: 'center',
          backdropFilter: 'blur(20px)',
          background: 'rgba(5, 5, 8, 0.95)',
          border: '1px solid rgba(255, 255, 255, 0.14)',
          borderRadius: '8px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.8)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#00e599', boxShadow: '0 0 8px #00e599' }} />
          <span style={{ color: '#f8fafc', fontWeight: 600 }}>Nominal</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#ffb800', boxShadow: '0 0 8px #ffb800' }} />
          <span style={{ color: '#f8fafc', fontWeight: 600 }}>Suspect</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#ff3366', boxShadow: '0 0 8px #ff3366' }} />
          <span style={{ color: '#f8fafc', fontWeight: 600 }}>Anomaly</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#00f0ff', boxShadow: '0 0 8px #00f0ff' }} />
          <span style={{ color: '#f8fafc', fontWeight: 600 }}>Extreme Weather</span>
        </div>
      </div>
    </div>
  );
}
