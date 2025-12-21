"""
Web Application Generator
"""
from typing import Dict, Optional
from .base import CodeGenerator


class WebAppGenerator(CodeGenerator):
    """Generator for web applications (React, Vue, Angular, etc.)"""
    
    def __init__(self, ai_provider, output_dir: str, framework: str = "react", generate_tests: bool = False):
        super().__init__(ai_provider, output_dir)
        self.framework = framework.lower()
        self.generate_tests = generate_tests
    
    def generate_project(self, description: str, requirements: Dict) -> Dict:
        """Generate a web application project"""
        
        # Generate project structure
        structure = self._generate_structure()
        
        # Generate package.json
        package_json = self._generate_package_json(description, requirements)
        self.create_file("package.json", package_json)
        
        # Generate main files based on framework
        if self.framework == "react":
            self._generate_react_project(description, requirements)
        elif self.framework == "vue":
            self._generate_vue_project(description, requirements)
        elif self.framework == "angular":
            self._generate_angular_project(description, requirements)
        elif self.framework == "svelte":
            self._generate_svelte_project(description, requirements)
        elif self.framework in ["nextjs", "next"]:
            self._generate_nextjs_project(description, requirements)
        else:
            self._generate_react_project(description, requirements)
        
        # Generate README
        readme = self._generate_readme(description)
        self.create_file("README.md", readme)
        
        # Generate tests if requested
        if self.generate_tests:
            self._generate_tests(description)
        
        return {
            "framework": self.framework,
            "files": self.generated_files,
            "structure": structure,
            "tests_generated": self.generate_tests
        }
    
    def _generate_structure(self) -> Dict:
        """Create project directory structure"""
        dirs = [
            "src",
            "src/components",
            "src/styles",
            "src/utils",
            "src/services",
            "public"
        ]
        
        for dir_path in dirs:
            self.create_directory(dir_path)
        
        return {"directories": dirs}
    
    def _generate_package_json(self, description: str, requirements: Dict) -> str:
        """Generate package.json"""
        prompt = f"""Generate a package.json file for a {self.framework} web application.

Project Description: {description}
Requirements: {requirements}

Include all necessary dependencies and scripts for development and production.
Return only the JSON content, no explanations."""

        system_prompt = "You are an expert web developer. Generate valid package.json files."
        
        response = self.ai_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3
        )
        
        # Extract JSON content
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            return response[start:end].strip()
        
        return response.strip()
    
    def _generate_react_project(self, description: str, requirements: Dict):
        """Generate React project files"""
        # Generate App.js
        app_js = self._generate_component("App", description, requirements, is_main=True)
        self.create_file("src/App.js", app_js)
        
        # Generate index.js
        index_js = """import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
        self.create_file("src/index.js", index_js)
        
        # Generate basic CSS
        css = """* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
"""
        self.create_file("src/styles/index.css", css)
        
        # Generate index.html
        html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Web application" />
    <title>React App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
"""
        self.create_file("public/index.html", html)
    
    def _generate_vue_project(self, description: str, requirements: Dict):
        """Generate Vue project files"""
        # Generate App.vue
        app_vue = """<template>
  <div id="app">
    <h1>{{ title }}</h1>
    <!-- Your app content here -->
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      title: 'Vue Application'
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
"""
        self.create_file("src/App.vue", app_vue)
        
        # Generate main.js
        main_js = """import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
"""
        self.create_file("src/main.js", main_js)
    
    def _generate_angular_project(self, description: str, requirements: Dict):
        """Generate Angular project files"""
        # This would be expanded with full Angular structure
        app_component = """import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'angular-app';
}
"""
        self.create_file("src/app/app.component.ts", app_component)
    
    def _generate_svelte_project(self, description: str, requirements: Dict):
        """Generate Svelte project files"""
        # Generate App.svelte
        app_svelte = """<script>
  let title = 'Svelte Application';
</script>

<main>
  <h1>{title}</h1>
  <!-- Your app content here -->
</main>

<style>
  main {
    text-align: center;
    padding: 1em;
    max-width: 240px;
    margin: 0 auto;
  }

  h1 {
    color: #ff3e00;
    text-transform: uppercase;
    font-size: 4em;
    font-weight: 100;
  }

  @media (min-width: 640px) {
    main {
      max-width: none;
    }
  }
</style>
"""
        self.create_file("src/App.svelte", app_svelte)
        
        # Generate main.js
        main_js = """import App from './App.svelte';

const app = new App({
  target: document.body,
  props: {}
});

export default app;
"""
        self.create_file("src/main.js", main_js)
        
        # Generate index.html
        html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>Svelte App</title>
    <link rel='stylesheet' href='/build/bundle.css'>
    <script defer src='/build/bundle.js'></script>
  </head>
  <body>
  </body>
