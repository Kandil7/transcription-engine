import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Chip,
  Button,
  Paper,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  InputAdornment,
  IconButton,
  Autocomplete
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';

function SearchAndFilter({
  onSearch,
  onFilter,
  speakers = [],
  emotions = [],
  duration = 0,
  totalSegments = 0
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSpeakers, setSelectedSpeakers] = useState([]);
  const [selectedEmotions, setSelectedEmotions] = useState([]);
  const [timeRange, setTimeRange] = useState([0, duration]);
  const [sortBy, setSortBy] = useState('time');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    // Update time range when duration changes
    setTimeRange([0, duration]);
  }, [duration]);

  const handleSearch = async () => {
    if (!searchQuery.trim() && selectedSpeakers.length === 0 && selectedEmotions.length === 0) {
      return;
    }

    setIsSearching(true);

    const searchParams = {
      query: searchQuery.trim(),
      speakers: selectedSpeakers,
      emotions: selectedEmotions,
      timeRange: timeRange,
      sortBy: sortBy
    };

    try {
      // Call the search function passed from parent
      const searchResults = await onSearch(searchParams);
      setResults(searchResults || []);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleFilter = () => {
    const filters = {
      speakers: selectedSpeakers,
      emotions: selectedEmotions,
      timeRange: timeRange
    };

    onFilter(filters);
  };

  const clearAllFilters = () => {
    setSearchQuery('');
    setSelectedSpeakers([]);
    setSelectedEmotions([]);
    setTimeRange([0, duration]);
    setSortBy('time');
    setResults([]);
    onFilter({});
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const hasActiveFilters = searchQuery.trim() ||
    selectedSpeakers.length > 0 ||
    selectedEmotions.length > 0 ||
    timeRange[0] > 0 ||
    timeRange[1] < duration;

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <SearchIcon sx={{ mr: 1 }} />
        Search & Filter
      </Typography>

      {/* Search Input */}
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="Search transcript"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search for keywords, phrases, or speakers..."
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={handleSearch} disabled={isSearching}>
                  <SearchIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {/* Filters Accordion */}
      <Accordion>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          sx={{
            '& .MuiAccordionSummary-content': {
              alignItems: 'center'
            }
          }}
        >
          <FilterIcon sx={{ mr: 1 }} />
          <Typography>Advanced Filters</Typography>
          {hasActiveFilters && (
            <Chip
              label={`${Object.values({ selectedSpeakers, selectedEmotions, timeRange }).flat().length} active`}
              size="small"
              color="primary"
              sx={{ ml: 2 }}
            />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Speaker Filter */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Filter by Speakers
              </Typography>
              <Autocomplete
                multiple
                options={speakers}
                value={selectedSpeakers}
                onChange={(_, newValue) => setSelectedSpeakers(newValue)}
                renderInput={(params) => (
                  <TextField {...params} label="Select speakers" size="small" />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      label={option}
                      {...getTagProps({ index })}
                      size="small"
                    />
                  ))
                }
              />
            </Box>

            {/* Emotion Filter */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Filter by Emotions
              </Typography>
              <Autocomplete
                multiple
                options={emotions}
                value={selectedEmotions}
                onChange={(_, newValue) => setSelectedEmotions(newValue)}
                renderInput={(params) => (
                  <TextField {...params} label="Select emotions" size="small" />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      label={option}
                      {...getTagProps({ index })}
                      size="small"
                    />
                  ))
                }
              />
            </Box>

            {/* Time Range Filter */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Time Range: {formatTime(timeRange[0])} - {formatTime(timeRange[1])}
              </Typography>
              <Slider
                value={timeRange}
                onChange={(_, newValue) => setTimeRange(newValue)}
                valueLabelDisplay="auto"
                valueLabelFormat={formatTime}
                min={0}
                max={duration}
                step={1}
                marks={[
                  { value: 0, label: 'Start' },
                  { value: duration, label: 'End' }
                ]}
              />
            </Box>

            {/* Sort Options */}
            <Box>
              <FormControl fullWidth size="small">
                <InputLabel>Sort by</InputLabel>
                <Select
                  value={sortBy}
                  label="Sort by"
                  onChange={(e) => setSortBy(e.target.value)}
                >
                  <MenuItem value="time">Time (chronological)</MenuItem>
                  <MenuItem value="relevance">Relevance</MenuItem>
                  <MenuItem value="speaker">Speaker</MenuItem>
                  <MenuItem value="emotion">Emotion</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
        <Button
          variant="contained"
          onClick={handleSearch}
          disabled={isSearching || (!searchQuery.trim() && !hasActiveFilters)}
          startIcon={<SearchIcon />}
        >
          {isSearching ? 'Searching...' : 'Search'}
        </Button>

        <Button
          variant="outlined"
          onClick={handleFilter}
          startIcon={<FilterIcon />}
        >
          Apply Filters
        </Button>

        {hasActiveFilters && (
          <Button
            variant="text"
            onClick={clearAllFilters}
            startIcon={<ClearIcon />}
            color="secondary"
          >
            Clear All
          </Button>
        )}
      </Box>

      {/* Search Results Summary */}
      {results.length > 0 && (
        <Box sx={{ mt: 3, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
          <Typography variant="body2">
            Found <strong>{results.length}</strong> matching segments
            {totalSegments > 0 && ` out of ${totalSegments} total`}
          </Typography>
        </Box>
      )}
    </Paper>
  );
}

export default SearchAndFilter;