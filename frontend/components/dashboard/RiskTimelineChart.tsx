'use client'

import React from 'react'
import {
  LineChart,
  Line,
  ReferenceLine,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface RiskTimelineChartProps {
  data: number[]
  isLoading: boolean
}

export default function RiskTimelineChart({ data, isLoading }: RiskTimelineChartProps) {
  // Convert basic array of numbers into object format for recharts
  const chartData = data.slice(-40).map((val, i) => ({
    time: i,
    risk: parseFloat(val.toFixed(3))
  }))

  return (
    <div className="flex w-full flex-col overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-md">
      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950/30 px-4 py-3">
        <h3 className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">
          Risk Timeline
        </h3>

        <div className="flex gap-4">
          <div className="flex items-center gap-1.5">
            <span className="block h-1.5 w-1.5 rounded-full bg-red-500"></span>
            <span className="font-mono text-[9px] tracking-widest text-slate-500">CRITICAL (&gt;0.6)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="block h-1.5 w-1.5 rounded-full bg-yellow-500"></span>
            <span className="font-mono text-[9px] tracking-widest text-slate-500">WARNING (&gt;0.45)</span>
          </div>
        </div>
      </div>

      <div className="h-[280px] p-4 w-full relative">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <span className="font-mono text-[10px] tracking-widest text-slate-500 animate-pulse">Load Data...</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              
              <XAxis dataKey="time" hide />
              
              <YAxis 
                domain={[0, 1]} 
                tick={{ fontSize: 10, fill: '#64748b', fontFamily: 'monospace' }} 
                axisLine={false}
                tickLine={false}
              />
              
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  border: '1px solid #1e293b',
                  borderRadius: '6px',
                  fontFamily: 'monospace',
                  fontSize: '11px',
                  color: '#e2e8f0'
                }}
                formatter={(val: unknown) => {
                  if (typeof val === 'number') return val.toFixed(3)
                  return String(val)
                }}
              />

              <ReferenceLine y={0.6} stroke="#dc2626" strokeDasharray="4 4" opacity={0.5} />
              <ReferenceLine y={0.45} stroke="#eab308" strokeDasharray="4 4" opacity={0.5} />

              <Line
                type="monotone"
                dataKey="risk"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false} // Disable animation to prevent layout jumps on constant poll
                name="Risk Score"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
