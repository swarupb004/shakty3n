# Shakty3n Examples

This directory contains example scripts demonstrating various use cases of Shakty3n.

## Available Examples

### 1. create_todo_app.py
Creates a complete React-based todo list web application.

**Usage:**
```bash
python examples/create_todo_app.py
```

**Features:**
- User authentication
- CRUD operations for todos
- Filtering and categorization
- Responsive design
- Dark mode

### 2. create_android_app.py
Creates a weather application for Android.

**Usage:**
```bash
python examples/create_android_app.py
```

**Features:**
- Current weather conditions
- 7-day forecast
- Location search
- Weather alerts
- Material Design UI

### 3. test_providers.py
Tests all configured AI providers.

**Usage:**
```bash
python examples/test_providers.py
```

**Tests:**
- OpenAI (GPT-4)
- Anthropic (Claude)
- Google (Gemini)
- Ollama (Local models)

## Prerequisites

1. Install Shakty3n:
```bash
pip install -e .
```

2. Configure API keys:
```bash
python shakty3n.py configure
```

Or create a `.env` file:
```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
```

## Running Examples

All examples can be run directly:

```bash
# Run from project root
python examples/create_todo_app.py
python examples/create_android_app.py
python examples/test_providers.py
```

## Output

Generated projects will be created in the `examples/` directory:
- `examples/todo_app/` - React todo application
- `examples/weather_app/` - Android weather app

## Customization

You can modify the examples to:
- Change project descriptions
- Use different AI providers
- Add custom requirements
- Modify output directories
- Adjust generation parameters

## More Examples

For more usage patterns, see:
- Main README.md
- CLI help: `python shakty3n.py --help`
- Source code in `src/shakty3n/`
