# Shakty3n - Windows Setup Guide

## Prerequisites

1. **Python 3.8+** - Download from https://www.python.org/downloads/
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation!

2. **Node.js 18+** (for Web UI) - Download from https://nodejs.org

## Quick Start

### Step 1: Install Dependencies

1. Extract the shakty3n folder to your desired location
2. Open Command Prompt (cmd) or PowerShell
3. Navigate to the shakty3n folder:
   ```cmd
   cd C:\path\to\shakty3n
   ```
4. Run the installation script:
   ```cmd
   setup_windows\install.bat
   ```

   Or install manually:
   ```cmd
   pip install -r requirements.txt
   ```

### Step 2: Configure API Keys

Run the configuration script:
```cmd
setup_windows\configure.bat
```

Or manually:
```cmd
python shakty3n.py configure
```

You'll be prompted to enter your API keys for:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)

Alternatively, create a `.env` file in the project root with your keys:
```env
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
DEFAULT_AI_PROVIDER=openai
DEFAULT_MODEL=gpt-4
```

### Step 3: Start the Server

**Option A: Using batch script**
```cmd
setup_windows\start_server.bat
```

**Option B: Manual command**
```cmd
python shakty3n.py serve --host 0.0.0.0 --port 8000
```

The API server will be available at: http://localhost:8000

### Step 4: Start the Web UI (Optional)

Open a **new** Command Prompt/PowerShell window and run:

**Option A: Using batch script**
```cmd
setup_windows\start_web_ui.bat
```

**Option B: Manual commands**
```cmd
cd platform_web
npm install
npm run dev
```

The Web UI will be available at: http://localhost:3000

## Using Ollama (Local Models)

For running AI models locally without API keys:

1. Install Ollama from https://ollama.com/download
2. Start Ollama
3. Pull a coding model:
   ```cmd
   ollama pull deepseek-coder:6.7b
   ```
   or
   ```cmd
   ollama pull qwen2.5-coder:7b
   ```

4. Set in your `.env` file:
   ```env
   DEFAULT_AI_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   ```

## Command Reference

| Command | Description |
|---------|-------------|
| `python shakty3n.py serve` | Start the API server |
| `python shakty3n.py configure` | Configure API keys |
| `python shakty3n.py test --provider openai` | Test provider connection |
| `python shakty3n.py create --interactive` | Create project interactively |
| `python shakty3n.py --help` | Show all available commands |

## Creating Projects via Command Line

```cmd
python shakty3n.py create ^
  --description "A todo list with categories" ^
  --type web-react ^
  --provider openai
```

Note: Use `^` for line continuation in Windows Command Prompt.

## Troubleshooting

### "python is not recognized as an internal or external command"
- Python is not in your PATH
- Reinstall Python and check "Add Python to PATH"
- Or add Python manually to your PATH environment variable

### "npm is not recognized..."
- Node.js is not installed or not in PATH
- Download and install from https://nodejs.org

### "Connection refused" errors
- Make sure the API server is running
- Check if port 8000 is available
- Check your firewall settings

### Import errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

## Files in This Folder

| File | Description |
|------|-------------|
| `install.bat` | Installs Python dependencies |
| `configure.bat` | Configures API keys |
| `start_server.bat` | Starts the API server |
| `start_web_ui.bat` | Starts the Web UI development server |

## Support

- Check the main README.md for detailed documentation
- Open an issue on GitHub for bugs or questions
