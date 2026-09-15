import React, { useEffect, useRef, useState, memo } from 'react';
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Circle,
  Polyline,
  Tooltip,
  useMap,
} from 'react-leaflet';
import { ZoomIn, ZoomOut, Maximize2, Compass, Cloud } from 'lucide-react';

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
function MapControls({ showCloudLayer, setShowCloudLayer }) {
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
      <button
        className={`glass-card map-ctrl-btn ${showCloudLayer ? 'btn-ghost-active' : ''}`}
        onClick={() => setShowCloudLayer(!showCloudLayer)}
        title={showCloudLayer ? 'Hide Satellite Cloud Layer' : 'Show Live NOAA/INSAT Satellite IR Cloud Cover'}
        style={{ color: showCloudLayer ? '#38bdf8' : '#94a3b8' }}
      >
        <Cloud size={15} />
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
  const [showCloudLayer, setShowCloudLayer] = useState(true);
  const [radarTileUrl, setRadarTileUrl] = useState(null);
  const defaultCenter = [22.8, 79.5]; // Geographical center of India

  // Fetch latest live global precipitation radar / cloud frame from RainViewer
  useEffect(() => {
    fetch('https://api.rainviewer.com/public/weather-maps.json')
      .then((res) => res.json())
      .then((data) => {
        const latestPath = data?.radar?.past?.slice(-1)[0]?.path;
        if (latestPath) {
          setRadarTileUrl(`https://tilecache.rainviewer.com${latestPath}/256/{z}/{x}/{y}/2/1_1.png`);
        }
      })
      .catch((err) => {
        console.warn('Failed to load RainViewer weather tiles:', err);
      });
  }, []);

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
        <MapControls showCloudLayer={showCloudLayer} setShowCloudLayer={setShowCloudLayer} />

        {/* Esri World Dark Gray Base (Ultra-clean dark canvas without clutter or watermark) */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          attribution="&copy; Esri | IMD AWS National Mesonet"
          maxZoom={16}
        />

        {/* Real-Time RainViewer Live Weather Radar & Cloud Cover Layer */}
        {showCloudLayer && radarTileUrl && (
          <TileLayer
            url={radarTileUrl}
            attribution="&copy; RainViewer Real-Time Weather Radar &amp; Satellite Imagery"
            opacity={0.75}
            maxNativeZoom={6}
            maxZoom={16}
          />
        )}

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

      {/* Top-Right Unified Observatories & Status Legend Panel */}
      <div
        className="glass-panel map-header-legend"
        style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          padding: '8px 12px',
          zIndex: 1000,
          fontSize: '11px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          background: 'rgba(15, 23, 42, 0.92)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: '8px',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
          maxWidth: 'calc(100vw - 80px)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
            <span style={{ color: '#f8fafc', fontWeight: 700, fontSize: '0.75rem' }}>
              {stations.length} AWS Stations
            </span>
          </div>
          <button
            onClick={() => setShowCloudLayer(!showCloudLayer)}
            style={{
              background: showCloudLayer ? '#0284c7' : '#1e293b',
              border: showCloudLayer ? '1px solid #38bdf8' : '1px solid #475569',
              borderRadius: '12px',
              padding: '3px 10px',
              color: '#ffffff',
              fontSize: '0.72rem',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontWeight: 700,
              boxShadow: showCloudLayer ? '0 0 10px rgba(56, 189, 248, 0.4)' : 'none',
              transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
            title="Toggle Satellite IR Cloud Cover Layer on Map"
          >
            <Cloud size={13} color="#ffffff" />
            <span>Satellite Clouds</span>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: showCloudLayer ? '#38bdf8' : '#64748b',
                boxShadow: showCloudLayer ? '0 0 6px #38bdf8' : 'none',
              }}
            />
          </button>
        </div>

        {/* Legend Indicators */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', paddingTop: '4px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00e599' }} />
            <span style={{ color: '#cbd5e1', fontSize: '0.68rem' }}>Nominal</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ffb800' }} />
            <span style={{ color: '#cbd5e1', fontSize: '0.68rem' }}>Suspect</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ff3366' }} />
            <span style={{ color: '#cbd5e1', fontSize: '0.68rem' }}>Anomaly</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00f0ff' }} />
            <span style={{ color: '#cbd5e1', fontSize: '0.68rem' }}>Storm Event</span>
          </div>
        </div>
      </div>
    </div>
  );
}

