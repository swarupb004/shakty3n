"""
Reflexion Module for Autonomous Self-Correction

Implements self-critique and iterative refinement for autonomous agents.
When an LLM response fails or is unclear, this module:
1. Analyzes what went wrong
2. Generates a critique
3. Elaborates the query with failure context
4. Enables retry with enhanced understanding
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of evaluating an LLM response"""
    is_valid: bool
    confidence: float  # 0.0 to 1.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ReflectionResult:
    """Result of self-reflection on a failure"""
    critique: str
    failure_reason: str
    elaborated_query: str
    should_retry: bool
    retry_strategy: str  # "same", "simpler", "different_approach"


class ReflexionAgent:
    """
    Self-correcting agent with reflection capability.
    
    Implements the Reflexion pattern:
    1. Evaluate response quality
    2. Generate self-critique on failures
    3. Elaborate queries with failure context
    4. Retry with enhanced understanding
    """

    def __init__(self, ai_provider, max_retries: int = 3):
        """
        Initialize the Reflexion agent.
        
        Args:
            ai_provider: AI provider for generating reflections
            max_retries: Maximum retry attempts per task
        """
        self.ai_provider = ai_provider
        self.max_retries = max_retries
        self.reflection_history: List[ReflectionResult] = []

    def evaluate_response(
        self, 
        response: str, 
        expected_format: Optional[Dict[str, Any]] = None,
        task_description: str = ""
    ) -> EvaluationResult:
        """
        Check if LLM response meets expectations.
        
        Args:
            response: The LLM's response text
            expected_format: Optional dict describing expected structure
            task_description: What the task was trying to accomplish
            
        Returns:
            EvaluationResult with validity, confidence, and issues
        """
        issues = []
        suggestions = []
        confidence = 1.0
        
        # Check for empty or very short responses
        if not response or len(response.strip()) < 10:
            issues.append("Response is empty or too short")
            confidence = 0.0
            return EvaluationResult(False, confidence, issues, ["Retry with clearer prompt"])
        
        # Check for confusion indicators
        confusion_patterns = [
            r"i('m| am) not sure",
            r"could you (clarify|explain)",
            r"i don't understand",
            r"what do you mean",
            r"can you (provide|give) more",
            r"it's unclear",
            r"i need more (information|context|details)",
        ]
        
        for pattern in confusion_patterns:
            if re.search(pattern, response.lower()):
                issues.append(f"LLM appears confused: '{pattern}'")
                confidence -= 0.3
                suggestions.append("Provide more context in the query")
        
        # Check for hedging language
        hedging_patterns = [
            r"i think",
            r"maybe",
            r"perhaps",
            r"probably",
            r"might be",
            r"possibly",
        ]
        
        hedging_count = sum(1 for p in hedging_patterns if re.search(p, response.lower()))
        if hedging_count > 2:
            issues.append("Response contains excessive hedging")
            confidence -= 0.2
        
        # Check for expected JSON format if specified
        if expected_format and "json" in str(expected_format).lower():
            try:
                # Try to extract and parse JSON
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    json.loads(json_match.group())
                else:
                    issues.append("Expected JSON but none found")
                    confidence -= 0.4
            except json.JSONDecodeError:
                issues.append("Invalid JSON structure")
                confidence -= 0.4
        
        # Check for error indicators in response
        error_patterns = [
            r"error:",
            r"exception:",
            r"failed to",
            r"unable to",
            r"cannot",
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, response.lower()):
                issues.append(f"Response indicates error: '{pattern}'")
                confidence -= 0.2
        
        # Clamp confidence
        confidence = max(0.0, min(1.0, confidence))
        
        is_valid = confidence >= 0.5 and not any("confused" in i for i in issues)
        
        return EvaluationResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions
        )

    def generate_critique(
        self, 
        response: str, 
        task: str, 
        error: Optional[str] = None
    ) -> str:
        """
        Self-critique: What went wrong and why?
        
        Args:
            response: The LLM's response that failed
            task: What the task was trying to accomplish
            error: Optional error message from execution
            
        Returns:
            A critique explaining what went wrong
        """
        prompt = f"""You are a self-reflective AI analyzing why a task failed.

TASK: {task}

RESPONSE THAT FAILED:
{response[:500]}...

ERROR (if any): {error or 'No explicit error, but response was inadequate'}

Analyze what went wrong. Be specific and concise. Format:
1. What was attempted
2. Why it failed
3. What should be done differently

Keep your analysis under 100 words."""

        try:
            critique = self.ai_provider.generate(
                prompt=prompt,
                system_prompt="You are a code review assistant that analyzes failures concisely.",
                temperature=0.3
            )
            return critique.strip() if isinstance(critique, str) else str(critique)
        except Exception as e:
            logger.error("Failed to generate critique: %s", e)
            return f"Failed to analyze: {error or 'Response was inadequate'}"

    def elaborate_query(
        self, 
        original_query: str, 
        context: str, 
        failure_reason: str
    ) -> str:
        """
        Create more detailed query when original wasn't understood.
        
        Args:
            original_query: The original task/query that failed
            context: Project context
            failure_reason: Why the previous attempt failed
            
        Returns:
            Elaborated query with more details
        """
        prompt = f"""The following query failed because the AI didn't understand it properly.

ORIGINAL QUERY: {original_query}

CONTEXT: {context[:300]}

WHY IT FAILED: {failure_reason}

Rewrite this query to be clearer and more specific. Add:
1. Explicit step-by-step instructions
2. Expected output format
3. Any missing context

Output ONLY the improved query, nothing else."""

        try:
            elaborated = self.ai_provider.generate(
                prompt=prompt,
                system_prompt="You are a prompt engineer who makes queries clearer.",
                temperature=0.4
            )
            return elaborated.strip() if isinstance(elaborated, str) else original_query
        except Exception as e:
            logger.error("Failed to elaborate query: %s", e)
            # Fallback: add basic context
            return f"{original_query}\n\nBe specific and provide complete code. Previous attempt failed because: {failure_reason}"

    def reflect_and_decide(
        self, 
        task: str, 
        response: str, 
        error: Optional[str] = None,
        attempt_number: int = 1
    ) -> ReflectionResult:
        """
        Full reflection cycle: evaluate, critique, decide next action.
        
        Args:
            task: The task description
            response: The LLM's response
            error: Optional error message
            attempt_number: Current attempt number
            
        Returns:
            ReflectionResult with critique, elaborated query, and strategy
        """
        # Evaluate the response
        evaluation = self.evaluate_response(response, task_description=task)
        
        # If response is valid, no reflection needed
        if evaluation.is_valid and evaluation.confidence >= 0.7:
            return ReflectionResult(
                critique="Response appears valid",
                failure_reason="",
                elaborated_query=task,
                should_retry=False,
                retry_strategy="none"
            )
        
        # Generate critique
        critique = self.generate_critique(response, task, error)
        
        # Determine failure reason
        if evaluation.issues:
            failure_reason = "; ".join(evaluation.issues)
        else:
            failure_reason = error or "Response did not meet expectations"
        
        # Decide retry strategy
        if attempt_number >= self.max_retries:
            retry_strategy = "give_up"
            should_retry = False
        elif "confused" in failure_reason.lower() or "unclear" in failure_reason.lower():
            retry_strategy = "elaborate"
            should_retry = True
        elif evaluation.confidence < 0.3:
            retry_strategy = "simpler"
            should_retry = True
        else:
            retry_strategy = "same"
            should_retry = True
        
        # Elaborate query for retry
        if should_retry:
            elaborated_query = self.elaborate_query(task, "", failure_reason)
        else:
            elaborated_query = task
        
        result = ReflectionResult(
            critique=critique,
            failure_reason=failure_reason,
            elaborated_query=elaborated_query,
            should_retry=should_retry,
            retry_strategy=retry_strategy
        )
        
        self.reflection_history.append(result)
        return result

    def get_reflection_summary(self) -> str:
        """Get summary of all reflections for debugging"""
        if not self.reflection_history:
            return "No reflections recorded"
        
        lines = [f"Total reflections: {len(self.reflection_history)}"]
        for i, r in enumerate(self.reflection_history[-5:], 1):  # Last 5
            lines.append(f"{i}. Strategy: {r.retry_strategy}, Retry: {r.should_retry}")
        
        return "\n".join(lines)


__all__ = [
    "ReflexionAgent",
    "EvaluationResult",
    "ReflectionResult",
]
