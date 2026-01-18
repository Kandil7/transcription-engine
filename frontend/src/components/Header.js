import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import AudiotrackIcon from '@mui/icons-material/Audiotrack';
import StreamIcon from '@mui/icons-material/Stream';
import SettingsIcon from '@mui/icons-material/Settings';

function Header() {
  const navigate = useNavigate();

  return (
    <AppBar position="static" role="banner">
      <Toolbar>
        <AudiotrackIcon sx={{ mr: 2 }} aria-hidden="true" />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Transcription Engine
        </Typography>
        <Box role="navigation" aria-label="Main navigation">
          <Button
            color="inherit"
            onClick={() => navigate('/')}
            aria-label="Go to dashboard"
          >
            Dashboard
          </Button>
          <Button
            color="inherit"
            onClick={() => navigate('/upload')}
            aria-label="Go to upload page"
          >
            Upload
          </Button>
          <Button
            color="inherit"
            onClick={() => navigate('/streaming')}
            startIcon={<StreamIcon />}
            aria-label="Go to live streaming page"
          >
            Live Stream
          </Button>
          <Button
            color="inherit"
            onClick={() => navigate('/help')}
            aria-label="Go to help page"
          >
            Help
          </Button>
          <Button
            color="inherit"
            onClick={() => navigate('/settings')}
            startIcon={<SettingsIcon />}
            aria-label="Go to settings page"
          >
            Settings
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Header;