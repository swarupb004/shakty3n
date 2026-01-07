"""
Completion Verifier for Autonomous Execution

Verifies that all requested features are actually built and generates
tasks for any missing features to ensure true completion.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import os
import re
import logging
import textwrap
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of verifying project completion"""
    all_complete: bool
    verified_features: List[str] = field(default_factory=list)
    missing_features: List[str] = field(default_factory=list)
    confidence: float = 0.0
    file_evidence: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class GeneratedTask:
    """A task generated for a missing feature"""
    title: str
    description: str
    dependencies: List[int] = field(default_factory=list)


class CompletionVerifier:
    """
    Verifies all requested features are implemented.
    
    Capabilities:
    1. Extract expected features from plan
    2. Verify features exist in output files
    3. Generate tasks for missing features
    """

    def __init__(self, ai_provider=None):
        """
        Initialize the completion verifier.
        
        Args:
            ai_provider: Optional AI provider for smart feature detection
        """
        self.ai_provider = ai_provider
        self.verification_history: List[VerificationResult] = []

    def extract_expected_features(
        self, 
        plan_output: Dict[str, Any]
    ) -> List[str]:
        """
        Extract what should be built from the plan.
        
        Args:
            plan_output: The PlanningOutput as a dict
            
        Returns:
            List of expected features/capabilities
        """
        features = []
        
        # Extract from problem understanding
        problem = plan_output.get("problem_understanding", {})
        if problem.get("primary_goal"):
            features.append(problem["primary_goal"])
        features.extend(problem.get("secondary_goals", []))
        
        # Extract from functional requirements
        requirements = plan_output.get("requirements", {})
        features.extend(requirements.get("functional", []))
        
        # Extract from task breakdown
        tasks = plan_output.get("task_breakdown", [])
        for task in tasks:
            if isinstance(task, dict):
                title = task.get("title", "")
                if title and "initialize" not in title.lower() and "setup" not in title.lower():
                    features.append(title)
        
        # Deduplicate while preserving order
        seen = set()
        unique_features = []
        for f in features:
            f_lower = f.lower() if isinstance(f, str) else str(f)
            if f_lower not in seen:
                seen.add(f_lower)
                unique_features.append(f)
        
        return unique_features

    def verify_features_exist(
        self, 
        features: List[str], 
        output_dir: str,
        file_extensions: Optional[List[str]] = None
    ) -> VerificationResult:
        """
        Check if features actually exist in output.
        
        Args:
            features: List of expected features
            output_dir: Directory to scan for generated files
            file_extensions: Optional list of extensions to check (default: common code files)
            
        Returns:
            VerificationResult with verified and missing features
        """
        if file_extensions is None:
            file_extensions = [
                '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css',
                '.java', '.kt', '.swift', '.dart', '.vue', '.svelte'
            ]
        
        # Collect all relevant files and their content
        file_contents: Dict[str, str] = {}
        output_path = Path(output_dir)
        
        if output_path.exists():
            for ext in file_extensions:
                for file_path in output_path.rglob(f"*{ext}"):
                    # Skip node_modules and similar
                    if any(skip in str(file_path) for skip in ['node_modules', '__pycache__', '.git', 'venv']):
                        continue
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        rel_path = str(file_path.relative_to(output_path))
                        file_contents[rel_path] = content
                    except Exception as e:
                        logger.warning("Failed to read %s: %s", file_path, e)
        
        verified = []
        missing = []
        evidence: Dict[str, List[str]] = {}
        
        for feature in features:
            if self._feature_exists_in_files(feature, file_contents, evidence):
                verified.append(feature)
            else:
                missing.append(feature)
        
        # Calculate confidence based on verification
        if not features:
            confidence = 1.0
        else:
            confidence = len(verified) / len(features)
        
        result = VerificationResult(
            all_complete=len(missing) == 0,
            verified_features=verified,
            missing_features=missing,
            confidence=confidence,
            file_evidence=evidence
        )
        
        self.verification_history.append(result)
        return result

    def _feature_exists_in_files(
        self, 
        feature: str, 
        file_contents: Dict[str, str],
        evidence: Dict[str, List[str]]
    ) -> bool:
        """
        Check if a feature is implemented in any file.
        
        Uses keyword matching and pattern detection.
        """
        # Extract keywords from feature description
        keywords = self._extract_keywords(feature)
        
        for file_path, content in file_contents.items():
            content_lower = content.lower()
            
            # Check if enough keywords are present
            matches = sum(1 for kw in keywords if kw.lower() in content_lower)
            
            if matches >= len(keywords) * 0.5:  # At least 50% keyword match
                if feature not in evidence:
                    evidence[feature] = []
                evidence[feature].append(file_path)
                return True
        
        # Also check file names
        feature_words = set(self._extract_keywords(feature))
        for file_path in file_contents.keys():
            file_name = Path(file_path).stem.lower()
            file_words = set(re.split(r'[_\-.]', file_name))
            
            if feature_words & file_words:  # Intersection
                if feature not in evidence:
                    evidence[feature] = []
                evidence[feature].append(file_path)
                return True
        
        return False

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
            'from', 'up', 'about', 'into', 'over', 'after', 'and', 'or',
            'but', 'if', 'then', 'else', 'when', 'where', 'why', 'how',
            'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'just', 'create', 'implement',
            'add', 'build', 'make', 'user', 'system', 'feature'
        }
        
        # Split into words
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Filter stop words and short words
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords

    def generate_missing_tasks(
        self, 
        missing_features: List[str],
        next_task_id: int = 1
    ) -> List[GeneratedTask]:
        """
        Create tasks for any missing features.
        
        Args:
            missing_features: Features that weren't found
            next_task_id: Starting ID for new tasks
            
        Returns:
            List of GeneratedTask objects
        """
        tasks = []
        
        for i, feature in enumerate(missing_features):
            task = GeneratedTask(
                title=f"Implement: {feature[:50]}",
                description=textwrap.dedent(
                    f"""
                    This feature was not found in the generated code.

                    Feature: {feature}

                    Please implement this feature completely:
                    1. Create necessary files
                    2. Write working code (not placeholders)
                    3. Ensure it integrates with existing code
                    4. Test that it works
                    """
                ).strip(),
                dependencies=[next_task_id + i - 1] if i > 0 else []
            )
            tasks.append(task)
        
        return tasks

    def get_completion_summary(self) -> str:
        """Get summary of completion verification"""
        if not self.verification_history:
            return "No verification performed yet"
        
        latest = self.verification_history[-1]
        lines = [
            f"Completion: {latest.confidence * 100:.0f}%",
            f"Verified: {len(latest.verified_features)} features",
            f"Missing: {len(latest.missing_features)} features",
        ]
        
        if latest.missing_features:
            lines.append("Missing features:")
            for f in latest.missing_features[:5]:
                lines.append(f"  - {f[:50]}")
        
        return "\n".join(lines)


__all__ = [
    "CompletionVerifier",
    "VerificationResult",
    "GeneratedTask",
]
