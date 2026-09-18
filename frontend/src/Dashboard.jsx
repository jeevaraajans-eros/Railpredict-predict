import React from 'react';
import MapVisualization from './MapVisualization';
import ETATable from './ETATable';
import SimulationControls from './SimulationControls';

export default function Dashboard({ trainState, stationETAs, previousStationETAs, eventExplanation, networkConditions, backendUrl, simState }) {
  
  return (
    <div className="grid grid-cols-12 gap-6 pb-20">
      <div className="col-span-12 xl:col-span-7 flex flex-col gap-6">
        
        {/* NEW TRAIN PANEL */}
        <div className="rounded-xl bg-slate-900 border border-slate-700/60 p-6 shadow-xl relative overflow-hidden">
           {/* Glassy overlay effect */}
           <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl"></div>
           
           <div className="text-3xl font-black text-slate-50 mb-1 drop-shadow-md">TRAIN {trainState?.train_id} — {trainState?.type?.toUpperCase()}</div>
           
           <div className="grid grid-cols-2 md:grid-cols-3 gap-y-6 gap-x-8 mt-6">
              <div>
                <div className="text-slate-400 font-bold uppercase tracking-widest text-[10px] mb-1">Current Location</div>
                <div className="text-slate-100 font-black text-sm tracking-wide">{trainState?.current_section_id ? `Between ${trainState.current_section_id.replace('-', ' → ')}` : `At ${trainState?.current_station}`}</div>
              </div>
              <div>
                <div className="text-slate-400 font-bold uppercase tracking-widest text-[10px] mb-1">Speed</div>
                <div className="text-blue-400 font-black text-sm tracking-wide">{networkConditions?.average_speed_kmph ? networkConditions.average_speed_kmph.toFixed(0) : 80} km/h</div>
              </div>
              <div>
                <div className="text-slate-400 font-bold uppercase tracking-widest text-[10px] mb-1">Current Delay</div>
                <div className={`font-black text-sm tracking-wide ${trainState?.current_delay_min > 0 ? 'text-rose-400 drop-shadow-sm' : 'text-emerald-400'}`}>{trainState?.current_delay_min > 0 ? `+${trainState.current_delay_min}` : `${trainState?.current_delay_min || 0}`} min</div>
              </div>
              <div>
                <div className="text-slate-400 font-bold uppercase tracking-widest text-[10px] mb-1">Next Station</div>
                <div className="text-slate-100 font-black text-sm tracking-wide">{stationETAs.length > 0 ? stationETAs[0].station : '-'}</div>
              </div>
              <div>
                <div className="text-slate-400 font-bold uppercase tracking-widest text-[10px] mb-1">AI ETA</div>
                <div className="text-indigo-400 font-black text-sm tracking-wide">{stationETAs.length > 0 ? stationETAs[0].predicted_arrival.split(' ')[1] : '-'}</div>
              </div>
              <div>
                <div className="text-slate-400 font-bold uppercase tracking-widest text-[10px] mb-1">Delay Risk</div>
                <div className="text-amber-400 font-black text-sm tracking-wide">{stationETAs.length > 0 ? stationETAs[0].delay_risk : '-'}</div>
              </div>
           </div>
        </div>

        <div className="rounded-xl bg-slate-900/40 border border-slate-800/80 p-5 h-[450px] shadow flex flex-col">
          <div className="flex-1 w-full rounded-lg overflow-hidden border border-slate-700/50 shadow-inner bg-black/50 relative">
            <MapVisualization trainState={trainState} stationETAs={stationETAs} />
          </div>
        </div>
        
      </div>
      
      <div className="col-span-12 xl:col-span-5 flex flex-col gap-6">
        
        <SimulationControls trainId={trainState.train_id} backendUrl={backendUrl} simState={simState} />

        <div className="rounded-xl bg-slate-900 border border-slate-700/60 p-4 shadow-lg h-[220px] overflow-y-auto flex flex-col">
          <div className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3 sticky top-0 bg-slate-900 z-10 w-full drop-shadow-md">Simulation Event Timeline</div>
          <div className="flex flex-col gap-3 relative pl-2 mt-1">
             <div className="absolute left-0 top-1 bottom-1 w-px bg-slate-700"></div>
             {simState?.timeline?.slice().reverse().map((evt, idx) => (
                <div key={idx} className="flex gap-4 relative">
                   <div className={`w-2 h-2 rounded-full absolute -left-[9px] top-1 border-2 border-slate-900 shadow-sm ${evt.type === 'WARNING' ? 'bg-rose-500' : 'bg-blue-500'}`}></div>
                   <div className="text-[10px] font-mono font-bold text-slate-500 w-12 pt-0.5">{evt.time}</div>
                   <div className="text-xs font-bold text-slate-200">{evt.event}</div>
                </div>
             ))}
             {(!simState?.timeline || simState.timeline.length === 0) && <div className="text-xs text-slate-500 ml-4 font-bold">No events tracked.</div>}
          </div>
        </div>

        <div className="rounded-xl bg-slate-900 border border-slate-700/60 p-5 shadow-lg flex-col">
          <div className="text-[10px] font-black text-blue-400 uppercase tracking-widest flex items-center gap-2 mb-2">
             Why Did ETA Change?
          </div>
          <div className="font-mono text-[11px] text-slate-300 w-full mt-2">
             {eventExplanation && Array.isArray(eventExplanation) ? (
                 <div className="flex flex-col gap-1.5 w-64">
                    {eventExplanation.map((f, i) => (
                       <div key={i} className={`flex justify-between ${f.label === 'Net change' ? 'border-t border-slate-700 pt-1 mt-1 text-white font-bold' : ''}`}>
                          <span>{f.label}</span>
                          <span className={`font-black tracking-widest ${f.value.includes('+') ? 'text-rose-400' : 'text-emerald-400'}`}>{f.value}</span>
                       </div>
                    ))}
                 </div>
             ) : (
                <span className="text-slate-500">Awaiting ML Vector Generation...</span>
             )}
          </div>
        </div>

        <div className="rounded-xl bg-slate-900 border border-slate-700/60 p-5 flex-1 shadow-lg overflow-y-auto min-h-[350px]">
          <div className="flex justify-between items-center mb-5 pb-3 border-b border-slate-700/80">
            <div className="text-xs font-black text-slate-200 uppercase tracking-widest drop-shadow-sm">Station-Wise Dynamic ETA</div>
          </div>
          <ETATable stationETAs={stationETAs} previousStationETAs={previousStationETAs} />
        </div>
        
      </div>
    </div>
  );
}
