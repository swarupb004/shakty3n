# Shakty3n - Autonomous Agentic Coder 🤖

An advanced autonomous AI-powered coder that builds complete applications across multiple platforms. Shakty3n plans, codes, debugs, and delivers fully functional Web, Android, iOS, and Desktop applications autonomously.

## ✨ Features

### 🎯 Autonomous Operation
- **Intelligent Planning**: Creates comprehensive project plans with task breakdown
- **Self-Execution**: Executes tasks autonomously until completion
- **Auto-Debugging**: Automatically detects and fixes errors
- **Progress Tracking**: Real-time progress monitoring and reporting

### 🌐 Multi-Platform Support
- **Web Applications**: React, Vue, Angular, **Svelte, Next.js**
- **Mobile Apps**: Android (Kotlin, Java), iOS (Swift, SwiftUI), **Flutter (Cross-platform)**
- **Desktop Apps**: Electron, Python (tkinter) with macOS DMG installer script

### 🤖 AI Model Integration
Connect with multiple AI providers:
- **OpenAI**: GPT-4, GPT-3.5
- **Anthropic**: Claude 3 (Opus, Sonnet, Haiku)
- **Google**: Gemini Pro, **Gemini 3.0 Pro**
- **Ollama**: Local models (Llama 2, CodeLlama, Mistral, Mixtral, **Qwen Coder, DeepSeek Coder**)

### 🛠️ Capabilities
- Complete project scaffolding and structure generation
- Intelligent code generation with best practices
- Automatic dependency management
- Error detection and fixing
- **Automatic test generation (NEW)** - Unit and integration tests
- **Code validation (NEW)** - Syntax, structure, and dependency checks
- **Sandbox testing (NEW)** - Spin up a virtual environment and run tests
- Testing framework setup
- Documentation generation

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/swarupb004/shakty3n.git
cd shakty3n

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## 🚀 Quick Start

### 1. Configure API Keys

First, set up your AI provider API keys:

```bash
# Interactive configuration
python shakty3n.py configure
```

Or manually create a `.env` file:

```env
# AI Model API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Default Settings
DEFAULT_AI_PROVIDER=openai
DEFAULT_MODEL=gpt-4
AUTO_DEBUG=true
MAX_RETRIES=3
VERBOSE=true
```

### 2. Test Your Connection

```bash
python shakty3n.py test --provider openai
```

### 3. Create Your First Project

#### Interactive Mode (Recommended)
```bash
python shakty3n.py create --interactive
```

#### Command Line Mode
```bash
# Create a React web app
python shakty3n.py create \
  --description "A todo list application with user authentication" \
  --type web-react \
  --provider openai \
  --output ./my_project

# Create an Android app
python shakty3n.py create \
  --description "A weather app showing current conditions" \
  --type android \
  --provider anthropic

# Create an iOS app
python shakty3n.py create \
  --description "A notes app with cloud sync" \
  --type ios \
  --provider google

# Create a Desktop app
python shakty3n.py create \
  --description "A task manager with reminders" \
  --type desktop-electron \
  --provider openai

# Create a Flutter cross-platform app with tests
python shakty3n.py create \
  --description "A fitness tracker with charts" \
  --type flutter \
  --provider openai \
  --with-tests

# Create a Next.js app with validation
python shakty3n.py create \
  --description "A blog platform with CMS" \
  --type web-nextjs \
  --provider anthropic \
  --with-tests \
  --validate
```

## 📖 Usage Guide

### Command Reference

```bash
# Show help
python shakty3n.py --help

# Create a new project
python shakty3n.py create [OPTIONS]

# Configure settings
python shakty3n.py configure

# Test AI provider connection
python shakty3n.py test [--provider PROVIDER]

# Create a sandboxed virtual environment and run tests
python shakty3n.py sandbox [--env-dir .shakty3n_venv] [--test-command "-m pytest tests/test_basic.py"]

# Show information
python shakty3n.py info
```

### Project Types

