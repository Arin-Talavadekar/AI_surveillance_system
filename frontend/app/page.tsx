'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import VideoFeed from '@/components/VideoFeed'
import ThreatMetrics from '@/components/ThreatMetrics'
import AlertLog from '@/components/AlertLog'
import RiskTimeline from '@/components/RiskTimeline'
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
      // Map API AlertData to Alert format expected by AlertLog
      const mappedAlerts: Alert[] = data.map((item: AlertData, index: number) => ({
        id: typeof item.id === 'string' ? item.id : `alert-${index}-${item.timestamp}`,
        type: item.type,
        timestamp: item.timestamp,
        score: item.score
      })).reverse(); // Reverse so newest are at the top, since API sends them chronologically
      setAlerts(mappedAlerts)
    }

    const handleHistoryUpdate = async () => {
      const data = await fetchRiskHistory()
      // Map raw numbers to the { frame, risk } format the AreaChart expects
      const mappedHistory = data.map((val: number, idx: number) => ({
        frame: idx,
        risk: val
      }))
      setRiskHistory(mappedHistory)
    }

    handleAlertsUpdate()
    handleHistoryUpdate()
    
    // Poll slower endpoints every 2s
    const dataInterval = setInterval(() => {
      handleAlertsUpdate()
      handleHistoryUpdate()
    }, 2000)

    return () => clearInterval(dataInterval)
  }, [])

  return (
    <div className="min-h-screen bg-background text-foreground p-4 md:p-6 selection:bg-primary/30 font-mono">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
        className="max-w-[1700px] mx-auto grid grid-cols-1 gap-6 lg:grid-cols-12"
      >
        {/* Main Header */}
        <header className="col-span-1 border-b border-foreground/10 pb-4 lg:col-span-12 flex flex-col items-center justify-center text-center">
          <h1 className="text-xl md:text-3xl font-black tracking-tighter uppercase mb-1">SENTINEL COMMAND CONSOLE</h1>
          <p className="text-[10px] md:text-xs text-muted-foreground uppercase tracking-widest">Surveillance & Threat Detection</p>
        </header>

        {/* Video Feed — 8 cols */}
        <VideoFeed fps={status.fps} />

        {/* Right Panel — 4 cols */}
        <section className="col-span-1 lg:col-span-4 flex flex-col gap-6 h-full">
          <ThreatMetrics
            systemStatus={isBackendConnected ? "Online" : "Offline"}
            riskScore={status.risk_score}
            escalationTrend={status.risk_trend || 0.0}
            peopleCount={status.people_count}
            gruScore={status.gru_score}
            weaponDetected={status.weapon_detected}
          />
          <AlertLog alerts={alerts} />
        </section>

        {/* Timeline — full width */}
        <RiskTimeline history={riskHistory} />
      </motion.div>
    </div>
  )
}