import React, { useState } from 'react';
import axios from 'axios';

export default function SimulationControls({ trainId, backendUrl }) {
  const [loading, setLoading] = useState(false);

  const injectEvent = async (type, severity) => {
    setLoading(true);
    try {
      await axios.post(`${backendUrl}/simulation/event`, {
        train_id: trainId,
        event_type: type,
        severity: severity,
        details: 'Manual Operator HTTP Push'
      });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const btnStyle = "w-full py-2.5 px-3 rounded text-[11px] uppercase tracking-widest font-black transition-all disabled:opacity-50 disabled:cursor-not-allowed border shadow-sm flex items-center justify-center gap-2";
  
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3">
        <button 
          onClick={() => injectEvent('congestion', 0.9)}
          disabled={loading}
          className={`${btnStyle} bg-amber-500/10 text-amber-500 border-amber-500/20 hover:bg-amber-500/20`}
        >
          Inject Congestion
        </button>
        <button 
          onClick={() => injectEvent('speed restriction', 0.45)}
          disabled={loading}
          className={`${btnStyle} bg-orange-500/10 text-orange-400 border-orange-500/20 hover:bg-orange-500/20`}
        >
          Speed Limits (45%)
        </button>
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        <button 
          onClick={() => injectEvent('operational halt', 1.0)}
          disabled={loading}
          className={`${btnStyle} bg-rose-500/10 text-rose-500 border-rose-500/30 hover:bg-rose-500/20`}
        >
          Force Node Halt
        </button>
        <button 
          onClick={() => injectEvent('clear disruption', 0.0)}
          disabled={loading}
          className={`${btnStyle} bg-emerald-500/10 text-emerald-500 border-emerald-500/30 hover:bg-emerald-500/20`}
        >
          Verify Cleared
        </button>
      </div>
      
      <div className="mt-2 p-3 bg-slate-950 rounded border border-slate-800/50">
         <p className="text-[10px] text-slate-500 font-mono tracking-wide leading-relaxed">
           > These POST endpoints strictly circumvent static constraints, explicitly passing anomalies to the XGBoost predictor and calculating pure Markov-bounds across the cascaded graph via BackgroundTasks instances asynchronously triggering WebSockets streams.
         </p>
      </div>
    </div>
  );
}
