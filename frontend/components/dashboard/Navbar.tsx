'use client'

import { format } from 'date-fns'

interface NavbarProps {
  riskScore: number
  lastUpdate: Date | null
}

export default function Navbar({ riskScore, lastUpdate }: NavbarProps) {
  let status = 'SAFE'
  let badgeColor = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'

  if (riskScore >= 0.6) {
    status = 'CRITICAL'
    badgeColor = 'bg-red-500/10 text-red-500 border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.3)]'
  } else if (riskScore >= 0.45) {
    status = 'WARNING'
    badgeColor = 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
  }

  return (
    <nav className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-slate-800 bg-slate-950/80 px-6 backdrop-blur-md">
      {/* Left Axis */}
      <div className="flex flex-col">
        <h1 className="text-lg font-bold tracking-widest text-slate-100">
          SURVEILLANCE NEXUS
        </h1>
        <p className="font-mono text-[10px] uppercase tracking-wider text-slate-400">
          Real-time AI Threat Detection
        </p>
      </div>

      {/* Right Axis */}
      <div className="flex items-center gap-4">
        {/* Live Indicator */}
        <div className="flex items-center gap-2 rounded-md border border-slate-800 bg-slate-900 px-3 py-1.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
          </span>
          <span className="font-mono text-xs font-semibold text-slate-300 uppercase">Live</span>
        </div>

        {/* Status Badge */}
        <div className={`flex items-center justify-center rounded-md border px-4 py-1.5 ${badgeColor}`}>
          <span className="font-mono text-xs font-bold tracking-widest leading-none">
            {status}
          </span>
        </div>

        {/* Timestamp */}
        <div className="font-mono text-xs text-slate-500">
          {lastUpdate ? format(lastUpdate, 'HH:mm:ss') : '--:--:--'}
        </div>
      </div>
    </nav>
  )
}