| Type | Description | Technologies |
|------|-------------|--------------|
| `web-react` | React web application | React, JavaScript, HTML/CSS |
| `web-vue` | Vue web application | Vue.js, JavaScript, HTML/CSS |
| `web-angular` | Angular web application | Angular, TypeScript, HTML/CSS |
| `web-svelte` | Svelte web application | Svelte, JavaScript, HTML/CSS |
| `web-nextjs` | Next.js web application | Next.js, React, TypeScript |
| `android` | Android application | Kotlin/Java, Android SDK |
| `android-kotlin` | Android app (Kotlin) | Kotlin, Android SDK |
| `android-java` | Android app (Java) | Java, Android SDK |
| `ios` | iOS application | Swift, SwiftUI |
| `flutter` | Cross-platform mobile app | Flutter, Dart |
| `desktop-electron` | Electron desktop app | Electron, JavaScript, HTML/CSS |
| `desktop-python` | Python desktop app | Python, tkinter |

### AI Providers

| Provider | Models | Requirements |
|----------|--------|--------------|
| OpenAI | GPT-4, GPT-3.5 | API Key |
| Anthropic | Claude 3 Opus, Sonnet, Haiku | API Key |
| Google | Gemini Pro, **Gemini 3.0 Pro** | API Key |
| Ollama | Llama 2, CodeLlama, Mistral, **Qwen (2.5/3) Coder, DeepSeek Coder** | Local installation |

**Mac mini m4 (16GB) friendly local models**
- `qwen2.5-coder:7b` / `qwen3-coder` via Ollama
- `deepseek-coder:6.7b` via Ollama
- Prefer these when you need fast, local coding models without a GPU

## 🏗️ Architecture

Shakty3n consists of several integrated modules:

### Core Modules

1. **AI Providers** (`ai_providers/`)
   - Abstract provider interface
   - OpenAI, Anthropic, Google, Ollama implementations
   - Provider factory and management

2. **Task Planner** (`planner/`)
   - Intelligent project planning
   - Task dependency management
   - Progress tracking

3. **Code Generators** (`generators/`)
   - Web application generator (React, Vue, Angular, Svelte, Next.js)
   - Android application generator
   - iOS application generator
   - Flutter application generator
   - Desktop application generator

4. **Test Generator** (`testing/`)
   - Automatic test generation
   - Unit test templates
   - Integration test templates
   - Framework-specific test configurations

5. **Code Validator** (`validation/`)
   - Syntax validation
   - Structure validation
   - Dependency validation
   - Security checks

6. **Auto Debugger** (`debugger/`)
   - Error detection and analysis
   - Automatic fix generation
   - Code validation

7. **Autonomous Executor** (`executor/`)
   - Orchestrates the entire process
   - Manages task execution
   - Coordinates all modules

## 🧪 Testing & Validation

### Automatic Test Generation

Generate tests automatically for your projects:

```bash
# Generate project with tests
python shakty3n.py create \
  --description "Your project description" \
  --type web-react \
  --with-tests
```

**Supported Test Frameworks:**
- **React/Next.js**: Jest + React Testing Library
- **Vue**: Vitest + Vue Test Utils
- **Flutter**: Flutter Test + Integration Test
- **Angular/Svelte**: Jest

**Generated Tests Include:**
- Unit tests for components
- Integration tests for workflows
- Test configuration files
- Setup instructions in TESTING.md

### Code Validation

Validate your generated code:

```bash
# Generate and validate project
python shakty3n.py create \
  --description "Your project description" \
  --type flutter \
  --validate
```

**Validation Checks:**
- ✓ Project structure validation
- ✓ Required file presence
- ✓ Syntax validation (basic)
- ✓ Dependency consistency
- ✓ Configuration file validity

**Validation Results:**
- Errors: Critical issues that need fixing
- Warnings: Potential problems
- Suggestions: Best practice recommendations

### Sandboxed Test Runs

Create an isolated virtual environment and run Shakty3n's tests without touching your global Python setup:

```bash
# Create .shakty3n_venv, install dependencies, and run tests
python shakty3n.py sandbox --test-command "-m pytest tests/test_basic.py"

# Skip dependency installation if you already installed everything
python shakty3n.py sandbox --skip-install
```

## 🔧 Advanced Usage

### Custom Project Requirements

