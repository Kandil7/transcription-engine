import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Box,
  Button,
  Grid,
  Divider,
  Alert,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Tab,
  Tabs
} from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';
import DownloadIcon from '@mui/icons-material/Download';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import Timeline from '../components/Timeline';
import SearchAndFilter from '../components/SearchAndFilter';
import InteractiveTranscript from '../components/InteractiveTranscript';
import AnalyticsDashboard from '../components/AnalyticsDashboard';

function JobDetails() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [answers, setAnswers] = useState([]);
  const [currentTab, setCurrentTab] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredSegments, setFilteredSegments] = useState([]);
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    fetchJobDetails();
    // Set up polling for job status updates
    const interval = setInterval(fetchJobDetails, 5000);
    return () => clearInterval(interval);
  }, [jobId]);

  const fetchJobDetails = async () => {
    try {
      const response = await axios.get(`/api/v1/jobs/${jobId}`);
      setJob(response.data);

      // If job is completed, fetch results
      if (response.data.status === 'completed') {
        const resultsResponse = await axios.get(`/api/v1/jobs/${jobId}/results`);
        setResults(resultsResponse.data);
      }
    } catch (error) {
      enqueueSnackbar('Failed to load job details', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Extract segments from voice analytics for timeline and transcript
  const getSegments = () => {
    if (results?.voice_analytics?.speaker_segments) {
      return results.voice_analytics.speaker_segments;
    }
    return [];
  };

  const getSpeakers = () => {
    const segments = getSegments();
    return [...new Set(segments.map(s => s.speaker).filter(Boolean))];
  };

  const getEmotions = () => {
    const segments = getSegments();
    return [...new Set(segments.map(s => s.emotion).filter(Boolean))];
  };

  const handleSearch = async (searchParams) => {
    // Simple client-side search for now
    const segments = getSegments();
    let filtered = segments;

    // Text search
    if (searchParams.query) {
      const query = searchParams.query.toLowerCase();
      filtered = filtered.filter(segment =>
        segment.text?.toLowerCase().includes(query)
      );
    }

    // Speaker filter
    if (searchParams.speakers?.length > 0) {
      filtered = filtered.filter(segment =>
        searchParams.speakers.includes(segment.speaker)
      );
    }

    // Emotion filter
    if (searchParams.emotions?.length > 0) {
      filtered = filtered.filter(segment =>
        searchParams.emotions.includes(segment.emotion)
      );
    }

    // Time range filter
    if (searchParams.timeRange) {
      const [startTime, endTime] = searchParams.timeRange;
      filtered = filtered.filter(segment =>
        segment.start >= startTime && segment.end <= endTime
      );
    }

    return filtered;
  };

  const handleFilter = (filters) => {
    // Apply filters to current view
    console.log('Applying filters:', filters);
  };

  const askQuestion = async () => {
    if (!question.trim()) {
      enqueueSnackbar('Please enter a question', { variant: 'warning' });
      return;
    }

    setAsking(true);
    try {
      const response = await axios.post(`/api/v1/qa/${jobId}/ask`, {
        question: question.trim()
      });

      const newAnswer = {
        id: Date.now(),
        question: question.trim(),
        ...response.data,
        timestamp: new Date().toLocaleString()
      };

      setAnswers(prev => [newAnswer, ...prev]);
      setQuestion('');

    } catch (error) {
      enqueueSnackbar('Failed to get answer', { variant: 'error' });
    } finally {
      setAsking(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'warning',
      processing: 'info',
      completed: 'success',
      failed: 'error',
      cancelled: 'default'
    };
    return colors[status] || 'default';
  };

  const handleDownload = (content, filename, mimeType = 'text/plain') => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography>Loading job details...</Typography>
      </Container>
    );
  }

  if (!job) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">Job not found</Alert>
      </Container>
    );
  }

  const segments = getSegments();
  const speakers = getSpeakers();
  const emotions = getEmotions();

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Job Details
      </Typography>

      {/* Job Status Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {job.filename}
          </Typography>

          <Box mb={2}>
            <Chip
              label={job.status}
              color={getStatusColor(job.status)}
              size="small"
            />
          </Box>

          {job.progress !== null && job.progress !== undefined && (
            <Box mb={2}>
              <LinearProgress
                variant="determinate"
                value={job.progress}
                sx={{ mb: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {job.progress}% complete
              </Typography>
            </Box>
          )}

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">
                Language
              </Typography>
              <Typography variant="body1">{job.language}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">
                Created
              </Typography>
              <Typography variant="body1">
                {new Date(job.created_at).toLocaleString()}
              </Typography>
            </Grid>
            {job.duration && (
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Duration
                </Typography>
                <Typography variant="body1">
                  {Math.round(job.duration)}s
                </Typography>
              </Grid>
            )}
          </Grid>

          {job.message && (
            <Alert severity={job.status === 'failed' ? 'error' : 'info'} sx={{ mb: 2 }}>
              {job.message}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Tab Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)}>
          <Tab label="Overview" />
          <Tab label="Transcript" />
          <Tab label="Analytics" disabled={!results?.voice_analytics} />
          <Tab label="Q&A" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {currentTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            {/* Timeline */}
            {segments.length > 0 && (
              <Timeline
                segments={segments}
                duration={job.duration || 0}
                currentTime={currentTime}
                onTimeChange={setCurrentTime}
                speakers={speakers}
                emotions={emotions}
              />
            )}

            {/* Basic transcript */}
            {results?.transcript && (
              <Card sx={{ mt: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Full Transcript
                  </Typography>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {results.transcript}
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Downloads
                </Typography>

                {results && (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {results.transcript && (
                      <Button
                        variant="outlined"
                        startIcon={<DownloadIcon />}
                        onClick={() => handleDownload(results.transcript, 'transcript.txt')}
                        fullWidth
                      >
                        Transcript
                      </Button>
                    )}

                    {results.translation && (
                      <Button
                        variant="outlined"
                        startIcon={<DownloadIcon />}
                        onClick={() => handleDownload(results.translation, 'translation.txt')}
                        fullWidth
                      >
                        Translation
                      </Button>
                    )}

                    {results.summary && (
                      <Button
                        variant="outlined"
                        startIcon={<DownloadIcon />}
                        onClick={() => handleDownload(results.summary, 'summary.txt')}
                        fullWidth
                      >
                        Summary
                      </Button>
                    )}

                    {results.subtitles_srt && (
                      <Button
                        variant="outlined"
                        startIcon={<DownloadIcon />}
                        onClick={() => handleDownload(results.subtitles_srt, 'subtitles.srt')}
                        fullWidth
                      >
                        SRT Subtitles
                      </Button>
                    )}

                    {results.subtitles_vtt && (
                      <Button
                        variant="outlined"
                        startIcon={<DownloadIcon />}
                        onClick={() => handleDownload(results.subtitles_vtt, 'subtitles.vtt')}
                        fullWidth
                      >
                        VTT Subtitles
                      </Button>
                    )}
                  </Box>
                )}

                {!results && job.status !== 'completed' && (
                  <Typography variant="body2" color="text.secondary">
                    Downloads will be available once processing is complete.
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {currentTab === 1 && (
        <Box>
          {/* Search and Filter */}
          <SearchAndFilter
            onSearch={handleSearch}
            onFilter={handleFilter}
            speakers={speakers}
            emotions={emotions}
            duration={job.duration || 0}
            totalSegments={segments.length}
          />

          {/* Interactive Transcript */}
          <InteractiveTranscript
            segments={segments}
            currentTime={currentTime}
            onTimeChange={setCurrentTime}
            searchQuery={searchQuery}
            speakers={speakers}
            emotions={emotions}
          />
        </Box>
      )}

      {currentTab === 2 && results?.voice_analytics && (
        <AnalyticsDashboard
          voiceAnalytics={results.voice_analytics}
          duration={job.duration || 0}
        />
      )}

      {currentTab === 3 && (
        results && (

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {job.filename}
              </Typography>

              <Box mb={2}>
                <Chip
                  label={job.status}
                  color={getStatusColor(job.status)}
                  size="small"
                />
              </Box>

              {job.progress !== null && job.progress !== undefined && (
                <Box mb={2}>
                  <LinearProgress
                    variant="determinate"
                    value={job.progress}
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {job.progress}% complete
                  </Typography>
                </Box>
              )}

              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Language
                  </Typography>
                  <Typography variant="body1">{job.language}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body1">
                    {new Date(job.created_at).toLocaleString()}
                  </Typography>
                </Grid>
                {job.duration && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Duration
                    </Typography>
                    <Typography variant="body1">
                      {Math.round(job.duration)}s
                    </Typography>
                  </Grid>
                )}
              </Grid>

              {job.message && (
                <Alert severity={job.status === 'failed' ? 'error' : 'info'} sx={{ mb: 2 }}>
                  {job.message}
                </Alert>
              )}
            </CardContent>
          </Card>

          {results && (
            <>
              <Card sx={{ mt: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Transcript
                  </Typography>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {results.transcript}
                  </Typography>
                </CardContent>
              </Card>

              {results.translation && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Translation ({job.target_language})
                    </Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {results.translation}
                    </Typography>
                  </CardContent>
                </Card>
              )}

              {results.summary && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Summary
                    </Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {results.summary}
                    </Typography>
                  </CardContent>
                </Card>
              )}

              {results.hierarchical_summary && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Hierarchical Summary
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Multiple levels of summarization for different needs
                    </Typography>

                    <Box sx={{ mt: 2 }}>
                      {results.hierarchical_summary.level_1_elevator_pitch && (
                        <Box sx={{ mb: 3 }}>
                          <Typography variant="subtitle1" color="primary" gutterBottom>
                            📄 Elevator Pitch (30 seconds read)
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', pl: 2 }}>
                            {results.hierarchical_summary.level_1_elevator_pitch}
                          </Typography>
                        </Box>
                      )}

                      {results.hierarchical_summary.level_2_key_points && (
                        <Box sx={{ mb: 3 }}>
                          <Typography variant="subtitle1" color="primary" gutterBottom>
                            🎯 Key Points (2 minutes read)
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', pl: 2 }}>
                            {results.hierarchical_summary.level_2_key_points}
                          </Typography>
                        </Box>
                      )}

                      {results.hierarchical_summary.level_3_comprehensive && (
                        <Box sx={{ mb: 3 }}>
                          <Typography variant="subtitle1" color="primary" gutterBottom>
                            📚 Comprehensive Summary (5+ minutes read)
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', pl: 2 }}>
                            {results.hierarchical_summary.level_3_comprehensive}
                          </Typography>
                        </Box>
                      )}
                    </Box>

                    {results.hierarchical_summary.metadata && (
                      <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Generated using {results.hierarchical_summary.metadata.method} •
                          Original text: {results.hierarchical_summary.metadata.original_length} characters •
                          {results.hierarchical_summary.metadata.levels_generated} summary levels
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              )}

              {results.voice_analytics && results.voice_analytics.meeting_analysis && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      🎭 Meeting Analytics
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Speaker participation and meeting dynamics
                    </Typography>

                    <Grid container spacing={3} sx={{ mt: 1 }}>
                      <Grid item xs={12} md={4}>
                        <Box sx={{ p: 2, bgcolor: 'primary.light', borderRadius: 1, color: 'white' }}>
                          <Typography variant="h6">
                            {results.voice_analytics.meeting_analysis.total_speakers}
                          </Typography>
                          <Typography variant="body2">
                            Total Speakers
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12} md={4}>
                        <Box sx={{ p: 2, bgcolor: 'secondary.light', borderRadius: 1, color: 'white' }}>
                          <Typography variant="h6">
                            {Math.round(results.voice_analytics.meeting_analysis.total_duration)}s
                          </Typography>
                          <Typography variant="body2">
                            Total Duration
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12} md={4}>
                        <Box sx={{ p: 2, bgcolor: 'success.light', borderRadius: 1, color: 'white' }}>
                          <Typography variant="h6">
                            {results.voice_analytics.meeting_analysis.meeting_balance_score}%
                          </Typography>
                          <Typography variant="body2">
                            Balance Score
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>

                    {results.voice_analytics.meeting_analysis.dominant_speaker && (
                      <Box sx={{ mt: 3 }}>
                        <Typography variant="subtitle1" gutterBottom>
                          👑 Dominant Speaker: {results.voice_analytics.meeting_analysis.dominant_speaker}
                        </Typography>
                      </Box>
                    )}

                    {results.voice_analytics.meeting_analysis.speaker_stats && (
                      <Box sx={{ mt: 3 }}>
                        <Typography variant="subtitle1" gutterBottom>
                          Speaker Statistics
                        </Typography>
                        {Object.entries(results.voice_analytics.meeting_analysis.speaker_stats).map(([speaker, stats]) => (
                          <Box key={speaker} sx={{ mb: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                            <Typography variant="subtitle2" color="primary">
                              {speaker}
                            </Typography>
                            <Grid container spacing={2} sx={{ mt: 1 }}>
                              <Grid item xs={4}>
                                <Typography variant="body2" color="text.secondary">
                                  Speech Time
                                </Typography>
                                <Typography variant="body1">
                                  {Math.round(stats.total_speech_time)}s ({stats.speech_percentage.toFixed(1)}%)
                                </Typography>
                              </Grid>
                              <Grid item xs={4}>
                                <Typography variant="body2" color="text.secondary">
                                  Segments
                                </Typography>
                                <Typography variant="body1">
                                  {stats.segment_count}
                                </Typography>
                              </Grid>
                              <Grid item xs={4}>
                                <Typography variant="body2" color="text.secondary">
                                  Avg Length
                                </Typography>
                                <Typography variant="body1">
                                  {stats.avg_segment_length.toFixed(1)}s
                                </Typography>
                              </Grid>
                            </Grid>
                            {stats.emotions && Object.keys(stats.emotions).length > 0 && (
                              <Box sx={{ mt: 1 }}>
                                <Typography variant="body2" color="text.secondary">
                                  Emotions: {Object.entries(stats.emotions).map(([emotion, count]) =>
                                    `${emotion}(${count})`
                                  ).join(', ')}
                                </Typography>
                              </Box>
                            )}
                          </Box>
                        ))}
                      </Box>
                    )}
                  </CardContent>
                </Card>
              )}

              {results.voice_analytics && results.voice_analytics.speaker_segments && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      👥 Speaker Segments
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Transcription with speaker attribution and emotion analysis
                    </Typography>

                    <Box sx={{ mt: 2, maxHeight: 400, overflow: 'auto' }}>
                      {results.voice_analytics.speaker_segments.map((segment, index) => (
                        <Box key={index} sx={{ mb: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Chip
                                label={segment.speaker}
                                color="primary"
                                size="small"
                              />
                              <Chip
                                label={segment.emotion}
                                variant="outlined"
                                size="small"
                              />
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                              {segment.start.toFixed(1)}s - {segment.end.toFixed(1)}s
                              ({segment.duration.toFixed(1)}s)
                            </Typography>
                          </Box>
                          <Typography variant="body2" sx={{ pl: 1 }}>
                            {segment.text}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              )}

              {results && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      <QuestionAnswerIcon sx={{ mr: 1 }} />
                      Ask Questions About Your Content
                    </Typography>

                    <Box sx={{ mb: 3 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={9}>
                          <TextField
                            fullWidth
                            label="Ask a question about this transcript"
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && askQuestion()}
                            placeholder="e.g., What are the main points discussed?"
                          />
                        </Grid>
                        <Grid item xs={3}>
                          <Button
                            fullWidth
                            variant="contained"
                            onClick={askQuestion}
                            disabled={asking || !question.trim()}
                            sx={{ height: 56 }}
                          >
                            {asking ? <CircularProgress size={24} /> : 'Ask'}
                          </Button>
                        </Grid>
                      </Grid>
                    </Box>

                    {answers.length > 0 && (
                      <Box>
                        <Typography variant="subtitle1" gutterBottom>
                          Previous Questions & Answers
                        </Typography>
                        {answers.map((answer) => (
                          <Accordion key={answer.id} sx={{ mb: 1 }}>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                              <Box sx={{ width: '100%' }}>
                                <Typography variant="subtitle2">
                                  Q: {answer.question}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {answer.timestamp} • Confidence: {(answer.confidence * 100).toFixed(0)}%
                                </Typography>
                              </Box>
                            </AccordionSummary>
                            <AccordionDetails>
                              <Typography variant="body1" paragraph>
                                <strong>Answer:</strong> {answer.answer}
                              </Typography>

                              {answer.sources && answer.sources.length > 0 && (
                                <Box>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Sources:
                                  </Typography>
                                  {answer.sources.map((source, index) => (
                                    <Box key={index} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                                      <Typography variant="body2">
                                        {source.text}
                                      </Typography>
                                      {source.chunk_id !== undefined && (
                                        <Typography variant="caption" color="text.secondary">
                                          Chunk {source.chunk_id}
                                        </Typography>
                                      )}
                                    </Box>
                                  ))}
                                </Box>
                              )}
                            </AccordionDetails>
                          </Accordion>
                        ))}
                      </Box>
                    )}

                    <Alert severity="info" sx={{ mt: 2 }}>
                      <Typography variant="body2">
                        Ask questions in Arabic or English about the content of your transcript.
                        The AI will search through the entire transcript to provide accurate answers with source references.
                      </Typography>
                    </Alert>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Downloads
              </Typography>

              {results && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {results.transcript && (
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(results.transcript, 'transcript.txt')}
                      fullWidth
                    >
                      Transcript
                    </Button>
                  )}

                  {results.translation && (
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(results.translation, 'translation.txt')}
                      fullWidth
                    >
                      Translation
                    </Button>
                  )}

                  {results.summary && (
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(results.summary, 'summary.txt')}
                      fullWidth
                    >
                      Summary
                    </Button>
                  )}

                  {results.subtitles_srt && (
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(results.subtitles_srt, 'subtitles.srt')}
                      fullWidth
                    >
                      SRT Subtitles
                    </Button>
                  )}

                  {results.subtitles_vtt && (
                    <Button
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(results.subtitles_vtt, 'subtitles.vtt')}
                      fullWidth
                    >
                      VTT Subtitles
                    </Button>
                  )}
                </Box>
              )}

              {!results && job.status !== 'completed' && (
                <Typography variant="body2" color="text.secondary">
                  Downloads will be available once processing is complete.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      )}

      {currentTab === 3 && (
        results && (
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <QuestionAnswerIcon sx={{ mr: 1 }} />
                Ask Questions About Your Content
              </Typography>

              <Box sx={{ mb: 3 }}>
                <Grid container spacing={2}>
                  <Grid item xs={9}>
                    <TextField
                      fullWidth
                      label="Ask a question about this transcript"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && askQuestion()}
                      placeholder="e.g., What are the main points discussed?"
                    />
                  </Grid>
                  <Grid item xs={3}>
                    <Button
                      fullWidth
                      variant="contained"
                      onClick={askQuestion}
                      disabled={asking || !question.trim()}
                      sx={{ height: 56 }}
                    >
                      {asking ? <CircularProgress size={24} /> : 'Ask'}
                    </Button>
                  </Grid>
                </Grid>
              </Box>

              {answers.length > 0 && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    Previous Questions & Answers
                  </Typography>
                  {answers.map((answer) => (
                    <Accordion key={answer.id} sx={{ mb: 1 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ width: '100%' }}>
                          <Typography variant="subtitle2">
                            Q: {answer.question}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {answer.timestamp} • Confidence: {(answer.confidence * 100).toFixed(0)}%
                          </Typography>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography variant="body1" paragraph>
                          <strong>Answer:</strong> {answer.answer}
                        </Typography>

                        {answer.sources && answer.sources.length > 0 && (
                          <Box>
                            <Typography variant="subtitle2" gutterBottom>
                              Sources:
                            </Typography>
                            {answer.sources.map((source, index) => (
                              <Box key={index} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                                <Typography variant="body2">
                                  {source.text}
                                </Typography>
                                {source.chunk_id !== undefined && (
                                  <Typography variant="caption" color="text.secondary">
                                    Chunk {source.chunk_id}
                                  </Typography>
                                )}
                              </Box>
                            ))}
                          </Box>
                        )}
                      </AccordionDetails>
                    </Accordion>
                  ))}
                </Box>
              )}

              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  Ask questions in Arabic or English about the content of your transcript.
                  The AI will search through the entire transcript to provide accurate answers with source references.
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        )
      )}
    </Container>
  );
}

export default JobDetails;