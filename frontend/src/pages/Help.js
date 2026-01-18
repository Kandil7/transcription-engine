import React from 'react';
import { Container, Typography, Paper, Box, Grid, Card, CardContent, Button, Divider } from '@mui/material';
import {
    CloudUpload as UploadIcon,
    Mic as MicIcon,
    Dashboard as DashboardIcon,
    QuestionAnswer as QaIcon,
    Description as DescriptionIcon
} from '@mui/icons-material';

function Help() {
    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Typography variant="h4" component="h1" gutterBottom>
                Help & Documentation
            </Typography>

            <Typography variant="body1" color="text.secondary" paragraph>
                Welcome to the SoutiAI Transcription Engine. Here's a quick guide to help you get started with the main features.
            </Typography>

            <Box sx={{ mb: 4 }}>
                <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
                    Quick Start Guide
                </Typography>

                <Grid container spacing={3}>
                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%' }}>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                    <UploadIcon color="primary" sx={{ mr: 1, fontSize: 30 }} />
                                    <Typography variant="h6">1. Upload Files</Typography>
                                </Box>
                                <Typography variant="body2" color="text.secondary">
                                    Go to the <strong>Upload</strong> page to submit audio or video files.
                                    Supported formats include MP3, WAV, MP4, MKV.
                                    You can select the source language and enable translation.
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%' }}>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                    <DashboardIcon color="primary" sx={{ mr: 1, fontSize: 30 }} />
                                    <Typography variant="h6">2. Track Progress</Typography>
                                </Box>
                                <Typography variant="body2" color="text.secondary">
                                    Monitor the status of your jobs on the <strong>Dashboard</strong>.
                                    Processing time varies depending on file length and current server load.
                                    You'll see real-time progress bars for active jobs.
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%' }}>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                    <DescriptionIcon color="primary" sx={{ mr: 1, fontSize: 30 }} />
                                    <Typography variant="h6">3. View Results</Typography>
                                </Box>
                                <Typography variant="body2" color="text.secondary">
                                    Click on any completed job to view the full <strong>Job Details</strong>.
                                    Access transcripts, translations, summaries, and meeting analytics.
                                    You can also download results in various formats (TXT, SRT, VTT).
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </Box>

            <Paper sx={{ p: 3, mb: 4 }}>
                <Typography variant="h5" gutterBottom>
                    Advanced Features
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                            <MicIcon color="secondary" />
                            <Box>
                                <Typography variant="subtitle1 font-bold">Real-time Streaming</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Use the <strong>Live Stream</strong> feature to transcribe audio in real-time.
                                    Perfect for meetings or lectures where you need immediate captions.
                                </Typography>
                            </Box>
                        </Box>
                    </Grid>

                    <Grid item xs={12} md={6}>
                        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                            <QaIcon color="secondary" />
                            <Box>
                                <Typography variant="subtitle1 font-bold">AI Q&A</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    On the Job Details page, switch to the <strong>Q&A tab</strong> to ask questions about your content.
                                    The AI will answer based on the transcript and cite the specific segments used.
                                </Typography>
                            </Box>
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            <Paper sx={{ p: 3, bgcolor: '#f5f5f5' }}>
                <Typography variant="h6" gutterBottom>
                    Need more help?
                </Typography>
                <Typography variant="body2" paragraph>
                    For detailed technical documentation, API reference, and deployment guides,
                    please refer to the project documentation included in the <code>docs/</code> folder
                    or visit the API documentation.
                </Typography>
                <Button
                    variant="outlined"
                    href="http://localhost:8000/docs"
                    target="_blank"
                    sx={{ mt: 1 }}
                >
                    Open API Documentation
                </Button>
            </Paper>
        </Container>
    );
}

export default Help;
