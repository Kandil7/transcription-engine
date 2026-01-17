# Contributing Guide

Welcome to the SoutiAI Transcription Engine! We're excited that you're interested in contributing to our Arabic AI mission. This guide will help you get started with contributing to the project.

## 🌟 Ways to Contribute

### Code Contributions
- **Bug Fixes**: Identify and fix issues in the codebase
- **Feature Development**: Implement new features from our roadmap
- **Performance Improvements**: Optimize existing functionality
- **Security Enhancements**: Improve security measures and practices

### Non-Code Contributions
- **Documentation**: Improve or translate documentation
- **Testing**: Write tests or improve test coverage
- **Design**: UI/UX improvements and design contributions
- **Research**: Arabic NLP research and model improvements
- **Community**: Help other contributors and users

### Arabic Language Contributions
- **Dialect Research**: Research and document Arabic dialects
- **Cultural Context**: Provide cultural context for Arabic content
- **Language Testing**: Test accuracy with different Arabic content
- **Localization**: Help with Arabic localization and RTL support

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:
- Python 3.11+ installed
- Node.js 18+ installed
- Docker and Docker Compose
- Git configured with SSH
- VS Code with recommended extensions (optional)

### Development Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/transcription-engine.git
   cd transcription-engine
   ```

2. **Set Up Development Environment**
   ```bash
   # Copy environment template
   cp env-example.txt .env.dev

   # Start development environment
   docker-compose -f docker-compose.dev.yml up -d

   # Backend setup
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt

   # Frontend setup
   cd ../frontend
   npm install
   npm start
   ```

3. **Run Tests**
   ```bash
   # Backend tests
   cd backend
   pytest tests/ -v --cov=app

   # Frontend tests
   cd ../frontend
   npm test
   ```

### Development Workflow

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number-description
   ```

2. **Make Changes**
   - Follow coding standards (see below)
   - Write tests for new functionality
   - Update documentation if needed
   - Ensure all tests pass

3. **Commit Changes**
   ```bash
   # Stage your changes
   git add .

   # Commit with descriptive message
   git commit -m "feat: add Arabic dialect detection

   - Implement ML-based dialect classification
   - Add support for Cairo, Alexandria, and Upper Egypt dialects
   - Improve transcription accuracy by 15-25%
   - Add comprehensive tests for dialect detection

   Closes #123"
   ```

4. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

## 📝 Coding Standards

### Python Code Style

We follow PEP 8 with some modifications:

```python
# Good: Descriptive naming and clear structure
def transcribe_audio_file(file_path: Path, language: str = "ar") -> TranscriptionResult:
    """
    Transcribe an audio file using the appropriate AI model.

    Args:
        file_path: Path to the audio file
        language: Language code (default: Arabic)

    Returns:
        TranscriptionResult with text and metadata

    Raises:
        FileNotFoundError: If audio file doesn't exist
        TranscriptionError: If transcription fails
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Validate file format
    if not _is_supported_format(file_path):
        raise ValueError(f"Unsupported audio format: {file_path.suffix}")

    # Load appropriate model based on language
    model = _load_model_for_language(language)

    # Perform transcription
    result = model.transcribe(str(file_path))

    return TranscriptionResult(
        text=result["text"],
        language=language,
        confidence=result.get("confidence", 0.0),
        segments=result.get("segments", [])
    )
```

#### Key Guidelines
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Write comprehensive docstrings using Google style
- **Error Handling**: Use custom exceptions, not generic ones
- **Logging**: Use structured logging with appropriate levels
- **Testing**: Write tests before implementing features (TDD)

### JavaScript/React Code Style

```javascript
// Good: Clean React component with TypeScript
import React, { useState, useEffect } from 'react';
import { Button, CircularProgress, Typography } from '@mui/material';
import { useTranscription } from '../hooks/useTranscription';

interface TranscriptionButtonProps {
  file: File;
  language: string;
  onComplete: (result: TranscriptionResult) => void;
  onError: (error: Error) => void;
}

export const TranscriptionButton: React.FC<TranscriptionButtonProps> = ({
  file,
  language,
  onComplete,
  onError
}) => {
  const [isTranscribing, setIsTranscribing] = useState(false);
  const { transcribeFile } = useTranscription();

  const handleTranscription = async () => {
    try {
      setIsTranscribing(true);
      const result = await transcribeFile(file, language);
      onComplete(result);
    } catch (error) {
      onError(error);
    } finally {
      setIsTranscribing(false);
    }
  };

  return (
    <Button
      variant="contained"
      onClick={handleTranscription}
      disabled={isTranscribing}
      startIcon={isTranscribing ? <CircularProgress size={20} /> : null}
    >
      {isTranscribing ? 'Transcribing...' : 'Start Transcription'}
    </Button>
  );
};
```

#### Key Guidelines
- **TypeScript**: Use TypeScript for type safety
- **Functional Components**: Prefer functional components with hooks
- **Error Boundaries**: Implement error boundaries for error handling
- **Accessibility**: Follow WCAG guidelines for accessibility
- **Performance**: Use React.memo and useMemo for optimization

