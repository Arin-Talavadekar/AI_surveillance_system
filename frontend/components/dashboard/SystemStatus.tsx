'use client'

import { SystemStatus } from '@/lib/api'

interface SystemStatusCardProps {
  status: SystemStatus
  isBackendConnected: boolean
}

export default function SystemStatusCard({ status, isBackendConnected }: SystemStatusCardProps) {
  const { fps, weapon_detected } = status

  const getStatusColor = (state: 'good' | 'warning' | 'critical') => {
    switch (state) {
      case 'good':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
      case 'warning':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'critical':
        return 'bg-red-500/20 text-red-400 border-red-500/30'
    }
  }

  type StatusState = 'good' | 'warning' | 'critical'
  
  const items: Array<{label: string, value: string, state: StatusState}> = [
    {
      label: 'CAMERA FEED',
      value: fps > 0 ? 'CONNECTED' : 'OFFLINE',
      state: fps > 20 ? 'good' : (fps > 0 ? 'warning' : 'critical')
    },
    {
      label: 'BACKEND API',
      value: isBackendConnected ? 'ONLINE' : 'UNREACHABLE',
      state: isBackendConnected ? 'good' : 'critical'
    },
    {
      label: 'AI MODELS',
      value: weapon_detected ? 'ACTIVE ALERTS' : 'LOADED',
      state: isBackendConnected ? (weapon_detected ? 'warning' : 'good') : 'critical'
    }
  ]

  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-900 shadow-md">
      <div className="border-b border-slate-800 bg-slate-950/30 px-4 py-2">
        <h3 className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">
          System Diagnostics
        </h3>
      </div>
      
      <div className="flex flex-col p-4 space-y-4">
        {items.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between">
            <span className="text-[10px] font-semibold tracking-wider text-slate-400">
              {item.label}
            </span>
            <div className={`rounded border px-2 py-0.5 ${getStatusColor(item.state)}`}>
              <span className="font-mono text-[9px] font-bold tracking-widest">
                {item.value}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
