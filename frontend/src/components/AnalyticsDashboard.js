import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts';
import {
  People as PeopleIcon,
  AccessTime as TimeIcon,
  TrendingUp as TrendingUpIcon,
  SentimentSatisfied as SentimentIcon
} from '@mui/icons-material';

function AnalyticsDashboard({ voiceAnalytics, duration }) {
  if (!voiceAnalytics || !voiceAnalytics.meeting_analysis) {
    return (
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Analytics Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Voice analytics data will appear here once processing is complete.
        </Typography>
      </Paper>
    );
  }

  const { meeting_analysis, speaker_segments } = voiceAnalytics;

  // Prepare data for charts
  const speakerParticipationData = Object.entries(meeting_analysis.speaker_stats || {}).map(
    ([speaker, stats]) => ({
      name: speaker,
      speechTime: Math.round(stats.total_speech_time),
      percentage: Math.round(stats.speech_percentage),
      segments: stats.segment_count
    })
  );

  const emotionData = speaker_segments ? speaker_segments.reduce((acc, segment) => {
    const emotion = segment.emotion || 'neutral';
    acc[emotion] = (acc[emotion] || 0) + 1;
    return acc;
  }, {}) : {};

  const emotionChartData = Object.entries(emotionData).map(([emotion, count]) => ({
    name: emotion,
    value: count,
    percentage: Math.round((count / speaker_segments.length) * 100)
  }));

  // Timeline data for emotions over time
  const timelineData = speaker_segments ? speaker_segments.map(segment => ({
    time: Math.round(segment.start),
    emotion: segment.emotion || 'neutral',
    speaker: segment.speaker,
    confidence: segment.confidence || 0
  })) : [];

  // Colors for charts
  const speakerColors = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00',
    '#ff00ff', '#00ffff', '#ff6347', '#32cd32', '#ffd700'
  ];

  const emotionColors = {
    happy: '#4caf50',
    sad: '#2196f3',
    angry: '#f44336',
    neutral: '#9e9e9e',
    excited: '#ff9800',
    calm: '#00bcd4',
    confident: '#8bc34a',
    nervous: '#ff5722'
  };

  const getEmotionColor = (emotion) => emotionColors[emotion] || emotionColors.neutral;

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
        📊 Meeting Analytics Dashboard
      </Typography>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PeopleIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">
                  {meeting_analysis.total_speakers}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Speakers
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TimeIcon sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="h6">
                  {Math.round(meeting_analysis.total_duration)}s
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Duration
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUpIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">
                  {meeting_analysis.meeting_balance_score}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Balance Score
              </Typography>
              <LinearProgress
                variant="determinate"
                value={meeting_analysis.meeting_balance_score}
                sx={{ mt: 1 }}
                color={meeting_analysis.meeting_balance_score > 70 ? "success" : "warning"}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <SentimentIcon sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">
                  {emotionChartData.length}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Emotion Types
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Row 1 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Speaker Participation */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Speaker Participation
            </Typography>
            <ResponsiveContainer width="100%" height="90%">
              <BarChart data={speakerParticipationData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip
                  formatter={(value, name) => [
                    name === 'speechTime' ? `${value}s` : `${value}%`,
                    name === 'speechTime' ? 'Speech Time' : 'Percentage'
                  ]}
                />
                <Legend />
                <Bar dataKey="speechTime" fill="#8884d8" name="Speech Time (seconds)" />
                <Bar dataKey="percentage" fill="#82ca9d" name="Percentage (%)" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Emotion Distribution */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Emotion Distribution
            </Typography>
            <ResponsiveContainer width="100%" height="90%">
              <PieChart>
                <Pie
                  data={emotionChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name} ${percentage}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {emotionChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getEmotionColor(entry.name)} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Charts Row 2 */}
      <Grid container spacing={3}>
        {/* Emotion Timeline */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Emotion Timeline
            </Typography>
            <ResponsiveContainer width="100%" height="90%">
              <AreaChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  type="number"
                  domain={[0, duration]}
                  tickFormatter={(value) => `${Math.floor(value / 60)}:${(value % 60).toString().padStart(2, '0')}`}
                />
                <YAxis hide />
                <Tooltip
                  labelFormatter={(value) => `Time: ${Math.floor(value / 60)}:${(value % 60).toString().padStart(2, '0')}`}
                  formatter={(value, name, props) => [
                    `${props.payload.emotion} (${props.payload.speaker})`,
                    'Emotion & Speaker'
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="confidence"
                  stroke="#8884d8"
                  fill="#8884d8"
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Detailed Speaker Stats */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Detailed Speaker Statistics
        </Typography>

        <Grid container spacing={2}>
          {Object.entries(meeting_analysis.speaker_stats || {}).map(([speaker, stats], index) => (
            <Grid item xs={12} md={6} key={speaker}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6" color="primary">
                      {speaker}
                    </Typography>
                    <Chip
                      label={`${stats.speech_percentage.toFixed(1)}%`}
                      color="primary"
                      size="small"
                    />
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Speech Time: {Math.round(stats.total_speech_time)}s
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Segments: {stats.segment_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Avg Length: {stats.avg_segment_length.toFixed(1)}s
                    </Typography>
                  </Box>

                  {stats.emotions && Object.keys(stats.emotions).length > 0 && (
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Emotions:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {Object.entries(stats.emotions).map(([emotion, count]) => (
                          <Chip
                            key={emotion}
                            label={`${emotion} (${count})`}
                            size="small"
                            sx={{
                              backgroundColor: getEmotionColor(emotion),
                              color: 'white',
                              fontSize: '0.7rem'
                            }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Meeting Insights */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          💡 Meeting Insights
        </Typography>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" color="primary" gutterBottom>
                Participation Balance
              </Typography>
              <Typography variant="body2">
                {meeting_analysis.meeting_balance_score > 80
                  ? "Excellent balance - all participants had equal speaking time."
                  : meeting_analysis.meeting_balance_score > 60
                  ? "Good balance with some variation in participation."
                  : "Consider encouraging quieter participants to speak more."}
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={6}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" color="primary" gutterBottom>
                Dominant Speaker
              </Typography>
              <Typography variant="body2">
                {meeting_analysis.dominant_speaker
                  ? `${meeting_analysis.dominant_speaker} was the most active participant.`
                  : "No single dominant speaker - good democratic discussion."}
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Box>
              <Typography variant="subtitle1" color="primary" gutterBottom>
                Emotional Climate
              </Typography>
              <Typography variant="body2">
                The meeting showed {emotionChartData.length} different emotional states.
                {emotionChartData.find(e => e.name === 'positive') &&
                  " Overall positive sentiment detected."}
                {emotionChartData.find(e => e.name === 'negative') &&
                  " Some challenging moments were noted."}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}

export default AnalyticsDashboard;