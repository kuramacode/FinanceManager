class AIError(Exception):
    """Base AI exception."""
    
class AIConfigurationError(AIError):
    """Raised when AI configuration is invalid"""

class AIClientError(AIError):
    """Raised when provider request fails."""


class AIResponseFormatError(AIError):
    """Raised when AI response has invalid format."""