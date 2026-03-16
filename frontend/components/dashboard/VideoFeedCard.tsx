'use client'

interface VideoFeedCardProps {
  fps: number
}

const STREAM_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000') + '/video_stream'

export default function VideoFeedCard({ fps }: VideoFeedCardProps) {
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950/50 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
          <h2 className="text-xs font-bold tracking-widest text-slate-300 uppercase">
            Live Stream
          </h2>
        </div>
        
        <div className="flex items-center gap-2 rounded border border-slate-700 bg-slate-800/50 px-2 py-0.5">
          <span className="font-mono text-[10px] tracking-wider text-slate-400">FPS:</span>
          <span className="font-mono text-[10px] font-bold text-slate-200">{fps.toFixed(1)}</span>
        </div>
      </div>

      {/* Video Container (Constrained Height) */}
      <div className="group relative flex h-[420px] w-full items-center justify-center bg-black overflow-hidden object-contain">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={STREAM_URL}
          alt="Surveillance Feed"
          className="h-full w-full object-contain"
          onError={(e) => {
            e.currentTarget.style.display = 'none'
            // Fallback could be handled here
          }}
        />

        {/* Tactical overlay elements */}
        <div className="pointer-events-none absolute inset-0 sm:border-2 border-emerald-500/10 opacity-50 mix-blend-overlay"></div>
        <div className="absolute top-4 left-4 border-l-2 border-t-2 border-slate-500 h-8 w-8 opacity-50"></div>
        <div className="absolute top-4 right-4 border-r-2 border-t-2 border-slate-500 h-8 w-8 opacity-50"></div>
        <div className="absolute bottom-4 left-4 border-l-2 border-b-2 border-slate-500 h-8 w-8 opacity-50"></div>
        <div className="absolute bottom-4 right-4 border-r-2 border-b-2 border-slate-500 h-8 w-8 opacity-50"></div>
        
        {/* Cam ID overlay */}
        <div className="absolute left-6 bottom-6 flex flex-col gap-1">
          <span className="font-mono text-[10px] text-emerald-400/80 uppercase">CAM_SYS_01</span>
          <span className="font-mono text-[10px] text-white/50">{new Date().toISOString().split('T')[0]}</span>
        </div>
      </div>
    </div>
  )
}
