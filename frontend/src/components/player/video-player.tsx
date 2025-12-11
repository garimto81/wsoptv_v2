'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import ReactPlayer from 'react-player';
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Volume1,
  Maximize,
  Minimize,
  RotateCcw,
  RotateCw,
  Settings,
  ChevronLeft,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { cn } from '@/lib/utils';

interface VideoPlayerProps {
  url: string;
  title?: string;
  subtitle?: string;
  contentId?: string;
  initialProgress?: number;
  onProgress?: (progress: { played: number; playedSeconds: number; duration: number }) => void;
  onEnded?: () => void;
  onBack?: () => void;
  className?: string;
  autoSaveProgress?: boolean;
}

const PLAYBACK_RATES = [0.5, 0.75, 1, 1.25, 1.5, 2];

export function VideoPlayer({
  url,
  title,
  subtitle,
  contentId,
  initialProgress = 0,
  onProgress,
  onEnded,
  onBack,
  className,
  autoSaveProgress = true,
}: VideoPlayerProps) {
  const playerRef = useRef<ReactPlayer>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const progressSaveTimeout = useRef<NodeJS.Timeout>();

  const [playing, setPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [played, setPlayed] = useState(initialProgress);
  const [loaded, setLoaded] = useState(0);
  const [duration, setDuration] = useState(0);
  const [seeking, setSeeking] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [showSkipIndicator, setShowSkipIndicator] = useState<'forward' | 'backward' | null>(null);
  const [isBuffering, setIsBuffering] = useState(false);
  const hideControlsTimeout = useRef<NodeJS.Timeout>();

  // Format time (seconds -> HH:MM:SS)
  const formatTime = (seconds: number): string => {
    if (isNaN(seconds) || seconds === 0) return '0:00';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);

    if (h > 0) {
      return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  // Handle progress
  const handleProgress = useCallback(
    (state: { played: number; playedSeconds: number; loaded: number }) => {
      if (!seeking) {
        setPlayed(state.played);
        setLoaded(state.loaded);
        onProgress?.({ played: state.played, playedSeconds: state.playedSeconds, duration });
      }
    },
    [seeking, onProgress, duration]
  );

  // Seek to position
  const handleSeekChange = (value: number[]) => {
    setPlayed(value[0]);
  };

  const handleSeekMouseDown = () => {
    setSeeking(true);
  };

  const handleSeekMouseUp = (value: number[]) => {
    setSeeking(false);
    playerRef.current?.seekTo(value[0]);
  };

  // Skip forward/backward with visual indicator
  const skip = (seconds: number) => {
    const currentTime = playerRef.current?.getCurrentTime() || 0;
    const newTime = Math.max(0, Math.min(duration, currentTime + seconds));
    playerRef.current?.seekTo(newTime);
    setShowSkipIndicator(seconds > 0 ? 'forward' : 'backward');
    setTimeout(() => setShowSkipIndicator(null), 600);
  };

  // Toggle fullscreen
  const toggleFullscreen = async () => {
    if (!containerRef.current) return;

    try {
      if (!document.fullscreenElement) {
        await containerRef.current.requestFullscreen();
        setFullscreen(true);
      } else {
        await document.exitFullscreen();
        setFullscreen(false);
      }
    } catch (error) {
      console.error('Fullscreen error:', error);
    }
  };

  // Show/hide controls
  const handleMouseMove = () => {
    setShowControls(true);
    setShowSettings(false);
    if (hideControlsTimeout.current) {
      clearTimeout(hideControlsTimeout.current);
    }
    hideControlsTimeout.current = setTimeout(() => {
      if (playing) setShowControls(false);
    }, 3000);
  };

  // Handle click to play/pause
  const handleVideoClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.controls-area')) return;
    setPlaying((p) => !p);
  };

  // Handle double click to fullscreen
  const handleDoubleClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.controls-area')) return;
    toggleFullscreen();
  };

  // Get volume icon
  const VolumeIcon = muted || volume === 0 ? VolumeX : volume < 0.5 ? Volume1 : Volume2;

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;

      switch (e.key) {
        case ' ':
        case 'k':
          e.preventDefault();
          setPlaying((p) => !p);
          break;
        case 'ArrowLeft':
        case 'j':
          e.preventDefault();
          skip(-10);
          break;
        case 'ArrowRight':
        case 'l':
          e.preventDefault();
          skip(10);
          break;
        case 'ArrowUp':
          e.preventDefault();
          setVolume((v) => Math.min(1, v + 0.1));
          setMuted(false);
          break;
        case 'ArrowDown':
          e.preventDefault();
          setVolume((v) => Math.max(0, v - 0.1));
          break;
        case 'f':
          e.preventDefault();
          toggleFullscreen();
          break;
        case 'm':
          e.preventDefault();
          setMuted((m) => !m);
          break;
        case 'Escape':
          if (showSettings) setShowSettings(false);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showSettings]);

  // Seek to initial progress on load
  useEffect(() => {
    if (initialProgress > 0 && playerRef.current && duration > 0) {
      playerRef.current.seekTo(initialProgress);
    }
  }, [initialProgress, duration]);

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  return (
    <div
      ref={containerRef}
      className={cn('relative bg-black aspect-video', className)}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => playing && setShowControls(false)}
      onClick={handleVideoClick}
      onDoubleClick={handleDoubleClick}
    >
      {/* Player */}
      <ReactPlayer
        ref={playerRef}
        url={url}
        playing={playing}
        volume={volume}
        muted={muted}
        playbackRate={playbackRate}
        width="100%"
        height="100%"
        onProgress={handleProgress}
        onDuration={setDuration}
        onEnded={onEnded}
        onBuffer={() => setIsBuffering(true)}
        onBufferEnd={() => setIsBuffering(false)}
        progressInterval={1000}
        config={{
          file: {
            attributes: {
              crossOrigin: 'anonymous',
            },
          },
        }}
      />

      {/* Skip Indicator */}
      {showSkipIndicator && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className={cn(
            "flex items-center gap-2 px-6 py-3 rounded-full bg-black/60 text-white animate-pulse",
            showSkipIndicator === 'forward' ? 'translate-x-20' : '-translate-x-20'
          )}>
            {showSkipIndicator === 'backward' ? (
              <>
                <RotateCcw className="h-8 w-8" />
                <span className="text-lg font-medium">10</span>
              </>
            ) : (
              <>
                <span className="text-lg font-medium">10</span>
                <RotateCw className="h-8 w-8" />
              </>
            )}
          </div>
        </div>
      )}

      {/* Buffering Indicator */}
      {isBuffering && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="h-12 w-12 border-4 border-white/30 border-t-white rounded-full animate-spin" />
        </div>
      )}

      {/* Controls Overlay */}
      <div
        className={cn(
          'controls-area absolute inset-0 flex flex-col justify-between transition-opacity duration-300',
          showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
      >
        {/* Top Gradient & Header */}
        <div className="bg-gradient-to-b from-black/70 via-black/30 to-transparent p-4">
          <div className="flex items-center gap-4">
            {onBack && (
              <Button
                variant="ghost"
                size="icon"
                className="text-white hover:bg-white/20"
                onClick={(e) => { e.stopPropagation(); onBack(); }}
              >
                <ChevronLeft className="h-8 w-8" />
              </Button>
            )}
            <div>
              {title && <h2 className="text-xl font-semibold text-white">{title}</h2>}
              {subtitle && <p className="text-sm text-white/70">{subtitle}</p>}
            </div>
          </div>
        </div>

        {/* Center Play Button (when paused) */}
        {!playing && !isBuffering && (
          <div className="flex-1 flex items-center justify-center">
            <Button
              variant="ghost"
              size="icon"
              className="h-20 w-20 rounded-full bg-white/20 text-white hover:bg-white/30 backdrop-blur-sm"
              onClick={(e) => { e.stopPropagation(); setPlaying(true); }}
            >
              <Play className="h-10 w-10 ml-1" />
            </Button>
          </div>
        )}

        {/* Bottom Gradient & Controls */}
        <div className="bg-gradient-to-t from-black/80 via-black/40 to-transparent">
          {/* Progress Bar */}
          <div className="px-4 py-2">
            <div className="relative group">
              {/* Loaded buffer indicator */}
              <div
                className="absolute h-1 bg-white/30 rounded-full top-1/2 -translate-y-1/2"
                style={{ width: `${loaded * 100}%` }}
              />
              <Slider
                value={[played]}
                max={1}
                step={0.0001}
                onValueChange={handleSeekChange}
                onPointerDown={handleSeekMouseDown}
                onPointerUp={() => handleSeekMouseUp([played])}
                className="cursor-pointer [&_[data-orientation=horizontal]]:h-1 group-hover:[&_[data-orientation=horizontal]]:h-2 transition-all"
              />
            </div>
          </div>

          {/* Control Buttons */}
          <div className="flex items-center justify-between px-4 pb-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-1">
              {/* Play/Pause */}
              <Button
                variant="ghost"
                size="icon"
                className="text-white hover:bg-white/20"
                onClick={() => setPlaying(!playing)}
              >
                {playing ? <Pause className="h-7 w-7" /> : <Play className="h-7 w-7" />}
              </Button>

              {/* Skip Back 10s */}
              <Button
                variant="ghost"
                size="icon"
                className="text-white hover:bg-white/20"
                onClick={() => skip(-10)}
                title="10초 뒤로 (J)"
              >
                <RotateCcw className="h-6 w-6" />
              </Button>

              {/* Skip Forward 10s */}
              <Button
                variant="ghost"
                size="icon"
                className="text-white hover:bg-white/20"
                onClick={() => skip(10)}
                title="10초 앞으로 (L)"
              >
                <RotateCw className="h-6 w-6" />
              </Button>

              {/* Volume */}
              <div className="flex items-center group">
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-white hover:bg-white/20"
                  onClick={() => setMuted(!muted)}
                >
                  <VolumeIcon className="h-6 w-6" />
                </Button>
                <div className="w-0 overflow-hidden group-hover:w-20 transition-all duration-200">
                  <Slider
                    value={[muted ? 0 : volume]}
                    max={1}
                    step={0.05}
                    onValueChange={(v) => {
                      setVolume(v[0]);
                      setMuted(false);
                    }}
                    className="w-20"
                  />
                </div>
              </div>

              {/* Time */}
              <span className="text-sm text-white ml-2 tabular-nums">
                {formatTime(played * duration)} / {formatTime(duration)}
              </span>
            </div>

            <div className="flex items-center gap-1">
              {/* Playback Speed */}
              <div className="relative">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-white hover:bg-white/20 text-sm"
                  onClick={() => setShowSettings(!showSettings)}
                >
                  {playbackRate}x
                </Button>

                {/* Settings Menu */}
                {showSettings && (
                  <div className="absolute bottom-full right-0 mb-2 bg-black/90 rounded-lg py-2 min-w-[120px] backdrop-blur-sm">
                    <div className="px-3 py-1 text-xs text-white/50 uppercase tracking-wider">재생 속도</div>
                    {PLAYBACK_RATES.map((rate) => (
                      <button
                        key={rate}
                        className={cn(
                          "w-full px-3 py-2 text-left text-sm hover:bg-white/10 transition-colors",
                          playbackRate === rate ? "text-red-500" : "text-white"
                        )}
                        onClick={() => {
                          setPlaybackRate(rate);
                          setShowSettings(false);
                        }}
                      >
                        {rate}x {rate === 1 && '(기본)'}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Fullscreen */}
              <Button
                variant="ghost"
                size="icon"
                className="text-white hover:bg-white/20"
                onClick={toggleFullscreen}
                title="전체화면 (F)"
              >
                {fullscreen ? (
                  <Minimize className="h-6 w-6" />
                ) : (
                  <Maximize className="h-6 w-6" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default VideoPlayer;
