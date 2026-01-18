# Frontend Documentation

## Overview
The frontend of the SoutiAI Transcription Engine is built with React and Material-UI, providing a modern, responsive interface for interacting with the transcription API. The frontend handles file uploads, real-time job monitoring, results visualization, and interactive features like Q&A and voice analytics.

## Architecture

### Tech Stack
- **Framework**: React 18
- **Styling**: Material-UI (MUI) v5
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **State Management**: React Hooks
- **Notifications**: notistack
- **File Upload**: react-dropzone
- **Charts**: Recharts
- **Icons**: Material Icons

### Folder Structure
```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable UI components
│   ├── pages/             # Route components
│   ├── hooks/             # Custom React hooks
│   ├── utils/             # Utility functions
│   ├── theme.js           # MUI theme configuration
│   ├── App.js             # Main application component
│   └── index.js           # Application entry point
├── package.json           # Dependencies and scripts
└── nginx.conf            # Nginx configuration
```

## Components

### Core Components
- **Header**: Navigation bar with links to all major sections
- **Footer**: Site-wide footer with contact information
- **ErrorBoundary**: Handles and displays application errors gracefully
- **LoadingSpinner**: Visual indicator for loading states
- **SkeletonLoader**: Placeholder UI for loading content

### Feature Components
- **Timeline**: Visual representation of transcription with speaker and emotion markers
- **InteractiveTranscript**: Scrollable, searchable transcript with speaker identification
- **SearchAndFilter**: Advanced search and filtering for transcript content
- **AnalyticsDashboard**: Charts and statistics for voice analytics data

## Pages

### Dashboard (`/`)
- Overview of all transcription jobs
- Job cards showing status, progress, and metadata
- Quick access to upload new files

### Upload (`/upload`)
- File drag-and-drop interface
- Processing settings configuration
- Language selection and feature toggles

### Job Details (`/jobs/:jobId`)
- Comprehensive view of transcription results
- Interactive transcript with timeline
- Download options for various formats
- Q&A interface for asking questions about content
- Voice analytics visualization

### Streaming (`/streaming`)
- Real-time audio streaming interface
- Live transcription display
- Connection status indicators

### Help (`/help`)
- Documentation and quick start guide
- Feature explanations

### Settings (`/settings`)
- User preferences and default configurations
- Notification settings
- Default language selections

## Key Features

### Real-time Updates
- WebSocket connections for live job progress updates
- Automatic polling for job status
- Live streaming transcription

### Rich Visualization
- Interactive timeline with speaker and emotion markers
- Searchable and filterable transcript
- Voice analytics with charts and statistics
- Hierarchical summaries

### Accessibility
- Keyboard navigation support
- Screen reader compatibility
- Proper contrast ratios
- Semantic HTML structure

### Responsive Design
- Mobile-first approach
- Adapts to various screen sizes
- Touch-friendly controls

## API Integration

### HTTP Requests
- All API calls use Axios with proper error handling
- Centralized error notifications via notistack
- Request/response interceptors for authentication and error handling

### Endpoints Used
- `/api/v1/upload/file` - File upload and transcription initiation
- `/api/v1/jobs/` - Job listing and status updates
- `/api/v1/jobs/{id}` - Individual job details
- `/api/v1/jobs/{id}/results` - Complete job results
- `/api/v1/qa/{id}/ask` - Question answering
- `/api/v1/ws/jobs/{id}` - WebSocket for real-time updates

## Utilities

### Helper Functions (`src/utils/helpers.js`)
- `formatFileSize()` - Human-readable file size formatting
- `formatDuration()` - Time duration formatting
- `downloadFile()` - File download utility
- `getStatusColor()` - Status badge color mapping
- `getEmotionColor()` - Emotion color mapping
- `getSpeakerColor()` - Speaker color mapping
- `debounce()` - Function debouncing utility

### Custom Hooks (`src/hooks/useApi.js`)
- `useApiCall()` - Generic API call handler with error management
- `useFetchData()` - Data fetching with loading/error states
- `useFormSubmit()` - Form submission with loading states

## Styling

### Theme
- Custom MUI theme defined in `src/theme.js`
- Consistent color palette and typography
- Enhanced component styling for better UX

### Responsive Design
- MUI's grid system for responsive layouts
- Breakpoint-specific styling
- Mobile-optimized interfaces

## Error Handling

### Error Boundaries
- Global error boundary in App.js
- Specific error handling in components
- User-friendly error messages

### API Error Handling
- Network error detection
- Server error response parsing
- User notifications for errors

## Performance Optimization

### Loading States
- Skeleton loaders for content placeholders
- Loading spinners for operations
- Progressive loading of heavy components

### Caching
- Browser caching for static assets
- Local storage for user preferences
- Efficient data fetching patterns

## Development

### Scripts
- `npm start` - Development server with hot reloading
- `npm run build` - Production build
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App (not recommended)

### Environment
- Proxy configured to backend API during development
- Environment-specific configurations

## Deployment

### Production Build
- Optimized bundle with minification
- Asset hashing for cache busting
- Static file serving ready

### Docker Integration
- Multi-stage Dockerfile for optimized builds
- Nginx serves static files in production
- Environment variable support