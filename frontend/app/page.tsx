'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import VideoFeed from '@/components/VideoFeed'
import ThreatMetrics from '@/components/ThreatMetrics'
import AlertLog from '@/components/AlertLog'
import RiskTimeline from '@/components/RiskTimeline'
import SpatialRadar from '@/components/SpatialRadar'
import type { Alert } from '@/components/AlertLog'

import { fetchSystemStatus, fetchAlerts, fetchRiskHistory, SystemStatus, AlertData } from '@/lib/api'

export default function Dashboard() {
  const [status, setStatus] = useState<SystemStatus>({
    fps: 0,
    people_count: 0,
    weapon_detected: false,
    gru_score: 0.0,
    risk_score: 0.0,
    risk_trend: 0.0,
    locations: [],
  })

  const [isBackendConnected, setIsBackendConnected] = useState(false)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [riskHistory, setRiskHistory] = useState<{ frame: number; risk: number }[]>([])

  useEffect(() => {
    const handleStatusUpdate = async () => {
      const data = await fetchSystemStatus()
      if (data) {
        setStatus(data)
        setIsBackendConnected(true)
      } else {
        setIsBackendConnected(false)
      }
    }
    
    // Initial fetch
    handleStatusUpdate()
    // Poll every 1s
    const statusInterval = setInterval(handleStatusUpdate, 1000)
    return () => clearInterval(statusInterval)
  }, [])

  useEffect(() => {
    const handleAlertsUpdate = async () => {
      const data = await fetchAlerts()
      const mappedAlerts: Alert[] = data.map((item: AlertData, index: number) => ({
        id: typeof item.id === 'string' ? item.id : `alert-${index}-${item.timestamp}`,
        type: item.type,
        timestamp: item.timestamp,
        score: item.score
      })).reverse().slice(0, 6);
      setAlerts(mappedAlerts)
    }

    const handleHistoryUpdate = async () => {
      const data = await fetchRiskHistory()
      const mappedHistory = data.map((val: number, idx: number) => ({
        frame: idx,
        risk: val
      }))
      setRiskHistory(mappedHistory)
    }

    handleAlertsUpdate()
    handleHistoryUpdate()
    
    const dataInterval = setInterval(() => {
      handleAlertsUpdate()
      handleHistoryUpdate()
    }, 2000)

    return () => clearInterval(dataInterval)
  }, [])

  return (
    <div className="min-h-screen bg-background text-foreground p-4 md:p-8 selection:bg-primary/30 font-mono overflow-x-hidden">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.2, 0.8, 0.2, 1] }}
        className="max-w-[1800px] mx-auto flex flex-col gap-8"
      >
        {/* Main Header */}
        <header className="flex flex-col items-center justify-center text-center py-4 border-b border-foreground/5 mb-2 relative">
           <div className="absolute top-0 left-0 w-32 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
           <div className="absolute bottom-0 right-0 w-32 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
          <h1 className="text-2xl md:text-4xl font-black tracking-tighter uppercase mb-2 bg-clip-text text-transparent bg-gradient-to-b from-foreground to-foreground/70">
            SIGHTLINE COMMAND CONSOLE
          </h1>
          <p className="text-[10px] md:text-xs text-muted-foreground uppercase tracking-[0.4em] font-bold opacity-60">
            Cognitive Surveillance & Threat Intelligence
          </p>
        </header>

        {/* Primary Intelligence Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Tactical Control & Video (8 cols) */}
          <div className="lg:col-span-8 flex flex-col gap-8">
            <VideoFeed fps={status.fps} />
          </div>

          {/* Right Column: Tactical Detail (4 cols) */}
          <aside className="lg:col-span-4 flex flex-col gap-8 h-full">
            <ThreatMetrics
              systemStatus={isBackendConnected ? "Online" : "Offline"}
              riskScore={status.risk_score}
              escalationTrend={status.risk_trend || 0.0}
              peopleCount={status.people_count}
              gruScore={status.gru_score}
              weaponDetected={status.weapon_detected}
            />
            
            <SpatialRadar locations={status.locations || []} />
          </aside>
        </div>

        {/* Intelligence History Desk (Bottom Row) */}
        <footer className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-4">
          <div className="lg:col-span-4">
            <AlertLog alerts={alerts} />
          </div>
          <div className="lg:col-span-8">
            <RiskTimeline history={riskHistory} />
          </div>
        </footer>

        {/* Footer Metadata */}
        <div className="flex justify-between items-center text-[9px] uppercase tracking-widest text-muted-foreground/30 font-black pt-8 border-t border-foreground/5">
            <span>SIGHTLINE_OS_V2.1</span>
            <span>ENCRYPTED_LINK_ESTABLISHED</span>
            <span>© 2026 COGNITIVE_SECURITY_SYSTEMS</span>
        </div>
      </motion.div>
    </div>
  )
}