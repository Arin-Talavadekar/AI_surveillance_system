'use client'

import { SystemStatus } from '@/lib/api'

interface QuickStatsProps {
  status: SystemStatus
}

export default function QuickStats({ status }: QuickStatsProps) {
  const { people_count, weapon_detected, gru_score, risk_score } = status

  const metrics = [
    {
      id: 'people',
      label: 'PEOPLE COUNT',
      value: people_count,
      colorClass: 'text-cyan-400'
    },
    {
      id: 'weapon',
      label: 'WEAPON STATUS',
      value: weapon_detected ? 'DETECTED' : 'CLEAR',
      colorClass: weapon_detected ? 'text-red-500' : 'text-emerald-400'
    },
    {
      id: 'anomaly',
      label: 'ANOMALY SCORE',
      value: gru_score.toFixed(3),
      colorClass: gru_score >= 0.6 ? 'text-red-500' : gru_score >= 0.45 ? 'text-yellow-500' : 'text-emerald-400'
    },
    {
      id: 'risk',
      label: 'RISK SCORE',
      value: risk_score.toFixed(3),
      colorClass: risk_score >= 0.6 ? 'text-red-500' : risk_score >= 0.45 ? 'text-yellow-500' : 'text-emerald-400'
    }
  ]

  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-900 shadow-md">
      <div className="border-b border-slate-800 bg-slate-950/30 px-4 py-2">
        <h3 className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">
          Quick Stats
        </h3>
      </div>
      
      <div className="grid grid-cols-2 gap-[1px] bg-slate-800 p-[1px]">
        {metrics.map((m) => (
          <div key={m.id} className="flex flex-col justify-center bg-slate-900 px-4 py-5">
            <span className="mb-1 text-[10px] font-semibold tracking-wider text-slate-500">
              {m.label}
            </span>
            <span className={`font-mono text-2xl font-bold tracking-tight ${m.colorClass}`}>
              {m.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
