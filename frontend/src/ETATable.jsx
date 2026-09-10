import React from 'react';

export default function ETATable({ stationETAs, previousStationETAs }) {
  if (!stationETAs || stationETAs.length === 0) return <div className="text-sm font-mono text-slate-500">Awaiting ML Pipeline inference...</div>;
  
  // Safely map previous states bridging structural cascades mathematically
  let previousMap = {};
  if (previousStationETAs && previousStationETAs.length > 0) {
     previousStationETAs.forEach(eta => {
        previousMap[eta.station] = eta;
     });
  } else {
     stationETAs.forEach(eta => {
        previousMap[eta.station] = eta;
     });
  }

  return (
    <div className="overflow-x-auto w-full">
      <table className="w-full text-left font-sans text-sm whitespace-nowrap">
        <thead>
          <tr className="border-b border-slate-800 tracking-widest text-slate-500 font-bold uppercase text-[10px]">
            <th className="py-3 px-3 w-[20%]">Node / Geometry</th>
            <th className="py-3 px-3">Prior Trajectory</th>
            <th className="py-3 px-3 relative">
                <span className="text-blue-400 bg-blue-500/10 px-2 py-1 rounded">Adjusted Cascade</span>
            </th>
            <th className="py-3 px-3 text-center">Δ Δelay Difference</th>
            <th className="py-3 px-3 text-right w-[20%]">Extrapolated Risk</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/20 text-[13px]">
          {stationETAs.map((eta, idx) => {
            const prev = previousMap[eta.station];
            const prevArrival = prev ? prev.predicted_arrival.split(' ')[1] : eta.predicted_arrival.split(' ')[1];
            const currArrival = eta.predicted_arrival.split(' ')[1];
            
            const prevDelay = prev ? prev.accumulated_delay_min : eta.accumulated_delay_min;
            const diffDelay = eta.accumulated_delay_min - prevDelay;
            const isWorse = diffDelay > 0;
            const isBetter = diffDelay < 0;
            
            let changeDisplay = "Stable Matrix";
            let changeColor = "text-slate-500 opacity-60";
            if (isWorse) {
              changeDisplay = `+${diffDelay} min (Accumulation)`;
              changeColor = "text-rose-400 font-black";
            } else if (isBetter) {
              changeDisplay = `${absOutput(diffDelay)} min (Recovery)`;
              changeColor = "text-emerald-400 font-black";
            }

            // Flashing highlight trigger when the UI notices Delta updates strictly!
            const isFlashingHighlight = diffDelay !== 0 ? 'bg-blue-500/5' : 'hover:bg-slate-900/30';

            return (
              <React.Fragment key={idx}>
                <tr className={`${isFlashingHighlight} transition-colors duration-1000 border-none`}>
                  <td className="pt-5 px-3 font-black text-slate-200 tracking-wider flex items-center gap-3">
                    <span className={`w-2 h-2 rounded-full ${diffDelay !== 0 ? 'bg-blue-500 animate-pulse' : 'bg-slate-700'}`}></span>
                    {eta.station}
                  </td>
                  
                  <td className="pt-5 px-3 font-mono text-slate-500">
                    {prevArrival}
                    <div className="text-[10px] uppercase font-sans mt-0.5 tracking-widest">{prevDelay > 0 ? '+'+prevDelay+'m cascaded' : 'Expected On-Time'}</div>
                  </td>
                  
                  <td className="pt-5 px-3 font-mono text-white text-[15px]">
                    {currArrival}
                    <div className={`text-[10px] font-bold uppercase font-sans mt-0.5 tracking-widest ${eta.accumulated_delay_min > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {eta.accumulated_delay_min > 0 ? '+'+eta.accumulated_delay_min+'m bound' : 'Expected On-Time'}
                    </div>
                  </td>
                  
                  <td className={`pt-5 px-3 font-mono text-center tracking-tight ${changeColor}`}>
                    {changeDisplay}
                  </td>
                  
                  <td className="pt-5 px-3 text-right">
                    <RiskBadge risk={eta.delay_risk} />
                    <div className="text-[10px] text-slate-500 font-mono mt-1 w-full flex justify-end">
                       CI Threshold: ±[{eta.confidence_interval.lower_bound_min}-{eta.confidence_interval.upper_bound_min}]
                    </div>
                  </td>
                </tr>
                {/* Explainability Engine Row */}
                <tr className={`${isFlashingHighlight} transition-colors duration-1000 border-b border-slate-800/50`}>
                  <td colSpan="5" className="px-3 pb-4 pt-2 border-none">
                     <div className="bg-slate-950/70 p-2.5 shadow-inner rounded border border-slate-800/50 flex flex-col gap-1 items-start w-full whitespace-normal">
                         <div className="text-[9px] uppercase font-black tracking-widest text-blue-500/80 flex items-center gap-1.5 opacity-80">
                           <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
                           AI Prediction Determinants
                         </div>
                         <div className="text-[11px] font-mono text-slate-300 w-full leading-relaxed mt-0.5">
                           > {eta.explanation || "Tracking pending inference cycle."}
                         </div>
                     </div>
                  </td>
                </tr>
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function absOutput(val) {
   return Math.abs(val);
}

function RiskBadge({ risk }) {
  const colors = {
    Low: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    Medium: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    High: "bg-rose-500/10 text-rose-400 border-rose-500/20"
  };
  return (
    <span className={`px-2 py-1 text-[10px] uppercase font-black rounded border tracking-widest shadow-sm ${colors[risk] || 'bg-slate-800 text-slate-300'}`}>
      {risk} RISK
    </span>
  );
}
