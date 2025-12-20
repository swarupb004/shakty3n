"""
Example: Creating an Android Weather App
"""
from shakty3n import (
    AIProviderFactory,
    AutonomousExecutor,
    load_env_vars
)

# Load environment variables
load_env_vars()

# Create AI provider (Anthropic Claude)
ai_provider = AIProviderFactory.create_provider(
    provider_name="anthropic",
    api_key=None,  # Will use ANTHROPIC_API_KEY from .env
    model="claude-3-opus-20240229"
)

# Create autonomous executor
executor = AutonomousExecutor(
    ai_provider=ai_provider,
    output_dir="./examples/weather_app"
)

# Project description
description = """
An Android weather application with the following features:
- Current weather conditions for user's location
- 7-day weather forecast
- Hourly forecast for the next 24 hours
- Search for weather in different cities
- Save favorite locations
- Weather alerts and notifications
- Beautiful weather icons and animations
- Temperature unit conversion (Celsius/Fahrenheit)
- Material Design 3 UI
"""

# Execute project
print("Starting autonomous Android app creation...")
result = executor.execute_project(
    description=description,
    project_type="android-kotlin",
    requirements={
        "language": "kotlin",
        "architecture": "mvvm",
        "networking": "retrofit",
        "database": "room",
        "dependency_injection": "hilt",
        "weather_api": "openweathermap"
    }
)

# Print results
if result["success"]:
    print("\n✓ Weather app created successfully!")
    print(f"Location: {result['generation']['output_dir']}")
    print(f"Files created: {len(result['generation'].get('files', []))}")
    
    print("\nTo build the app:")
    print("1. Open the project in Android Studio")
    print("2. Sync Gradle files")
    print("3. Run on emulator or device")
else:
    print("\n✗ Project creation failed")
    print(f"Error: {result.get('error', 'Unknown error')}")
