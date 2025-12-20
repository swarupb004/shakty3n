"""
Desktop Application Generator
"""
from typing import Dict
from .base import CodeGenerator


class DesktopAppGenerator(CodeGenerator):
    """Generator for desktop applications (Electron, Python, etc.)"""
    
    def __init__(self, ai_provider, output_dir: str, platform: str = "electron"):
        super().__init__(ai_provider, output_dir)
        self.platform = platform.lower()
    
    def generate_project(self, description: str, requirements: Dict) -> Dict:
        """Generate a desktop application project"""
        
        if self.platform == "electron":
            return self._generate_electron_project(description, requirements)
        elif self.platform == "python":
            return self._generate_python_project(description, requirements)
        else:
            return self._generate_electron_project(description, requirements)
    
    def _generate_electron_project(self, description: str, requirements: Dict) -> Dict:
        """Generate Electron project"""
        structure = self._generate_electron_structure()
        
        # Generate package.json
        package_json = """{
  "name": "desktop-app",
  "version": "1.0.0",
  "description": "Desktop application built with Electron",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder"
  },
  "keywords": [],
  "author": "",
  "license": "MIT",
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.9.1"
  }
}
"""
        self.create_file("package.json", package_json)
        
        # Generate main.js
        main_js = """const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  win.loadFile('index.html');
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
"""
        self.create_file("main.js", main_js)
        
        # Generate index.html
        index_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Desktop App</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div id="app">
        <h1>Desktop Application</h1>
        <p>Built with Electron</p>
    </div>
    <script src="renderer.js"></script>
</body>
</html>
"""
        self.create_file("index.html", index_html)
        
        # Generate styles.css
        css = """body {
    margin: 0;
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
        'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
}

#app {
    max-width: 1200px;
    margin: 0 auto;
}

h1 {
    color: #333;
}
"""
        self.create_file("styles.css", css)
        
        # Generate renderer.js
        renderer_js = """// Renderer process code
console.log('Electron app loaded');
"""
        self.create_file("renderer.js", renderer_js)
        
        # Generate README
        readme = self._generate_electron_readme(description)
        self.create_file("README.md", readme)
        
        return {
            "platform": "electron",
            "files": self.generated_files,
            "structure": structure
        }
    
    def _generate_python_project(self, description: str, requirements: Dict) -> Dict:
        """Generate Python desktop project (PyQt/Tkinter)"""
        structure = self._generate_python_structure()
        
        # Generate main.py with tkinter
        main_py = """import tkinter as tk
from tkinter import ttk

class DesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Desktop Application")
        self.root.geometry("800x600")
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Desktop Application", 
                               font=('Helvetica', 24, 'bold'))
        title_label.grid(row=0, column=0, pady=20)
        
        # Content area
        content_label = ttk.Label(main_frame, text="Built with Python")
        content_label.grid(row=1, column=0, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopApp(root)
    root.mainloop()
"""
        self.create_file("main.py", main_py)
        
        # Generate requirements.txt
        requirements_txt = """# Python Desktop App Requirements
# Uncomment the UI framework you want to use:

# For PyQt5
# PyQt5>=5.15.0

# For tkinter (usually comes with Python)
# No additional requirements

# For wxPython
# wxPython>=4.2.0
"""
        self.create_file("requirements.txt", requirements_txt)
        
        # Generate README
        readme = self._generate_python_readme(description)
        self.create_file("README.md", readme)
        
        return {
            "platform": "python",
            "files": self.generated_files,
            "structure": structure
        }
    
    def _generate_electron_structure(self) -> Dict:
        """Create Electron project structure"""
        dirs = ["assets", "src"]
        for dir_path in dirs:
            self.create_directory(dir_path)
        return {"directories": dirs}
    
    def _generate_python_structure(self) -> Dict:
        """Create Python project structure"""
        dirs = ["src", "assets", "utils"]
        for dir_path in dirs:
            self.create_directory(dir_path)
        return {"directories": dirs}
    
    def _generate_electron_readme(self, description: str) -> str:
        """Generate README for Electron app"""
        return f"""# Desktop Application (Electron)

{description}

## Platform
Electron (Cross-platform)

## Requirements
- Node.js 18+
- npm or yarn

## Setup

```bash
npm install
```

## Development

```bash
npm start
```

## Build

```bash
npm run build
```

## Generated by Shakty3n
Autonomous Agentic Coder
"""
    
    def _generate_python_readme(self, description: str) -> str:
        """Generate README for Python app"""
        return f"""# Desktop Application (Python)

{description}

## Platform
Python (Cross-platform with tkinter)

## Requirements
- Python 3.8+
- tkinter (usually comes with Python)

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Generated by Shakty3n
Autonomous Agentic Coder
"""
