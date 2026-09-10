import React from 'react';
import MapVisualization from './MapVisualization';
import ETATable from './ETATable';
import SimulationControls from './SimulationControls';

export default function Dashboard({ trainState, stationETAs, previousStationETAs, eventExplanation, networkConditions, backendUrl }) {
  
  return (
    <div className="grid grid-cols-12 gap-6 pb-20">
      {/* Structural Main Pillar - Geometry & State */}
      <div className="col-span-12 xl:col-span-6 flex flex-col gap-6">
        
        {/* HUD Statistics Indicators */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-xl bg-slate-900/50 border border-slate-800/80 p-5 shadow-sm backdrop-blur-sm">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Train Target</div>
            <div className="text-2xl font-black text-slate-100">{trainState.train_id}</div>
            <div className="text-sm font-medium text-blue-400 mt-1">{trainState.type || 'Shatabdi Exp'}</div>
          </div>
          
          <div className="rounded-xl bg-slate-900/50 border border-slate-800/80 p-5 shadow-sm backdrop-blur-sm">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Live Node State</div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold text-slate-200">Stn: {trainState.current_station}</span>
            </div>
            <div className={`mt-1 text-sm font-bold tracking-wide ${trainState.current_delay_min > 0 ? 'text-rose-400 animate-pulse' : 'text-emerald-400'}`}>
              Dev: +{trainState.current_delay_min} mins
            </div>
          </div>
          
          <div className="rounded-xl bg-slate-900/50 border border-slate-800/80 p-5 shadow-sm backdrop-blur-sm">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Constraints Map</div>
            <div className="text-xl font-bold text-slate-200">{networkConditions.average_speed_kmph.toFixed(0)} km/h</div>
            <div className="text-sm font-bold text-amber-500 mt-1">Block Stress: {(networkConditions.congestion_level * 100).toFixed(0)}%</div>
          </div>
          
          <div className="rounded-xl bg-slate-900/50 border border-slate-800/80 p-5 shadow-sm backdrop-blur-sm">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Node Anomaly</div>
            <div className={`text-lg font-black tracking-tight ${networkConditions.operational_event === 'Normal' ? 'text-emerald-500' : 'text-rose-500'}`}>
              {networkConditions.operational_event}
            </div>
            <div className="text-xs font-bold text-slate-500 mt-1 uppercase">Physics Overlay</div>
          </div>
        </div>

        {/* Topographic Visual Plot */}
        <div className="rounded-xl bg-slate-900/40 border border-slate-800/80 p-5 h-[400px] shadow flex flex-col">
          <div className="flex justify-between items-center mb-4">
             <div className="text-sm font-bold text-slate-300 uppercase tracking-wider">Spatial Trajectory Graph</div>
          </div>
          <div className="flex-1 w-full rounded-lg overflow-hidden border border-slate-800">
            <MapVisualization trainState={trainState} stationETAs={stationETAs} />
          </div>
        </div>
        
        {/* ML Simulator API Webhooks */}
        <div className="rounded-xl bg-gradient-to-br from-slate-900/80 to-slate-950/80 border border-blue-500/20 p-5 shadow relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4">
             <div className="w-16 h-16 bg-blue-500/10 rounded-full flex items-center justify-center border border-blue-500/20 shadow-inner">
                <span className="text-blue-500 text-xs font-black uppercase tracking-widest">Sim</span>
             </div>
          </div>
          <div className="text-sm font-black text-blue-400 uppercase tracking-widest mb-4 border-b border-slate-800 pb-2 max-w-sm">"What-If" Analysis Injection Tool</div>
          <SimulationControls trainId={trainState.train_id} backendUrl={backendUrl} />
        </div>
        
      </div>
      
      {/* Secondary Structural Pillar - ETA Calculations & Matrices */}
      <div className="col-span-12 xl:col-span-6 flex flex-col gap-6">
        
        {/* Cause / Logic Explanation Context Engine */}
        <div className="rounded-xl bg-blue-900/10 border border-blue-500/20 p-5 shadow flex flex-col">
          <div className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-2 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span> XGBoost Structural Analysis Context
          </div>
          <p className="font-mono text-[13px] text-slate-300 leading-relaxed max-w-xl">
            {eventExplanation}
          </p>
        </div>

        {/* Extrapolated ETA Output Feed comparing the Temporal Deltas */}
        <div className="rounded-xl bg-slate-900/50 border border-slate-800/80 p-5 flex-1 shadow overflow-y-auto min-h-[500px]">
          <div className="flex justify-between items-center mb-5 pb-3 border-b border-slate-800">
            <div className="text-sm font-bold text-slate-300 uppercase tracking-wider">Dynamic Cascade Table: Before vs After Event</div>
          </div>
          <ETATable stationETAs={stationETAs} previousStationETAs={previousStationETAs} />
        </div>
        
      </div>
    </div>
  );
}
