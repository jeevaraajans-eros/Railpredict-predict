import React from 'react';
import axios from 'axios';

export default function SimulationControls({ trainId, backendUrl, simState }) {
  const triggerEvent = (event_type, severity) => {
    axios.post(`${backendUrl}/simulation/event`, { train_id: trainId, event_type, severity })
      .catch(err => console.error("Webhook dispatch failed", err));
  };

  const handleSim = (action, mult = 1) => {
    axios.post(`${backendUrl}/simulation/control`, { action, speed_multiplier: mult }).catch(console.error);
  };

  const isRunning = simState?.isRunning || false;
  const speed = simState?.speedMultiplier || 1;

  return (
    <div className="flex flex-col gap-4">
      {/* Clock & Core execution */}
      <div className="bg-slate-900 border border-slate-700/60 p-4 rounded-xl shadow-lg">
         <div className="flex justify-between items-center mb-4">
             <div className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                 <span className={`${isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-slate-600'} w-2 h-2 rounded-full inline-block`}></span>
                 Simulation Clock
             </div>
             <div className="text-xl font-mono font-black text-emerald-400 tracking-widest bg-slate-950 px-3 py-1 rounded drop-shadow-md border border-slate-800">{simState?.time || '12:00:00'}</div>
         </div>
         <div className="flex gap-2 mb-3">
            {!isRunning ? (
               <button onClick={() => handleSim('START', speed)} className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-black text-xs tracking-wider flex-1 transition-colors drop-shadow">▶ START SIMULATION</button>
            ) : (
               <button onClick={() => handleSim('PAUSE')} className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-lg font-black text-xs tracking-wider flex-1 transition-colors drop-shadow">⏸ PAUSE</button>
            )}
            <button onClick={() => handleSim('RESET')} className="bg-slate-700 hover:bg-slate-600 text-slate-200 px-4 py-2 rounded-lg font-black text-xs tracking-wider transition-colors border border-slate-600">↻ RESET</button>
         </div>
         <div className="flex text-xs font-bold items-center gap-2">
            <span className="text-slate-500 uppercase tracking-widest mr-2 text-[10px]">Speed:</span>
            {[1, 5, 10, 60].map(s => (
               <button key={s} onClick={() => handleSim('START', s)} className={`px-2.5 py-1 rounded border ${speed === s ? 'bg-blue-600 text-white border-blue-500 shadow-inner' : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:bg-slate-700'}`}>{s}x</button>
            ))}
         </div>
      </div>
      
      {/* Event Webhooks */}
      <h3 className="text-slate-500 text-[10px] font-bold uppercase tracking-widest">Disruption Scenarios</h3>
      <div className="grid grid-cols-2 gap-2">
        <button onClick={() => triggerEvent('congestion', 1.0)} className="bg-blue-900/40 hover:bg-blue-800/60 border border-blue-800/60 text-blue-200 px-3 py-2 rounded text-[10px] font-bold tracking-wider transition-all uppercase text-left">Inject Congestion</button>
        <button onClick={() => triggerEvent('speed restriction', 0.5)} className="bg-orange-900/30 hover:bg-orange-800/40 border border-orange-800/50 text-orange-200 px-3 py-2 rounded text-[10px] font-bold tracking-wider transition-all uppercase text-left">Speed Restriction</button>
        <button onClick={() => triggerEvent('operational halt', 1.0)} className="bg-rose-900/30 hover:bg-rose-800/40 border border-rose-800/50 text-rose-200 px-3 py-2 rounded text-[10px] font-bold tracking-wider transition-all uppercase text-left">Operational Halt</button>
        <button onClick={() => triggerEvent('clear disruption', 0.0)} className="bg-slate-800/60 hover:bg-slate-700 border border-slate-700/80 text-slate-200 px-3 py-2 rounded text-[10px] font-bold tracking-wider transition-all uppercase text-left shadow-sm">Clear Disruption</button>
      </div>
    </div>
  );
}
