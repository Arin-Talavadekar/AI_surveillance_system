import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";

interface RiskTimelineProps {
  history: Array<{ frame: number; risk: number }>;
}

const RiskTimeline = ({ history }: RiskTimelineProps) => {
  const latestRisk = history.length > 0 ? history[history.length - 1].risk : 0;
  
  const getColor = (score: number) => {
    if (score > 0.8) return "hsl(347, 77%, 50%)"; // Critical
    if (score > 0.5) return "hsl(45, 93%, 47%)";  // Elevated
    return "hsl(142, 70%, 45%)";                 // Safe
  };

  const currentColor = getColor(latestRisk);

  return (
    <section className="col-span-12 glass-panel p-4 md:p-6 rounded-lg glass-ring h-[300px]">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground font-bold">
          Historical Risk Timeline (Last 100 Frames)
        </h2>
        <div className="flex gap-4 text-[10px] text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: currentColor }} /> 
            <span className="uppercase tracking-widest font-bold" style={{ color: currentColor }}>
              {latestRisk > 0.8 ? "Critical Risk" : latestRisk > 0.5 ? "Elevated Risk" : "Normal Operations"}
            </span>
          </div>
        </div>
      </div>
      <div className="w-full h-48">
        <ResponsiveContainer width="100%" height="100%" minWidth={0}>
          <AreaChart data={history}>
            <defs>
              <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={currentColor} stopOpacity={0.3} />
                <stop offset="95%" stopColor={currentColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="frame" hide />
            <YAxis domain={[0, 1]} hide />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(222, 50%, 6%)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "4px",
                fontSize: "10px",
                fontFamily: "monospace",
              }}
              itemStyle={{ color: "hsl(347, 77%, 50%)" }}
              labelStyle={{ display: 'none' }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(value: any) => [Number(value).toFixed(2), "Risk Score"]}
            />
            <Area
              type="monotone"
              dataKey="risk"
              stroke={currentColor}
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorRisk)"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};

export default RiskTimeline;
