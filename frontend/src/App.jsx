import React, { useState, useEffect } from 'react';
import Dashboard from './Dashboard';
import axios from 'axios';
import './index.css';

const BACKEND_URL = 'http://localhost:8123';
const WS_URL = 'ws://localhost:8123/ws/live';

function App() {
  const [trainState, setTrainState] = useState(null);
  const [stationETAs, setStationETAs] = useState([]);
  const [simState, setSimState] = useState({ isRunning: false, time: '12:00:00', speedMultiplier: 1 });
  const [previousStationETAs, setPreviousStationETAs] = useState([]);
  const [eventExplanation, setEventExplanation] = useState("System loaded constraints chronologically from historical base schedule without topological disruptions.");
  
  const [networkConditions, setNetworkConditions] = useState({ 
    congestion_level: 0.3, 
    operational_event: 'Normal', 
    average_speed_kmph: 80.0 
  });
  
  const selectedTrain = '12004';

  useEffect(() => {
    // 1. Initial Load Bootup 
    axios.get(`${BACKEND_URL}/trains/${selectedTrain}`)
      .then(res => {
        if(res.data) {
          setTrainState(res.data);
          // Zero delta baseline initialize
          if (res.data.latest_eta) {
             setStationETAs(res.data.latest_eta.station_wise_etas || []);
             setPreviousStationETAs(res.data.latest_eta.station_wise_etas || []);
             setEventExplanation(res.data.latest_eta.causal_breakdown || []);
          }
        }
      })
      .catch(err => console.error("Error fetching Native Engine API mapping:", err));
  }, []);

  useEffect(() => {
    // 2. Continuous Event WebSockets Architecture
    const ws = new WebSocket(WS_URL);
    
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'SIMULATION_TICK') {
          const ts = payload.trains[selectedTrain];
          if (ts) {
             setTrainState(ts);
             if (ts.latest_eta) {
                setStationETAs(ts.latest_eta.station_wise_etas || []);
                setEventExplanation(ts.latest_eta.causal_breakdown || []);
             }
          }
          if (payload.network) setNetworkConditions(payload.network);
          if (payload.sim_state) {
              setSimState({
                isRunning: payload.sim_state.is_running,
                time: payload.time,
                speedMultiplier: payload.sim_state.speed_multiplier,
                timeline: payload.sim_state.timeline
              });
          }
        }
        if (payload.type === 'ETA_UPDATE' && payload.train_id === selectedTrain) {
          // Store Before vs After cleanly without mutation leakage via cascade
          setStationETAs(prevCurrent => {
            setPreviousStationETAs(prevCurrent);
            return payload.data.station_wise_etas;
          });
          setTrainState(payload.data.initial_train_state);
        } else if (payload.type === 'NETWORK_EVENT') {
          // Trap explicit event hooks triggering snapshot locking across ETAs dynamically
          setStationETAs(current => {
             setPreviousStationETAs(current);
             return current;
          });
        }
      } catch (err) {
        console.error("WS Engine Parse Error:", err);
      }
    };
    
    return () => ws.close();
  }, [selectedTrain]);

  if (!trainState) return <div className="flex h-screen items-center justify-center bg-slate-950 font-mono text-slate-400">Loading ETA Simulation Matrix Engine...</div>;

  return (
    <div className="min-h-screen bg-slate-950 p-4 font-sans text-slate-200 selection:bg-blue-500/30">
      <header className="mb-6 flex items-center justify-between border-b border-slate-800 pb-4 max-w-8xl mx-auto">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-1">RailPredict AI Operations</h1>
          <p className="text-xs font-mono text-slate-400 uppercase tracking-widest">Context-Aware Neural Simulation Control Panel</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="rounded-md bg-slate-900 px-3 py-1.5 font-mono text-xs font-bold border border-slate-800 shadow-inner">
             ENGINE STATUS: <span className="text-emerald-400 animate-pulse ml-2">● LIVE_STREAM</span>
          </div>
        </div>
      </header>
      
      <main className="max-w-8xl mx-auto">
         <Dashboard 
           trainState={trainState} 
           stationETAs={stationETAs}
           previousStationETAs={previousStationETAs}
           eventExplanation={eventExplanation}
           networkConditions={networkConditions} 
           backendUrl={BACKEND_URL}
           simState={simState}
         />
      </main>
    </div>
  );
}

export default App;
