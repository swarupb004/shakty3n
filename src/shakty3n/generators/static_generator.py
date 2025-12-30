"""
Static HTML/CSS Generator for simple web pages
"""
from typing import Dict
from .base import CodeGenerator


class StaticHTMLGenerator(CodeGenerator):
    """Generator for simple static HTML/CSS pages without frameworks"""
    
    def __init__(self, ai_provider, output_dir: str):
        super().__init__(ai_provider, output_dir)
    
    def generate_project(self, description: str, requirements: Dict) -> Dict:
        """Generate a simple static HTML project"""
        
        # Generate the HTML content using AI
        html_content = self._generate_html(description, requirements)
        self.create_file("index.html", html_content)
        
        # Only generate CSS if styling is needed
        if self._needs_styling(description):
            css_content = self._generate_css(description, requirements)
            self.create_file("styles.css", css_content)
        
        return {
            "type": "static",
            "files": self.generated_files,
            "tests_generated": False
        }
    
    def _generate_html(self, description: str, requirements: Dict) -> str:
        """Generate HTML content using AI"""
        system_prompt = """You are an expert web developer.
Generate clean, semantic HTML5 code based on the user's description.
Keep it simple and minimal - only include what is necessary.
If the request is for a simple page, create a simple page.
Do NOT add unnecessary JavaScript, complex structures, or frameworks.
Return ONLY the HTML code, no explanations."""

        prompt = f"""Create a simple HTML5 page for:

Description: {description}

Requirements:
{self._format_requirements(requirements)}

Generate a minimal, clean HTML5 file that fulfills the request.
If styling is needed, link to 'styles.css'.
Keep it simple - don't over-engineer."""

        try:
            response = self.ai_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )
            return self._extract_code(response, "html")
        except Exception as e:
            # Fallback to basic HTML
            return self._fallback_html(description)
    
    def _generate_css(self, description: str, requirements: Dict) -> str:
        """Generate CSS content using AI"""
        system_prompt = """You are an expert web developer.
Generate clean, minimal CSS based on the user's description.
Keep it simple - only include what is necessary for the styling.
Return ONLY the CSS code, no explanations."""

        prompt = f"""Create minimal CSS for:

Description: {description}

Generate clean, simple CSS. Don't over-engineer."""

        try:
            response = self.ai_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )
            return self._extract_code(response, "css")
        except Exception:
            return "/* Basic styles */\nbody { font-family: sans-serif; margin: 20px; }"
    
    def _needs_styling(self, description: str) -> bool:
        """Check if the request likely needs CSS"""
        styling_keywords = ["style", "design", "beautiful", "modern", "theme", "color", "layout"]
        description_lower = description.lower()
        return any(kw in description_lower for kw in styling_keywords)
    
    def _format_requirements(self, requirements: Dict) -> str:
        """Format requirements dict as string"""
        if not requirements:
            return "None specified"
        return "\n".join(f"- {k}: {v}" for k, v in requirements.items())
    
    def _extract_code(self, response: str, lang: str) -> str:
        """Extract code from AI response, removing markdown fences"""
        lines = response.strip().split('\n')
        
        # Remove markdown code fences if present
        if lines and lines[0].strip().startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        
        return '\n'.join(lines)
    
    def _fallback_html(self, description: str) -> str:
        """Generate fallback HTML if AI fails"""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{description[:50]}</title>
</head>
<body>
    <h1>Hello World</h1>
    <p>{description}</p>
</body>
</html>'''
