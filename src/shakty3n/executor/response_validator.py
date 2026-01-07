"""
Response Validator for Autonomous Execution

Validates LLM outputs before accepting them to ensure quality
and detect when the LLM is confused or producing invalid output.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import json
import re
import logging
import ast

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating an LLM response"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    extracted_content: Optional[Any] = None


class ResponseValidator:
    """
    Validates LLM outputs for quality and correctness.
    
    Checks:
    - JSON structure validity
    - Code syntax validity
    - Task completion indicators
    - Confusion detection
    """

    def __init__(self):
        self.validation_history: List[ValidationResult] = []

    def validate_json_response(
        self, 
        response: str,
        required_fields: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Check JSON structure is valid and complete.
        
        Args:
            response: LLM response potentially containing JSON
            required_fields: Optional list of fields that must be present
            
        Returns:
            ValidationResult with extracted JSON if valid
        """
        errors = []
        warnings = []
        extracted = None
        
        # Try to extract JSON from response
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # Markdown code block
            r'```\s*([\s\S]*?)\s*```',       # Generic code block
            r'(\{[\s\S]*\})',                 # Raw JSON object
            r'(\[[\s\S]*\])',                 # Raw JSON array
        ]
        
        json_str = None
        for pattern in json_patterns:
            match = re.search(pattern, response)
            if match:
                json_str = match.group(1).strip()
                break
        
        if not json_str:
            errors.append("No JSON found in response")
            return ValidationResult(False, errors, warnings, None)
        
        # Try to parse JSON
        try:
            extracted = json.loads(json_str)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON syntax: {str(e)[:100]}")
            return ValidationResult(False, errors, warnings, None)
        
        # Check required fields
        if required_fields and isinstance(extracted, dict):
            for field in required_fields:
                if field not in extracted:
                    errors.append(f"Missing required field: {field}")
                elif not extracted[field]:
                    warnings.append(f"Field '{field}' is empty")
        
        is_valid = len(errors) == 0
        result = ValidationResult(is_valid, errors, warnings, extracted)
        self.validation_history.append(result)
        return result

    def validate_code_response(
        self, 
        response: str, 
        language: str = "python"
    ) -> ValidationResult:
        """
        Check code syntax is valid.
        
        Args:
            response: LLM response containing code
            language: Programming language (python, javascript, etc.)
            
        Returns:
            ValidationResult with extracted code if valid
        """
        errors = []
        warnings = []
        
        # Extract code from response
        code_patterns = [
            rf'```{language}\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
        ]
        
        code = None
        for pattern in code_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                code = match.group(1).strip()
                break
        
        if not code:
            # Try to find code without backticks
            lines = response.split('\n')
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
            if code_lines:
                code = '\n'.join(code_lines)
        
        if not code:
            errors.append("No code found in response")
            return ValidationResult(False, errors, warnings, None)
        
        # Validate syntax based on language
        if language.lower() == "python":
            try:
                ast.parse(code)
            except SyntaxError as e:
                errors.append(f"Python syntax error: {e.msg} at line {e.lineno}")
        
        # Basic checks for other languages
        elif language.lower() in ["javascript", "typescript", "js", "ts"]:
            # Check for obvious issues
            if code.count('{') != code.count('}'):
                warnings.append("Mismatched curly braces")
            if code.count('(') != code.count(')'):
                warnings.append("Mismatched parentheses")
        
        is_valid = len(errors) == 0
        result = ValidationResult(is_valid, errors, warnings, code)
        self.validation_history.append(result)
        return result

    def validate_task_completion(
        self, 
        response: str, 
        task_description: str
    ) -> ValidationResult:
        """
        Verify task requirements are addressed in response.
        
        Args:
            response: LLM response
            task_description: What the task was supposed to do
            
        Returns:
            ValidationResult indicating completeness
        """
        errors = []
        warnings = []
        
        # Check for completion indicators
        completion_patterns = [
            r'finish\(\)',
            r'task (complete|done|finished)',
            r'successfully (created|implemented|completed)',
            r'all (requirements|features) (met|implemented)',
        ]
        
        has_completion = any(
            re.search(p, response.lower()) 
            for p in completion_patterns
        )
        
        if not has_completion:
            warnings.append("Response doesn't indicate task completion")
        
        # Check for incomplete indicators
        incomplete_patterns = [
            r'todo:',
            r'not implemented',
            r'placeholder',
            r'# \.\.\.',
            r'pass\s*$',
            r'raise NotImplementedError',
        ]
        
        for pattern in incomplete_patterns:
            if re.search(pattern, response, re.MULTILINE):
                errors.append(f"Response contains incomplete code: '{pattern}'")
        
        is_valid = len(errors) == 0 and has_completion
        return ValidationResult(is_valid, errors, warnings, None)

    def detect_confusion(self, response: str) -> Tuple[bool, List[str]]:
        """
        Detect if LLM is confused (hedging, asking questions).
        
        Args:
            response: LLM response to analyze
            
        Returns:
            Tuple of (is_confused, reasons)
        """
        confusion_indicators = []
        
        # Direct questions back to user
        question_patterns = [
            r'could you (please )?(clarify|explain|tell me|provide)',
            r'what (do you |would you )?prefer',
            r'which (option|approach) (would you|should)',
            r'can you (tell me|provide|give)',
            r'i need (more information|clarification|context)',
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, response.lower()):
                confusion_indicators.append(f"Asking for clarification: '{pattern}'")
        
        # Uncertainty expressions
        uncertainty_patterns = [
            (r"i'?m not (entirely )?sure", "Expressed uncertainty"),
            (r"i don'?t (fully )?understand", "Doesn't understand task"),
            (r"it'?s (unclear|ambiguous)", "Found task unclear"),
            (r"there (are|might be) (multiple|several) (ways|options)", "Can't decide approach"),
        ]
        
        for pattern, reason in uncertainty_patterns:
            if re.search(pattern, response.lower()):
                confusion_indicators.append(reason)
        
        # Multiple alternatives without choosing
        if re.search(r'option\s*[12a]:.*option\s*[23b]:', response.lower()):
            confusion_indicators.append("Presented options instead of choosing")
        
        is_confused = len(confusion_indicators) >= 2
        return is_confused, confusion_indicators

    def validate_response(
        self, 
        response: str,
        expected_type: str = "any"
    ) -> ValidationResult:
        """
        General validation combining all checks.
        
        Args:
            response: LLM response
            expected_type: "json", "code", "text", or "any"
            
        Returns:
            Combined ValidationResult
        """
        errors = []
        warnings = []
        
        # Check for empty response
        if not response or len(response.strip()) < 5:
            return ValidationResult(False, ["Empty or minimal response"], [], None)
        
        # Check for confusion
        is_confused, confusion_reasons = self.detect_confusion(response)
        if is_confused:
            errors.append("LLM appears confused")
            warnings.extend(confusion_reasons)
        
        # Type-specific validation
        if expected_type == "json":
            result = self.validate_json_response(response)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
        elif expected_type == "code":
            result = self.validate_code_response(response)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
        
        is_valid = len(errors) == 0 and not is_confused
        return ValidationResult(is_valid, errors, warnings, None)


__all__ = [
    "ResponseValidator",
    "ValidationResult",
]
