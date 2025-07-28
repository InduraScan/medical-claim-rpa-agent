import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the Medical Claim RPA Agent"""
    
    # Google Drive API Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REFRESH_TOKEN = os.getenv('GOOGLE_REFRESH_TOKEN')
    
    # OpenAI Configuration (if using OpenAI for enhanced AI reasoning)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Application Settings
    MAX_LINES_PER_CLAIM = int(os.getenv('MAX_LINES_PER_CLAIM', '28'))
    ER_CONSOLIDATION_HOURS = int(os.getenv('ER_CONSOLIDATION_HOURS', '24'))
    IMAGING_GROUPING_HOURS = int(os.getenv('IMAGING_GROUPING_HOURS', '24'))
    
    # File Processing Settings
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
    SUPPORTED_FILE_TYPES = ['csv', 'xlsx', 'xls']
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Streamlit Configuration
    STREAMLIT_PORT = int(os.getenv('PORT', '8501'))
    STREAMLIT_HOST = os.getenv('HOST', '0.0.0.0')
    
    # Medical Code Validation
    VALIDATE_MEDICAL_CODES = os.getenv('VALIDATE_MEDICAL_CODES', 'True').lower() == 'true'
    
    # Business Rules
    BUSINESS_RULES = {
        'max_lines_per_claim': MAX_LINES_PER_CLAIM,
        'er_consolidation_window_hours': ER_CONSOLIDATION_HOURS,
        'imaging_grouping_window_hours': IMAGING_GROUPING_HOURS,
        'maintain_service_relationships': True,
        'prioritize_high_value_services': True,
        'natural_break_points': True
    }
    
    # UI Configuration
    UI_CONFIG = {
        'theme': 'light',
        'sidebar_width': 300,
        'show_processing_details': True,
        'enable_prompt_tuning': True,
        'show_medical_code_insights': True
    }
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        issues = []
        
        # Check required Google Drive settings for production
        if not cls.GOOGLE_CLIENT_ID and os.getenv('RENDER'):
            issues.append("GOOGLE_CLIENT_ID not set for production deployment")
        
        if not cls.GOOGLE_CLIENT_SECRET and os.getenv('RENDER'):
            issues.append("GOOGLE_CLIENT_SECRET not set for production deployment")
        
        # Check file size limits
        if cls.MAX_FILE_SIZE_MB > 100:
            issues.append("MAX_FILE_SIZE_MB should not exceed 100MB for performance")
        
        # Check line limits
        if cls.MAX_LINES_PER_CLAIM < 1 or cls.MAX_LINES_PER_CLAIM > 100:
            issues.append("MAX_LINES_PER_CLAIM should be between 1 and 100")
        
        return issues
    
    @classmethod
    def get_google_oauth_config(cls):
        """Get Google OAuth configuration"""
        return {
            "web": {
                "client_id": cls.GOOGLE_CLIENT_ID,
                "client_secret": cls.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080/callback"]
            }
        }

# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    
    # Enhanced security for production
    VALIDATE_MEDICAL_CODES = True

# Select configuration based on environment
environment = os.getenv('ENVIRONMENT', 'development').lower()

if environment == 'production':
    config = ProductionConfig()
else:
    config = DevelopmentConfig()

# Export the active configuration
__all__ = ['config']