</html>
"""
        self.create_file("public/index.html", html)
    
    def _generate_nextjs_project(self, description: str, requirements: Dict):
        """Generate Next.js project files"""
        # Generate pages/_app.js
        app_js = """import '../styles/globals.css'

function MyApp({ Component, pageProps }) {
  return <Component {...pageProps} />
}

export default MyApp
"""
        self_dirs = ["pages", "pages/api", "styles", "public"]
        for dir_path in self_dirs:
            self.create_directory(dir_path)
        
        self.create_file("pages/_app.js", app_js)
        
        # Generate pages/index.js
        index_js = """import Head from 'next/head'
import styles from '../styles/Home.module.css'

export default function Home() {
  return (
    <div className={styles.container}>
      <Head>
        <title>Next.js App</title>
        <meta name="description" content="Generated by Shakty3n" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>
          Welcome to Next.js!
        </h1>
        <p className={styles.description}>
          Get started by editing <code>pages/index.js</code>
        </p>
      </main>
    </div>
  )
}
"""
        self.create_file("pages/index.js", index_js)
        
        # Generate API route example
        hello_api = """export default function handler(req, res) {
  res.status(200).json({ name: 'John Doe' })
}
"""
        self.create_file("pages/api/hello.js", hello_api)
        
        # Generate styles
        globals_css = """html,
body {
  padding: 0;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen,
    Ubuntu, Cantarell, Fira Sans, Droid Sans, Helvetica Neue, sans-serif;
}

a {
  color: inherit;
  text-decoration: none;
}

* {
  box-sizing: border-box;
}
"""
        self.create_file("styles/globals.css", globals_css)
        
        home_module_css = """.container {
  padding: 0 2rem;
}

.main {
  min-height: 100vh;
  padding: 4rem 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.title {
  margin: 0;
  line-height: 1.15;
  font-size: 4rem;
}

.description {
  margin: 4rem 0;
  line-height: 1.5;
  font-size: 1.5rem;
}
"""
        self.create_file("styles/Home.module.css", home_module_css)
    
    def _generate_component(self, name: str, description: str, 
                           requirements: Dict, is_main: bool = False) -> str:
        """Generate a React component using AI"""
        prompt = f"""Generate a React component named {name}.

Project Description: {description}
Requirements: {requirements}
Main Component: {is_main}

Generate a complete, functional React component with modern best practices.
Include necessary imports, state management, and JSX.
Return only the JavaScript code, no explanations."""

        system_prompt = "You are an expert React developer. Generate clean, modern React components."
        
        response = self.ai_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4
        )
        
        # Extract code content
        if "```javascript" in response or "```jsx" in response:
            start = response.find("```") + 3
            if response[start:start+10].startswith("javascript") or response[start:start+3].startswith("jsx"):
                start = response.find("\n", start) + 1
            end = response.find("```", start)
            return response[start:end].strip()
        
        return response.strip()
    
    def _generate_readme(self, description: str) -> str:
        """Generate README.md"""
        return f"""# Web Application

{description}

## Framework
{self.framework.capitalize()}

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

## Features

- Modern {self.framework.capitalize()} application
- Responsive design
- Ready for deployment

## Generated by Shakty3n
Autonomous Agentic Coder
"""
    
    def _generate_tests(self, description: str):
        """Generate test files for the project"""
        from ..testing import TestGenerator
        
        # Create test generator
        test_gen = TestGenerator(self.framework)
        
        # Generate tests for main components
        components = ['App']  # Could be expanded based on generated components
        tests = test_gen.generate_tests(components, description)
        
        # Create test directory
        test_dir = "src/__tests__" if self.framework in ["react", "nextjs"] else "tests"
        self.create_directory(test_dir)
        
        # Write test files
        for test_file, test_content in tests.items():
            file_path = f"{test_dir}/{test_file}"
            self.create_file(file_path, test_content)
        
        # Create setupTests.js for React
        if self.framework in ["react", "nextjs"]:
            setup_tests = """import '@testing-library/jest-dom';
"""
            self.create_file("src/setupTests.js", setup_tests)
        
        # Add test instructions to a separate file
        test_instructions = test_gen.get_setup_instructions()
        self.create_file("TESTING.md", test_instructions)
