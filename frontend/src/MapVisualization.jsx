import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMapEvents } from 'react-leaflet';
import L from 'leaflet';

// Internal leaflet bundle explicit re-anchoring to fix specific React path bugs
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
});
L.Marker.prototype.options.icon = DefaultIcon;

function ZoomListener({ onZoom }) {
  const map = useMapEvents({
    zoomend: () => onZoom(map.getZoom()),
  });
  useEffect(() => {
    onZoom(map.getZoom());
  }, [map, onZoom]);
  return null;
}

function AutoPanEngine({ currentLocation, isAutoPan, setIsAutoPan }) {
  const map = useMapEvents({
    dragstart: () => {
      // If user physically grabs the map, break the auto-lock
      if (isAutoPan) setIsAutoPan(false);
    }
  });

  useEffect(() => {
    if (isAutoPan && currentLocation) {
      map.panTo(currentLocation, { animate: true, duration: 1.0 });
    }
  }, [currentLocation, isAutoPan, map]);

  return null;
}

export default function MapVisualization({ trainState, stationETAs, allTrains, networkConditions }) {
  const [zoomLevel, setZoomLevel] = useState(7);
  const [isAutoPan, setIsAutoPan] = useState(true);
  // Hardcoded Topographic Nodes mapping exclusively mapping to the Engine defaults cleanly
  const STATION_COORDS = {
    'NDLS': [28.6429, 77.2191], // New Delhi Railway Station Track Layout
    'GZB': [28.6525, 77.4300],
    'ALJN': [27.8817, 78.0820],
    'CNB': [26.4547, 80.3506],
    'LKO': [26.8306, 80.9208]
  };

  const center = STATION_COORDS['ALJN']; // Center heavily framing the central segment trajectory
  const routePath = Object.values(STATION_COORDS); 

  // Guard against missing coords
  const currentLocation = trainState.current_location || STATION_COORDS[trainState.current_station] || center;

  // Derive unique markers for nodes currently waiting prediction logic
  const upcomingStationsList = stationETAs.map(eta => eta.station);

  // Dynamic zoom-aware CSS icons
  const isZoomedIn = zoomLevel >= 10;
  const dotIconHtml = `<div style="width: 16px; height: 16px; background-color: #3b82f6; border: 3px solid white; border-radius: 50%; box-shadow: 0 4px 10px rgba(0,0,0,0.5);"></div>`;
  const trainIconHtml = `<div style="font-size: 28px; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.6));">🚂</div>`;

  const dynamicTrainIcon = new L.divIcon({
    html: isZoomedIn ? trainIconHtml : dotIconHtml,
    className: '',
    iconAnchor: isZoomedIn ? [14, 14] : [8, 8]
  });

  const isCongested = networkConditions?.congestion_level > 0.3;
  const polylineColor = isCongested ? "#ef4444" : "#3b82f6";

  return (
    <div className="relative h-full w-full">
      <MapContainer center={center} zoom={7} className="h-full w-full bg-slate-900" scrollWheelZoom={true}>
        
        <ZoomListener onZoom={setZoomLevel} />
        <AutoPanEngine currentLocation={currentLocation} isAutoPan={isAutoPan} setIsAutoPan={setIsAutoPan} />
      
      {/* Vibrant Topography Map maintaining the colorful base but avoiding the heavy red highways of standard OSM */}
      <TileLayer
        attribution='Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community'
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
      />
      
      {/* Underlying Trajectory geometry bounds with active Congestion Coloring */}
      <Polyline positions={routePath} color={polylineColor} weight={5} opacity={isCongested ? 0.9 : 0.4} dashArray={isCongested ? "" : "8, 12"} />

      {/* Structural Geometry Markers */}
      {Object.entries(STATION_COORDS).map(([code, coords]) => {
         const isCurrent = trainState.current_station === code;
         const isUpcoming = upcomingStationsList.includes(code);
         
         if(isCurrent) return null; // Treated prominently via live Train tracker 
         
         return (
           <Marker key={code} position={coords} opacity={isUpcoming ? 0.7 : 0.3}>
             <Popup>
                 <div className="text-slate-900 font-sans tracking-wide">
                     <div className="font-black text-sm">{code} Node</div>
                     <div className="text-xs">{isUpcoming ? 'Scheduled Prediction Pending' : 'Node Cleared'}</div>
                 </div>
             </Popup>
           </Marker>
         );
      })}

      {/* Ghost Network Trains */}
      {allTrains && Object.values(allTrains).map(train => {
        if (!trainState || train.train_id === trainState.train_id) return null; // Avoid duplicating primary tracker
        if (train.status !== 'EN_ROUTE' && train.status !== 'SIDING') return null;
        
        const ghostLoc = train.current_location || STATION_COORDS[train.current_station] || center;
        
        const ghostTrainIconHtml = `<div style="font-size: 20px; filter: grayscale(1) opacity(0.8);">🚂</div>`;
        const ghostDotIconHtml = `<div style="width: 10px; height: 10px; background-color: #64748b; border: 2px solid white; border-radius: 50%; opacity: 0.8"></div>`;
        const dynamicGhostTrainIcon = new L.divIcon({
          html: isZoomedIn ? ghostTrainIconHtml : ghostDotIconHtml,
          className: '',
          iconAnchor: isZoomedIn ? [10, 10] : [5, 5]
        });

        return (
          <Marker key={train.train_id} position={ghostLoc} zIndexOffset={500} icon={dynamicGhostTrainIcon}>
             <Popup>
                <div className="text-slate-900 font-sans tracking-wide min-w-[120px]">
                   <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Network Traffic</div>
                   <div className="font-black text-sm">{train.train_id} ({train.type})</div>
                   <div className="text-xs mt-1 font-bold text-slate-600">{train.status === 'SIDING' ? 'Waiting in Siding' : 'Mainline Occupancy'}</div>
                </div>
             </Popup>
          </Marker>
        );
      })}

      {/* Live Train Object Marker (Dynamic Zoom Contextual Icon) */}
      <Marker position={currentLocation} zIndexOffset={1000} icon={dynamicTrainIcon}>
        <Popup>
          <div className="text-slate-900 font-sans tracking-wide min-w-[140px]">
            <div className="text-[10px] text-blue-600 font-bold uppercase tracking-widest">Active Object</div>
            <div className="font-black text-sm mb-1">{trainState.train_id} ({trainState.type})</div>
            <div className="bg-slate-100 rounded p-1.5 text-xs border border-slate-200">
               <div><strong>Loc:</strong> {trainState.current_station}</div>
               <div className={`${trainState.current_delay_min > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                  <strong>Dev:</strong> +{trainState.current_delay_min}m
               </div>
            </div>
          </div>
        </Popup>
      </Marker>
      
      </MapContainer>

      {/* Recenter Override UI Overlay */}
      {!isAutoPan && (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[1000]">
          <button 
             onClick={() => setIsAutoPan(true)}
             className="bg-blue-600/90 hover:bg-blue-500 text-white px-5 py-2.5 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.6)] text-[10px] font-bold tracking-widest uppercase border border-blue-400 transition-all flex items-center justify-center gap-2 backdrop-blur-sm"
          >
             <span className="text-sm leading-none">⌖</span> Recenter Train
          </button>
        </div>
      )}
    </div>
  );
}
