import { motion } from "framer-motion";
import { AlertTriangle, Activity, Users, ShieldCheck, ChevronUp, ChevronDown } from "lucide-react";

interface ThreatMetricsProps {
  systemStatus: "Online" | "Offline";
  riskScore: number;
  escalationTrend: number;
  peopleCount: number;
  gruScore: number;
  weaponDetected: boolean;
}

const getRiskClass = (score: number) => {
  if (score > 0.8) return "risk-critical";
  if (score > 0.5) return "risk-elevated";
  return "risk-safe";
};

const ThreatMetrics = ({ systemStatus, riskScore, escalationTrend, peopleCount, gruScore, weaponDetected }: ThreatMetricsProps) => {
  return (
    <div className="glass-panel p-6 rounded-lg glass-ring flex flex-col gap-6">
      {/* System Status */}
      <header className="flex justify-between items-center border-b border-foreground/5 pb-4">
        <h2 className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground font-bold">System Status</h2>
        <div className="flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full ${systemStatus === "Online" ? "bg-[hsl(var(--risk-safe))] animate-pulse" : "bg-muted-foreground"}`} />
          <span className="text-xs uppercase text-foreground font-bold">{systemStatus}</span>
        </div>
      </header>

      {/* Overall Risk Score */}
      <div className="space-y-1">
        <span className="text-[10px] uppercase tracking-widest text-muted-foreground">Overall Risk Score</span>
        <div className="flex items-baseline gap-3">
          <span className={`text-6xl font-black tabular-nums tracking-tighter ${getRiskClass(riskScore)}`}>
            {(riskScore * 100).toFixed(0)}%
          </span>
          <div className={`flex items-center text-sm ${escalationTrend > 0 ? "risk-critical" : "risk-safe"}`}>
            {escalationTrend > 0 ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            {escalationTrend > 0 ? "+" : ""}{escalationTrend.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Sub-metrics */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 bg-foreground/[0.03] rounded glass-ring transition-colors hover:bg-foreground/[0.06]">
          <div className="text-[9px] uppercase text-muted-foreground mb-1 flex items-center gap-2">
            <Users size={10} /> Crowd Density
          </div>
          <div className="text-xl font-bold text-foreground">{peopleCount} <span className="text-[10px] text-muted-foreground font-normal">INDV</span></div>
        </div>
        <div className="p-3 bg-foreground/[0.03] rounded glass-ring transition-colors hover:bg-foreground/[0.06]">
          <div className="text-[9px] uppercase text-muted-foreground mb-1 flex items-center gap-2">
            <Activity size={10} /> GRU Score
          </div>
          <div className="text-xl font-bold text-foreground">{gruScore.toFixed(2)}</div>
        </div>
      </div>

      {/* Weapon Detection */}
      <motion.div
        animate={weaponDetected ? { backgroundColor: ["hsla(347,77%,50%,0.05)", "hsla(347,77%,50%,0.15)", "hsla(347,77%,50%,0.05)"] } : {}}
        transition={{ duration: 2, repeat: Infinity }}
        className={`p-4 rounded ${weaponDetected ? "border border-[hsl(var(--risk-critical))]/50 bg-[hsl(var(--risk-critical))]/10" : "border border-foreground/5 bg-foreground/[0.02]"} flex items-center gap-3`}
      >
        {weaponDetected ? <AlertTriangle className="risk-critical" size={18} /> : <ShieldCheck className="risk-safe" size={18} />}
        <span className={`text-[11px] font-bold tracking-widest uppercase ${weaponDetected ? "risk-critical" : "risk-safe"}`}>
          {weaponDetected ? "Weapon Detected" : "Status: Active"}
        </span>
      </motion.div>
    </div>
  );
};

export default ThreatMetrics;
