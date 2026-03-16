import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Activity, Upload, Video, X, Server } from "lucide-react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

interface VideoFeedProps {
  fps: number;
}

type FeedSource = "none" | "backend";

const VideoFeed = ({ fps }: VideoFeedProps) => {
  const [source, setSource] = useState<FeedSource>("none");
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const startLiveFeed = async () => {
    try {
      await fetch(`${BACKEND_URL}/switch_to_live`, { method: "POST" });
      // Add a timestamp to bypass image caching when changing streams
      setSource("backend");
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpload = async (file: File) => {
    if (!file.type.startsWith("video/")) return;
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await fetch(`${BACKEND_URL}/upload_video`, {
        method: "POST",
        body: formData,
      });
      setSource("backend");
    } catch (e) {
      console.error(e);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  }, []);

  const clearFeed = useCallback(async () => {
    setSource("none");
    if (fileInputRef.current) fileInputRef.current.value = "";
    try {
      await fetch(`${BACKEND_URL}/stop_system`, { method: "POST" });
    } catch (e) {
      console.error("Failed to stop system on backend:", e);
    }
  }, []);

  const isActive = source !== "none";

  return (
    <section className="col-span-12 lg:col-span-8 relative group">
      <div
        className={`relative aspect-video w-full bg-black rounded-lg overflow-hidden glass-ring transition-shadow duration-300 ${isDragging ? "shadow-[0_0_0_2px_hsl(var(--risk-critical)/0.5)]" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        {/* Corner crosshairs */}
        <div className="absolute inset-0 pointer-events-none z-10">
          <div className="absolute top-4 left-4 w-8 h-8 border-t border-l border-foreground/10" />
          <div className="absolute top-4 right-4 w-8 h-8 border-t border-r border-foreground/10" />
          <div className="absolute bottom-4 left-4 w-8 h-8 border-b border-l border-foreground/10" />
          <div className="absolute bottom-4 right-4 w-8 h-8 border-b border-r border-foreground/10" />
        </div>

        {/* LIVE indicator */}
        {isActive && (
          <div className="absolute top-6 left-6 flex items-center gap-3 bg-background/40 backdrop-blur-md px-3 py-1.5 rounded-full glass-ring z-20">
            <motion.div
              animate={{ opacity: [1, 0.4, 1] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
              className="w-2 h-2 rounded-full bg-[hsl(var(--risk-critical))]"
              style={{ boxShadow: "0 0 8px hsl(var(--risk-critical) / 0.8)" }}
            />
            <span className="text-[10px] uppercase tracking-[0.2em] font-bold text-foreground">
              {source === "backend" ? "Live" : "Playback"}
            </span>
          </div>
        )}

        {/* FPS */}
        {isActive && (
          <div className="absolute top-6 right-6 bg-background/40 backdrop-blur-md px-3 py-1.5 rounded glass-ring z-20">
            <span className="text-[11px] text-muted-foreground">{fps.toFixed(1)} FPS</span>
          </div>
        )}

        {/* Clear button */}
        {isActive && (
          <button
            onClick={clearFeed}
            className="absolute bottom-6 right-6 bg-background/60 backdrop-blur-md p-2 rounded glass-ring z-20 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
          >
            <X size={14} />
          </button>
        )}

        {source === "backend" && (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`${BACKEND_URL}/video_stream?t=${Date.now()}`}
              alt="Live Surveillance Feed"
              className="w-full h-full object-contain"
              unselectable="on"
            />
            {/* Scanline overlay for that premium hacker aesthetic */}
            <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(0,0,0,0)_50%,rgba(0,0,0,0.1)_50%)] bg-[length:100%_4px] opacity-10 z-10" />
          </>
        )}

        {/* Source selection */}
        {source === "none" && (
          <div className="w-full h-full bg-[radial-gradient(circle_at_center,hsl(var(--secondary)),hsl(var(--background)))] flex flex-col items-center justify-center gap-6">
            {isDragging || isUploading ? (
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="flex flex-col items-center gap-3"
              >
                <Video className="w-10 h-10 text-[hsl(var(--risk-critical))]/40" />
                <span className="text-[11px] uppercase tracking-[0.2em] text-foreground/40 font-bold">{isUploading ? "Uploading..." : "Drop Video"}</span>
              </motion.div>
            ) : (
              <>
                <Activity className="w-8 h-8 text-foreground/5 animate-pulse" />
                <span className="text-[9px] uppercase tracking-[0.25em] text-muted-foreground/50 font-bold">Select Input Source</span>

                <div className="flex flex-col md:flex-row items-center gap-4">
                  {/* Backend Server option */}
                  <button
                    onClick={startLiveFeed}
                    className="flex flex-col items-center justify-center w-36 h-28 gap-2.5 bg-foreground/[0.03] hover:bg-foreground/[0.07] transition-all rounded-lg glass-ring group/btn cursor-pointer"
                  >
                    <Server size={18} className="text-[hsl(var(--risk-critical))] group-hover/btn:text-[hsl(var(--risk-critical))] transition-colors drop-shadow-[0_0_8px_hsl(var(--risk-critical)/0.5)]" />
                    <span className="text-[10px] uppercase tracking-[0.1em] text-muted-foreground group-hover/btn:text-foreground font-bold transition-colors">
                      Live Feed
                    </span>
                    <span className="text-[8px] text-muted-foreground/50 tracking-wide text-center px-2">Local CCTV feed</span>
                  </button>
                  
                  {/* Divider */}
                  <div className="hidden md:block h-16 w-px bg-foreground/10" />

                  {/* File option */}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="flex flex-col items-center justify-center w-36 h-28 gap-2.5 bg-foreground/[0.03] hover:bg-foreground/[0.07] transition-all rounded-lg glass-ring group/btn cursor-pointer"
                  >
                    <Upload size={18} className="text-muted-foreground group-hover/btn:text-foreground transition-colors" />
                    <span className="text-[10px] uppercase tracking-[0.1em] text-muted-foreground group-hover/btn:text-foreground font-bold transition-colors">
                      Video File
                    </span>
                    <span className="text-[8px] text-muted-foreground/50 tracking-wide text-center px-2">Upload or drop</span>
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleUpload(file);
          }}
        />
      </div>
    </section>
  );
};

export default VideoFeed;
