import { motion } from "framer-motion";
import { AlertTriangle, Activity, Users, ShieldCheck, ChevronUp, ChevronDown, Radio } from "lucide-react";

interface ThreatMetricsProps {
  systemStatus: "Online" | "Offline";
  riskScore: number;
  escalationTrend: number;
  peopleCount: number;
  gruScore: number;
  weaponDetected: boolean;
}

const MetricCard = ({ title, value, unit, icon: Icon, trend }: any) => (
  <div className="bg-card/20 border border-foreground/5 p-4 rounded-xl backdrop-blur-sm group hover:border-primary/20 transition-colors">
    <div className="flex items-center justify-between mb-2">
      <span className="text-[10px] font-black tracking-widest text-muted-foreground uppercase flex items-center gap-2">
        <Icon size={12} className="text-primary/50" />
        {title}
      </span>
      {trend !== undefined && (
        <span className={`text-[10px] flex items-center font-bold ${trend > 0 ? 'text-destructive' : 'text-primary'}`}>
          {trend > 0 ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {Math.abs(trend).toFixed(2)}
        </span>
      )}
    </div>
    <div className="flex items-baseline gap-2">
      <span className="text-2xl font-black font-mono tracking-tighter">{value}</span>
      {unit && <span className="text-[10px] text-muted-foreground font-bold uppercase">{unit}</span>}
    </div>
  </div>
);

const ThreatMetrics = ({ systemStatus, riskScore, escalationTrend, peopleCount, gruScore, weaponDetected }: ThreatMetricsProps) => {
  const isCritical = riskScore > 0.8 || weaponDetected;
  
  return (
    <div className="flex flex-col gap-4">
      {/* Primary HUD Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Risk Score Console */}
        <div className="col-span-1 bg-card/40 border border-foreground/10 p-5 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-3 opacity-20">
             <Radio className={isCritical ? "text-destructive animate-pulse" : "text-primary"} size={40} />
          </div>
          
          <p className="text-[10px] font-black tracking-[0.2em] text-muted-foreground uppercase mb-4 flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${isCritical ? 'bg-destructive animate-ping' : 'bg-primary'}`} />
            Risk Factor
          </p>
          
          <div className="flex items-baseline gap-4">
            <span className={`text-7xl font-black tracking-tighter font-mono ${isCritical ? 'text-destructive' : 'text-primary'} drop-shadow-2xl`}>
              {(riskScore * 100).toFixed(0)}
              <span className="text-3xl opacity-50">%</span>
            </span>
          </div>

          <div className="mt-4 pt-4 border-t border-foreground/5 flex items-center justify-between">
            <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wide">Threat Level</span>
            <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded border ${isCritical ? 'bg-destructive/10 border-destructive text-destructive' : 'bg-primary/10 border-primary text-primary'}`}>
              {isCritical ? 'CRITICAL_THREAT' : 'STABLE_ENVIRONMENT'}
            </span>
          </div>
        </div>

        {/* Secondary Modules */}
        <div className="flex flex-col gap-4">
          <MetricCard 
            title="Crowd Density" 
            value={peopleCount} 
            unit="INDV" 
            icon={Users} 
          />
          <MetricCard 
            title="GRU Anomaly" 
            value={gruScore.toFixed(2)} 
            icon={Activity}
            trend={escalationTrend}
          />
        </div>
      </div>

      {/* Weapon Status Banner */}
      <motion.div
        animate={weaponDetected ? { 
            borderColor: ["rgba(239, 68, 68, 0.2)", "rgba(239, 68, 68, 0.8)", "rgba(239, 68, 68, 0.2)"],
            backgroundColor: ["rgba(239, 68, 68, 0.05)", "rgba(239, 68, 68, 0.15)", "rgba(239, 68, 68, 0.05)"]
        } : {}}
        transition={{ duration: 1.5, repeat: Infinity }}
        className={`p-4 rounded-xl border flex items-center justify-between ${weaponDetected ? "border-destructive text-destructive" : "border-foreground/5 bg-foreground/5 text-muted-foreground"}`}
      >
        <div className="flex items-center gap-3">
          {weaponDetected ? <AlertTriangle size={20} className="animate-bounce" /> : <ShieldCheck size={20} className="opacity-50" />}
          <span className="text-[11px] font-black tracking-[0.25em] uppercase">
            {weaponDetected ? "TACTICAL ALERT: WEAPON_DETECTED" : "DEFENSE_PROTOCOL: SECURE"}
          </span>
        </div>
        <div className="flex items-center gap-2">
            <span className="text-[9px] opacity-40 font-mono tracking-tighter uppercase whitespace-nowrap">ID: {systemStatus}</span>
        </div>
      </motion.div>
    </div>
  );
};

export default ThreatMetrics;
