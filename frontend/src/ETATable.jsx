import React from 'react';

export default function ETATable({ stationETAs, previousStationETAs }) {
  if (!stationETAs || stationETAs.length === 0) return <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-2">Awaiting Timeline Engine Start...</div>;

  const previousMap = {};
  if (previousStationETAs) {
    previousStationETAs.forEach(eta => {
        previousMap[eta.station] = eta;
    });
  }

  return (
    <div className="overflow-x-auto w-full">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-slate-800/30 text-[10px] uppercase tracking-widest text-slate-500 font-bold border-y border-slate-700">
            <th className="p-3 w-1/4">Station</th>
            <th className="p-3 w-1/5">AI ETA</th>
            <th className="p-3 w-1/6">Delay</th>
            <th className="p-3 w-1/6">Change</th>
            <th className="p-3 w-1/6">Risk</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/40">
          {stationETAs.map((eta, idx) => {
            const prev = previousMap[eta.station];
            const currArrival = eta.predicted_arrival.split(' ')[1];
            
            const diff = prev ? (eta.accumulated_delay_min - prev.accumulated_delay_min) : 0;
            
            let diffEl = <span className="text-slate-600">-</span>;
            if (diff > 0) diffEl = <span className="text-rose-400 font-bold bg-rose-500/10 px-1.5 py-0.5 rounded text-[10px] flex items-center w-max gap-1">+{diff}m <span className="text-xs font-black">↑</span></span>;
            if (diff < 0) diffEl = <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded text-[10px] flex items-center w-max gap-1">{diff}m <span className="text-xs font-black">↓</span></span>;

            return (
              <tr key={idx} className="hover:bg-slate-800/20 transition-colors text-sm font-black group">
                <td className="p-3 text-slate-200 group-hover:text-blue-400 transition-colors tracking-wide">{eta.station}</td>
                <td className="p-3 text-indigo-400 font-mono tracking-widest bg-slate-950/20">{currArrival}</td>
                <td className={`p-3 tracking-widest ${eta.accumulated_delay_min > 0 ? 'text-orange-400 drop-shadow-sm' : 'text-emerald-500'}`}>
                   {eta.accumulated_delay_min > 0 ? `+${eta.accumulated_delay_min}` : `${eta.accumulated_delay_min}`}m
                </td>
                <td className="p-3">{diffEl}</td>
                <td className="p-3 text-[10px] tracking-widest uppercase">
                  <span className={`px-2 py-1 rounded inline-block shadow-inner font-bold ${eta.delay_risk === 'High' ? 'bg-rose-900/40 text-rose-400 border border-rose-800/60' : eta.delay_risk === 'Medium' ? 'bg-amber-900/30 text-amber-400 border border-amber-800/40' : 'bg-emerald-900/20 text-emerald-400 border border-emerald-800/30'}`}>
                    {eta.delay_risk}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
