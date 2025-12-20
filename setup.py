"""
Setup script for Shakty3n
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="shakty3n",
    version="1.0.0",
    author="Shakty3n Team",
    description="Autonomous Agentic Coder for building applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/swarupb004/shakty3n",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        "google-generativeai>=0.3.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "colorama>=0.4.6",
        "rich>=13.0.0",
        "pyyaml>=6.0.0",
        "gitpython>=3.1.40",
        "jinja2>=3.1.0",
    ],
    entry_points={
        "console_scripts": [
            "shakty3n=shakty3n:cli",
        ],
    },
)
