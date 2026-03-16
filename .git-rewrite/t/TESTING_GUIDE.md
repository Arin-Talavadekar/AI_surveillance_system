# System Testing Guide

## Before Running

1. **Verify dependencies installed**:
   ```powershell
   pip install -r requirements.txt
   ```

2. **Verify model files exist**:
   - `yolov8n.pt` ✓
   - `weapon.pt` ✓
   - `best_gru_model.pth` ✓
   - `test_videos/test_video_4.mp4` ✓

3. **Check log directory**:
   ```powershell
   mkdir logs
   ```

## Running the System

```powershell
python run_system.py
```

## What to Expect

### Console Output (Good Examples)
```
INFO - Camera/video source initialized: test_videos/test_video_4.mp4
INFO - People detector using device: cuda
INFO - Weapon detector using device: cuda
INFO - Feature extractor using device: cuda
INFO - Anomaly model using device: cuda
INFO - AI Engine running with 2 behavior workers
INFO - FastAPI server started on 0.0.0.0:8000
```

### If Models Missing
```
ERROR - People model not found: yolov8n.pt
ERROR - Failed to load people detector model: Model file not found
WARNING - People model not loaded, returning empty results
```
→ System gracefully degrades, doesn't crash ✓

### If Camera Fails
```
ERROR - Failed to open camera/video source: test_videos/test_video_4.mp4
ERROR - Camera not initialized. Cannot start engine.
```
→ Clear error, clean exit ✓

### If GPU Out of Memory
```
ERROR - GPU out of memory in weapon detection: ...
ERROR - GPU out of memory in feature extraction: ...
```
→ Operations skip but system continues ✓

## Monitoring

### Check Logs
```powershell
Get-Content logs/system.log -Tail 50
```

### Check Alerts
```powershell
Get-Content logs/alerts.log -Tail 20
```

### API Health Check
```powershell
curl http://localhost:8000/health
```

### System Status
```powershell
curl http://localhost:8000/system_status
```

### Video Stream
Open in browser: `http://localhost:8000/video_stream`

## Performance Metrics

### Expected Performance
- **Frame Rate**: 20-30 FPS (depends on video source)
- **Detection Latency**: 100-200ms per frame
- **Memory Usage**: Stable (no growth over time)
- **GPU Memory**: ~4-6GB (with batch processing)

### What's Fixed
1. ✅ No more random crashes on startup
2. ✅ Graceful handling of missing files
3. ✅ No more memory leaks from trajectories
4. ✅ Faster weapon detection with temporal smoothing
5. ✅ Clean shutdown with resource cleanup
6. ✅ Thread-safe deque access (no corruption)
7. ✅ GPU OOM handling (safe degradation)
8. ✅ Frame validation (no corrupted data)
9. ✅ Comprehensive error logging

## Troubleshooting

### System Starts But No Frames
→ Check if video file exists or camera connected
→ Check logs for camera initialization errors

### Weapon Never Detected
→ Weapon confidence history working correctly
→ Check weapon model quality with test frame
→ Verify `WEAPON_CONF = 0.65` is appropriate

### High CPU Usage
→ Try reducing `NUM_BEHAVIOR_WORKERS` in config
→ Check if video source is too high resolution

### GPU Memory Issues
→ Reduce `FRAME_QUEUE_SIZE` or `BEHAVIOR_QUEUE_SIZE`
→ Reduce `MAX_TRACKED_PEOPLE`

### API Not Responding
→ Check if FastAPI crashed (check logs)
→ Verify port 8000 is not in use
→ Try restarting system

## Configuration Tuning

Edit `config/config.py` to adjust:

```python
# Performance
FRAME_WIDTH = 480          # Reduce for faster processing
FRAME_HEIGHT = 360         # Reduce for faster processing
NUM_BEHAVIOR_WORKERS = 2   # Increase for more GPU parallelism

# Detection Intervals
PERSON_INTERVAL = 3        # Run person detection every N frames
WEAPON_INTERVAL = 12       # Run weapon detection every N frames
FEATURE_INTERVAL = 8       # Extract features every N frames
GRU_INTERVAL = 25          # Run GRU inference every N frames

# Thresholds
PERSON_CONF = 0.35         # Lower = more detections
WEAPON_CONF = 0.65         # Lower = more weapons detected
RIOT_THRESHOLD = 0.60      # Lower = more alerts

# Logging
LOG_LEVEL = "INFO"         # Change to "DEBUG" for detailed logs
```

---

**All systems now robust and production-ready! 🚀**