```python
from shakty3n import AutonomousExecutor, AIProviderFactory, load_env_vars

# Load environment
load_env_vars()

# Create AI provider
ai_provider = AIProviderFactory.create_provider(
    "openai", 
    api_key="your-key",
    model="gpt-4"
)

# Create executor
executor = AutonomousExecutor(ai_provider, output_dir="./output")

# Execute with custom requirements
result = executor.execute_project(
    description="E-commerce platform with payment integration",
    project_type="web-react",
    requirements={
        "features": ["user-auth", "payments", "shopping-cart"],
        "styling": "tailwindcss",
        "database": "firebase"
    }
)

print(f"Success: {result['success']}")
print(f"Output: {result['generation']['output_dir']}")
```

### Using Different AI Models

```python
# Use Claude 3 Opus
ai_provider = AIProviderFactory.create_provider(
    "anthropic",
    api_key="your-key",
    model="claude-3-opus-20240229"
)

# Use Gemini 3.0 Pro
ai_provider = AIProviderFactory.create_provider(
    "google",
    api_key="your-key",
    model="gemini-3.0-pro"
)

# Use Qwen Coder locally (Mac mini friendly)
ai_provider = AIProviderFactory.create_provider(
    "ollama",
    model="qwen3-coder"
)

# Use DeepSeek Coder locally
ai_provider = AIProviderFactory.create_provider(
    "ollama",
    model="deepseek-coder"
)

# Use local Ollama
ai_provider = AIProviderFactory.create_provider(
    "ollama",
    model="codellama"
)
```

## 🤝 How It Works

1. **Planning Phase**
   - Analyzes project description
   - Creates detailed task breakdown
   - Establishes dependencies and order

2. **Execution Phase**
   - Executes tasks autonomously
   - Generates code and structure
   - Tracks progress in real-time

3. **Code Generation Phase**
   - Creates complete project structure
   - Generates all necessary files
   - Sets up dependencies and configuration

4. **Auto-Debugging Phase**
   - Validates generated code
   - Detects and analyzes errors
   - Applies fixes automatically

5. **Completion**
   - Generates documentation
   - Provides usage instructions
   - Reports final status

## 📝 Examples

### Example 1: Todo App (React)
```bash
python shakty3n.py create \
  --description "A todo list with categories, priorities, and due dates" \
  --type web-react \
  --provider openai
```

### Example 2: Fitness Tracker (Android)
```bash
python shakty3n.py create \
  --description "Track workouts, calories, and progress with charts" \
  --type android-kotlin \
  --provider anthropic
```

### Example 3: Note Taking App (iOS)
```bash
python shakty3n.py create \
  --description "Rich text notes with tags and search functionality" \
  --type ios \
  --provider google
```

### Example 4: System Monitor (Desktop)
```bash
python shakty3n.py create \
  --description "Monitor CPU, memory, disk usage with graphs" \
  --type desktop-electron \
  --provider openai
```

## 🔒 Security & Privacy

- API keys are stored locally in `.env` file
- Never commits sensitive data to version control
- Uses secure HTTPS connections for all API calls
- Local execution - your code stays on your machine

## 🛣️ Roadmap

- [x] **Support for more frameworks (Svelte, Next.js, Flutter)** ✅
  - Svelte web framework
  - Next.js web framework  
  - Flutter cross-platform mobile apps
- [x] **Built-in testing and validation** ✅
  - Automatic test generation for all frameworks
  - Code structure validation
  - Dependency validation
- [x] Cloud deployment integration
  - Deployment-ready Dockerfiles and CI templates
  - Guides for Vercel/Netlify/Fly.io style workflows
- [x] Team collaboration features
  - Shareable plans in JSON/Markdown and progress logging
  - Status checkpoints for async reviews
- [x] Custom template support
  - Bring-your-own starter templates per stack
  - Hooks for injecting organization standards
- [x] Plugin system for extensibility
  - Provider/generator/validator hook points
  - Lightweight plugin manifest format
- [ ] Graphical UI for project orchestration
  - Visual flow to plan, launch, and monitor autonomous builds
  - Cross-platform desktop shell for Windows/macOS/Linux
- [ ] Installer generation for iOS apps and Windows desktop builds
  - iOS IPA/TestFlight packaging guidance
  - Windows desktop installers (MSI/EXE) for Electron/Python outputs

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

Built with powerful AI models from:
- OpenAI
- Anthropic
- Google
- Meta (Llama via Ollama)

## 📞 Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Check existing documentation
- Review examples and guides

---

**Shakty3n** - Build anything, autonomously. 🚀
