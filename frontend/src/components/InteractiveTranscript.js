import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Button,
  TextField,
  InputAdornment,
  IconButton,
  Divider,
  Tooltip,
  Fade
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Bookmark as BookmarkIcon,
  BookmarkBorder as BookmarkBorderIcon
} from '@mui/icons-material';
import { getEmotionColor, getSpeakerColor } from '../utils/helpers';

function InteractiveTranscript({
  segments = [],
  currentTime = 0,
  onTimeChange,
  searchQuery = '',
  searchResults = [],
  speakers = [],
  emotions = []
}) {
  const [expandedSegments, setExpandedSegments] = useState(new Set());
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery);
  const [bookmarkedSegments, setBookmarkedSegments] = useState(new Set());
  const transcriptRef = useRef(null);

  useEffect(() => {
    setLocalSearchQuery(searchQuery);
  }, [searchQuery]);

  // Auto-scroll to current segment
  useEffect(() => {
    if (transcriptRef.current && segments.length > 0) {
      const currentSegmentIndex = segments.findIndex(
        segment => currentTime >= segment.start && currentTime <= segment.end
      );

      if (currentSegmentIndex !== -1) {
        const segmentElement = transcriptRef.current.children[currentSegmentIndex];
        if (segmentElement) {
          segmentElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
          });
        }
      }
    }
  }, [currentTime, segments]);

  const handleSegmentClick = (segment) => {
    if (onTimeChange) {
      onTimeChange(segment.start);
    }
  };

  const toggleSegmentExpansion = (segmentId) => {
    const newExpanded = new Set(expandedSegments);
    if (newExpanded.has(segmentId)) {
      newExpanded.delete(segmentId);
    } else {
      newExpanded.add(segmentId);
    }
    setExpandedSegments(newExpanded);
  };

  const toggleBookmark = (segmentId) => {
    const newBookmarks = new Set(bookmarkedSegments);
    if (newBookmarks.has(segmentId)) {
      newBookmarks.delete(segmentId);
    } else {
      newBookmarks.add(segmentId);
    }
    setBookmarkedSegments(newBookmarks);
  };

  const highlightSearchText = (text, query) => {
    if (!query || !text) return text;

    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} style={{
          backgroundColor: '#fff3cd',
          padding: '2px 4px',
          borderRadius: '3px',
          fontWeight: 'bold'
        }}>
          {part}
        </mark>
      ) : part
    );
  };

  // The getEmotionColor and getSpeakerColor functions are now available from the helpers utility

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const filteredSegments = segments.filter(segment => {
    // Apply search filter
    if (localSearchQuery.trim()) {
      return segment.text?.toLowerCase().includes(localSearchQuery.toLowerCase());
    }
    return true;
  });

  return (
    <Paper sx={{ p: 3, maxHeight: '70vh', overflow: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        Interactive Transcript
      </Typography>

      {/* Search within transcript */}
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Search within transcript..."
          value={localSearchQuery}
          onChange={(e) => setLocalSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
            endAdornment: localSearchQuery && (
              <InputAdornment position="end">
                <IconButton size="small" onClick={() => setLocalSearchQuery('')}>
                  <ClearIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {/* Transcript segments */}
      <Box ref={transcriptRef}>
        {filteredSegments.map((segment, index) => {
          const isCurrentSegment = currentTime >= segment.start && currentTime <= segment.end;
          const isBookmarked = bookmarkedSegments.has(segment.start);
          const speakerIndex = speakers.indexOf(segment.speaker);

          return (
            <Fade in={true} key={segment.start || index}>
              <Box
                sx={{
                  mb: 2,
                  p: 2,
                  borderRadius: 1,
                  border: isCurrentSegment ? '2px solid #1976d2' : '1px solid #e0e0e0',
                  backgroundColor: isCurrentSegment
                    ? '#e3f2fd'
                    : getSpeakerColor(segment.speaker, speakerIndex),
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  position: 'relative',
                  '&:hover': {
                    boxShadow: 2,
                    transform: 'translateY(-1px)'
                  }
                }}
                onClick={() => handleSegmentClick(segment)}
              >
                {/* Header with speaker and time */}
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={segment.speaker || 'Unknown'}
                      size="small"
                      sx={{
                        backgroundColor: getSpeakerColor(segment.speaker, speakerIndex),
                        color: '#333',
                        fontWeight: 'bold'
                      }}
                    />
                    {segment.emotion && (
                      <Chip
                        label={segment.emotion}
                        size="small"
                        sx={{
                          backgroundColor: getEmotionColor(segment.emotion),
                          color: 'white'
                        }}
                      />
                    )}
                    {isBookmarked && (
                      <BookmarkIcon sx={{ color: '#ff9800', fontSize: 18 }} />
                    )}
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      {formatTime(segment.start)} - {formatTime(segment.end)}
                    </Typography>

                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleBookmark(segment.start);
                      }}
                    >
                      {isBookmarked ? <BookmarkIcon /> : <BookmarkBorderIcon />}
                    </IconButton>

                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSegmentClick(segment);
                      }}
                    >
                      <PlayIcon />
                    </IconButton>
                  </Box>
                </Box>

                {/* Transcript text */}
                <Typography
                  variant="body1"
                  sx={{
                    lineHeight: 1.6,
                    textAlign: 'justify'
                  }}
                >
                  {highlightSearchText(segment.text, localSearchQuery)}
                </Typography>

                {/* Confidence and metadata */}
                {segment.confidence && (
                  <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Confidence: {Math.round(segment.confidence * 100)}%
                    </Typography>
                    {segment.duration && (
                      <Typography variant="caption" color="text.secondary">
                        Duration: {segment.duration.toFixed(1)}s
                      </Typography>
                    )}
                  </Box>
                )}

                {/* Expand/collapse for long segments */}
                {segment.text && segment.text.length > 200 && (
                  <Box sx={{ mt: 1 }}>
                    <Button
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSegmentExpansion(segment.start);
                      }}
                      endIcon={expandedSegments.has(segment.start) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    >
                      {expandedSegments.has(segment.start) ? 'Show Less' : 'Show More'}
                    </Button>
                  </Box>
                )}
              </Box>
            </Fade>
          );
        })}
      </Box>

      {filteredSegments.length === 0 && segments.length > 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" color="text.secondary">
            No segments match your search criteria.
          </Typography>
          <Button
            variant="text"
            onClick={() => setLocalSearchQuery('')}
            sx={{ mt: 1 }}
          >
            Clear Search
          </Button>
        </Box>
      )}

      {segments.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" color="text.secondary">
            No transcript segments available.
          </Typography>
        </Box>
      )}

      {/* Summary */}
      <Divider sx={{ my: 3 }} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          {filteredSegments.length} of {segments.length} segments
          {bookmarkedSegments.size > 0 && ` • ${bookmarkedSegments.size} bookmarked`}
        </Typography>

        {bookmarkedSegments.size > 0 && (
          <Button
            size="small"
            variant="outlined"
            onClick={() => setBookmarkedSegments(new Set())}
          >
            Clear Bookmarks
          </Button>
        )}
      </Box>
    </Paper>
  );
}

export default InteractiveTranscript;