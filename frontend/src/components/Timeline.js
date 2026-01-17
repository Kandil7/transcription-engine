import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Slider,
  IconButton,
  Tooltip,
  Zoom
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  SkipNext as SkipNextIcon,
  SkipPrevious as SkipPreviousIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon
} from '@mui/icons-material';

function Timeline({
  segments,
  duration,
  currentTime = 0,
  onTimeChange,
  speakers = [],
  emotions = [],
  height = 120
}) {
  const [zoom, setZoom] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const timelineRef = useRef(null);
  const animationRef = useRef(null);

  // Auto-scroll to current time
  useEffect(() => {
    if (timelineRef.current && currentTime > 0) {
      const container = timelineRef.current;
      const scrollPosition = (currentTime / duration) * container.scrollWidth - container.clientWidth / 2;
      container.scrollLeft = Math.max(0, scrollPosition);
    }
  }, [currentTime, duration]);

  const handleTimelineClick = (event) => {
    if (!timelineRef.current) return;

    const rect = timelineRef.current.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const timelineWidth = rect.width;
    const time = (clickX / timelineWidth) * duration;

    if (onTimeChange) {
      onTimeChange(Math.max(0, Math.min(duration, time)));
    }
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev * 1.5, 5));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev / 1.5, 0.5));
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getEmotionColor = (emotion) => {
    const colors = {
      happy: '#4caf50',
      sad: '#2196f3',
      angry: '#f44336',
      neutral: '#9e9e9e',
      excited: '#ff9800',
      calm: '#00bcd4',
      confident: '#8bc34a',
      nervous: '#ff5722'
    };
    return colors[emotion] || colors.neutral;
  };

  const getSpeakerColor = (speaker, index) => {
    const colors = [
      '#e3f2fd', '#f3e5f5', '#e8f5e8', '#fff3e0', '#fce4ec',
      '#f1f8e9', '#e0f2f1', '#f9fbe7', '#efebe9', '#fafafa'
    ];
    return colors[index % colors.length];
  };

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Timeline</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Zoom Out">
            <IconButton onClick={handleZoomOut} size="small">
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>
          <Typography variant="caption" sx={{ minWidth: 60, textAlign: 'center' }}>
            {Math.round(zoom * 100)}%
          </Typography>
          <Tooltip title="Zoom In">
            <IconButton onClick={handleZoomIn} size="small">
              <ZoomInIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Timeline container */}
      <Box
        ref={timelineRef}
        sx={{
          position: 'relative',
          height: height,
          overflowX: 'auto',
          overflowY: 'hidden',
          border: '1px solid #e0e0e0',
          borderRadius: 1,
          cursor: 'pointer'
        }}
        onClick={handleTimelineClick}
      >
        {/* Time markers */}
        <Box sx={{ position: 'relative', height: '100%' }}>
          {Array.from({ length: Math.ceil(duration / 60) + 1 }, (_, i) => {
            const time = i * 60;
            const left = (time / duration) * 100 * zoom;
            return (
              <Box
                key={i}
                sx={{
                  position: 'absolute',
                  left: `${left}%`,
                  top: 0,
                  bottom: 0,
                  width: '1px',
                  backgroundColor: '#e0e0e0',
                  zIndex: 1
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    position: 'absolute',
                    top: -20,
                    left: -15,
                    fontSize: '0.7rem',
                    color: '#666'
                  }}
                >
                  {formatTime(time)}
                </Typography>
              </Box>
            );
          })}

          {/* Speaker segments */}
          {segments && segments.map((segment, index) => {
            const startPercent = (segment.start / duration) * 100 * zoom;
            const widthPercent = ((segment.end - segment.start) / duration) * 100 * zoom;
            const speakerIndex = speakers.indexOf(segment.speaker);

            return (
              <Tooltip
                key={index}
                title={
                  <Box>
                    <Typography variant="body2">
                      {segment.speaker} ({formatTime(segment.start)} - {formatTime(segment.end)})
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 0.5 }}>
                      {segment.text?.substring(0, 100)}...
                    </Typography>
                    {segment.emotion && (
                      <Chip
                        label={segment.emotion}
                        size="small"
                        sx={{
                          mt: 0.5,
                          backgroundColor: getEmotionColor(segment.emotion),
                          color: 'white'
                        }}
                      />
                    )}
                  </Box>
                }
                placement="top"
                arrow
              >
                <Box
                  sx={{
                    position: 'absolute',
                    left: `${startPercent}%`,
                    top: 20,
                    height: 40,
                    width: `${Math.max(widthPercent, 0.5)}%`,
                    backgroundColor: getSpeakerColor(segment.speaker, speakerIndex),
                    border: '1px solid #ccc',
                    borderRadius: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'hidden',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      transform: 'scaleY(1.1)',
                      zIndex: 10
                    }
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{
                      fontSize: '0.7rem',
                      fontWeight: 'bold',
                      color: '#333',
                      textAlign: 'center',
                      px: 0.5,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {segment.speaker}
                  </Typography>
                  {segment.emotion && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: -8,
                        right: -8,
                        width: 16,
                        height: 16,
                        borderRadius: '50%',
                        backgroundColor: getEmotionColor(segment.emotion),
                        border: '2px solid white'
                      }}
                    />
                  )}
                </Box>
              </Tooltip>
            );
          })}

          {/* Current time indicator */}
          {currentTime > 0 && (
            <Box
              sx={{
                position: 'absolute',
                left: `${(currentTime / duration) * 100 * zoom}%`,
                top: 0,
                bottom: 0,
                width: '2px',
                backgroundColor: '#f44336',
                zIndex: 20,
                boxShadow: '0 0 4px rgba(244, 67, 54, 0.5)'
              }}
            />
          )}
        </Box>
      </Box>

      {/* Controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 2, gap: 1 }}>
        <IconButton size="small">
          <SkipPreviousIcon />
        </IconButton>

        <IconButton
          onClick={() => setIsPlaying(!isPlaying)}
          color="primary"
        >
          {isPlaying ? <PauseIcon /> : <PlayIcon />}
        </IconButton>

        <IconButton size="small">
          <SkipNextIcon />
        </IconButton>

        <Box sx={{ ml: 3, minWidth: 200 }}>
          <Slider
            value={currentTime}
            onChange={(_, value) => onTimeChange && onTimeChange(value)}
            min={0}
            max={duration}
            step={0.1}
            valueLabelDisplay="auto"
            valueLabelFormat={formatTime}
          />
        </Box>

        <Typography variant="caption" sx={{ ml: 2, minWidth: 80 }}>
          {formatTime(currentTime)} / {formatTime(duration)}
        </Typography>
      </Box>

      {/* Legend */}
      <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="caption" sx={{ mr: 2, fontWeight: 'bold' }}>
          Speakers:
        </Typography>
        {speakers.map((speaker, index) => (
          <Chip
            key={speaker}
            label={speaker}
            size="small"
            sx={{
              backgroundColor: getSpeakerColor(speaker, index),
              color: '#333'
            }}
          />
        ))}

        <Typography variant="caption" sx={{ mr: 2, ml: 3, fontWeight: 'bold' }}>
          Emotions:
        </Typography>
        {emotions.map(emotion => (
          <Chip
            key={emotion}
            label={emotion}
            size="small"
            sx={{
              backgroundColor: getEmotionColor(emotion),
              color: 'white'
            }}
          />
        ))}
      </Box>
    </Paper>
  );
}

export default Timeline;