# Quick Start Guide - Shakty3n

Get started with Shakty3n in 5 minutes!

## Step 1: Installation

```bash
# Clone the repository
git clone https://github.com/swarupb004/shakty3n.git
cd shakty3n

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure API Keys

You need at least one AI provider API key. Choose one:

### Option A: Interactive Configuration (Recommended)
```bash
python shakty3n.py configure
```

### Option B: Manual Configuration
Create a `.env` file in the project root:

```env
# For OpenAI
OPENAI_API_KEY=sk-your-key-here
DEFAULT_AI_PROVIDER=openai
DEFAULT_MODEL=gpt-4

# OR for Anthropic
ANTHROPIC_API_KEY=your-key-here
DEFAULT_AI_PROVIDER=anthropic
DEFAULT_MODEL=claude-3-opus-20240229

# OR for Google
GOOGLE_API_KEY=your-key-here
DEFAULT_AI_PROVIDER=google
DEFAULT_MODEL=gemini-3.0-pro
```

### Option C: Use Local Models (No API Key Required)
Install Ollama first: https://ollama.ai

```bash
# Pull a model (Mac mini m4 16GB friendly options)
ollama pull qwen3-coder   # or qwen2.5-coder:7b
ollama pull deepseek-coder

# Then use it with Shakty3n
DEFAULT_AI_PROVIDER=ollama
DEFAULT_MODEL=qwen3-coder
```

## Step 3: Test Connection

```bash
python shakty3n.py test --provider openai
```

If successful, you'll see:
```
✓ Connection successful!
Response: Hello from Shakty3n!...
```

## Step 4: Create Your First Project

### Interactive Mode (Easiest)
```bash
python shakty3n.py create --interactive
```

Follow the prompts:
1. What do you want to build?
2. Select project type (Web/Android/iOS/Desktop)
3. Select AI provider

### Command Line Mode
```bash
# Example: Create a todo app
python shakty3n.py create \
  --description "A todo list with categories and priorities" \
  --type web-react \
  --provider openai
```

## Step 5: Create Projects

### Option A: Web UI (Recommended)

Start the web interface for a visual experience:

```bash
# Start the API server
python shakty3n.py serve

# In another terminal, start the web UI
cd platform_web
npm install
npm run dev
```

Then open http://localhost:3000 and:
1. Click "New Project"
2. Fill in the project description
3. Select project type and AI provider
4. Click "Create Project"
5. Watch real-time logs and download when complete

**Or use Docker Compose:**
```bash
docker-compose up
```
Then open http://localhost:3000

### Option B: Command Line

#### Interactive Mode (Easiest)
```bash
python shakty3n.py create --interactive
```

Follow the prompts:
1. What do you want to build?
2. Select project type (Web/Android/iOS/Desktop)
3. Select AI provider

#### Command Line Mode
```bash
# Example: Create a todo app
python shakty3n.py create \
  --description "A todo list with categories and priorities" \
  --type web-react \
  --provider openai
```

## Step 6: View Your Generated Project

After creation completes:

```bash
# The output will show you the location
cd generated_projects/project

# For web apps:
npm install
npm start

# For Android apps:
# Open in Android Studio

# For iOS apps:
# Open in Xcode

# For desktop apps:
npm install
npm start
```

### Optional: Run tests in an isolated virtual environment

```bash
# Creates .shakty3n_venv, installs deps, and runs tests/test_basic.py
python shakty3n.py sandbox --test-command "-m pytest tests/test_basic.py"
```

## Common Use Cases

### Create a React Web App
```bash
python shakty3n.py create \
  --description "E-commerce store with shopping cart" \
  --type web-react
```

### Create an Android App
```bash
python shakty3n.py create \
  --description "Fitness tracker with workout logging" \
  --type android-kotlin
```

### Create an iOS App
```bash
python shakty3n.py create \
  --description "Expense tracker with charts" \
  --type ios
```

### Create a Desktop App
```bash
python shakty3n.py create \
  --description "Note-taking app with markdown support" \
  --type desktop-electron
```

## Next Steps

1. **Explore Examples**: Check the `examples/` directory for more detailed usage
2. **Read Documentation**: See full README.md for advanced features
3. **Customize**: Modify generated code to fit your exact needs
4. **Deploy**: Use the generated code as a foundation for production apps

## Troubleshooting

### "No API key found"
- Make sure you created a `.env` file or ran `configure`
- Check that your API key is valid
- Try `python shakty3n.py test` to verify connection

### "Import errors"
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

### "Generation failed"
- Check your internet connection (for cloud AI providers)
- Try a different AI provider
- Simplify your project description
- Check API quota/limits

## Getting Help

- Run `python shakty3n.py --help` for all commands
- Check `examples/` for working code samples
- Read the main README.md for detailed documentation
- Open an issue on GitHub for bugs or questions

## Tips for Best Results

1. **Be Specific**: Detailed descriptions get better results
   - ❌ "Make a web app"
   - ✅ "Create a todo list with user auth, categories, and priority levels"

2. **Start Simple**: Build core features first, add complexity later

3. **Try Different Providers**: Each AI has different strengths
   - GPT-4: Great for complex logic
   - Claude: Excellent for detailed planning
   - Gemini: Good for creative solutions

4. **Iterate**: Generated code is a starting point - customize it!

---

**You're ready to build! 🚀**

Start creating amazing applications autonomously with Shakty3n.
