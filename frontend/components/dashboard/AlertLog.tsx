'use client'

import { AlertData } from '@/lib/api'

interface AlertLogProps {
  alerts: AlertData[]
}

export default function AlertLog({ alerts }: AlertLogProps) {
  return (
    <div className="flex flex-1 flex-col overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-md">
      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950/30 px-4 py-2 flex-shrink-0">
        <h3 className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">
          Alert Log
        </h3>
        <div className="flex items-center gap-1.5">
          <div className="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse"></div>
          <span className="font-mono text-[9px] font-semibold tracking-widest text-red-500 uppercase">
            Live Monitoring
          </span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar min-h-[150px] max-h-[300px]">
        {alerts.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center space-y-2 opacity-50">
            <p className="text-[10px] font-semibold tracking-widest text-slate-500 uppercase">
              No Active Alerts
            </p>
          </div>
        ) : (
          alerts.map((alert, idx) => (
            <div key={idx} className="relative overflow-hidden rounded border border-red-500/20 bg-red-950/20 p-2 text-left">
              <div className="absolute left-0 top-0 h-full w-0.5 bg-red-500 opacity-80" />
              <div className="flex flex-col pl-2">
                <span className="font-mono text-[10px] font-bold tracking-wider text-red-400">
                  {alert.type || 'UNKNOWN ALERT'}
                </span>
                <span className="mt-1 font-mono text-[9px] text-slate-500">
                  {alert.timestamp || new Date().toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
