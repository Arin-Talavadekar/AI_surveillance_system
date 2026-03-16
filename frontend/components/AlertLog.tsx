import { motion, AnimatePresence } from "framer-motion";

export interface Alert {
  id: string;
  type: string;
  timestamp: string;
  score: number;
}

interface AlertLogProps {
  alerts: Alert[];
}

const getRiskClass = (score: number) => {
  if (score > 0.8) return "risk-critical";
  if (score > 0.5) return "risk-elevated";
  return "risk-safe";
};

const AlertLog = ({ alerts }: AlertLogProps) => {
  return (
    <div className="flex-1 glass-panel rounded-lg glass-ring overflow-hidden flex flex-col min-h-[300px]">
      <div className="p-4 border-b border-foreground/5 bg-foreground/[0.02]">
        <h2 className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground font-bold">Recent Alert Log</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {alerts.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center space-y-2 opacity-50">
            <p className="text-[10px] font-semibold tracking-widest text-slate-500 uppercase">
              No Active Alerts
            </p>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {alerts.map((alert, idx) => (
              <motion.div
                key={alert.id || idx}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
                className={`p-3 rounded bg-foreground/[0.03] glass-ring flex justify-between items-center transition-colors hover:bg-foreground/[0.06] ${
                  idx === 0 && alert.score > 0.5 ? "shadow-[0_0_0_1px_hsl(var(--risk-critical)/0.3)] bg-[hsl(var(--risk-critical))]/5" : ""
                }`}
              >
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-tight text-foreground">{alert.type}</div>
                  <div className="text-[9px] text-muted-foreground">{alert.timestamp}</div>
                </div>
                <div className={`text-xs font-bold ${getRiskClass(alert.score)}`}>
                  {alert.score.toFixed(2)}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
};

export default AlertLog;
