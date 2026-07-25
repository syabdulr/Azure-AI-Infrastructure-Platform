"""Unit tests for settings configuration"""

import pytest
from src.config.settings import Settings, get_settings, reload_settings
import os


@pytest.mark.unit
class TestSettings:
    """Test application settings"""
    
    def test_settings_default_values(self):
        """Test default settings values"""
        settings = Settings()
        
        assert settings.app_name == "Azure AI Infrastructure Platform"
        assert settings.app_version == "1.0.0"
        assert settings.app_environment == "dev"
        assert settings.log_level == "INFO"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.rate_limit_enabled is True
        assert settings.monitoring_enabled is True
    
    def test_settings_custom_values(self):
        """Test custom settings values"""
        settings = Settings(
            app_name="Custom App",
            app_version="2.0.0",
            app_environment="prod",
            log_level="DEBUG"
        )
        
        assert settings.app_name == "Custom App"
        assert settings.app_version == "2.0.0"
        assert settings.app_environment == "prod"
        assert settings.log_level == "DEBUG"
    
    def test_settings_validation_environment(self):
        """Test environment validation"""
        # Valid environments should pass
        valid_environments = ["dev", "staging", "prod"]
        for env in valid_environments:
            settings = Settings(app_environment=env)
            assert settings.app_environment == env
    
    def test_settings_validation_invalid_environment(self):
        """Test invalid environment raises error"""
        with pytest.raises(ValueError):
            Settings(app_environment="invalid")
    
    def test_settings_validation_log_level(self):
        """Test log level validation"""
        # Valid log levels should pass
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            settings = Settings(log_level=level)
            assert settings.log_level == level
    
    def test_settings_validation_port(self):
        """Test port validation"""
        # Valid ports should pass
        valid_ports = [1, 8000, 65535]
        for port in valid_ports:
            settings = Settings(port=port)
            assert settings.port == port
    
    def test_settings_validation_invalid_port_low(self):
        """Test invalid port (too low) raises error"""
        with pytest.raises(ValueError):
            Settings(port=0)
    
    def test_settings_validation_invalid_port_high(self):
        """Test invalid port (too high) raises error"""
        with pytest.raises(ValueError):
            Settings(port=65536)
    
    def test_settings_validation_temperature(self):
        """Test temperature validation"""
        # Valid temperatures should pass
        valid_temps = [0.0, 0.5, 1.0, 2.0]
        for temp in valid_temps:
            settings = Settings(chat_temperature_default=temp)
            assert settings.chat_temperature_default == temp
    
    def test_settings_validation_invalid_temperature_low(self):
        """Test invalid temperature (too low) raises error"""
        with pytest.raises(ValueError):
            Settings(chat_temperature_default=-0.1)
    
    def test_settings_validation_invalid_temperature_high(self):
        """Test invalid temperature (too high) raises error"""
        with pytest.raises(ValueError):
            Settings(chat_temperature_default=2.1)
    
    def test_get_settings_singleton(self):
        """Test get_settings returns singleton"""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_reload_settings(self):
        """Test reload settings"""
        # Set environment variable
        os.environ["APP_NAME"] = "Test App"
        
        settings = reload_settings()
        
        assert settings is not None
        assert isinstance(settings, Settings)
        
        # Clean up
        del os.environ["APP_NAME"]