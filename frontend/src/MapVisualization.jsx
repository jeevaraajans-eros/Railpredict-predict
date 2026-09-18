import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
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

export default function MapVisualization({ trainState, stationETAs }) {
  // Hardcoded Topographic Nodes mapping exclusively mapping to the Engine defaults cleanly
  const STATION_COORDS = {
    'NDLS': [28.6139, 77.2090],
    'GZB': [28.6692, 77.4538],
    'ALJN': [27.8815, 78.0746],
    'CNB': [26.4499, 80.3319],
    'LKO': [26.8467, 80.9462]
  };

  const center = STATION_COORDS['ALJN']; // Center heavily framing the central segment trajectory
  const routePath = Object.values(STATION_COORDS); 

  // Guard against missing coords
  const currentLocation = trainState.current_location || STATION_COORDS[trainState.current_station] || center;

  // Derive unique markers for nodes currently waiting prediction logic
  const upcomingStationsList = stationETAs.map(eta => eta.station);

  return (
    <MapContainer center={center} zoom={7} className="h-full w-full bg-slate-900" scrollWheelZoom={true}>
      
      {/* Dark minimalist tile layer heavily respecting operational bounds visual aesthetics */}
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      
      {/* Underlying Trajectory geometry bounds */}
      <Polyline positions={routePath} color="#3b82f6" weight={4} opacity={0.4} dashArray="8, 12" />

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

      {/* Live Train Object Marker */}
      <Marker position={currentLocation} zIndexOffset={1000}>
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
  );
}
