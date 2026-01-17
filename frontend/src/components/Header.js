import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import AudiotrackIcon from '@mui/icons-material/Audiotrack';

function Header() {
  const navigate = useNavigate();

  return (
    <AppBar position="static">
      <Toolbar>
        <AudiotrackIcon sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Transcription Engine
        </Typography>
        <Box>
          <Button color="inherit" onClick={() => navigate('/')}>
            Dashboard
          </Button>
          <Button color="inherit" onClick={() => navigate('/upload')}>
            Upload
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Header;