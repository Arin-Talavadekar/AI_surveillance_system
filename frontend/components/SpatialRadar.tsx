'use client'

import { motion } from 'framer-motion'
import { Location } from '@/lib/api'

interface SpatialRadarProps {
  locations: Location[]
}

export default function SpatialRadar({ locations }: SpatialRadarProps) {
  return (
    <div className="bg-card/30 border border-foreground/10 rounded-xl p-4 flex flex-col gap-4 relative overflow-hidden backdrop-blur-md">
      <div className="flex items-center justify-between border-b border-foreground/10 pb-2 mb-2">
        <h3 className="text-[10px] font-black tracking-widest uppercase text-muted-foreground flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          Spatial Surveillance Radar
        </h3>
        <span className="text-[9px] font-mono text-primary/70 tracking-tighter uppercase">GRID_01_ACTIVE</span>
      </div>

      <div className="relative aspect-square w-full max-w-[300px] mx-auto group">
        {/* Radar Background - Circular Grids */}
        <div className="absolute inset-0 border border-foreground/10 rounded-full" />
        <div className="absolute inset-[15%] border border-foreground/5 rounded-full" />
        <div className="absolute inset-[30%] border border-foreground/5 rounded-full" />
        <div className="absolute inset-[45%] border border-foreground/5 rounded-full" />
        
        {/* Radar Crosshair */}
        <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-foreground/10" />
        <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-foreground/10" />

        {/* Sweep Effect */}
        <motion.div
            className="absolute inset-0 rounded-full"
            style={{
                background: 'conic-gradient(from 0deg, transparent 70%, rgba(var(--primary-rgb), 0.1) 100%)',
                zIndex: 1
            }}
            animate={{ rotate: 360 }}
            transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        />

        {/* Location Pings */}
        <div className="absolute inset-0 z-10">
          {locations.map((loc, i) => (
            <motion.div
              key={`${loc.id}-${i}`}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ 
                  opacity: 1, 
                  scale: 1,
                  left: `${loc.x * 100}%`, 
                  top: `${loc.y * 100}%` 
              }}
              transition={{ type: "spring", stiffness: 100, damping: 10 }}
              className="absolute -translate-x-1/2 -translate-y-1/2 group/ping"
            >
              {/* Outer Glow */}
              <motion.div
                animate={{ scale: [1, 1.5, 1], opacity: [0.3, 0.1, 0.3] }}
                transition={{ duration: 2, repeat: Infinity }}
                className={`absolute inset-[-8px] rounded-full ${loc.is_anomalous ? 'bg-destructive/30' : 'bg-primary/20'}`}
              />
              
              {/* Core Point */}
              <div className={`w-2 h-2 rounded-full border border-background shadow-lg ${loc.is_anomalous ? 'bg-destructive' : 'bg-primary'}`} />
              
              {/* Tooltip Label (Visible on hover or if anomalous) */}
              <div className={`absolute left-4 top-1/2 -translate-y-1/2 whitespace-nowrap text-[8px] font-mono px-1.5 py-0.5 rounded border ${loc.is_anomalous ? 'bg-destructive/20 border-destructive text-destructive' : 'bg-background/80 border-foreground/10 text-foreground'} opacity-0 group-hover/ping:opacity-100 transition-opacity`}>
                TGT_{loc.id}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Stats Footer */}
      <div className="grid grid-cols-2 gap-2 mt-2">
        <div className="bg-background/50 border border-foreground/5 rounded-lg p-2">
          <p className="text-[8px] text-muted-foreground uppercase mb-1">Active Targets</p>
          <p className="text-sm font-black font-mono">{locations.length}</p>
        </div>
        <div className="bg-background/50 border border-foreground/5 rounded-lg p-2">
          <p className="text-[8px] text-muted-foreground uppercase mb-1">Threat Context</p>
          <p className={`text-sm font-black font-mono ${locations.some(l => l.is_anomalous) ? 'text-destructive' : 'text-primary'}`}>
            {locations.some(l => l.is_anomalous) ? 'ALERT' : 'SECURE'}
          </p>
        </div>
      </div>
    </div>
  )
}