### Commit Message Guidelines

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat: add Egyptian dialect detection
fix: resolve memory leak in transcription service
docs: update API reference for new endpoints
test: add integration tests for file upload
refactor: simplify transcription pipeline logic
```

## 🧪 Testing Guidelines

### Test Coverage Requirements

- **Unit Tests**: 80%+ coverage for all modules
- **Integration Tests**: Cover all API endpoints and service interactions
- **End-to-End Tests**: Critical user workflows
- **Performance Tests**: Load testing and benchmarks

### Writing Tests

```python
# Unit test example
import pytest
from unittest.mock import Mock, patch
from app.services.transcription_service import TranscriptionService

class TestTranscriptionService:

    @pytest.fixture
    def service(self):
        return TranscriptionService()

    def test_transcribe_valid_audio(self, service):
        """Test successful transcription of valid audio."""
        # Arrange
        audio_path = "/path/to/test.wav"
        expected_result = {
            "text": "Hello world",
            "confidence": 0.95,
            "language": "en"
        }

        with patch.object(service, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = expected_result

            # Act
            result = service.transcribe_audio(audio_path, "en")

            # Assert
            assert result["text"] == "Hello world"
            assert result["confidence"] == 0.95
            mock_transcribe.assert_called_once_with(audio_path, "en")

    def test_transcribe_invalid_file(self, service):
        """Test error handling for invalid files."""
        with pytest.raises(FileNotFoundError):
            service.transcribe_audio("/nonexistent/file.wav", "en")
```

### Test Categories

#### Unit Tests (`tests/`)
- Test individual functions and classes
- Mock external dependencies
- Fast execution, high coverage

#### Integration Tests (`tests/integration/`)
- Test service interactions
- Database and external API calls
- Medium execution time

#### E2E Tests (`tests/e2e/`)
- Complete user workflows
- Full system testing
- Slow execution, critical path coverage

## 📚 Documentation Guidelines

### API Documentation

Use OpenAPI/Swagger standards:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

class TranscriptionRequest(BaseModel):
    """Request model for transcription."""
    file_path: str = Field(..., description="Path to audio file")
    language: str = Field("ar", description="Language code")
    enable_translation: bool = Field(True, description="Enable translation to English")

class TranscriptionResponse(BaseModel):
    """Response model for transcription."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    estimated_time: int = Field(..., description="Estimated completion time in seconds")

@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Start audio transcription",
    description="Upload and transcribe an audio file with optional translation."
)
async def transcribe_audio(request: TranscriptionRequest):
    """Transcribe audio file endpoint."""
    pass
```

### Code Documentation

```python
def process_transcription_job(job_id: str) -> bool:
    """
    Process a transcription job end-to-end.

    This function orchestrates the complete transcription pipeline:
    1. Audio preprocessing and validation
    2. AI model transcription
    3. Optional translation
    4. Optional summarization
    5. Result storage and notification

    Args:
        job_id: Unique identifier for the transcription job

    Returns:
        bool: True if processing completed successfully, False otherwise

    Raises:
        JobNotFoundError: If job doesn't exist
        TranscriptionError: If transcription fails
        StorageError: If result storage fails

    Example:
        >>> success = process_transcription_job("job_12345")
        >>> print(f"Job completed: {success}")
        Job completed: True
    """
    pass
```

## 🔒 Security Considerations

### Secure Coding Practices

1. **Input Validation**
   ```python
   def validate_file_upload(file_path: str, max_size: int = 500 * 1024 * 1024) -> bool:
       """Validate uploaded file for security."""
       if not os.path.exists(file_path):
           return False

       # Check file size
       if os.path.getsize(file_path) > max_size:
           return False

       # Check file type (allow only safe formats)
       allowed_extensions = {'.wav', '.mp3', '.m4a', '.mp4'}
       if not any(file_path.endswith(ext) for ext in allowed_extensions):
           return False

       return True
   ```

2. **Authentication & Authorization**
   ```python
   def require_authentication(func):
       """Decorator to require authentication."""
       @wraps(func)
       async def wrapper(*args, **kwargs):
           # Check for valid JWT token
           token = get_token_from_request()
           user = verify_token(token)

           # Add user to request context
           kwargs['current_user'] = user
           return await func(*args, **kwargs)
       return wrapper
   ```

3. **Data Sanitization**
   ```python
   import bleach

   def sanitize_text_input(text: str) -> str:
       """Sanitize user input to prevent XSS."""
       return bleach.clean(text, strip=True)

   def sanitize_filename(filename: str) -> str:
       """Sanitize filename to prevent path traversal."""
       # Remove path separators and dangerous characters
       safe_name = re.sub(r'[<>:"/\\|?*]', '', filename)
       return safe_name[:255]  # Limit length
   ```

### Reporting Security Issues

**DO NOT** report security vulnerabilities in public issues. Email security@souti.ai instead.

## 🚀 Performance Guidelines

### Code Performance

1. **Async/Await Usage**
   ```python
   # Good: Non-blocking I/O
   async def fetch_user_data(user_id: str) -> dict:
       async with aiohttp.ClientSession() as session:
           async with session.get(f'/api/users/{user_id}') as response:
               return await response.json()

   # Avoid: Blocking operations in async functions
   async def bad_example():
       time.sleep(1)  # Blocks event loop!
   ```

2. **Memory Management**
   ```python
   # Good: Context managers for resource cleanup
   @contextmanager
   def temporary_file():
       temp_path = tempfile.NamedTemporaryFile(delete=False)
       try:
           yield temp_path.name
       finally:
           os.unlink(temp_path.name)

   # Good: Generator for large datasets
   def process_large_dataset(data: List[dict]) -> Iterator[dict]:
       for item in data:
           processed = expensive_operation(item)
           yield processed
   ```

3. **Caching Strategy**
   ```python
   from functools import lru_cache
   import redis

   # In-memory caching for frequent computations
   @lru_cache(maxsize=1000)
   def compute_expensive_result(input_data: str) -> str:
       return expensive_computation(input_data)

   # Redis caching for distributed caching
   redis_client = redis.Redis(host='localhost', port=6379)

   def get_cached_result(key: str) -> Optional[str]:
       return redis_client.get(key)

   def set_cached_result(key: str, value: str, ttl: int = 3600):
       redis_client.setex(key, ttl, value)
   ```

## 🌍 Arabic Language Considerations

### Cultural Sensitivity

1. **Dialect Awareness**
   - Respect regional dialect differences
   - Provide dialect selection options
   - Document dialect-specific behavior

2. **RTL Support**
   - Ensure proper RTL text rendering
   - Test with Arabic content throughout
   - Consider RTL UI layouts

3. **Cultural Context**
   - Understand Arabic communication patterns
   - Respect privacy and data sensitivity
   - Consider local regulations and norms

### Arabic Testing

```python
def test_arabic_transcription_accuracy():
    """Test transcription accuracy with Arabic content."""
    test_cases = [
        {
            "audio": "arabic_meeting.wav",
            "expected_wer": 0.15,  # 15% WER acceptable for Arabic
            "language": "ar",
            "dialect": "cairo"
        },
        {
            "audio": "arabic_lecture.wav",
            "expected_wer": 0.12,
            "language": "ar",
            "dialect": "modern_standard"
        }
    ]

    for test_case in test_cases:
        result = transcribe_audio(test_case["audio"])
        wer = calculate_wer(result["text"], reference_text)

        assert wer <= test_case["expected_wer"], \
            f"WER too high for {test_case['audio']}: {wer}"
```

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Discord**: Real-time community chat
- **Email**: For sensitive or private matters

### Asking Good Questions

```markdown
<!-- Good issue template -->
## Problem Description
Brief description of the issue or feature request.

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen?

## Actual Behavior
What actually happens?

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.0]
- Browser: [e.g., Chrome 120.0]

## Additional Context
Any other relevant information, logs, screenshots, etc.
```

## 🎯 Recognition

### Contributor Recognition

Contributors are recognized through:
- **GitHub Contributors**: Listed in repository contributors
- **Changelog Credits**: Mentioned in release notes
- **Community Badges**: Special recognition for significant contributions
- **Co-Authorship**: For major features or architectural changes

### Contribution Levels

- **First-time Contributor**: Welcome and guidance provided
- **Regular Contributor**: Code review permissions
- **Core Contributor**: Repository write access
- **Maintainer**: Full project management access

## 📋 Code of Conduct

### Our Standards

- **Respect**: Treat all contributors with respect and kindness
- **Inclusion**: Welcome contributors from all backgrounds
- **Collaboration**: Work together constructively
- **Quality**: Maintain high standards for code and interactions
- **Responsibility**: Take ownership of your contributions

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks or insults
- Disruptive or trolling behavior
- Spam or off-topic content
- Violation of privacy or data protection

### Enforcement

Violations of the code of conduct will be addressed by the project maintainers. Serious violations may result in temporary or permanent bans from the project.

## 📚 Resources

### Learning Resources

- [Development Guide](DEVELOPMENT.md) - Complete development setup
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Testing Guide](TESTING.md) - Testing strategies and practices
- [Architecture Guide](ARCHITECTURE.md) - System design and patterns

### Arabic AI Resources

- [Arabic NLP Research Papers](https://scholar.google.com/)
- [Hugging Face Arabic Models](https://huggingface.co/models?language=ar)
- [Arabic AI Community](https://www.arabiai.org/)

### Development Tools

- [VS Code Extensions](https://marketplace.visualstudio.com/)
- [Python Development Tools](https://pypi.org/)
- [React Development Tools](https://react.dev/learn)

---

Thank you for contributing to the SoutiAI Transcription Engine! Your contributions help make Arabic AI more accessible and accurate for everyone. 🌟🇪🇬

*For questions about contributing, please reach out to the maintainers or open a discussion on GitHub.*