import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Box,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Alert,
  Grid,
  Divider
} from '@mui/material';
import { useSnackbar } from 'notistack';

function Settings() {
  const [settings, setSettings] = useState({
    autoSave: true,
    notifications: true,
    theme: 'light',
    language: 'en',
    defaultTranscriptionLanguage: 'ar',
    defaultTargetLanguage: 'en',
    enableTranslation: true,
    enableSummary: true,
    enableVoiceAnalytics: true,
    summaryLength: 'medium'
  });
  
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    // Load settings from localStorage or API
    const savedSettings = localStorage.getItem('transcription-settings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  const handleChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = () => {
    // Save settings to localStorage
    localStorage.setItem('transcription-settings', JSON.stringify(settings));
    
    // In a real app, you would also save to backend
    enqueueSnackbar('Settings saved successfully!', { variant: 'success' });
  };

  const handleReset = () => {
    const defaultSettings = {
      autoSave: true,
      notifications: true,
      theme: 'light',
      language: 'en',
      defaultTranscriptionLanguage: 'ar',
      defaultTargetLanguage: 'en',
      enableTranslation: true,
      enableSummary: true,
      enableVoiceAnalytics: true,
      summaryLength: 'medium'
    };
    
    setSettings(defaultSettings);
    localStorage.setItem('transcription-settings', JSON.stringify(defaultSettings));
    enqueueSnackbar('Settings reset to defaults', { variant: 'info' });
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          Configure your transcription preferences and default settings.
          Changes are saved automatically to your browser.
        </Typography>
      </Alert>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                General Settings
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.autoSave}
                      onChange={(e) => handleChange('autoSave', e.target.checked)}
                    />
                  }
                  label="Auto-save settings"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications}
                      onChange={(e) => handleChange('notifications', e.target.checked)}
                    />
                  }
                  label="Enable notifications"
                />
                
                <TextField
                  select
                  label="Interface Language"
                  value={settings.language}
                  onChange={(e) => handleChange('language', e.target.value)}
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="en">English</option>
                  <option value="ar">Arabic</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="es">Spanish</option>
                </TextField>
                
                <TextField
                  select
                  label="Default Theme"
                  value={settings.theme}
                  onChange={(e) => handleChange('theme', e.target.value)}
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="system">System</option>
                </TextField>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Transcription Defaults
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                <TextField
                  select
                  label="Default Source Language"
                  value={settings.defaultTranscriptionLanguage}
                  onChange={(e) => handleChange('defaultTranscriptionLanguage', e.target.value)}
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="ar">Arabic</option>
                  <option value="en">English</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="es">Spanish</option>
                </TextField>
                
                <TextField
                  select
                  label="Default Target Language"
                  value={settings.defaultTargetLanguage}
                  onChange={(e) => handleChange('defaultTargetLanguage', e.target.value)}
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="en">English</option>
                  <option value="ar">Arabic</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="es">Spanish</option>
                </TextField>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enableTranslation}
                      onChange={(e) => handleChange('enableTranslation', e.target.checked)}
                    />
                  }
                  label="Enable translation by default"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enableSummary}
                      onChange={(e) => handleChange('enableSummary', e.target.checked)}
                    />
                  }
                  label="Enable summarization by default"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enableVoiceAnalytics}
                      onChange={(e) => handleChange('enableVoiceAnalytics', e.target.checked)}
                    />
                  }
                  label="Enable voice analytics by default"
                />
                
                <TextField
                  select
                  label="Default Summary Length"
                  value={settings.summaryLength}
                  onChange={(e) => handleChange('summaryLength', e.target.value)}
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="short">Short</option>
                  <option value="medium">Medium</option>
                  <option value="long">Long</option>
                </TextField>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Account Information
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                <TextField
                  label="Email Address"
                  defaultValue="user@example.com"
                  disabled
                />
                
                <TextField
                  label="Organization"
                  defaultValue="SoutiAI"
                  disabled
                />
                
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    Account settings are managed through your organization administrator.
                    Contact support for account-related changes.
                  </Typography>
                </Alert>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSave}
        >
          Save Settings
        </Button>
        
        <Button
          variant="outlined"
          color="secondary"
          onClick={handleReset}
        >
          Reset to Defaults
        </Button>
      </Box>
    </Container>
  );
}

export default Settings;