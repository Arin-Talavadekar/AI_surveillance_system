'use client'

import { useEffect, useState } from 'react'
import Navbar from '@/components/dashboard/Navbar'
import VideoFeedCard from '@/components/dashboard/VideoFeedCard'
import QuickStats from '@/components/dashboard/QuickStats'
import SystemStatusCard from '@/components/dashboard/SystemStatus'
import AlertLog from '@/components/dashboard/AlertLog'
import RiskTimelineChart from '@/components/dashboard/RiskTimelineChart'

import { fetchSystemStatus, fetchAlerts, fetchRiskHistory, SystemStatus, AlertData } from '@/lib/api'

export default function Dashboard() {
  const [status, setStatus] = useState<SystemStatus>({
    fps: 0,
    people_count: 0,
    weapon_detected: false,
    gru_score: 0.0,
    risk_score: 0.0,
  })

  // Start disconnected until first poll succeeds
  const [isBackendConnected, setIsBackendConnected] = useState(false)
  const [alerts, setAlerts] = useState<AlertData[]>([])
  const [riskHistory, setRiskHistory] = useState<number[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  useEffect(() => {
    const handleStatusUpdate = async () => {
      const data = await fetchSystemStatus()
      if (data) {
        setStatus(data)
        setIsBackendConnected(true)
        setLastUpdate(new Date())
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
      setAlerts(data)
    }

    const handleHistoryUpdate = async () => {
      const data = await fetchRiskHistory()
      setRiskHistory(data)
      setIsLoadingHistory(false)
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
    <div className="min-h-screen bg-slate-950 font-sans text-slate-200">
      <Navbar riskScore={status.risk_score} lastUpdate={lastUpdate} />

      {/* Main Container */}
      <main className="mx-auto w-full max-w-[1800px] p-4 sm:p-6 pb-20">
        
        {/* ROW 1: 12-column Grid (Video 8 / Stats 4) */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 lg:gap-6">
          
          {/* Main Monitor (Left 8 columns on large screens) */}
          <div className="col-span-1 lg:col-span-8">
            <VideoFeedCard fps={status.fps} />
          </div>

          {/* Stats Stack (Right 4 columns on large screens) */}
          <div className="col-span-1 flex flex-col gap-4 lg:col-span-4 lg:gap-6 h-full">
            <QuickStats status={status} />
            <SystemStatusCard status={status} isBackendConnected={isBackendConnected} />
            <AlertLog alerts={alerts} />
          </div>

        </div>

        {/* ROW 2: Full width graph timeline */}
        <div className="mt-4 lg:mt-6">
          <RiskTimelineChart data={riskHistory} isLoading={isLoadingHistory} />
        </div>

      </main>
    </div>
  )
}