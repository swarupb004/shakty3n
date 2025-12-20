# Contributing to Shakty3n

Thank you for your interest in contributing to Shakty3n! This document provides guidelines and information for contributors.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, etc.)
- Relevant logs or error messages

### Suggesting Features

Feature suggestions are welcome! Please:
- Check existing issues first to avoid duplicates
- Describe the feature clearly
- Explain the use case and benefits
- Consider how it fits with existing features

### Code Contributions

1. **Fork the repository**
2. **Create a branch** for your feature or fix
3. **Make your changes** following our coding standards
4. **Test your changes** thoroughly
5. **Submit a pull request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/shakty3n.git
cd shakty3n

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Coding Standards

### Python Style
- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and concise

### Code Organization
- Place new AI providers in `src/shakty3n/ai_providers/`
- Add generators in `src/shakty3n/generators/`
- Keep utility functions in `src/shakty3n/utils/`

### Documentation
- Update README.md for user-facing changes
- Add docstrings for all public APIs
- Include examples for new features
- Update QUICKSTART.md if relevant

## Testing

Currently, manual testing is required:

```bash
# Test CLI
python shakty3n.py --help
python shakty3n.py info
python shakty3n.py test

# Test imports
python -c "from shakty3n import AIProviderFactory"

# Run examples
python examples/test_providers.py
```

## Adding New Features

### Adding a New AI Provider

1. Create a new file in `src/shakty3n/ai_providers/`
2. Implement the `AIProvider` interface
3. Add to the factory in `__init__.py`
4. Update documentation

Example:
```python
from .base import AIProvider

class NewProvider(AIProvider):
    def generate(self, prompt, system_prompt=None, **kwargs):
        # Implementation
        pass
```

### Adding a New Generator

1. Create a new file in `src/shakty3n/generators/`
2. Inherit from `CodeGenerator`
3. Implement `generate_project()` method
4. Update the executor to support the new type

### Adding New Commands

1. Add a new command function in `shakty3n.py`
2. Use Click decorators for options
3. Update help text
4. Test thoroughly

## Pull Request Process

1. **Update documentation** for any user-facing changes
2. **Test your changes** across different scenarios
3. **Keep PRs focused** - one feature/fix per PR
4. **Write clear commit messages**
5. **Respond to feedback** during code review

## Commit Message Format

```
<type>: <subject>

<body>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Example:
```
feat: Add support for Flutter mobile apps

- Implement Flutter generator
- Add Flutter-specific templates
- Update documentation
```

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion on GitHub
- Check existing documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain a welcoming environment

Thank you for contributing to Shakty3n! 🎉
