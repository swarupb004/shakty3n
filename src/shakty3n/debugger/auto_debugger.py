"""
Auto Debugger System
"""
from typing import Dict, List, Optional, Tuple
import re
import traceback


class AutoDebugger:
    """Automatic debugging and error fixing system"""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider
        self.error_history = []
        self.fix_attempts = {}
    
    def analyze_error(self, error_message: str, code_context: Optional[str] = None,
                     file_path: Optional[str] = None) -> Dict:
        """Analyze an error and suggest fixes"""
        
        # Parse error message
        error_info = self._parse_error(error_message)
        
        # Add to history
        self.error_history.append({
            "error": error_message,
            "file": file_path,
            "context": code_context
        })
        
        # Generate fix suggestions
        suggestions = self._generate_fix_suggestions(
            error_message, 
            code_context, 
            file_path,
            error_info
        )
        
        return {
            "error_type": error_info.get("type", "Unknown"),
            "error_message": error_message,
            "line_number": error_info.get("line"),
            "suggestions": suggestions,
            "severity": error_info.get("severity", "medium")
        }
    
    def _parse_error(self, error_message: str) -> Dict:
        """Parse error message to extract key information"""
        error_info = {
            "type": "Unknown",
            "severity": "medium",
            "line": None
        }
        
        # Common error patterns
        patterns = {
            "SyntaxError": r"SyntaxError",
            "TypeError": r"TypeError",
            "NameError": r"NameError",
            "ValueError": r"ValueError",
            "AttributeError": r"AttributeError",
            "ImportError": r"ImportError|ModuleNotFoundError",
            "IndentationError": r"IndentationError",
            "KeyError": r"KeyError",
            "IndexError": r"IndexError",
        }
        
        for error_type, pattern in patterns.items():
            if re.search(pattern, error_message):
                error_info["type"] = error_type
                break
        
        # Extract line number
        line_match = re.search(r"line (\d+)", error_message, re.IGNORECASE)
        if line_match:
            error_info["line"] = int(line_match.group(1))
        
        # Determine severity
        if error_info["type"] in ["SyntaxError", "IndentationError"]:
            error_info["severity"] = "high"
        elif error_info["type"] in ["ImportError", "NameError"]:
            error_info["severity"] = "high"
        
        return error_info
    
    def _generate_fix_suggestions(self, error_message: str, code_context: Optional[str],
                                  file_path: Optional[str], error_info: Dict) -> List[Dict]:
        """Generate fix suggestions using AI"""
        
        system_prompt = """You are an expert debugger and code fixer.
Analyze errors and provide clear, actionable fix suggestions.
For each suggestion, provide:
1. A clear description of what's wrong
2. The specific fix to apply
3. The corrected code if applicable

Return suggestions in a structured format."""

        prompt = f"""Analyze this error and provide fix suggestions:

Error Type: {error_info.get('type')}
Error Message: {error_message}
"""
        
        if file_path:
            prompt += f"\nFile: {file_path}"
        
        if code_context:
            prompt += f"\n\nCode Context:\n```\n{code_context}\n```"
        
        prompt += "\n\nProvide 2-3 specific fix suggestions with corrected code where applicable."
        
        try:
            response = self.ai_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            # Parse response into suggestions
            suggestions = self._parse_suggestions(response)
            return suggestions
            
        except Exception as e:
            # Fallback to basic suggestions
            return self._get_basic_suggestions(error_info)
    
    def _parse_suggestions(self, response: str) -> List[Dict]:
        """Parse AI response into structured suggestions"""
        suggestions = []
        
        # Try to extract numbered suggestions
        lines = response.split('\n')
        current_suggestion = None
        
        for line in lines:
            # Check for numbered items (1. 2. 3. etc.)
            if re.match(r'^\d+\.', line.strip()):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                current_suggestion = {
                    "description": line.strip(),
                    "code": None
                }
            elif current_suggestion and ("```" in line or "code" in line.lower()):
                # Look for code blocks
                if "```" in response:
                    start = response.find("```", response.find(current_suggestion["description"]))
                    if start != -1:
                        start = response.find("\n", start) + 1
                        end = response.find("```", start)
                        if end != -1:
                            current_suggestion["code"] = response[start:end].strip()
        
        if current_suggestion:
            suggestions.append(current_suggestion)
        
        # If no suggestions parsed, create one from the whole response
        if not suggestions:
            suggestions.append({
                "description": response.strip(),
                "code": None
            })
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _get_basic_suggestions(self, error_info: Dict) -> List[Dict]:
        """Get basic suggestions based on error type"""
        error_type = error_info.get("type", "Unknown")
        
        suggestions_map = {
            "SyntaxError": [
                {"description": "Check for missing parentheses, brackets, or quotes", "code": None},
                {"description": "Verify proper indentation", "code": None}
            ],
            "ImportError": [
                {"description": "Install the missing module using pip", "code": "pip install <module_name>"},
                {"description": "Check the module name spelling", "code": None}
            ],
            "NameError": [
                {"description": "Define the variable before using it", "code": None},
                {"description": "Check for typos in variable names", "code": None}
            ],
            "TypeError": [
                {"description": "Check the types of arguments passed to the function", "code": None},
                {"description": "Verify the operation is valid for the given types", "code": None}
            ],
            "IndentationError": [
                {"description": "Fix indentation to match Python standards (4 spaces)", "code": None},
                {"description": "Ensure consistent use of tabs or spaces", "code": None}
            ]
        }
        
        return suggestions_map.get(error_type, [
            {"description": f"Review the {error_type} and check the documentation", "code": None}
        ])
    
    def auto_fix(self, error_message: str, code: str, file_path: Optional[str] = None,
                max_attempts: int = 3) -> Tuple[bool, str, str]:
        """Attempt to automatically fix the code"""
        
        # Track fix attempts for this error
        error_key = hash(error_message)
        if error_key not in self.fix_attempts:
            self.fix_attempts[error_key] = 0
        
        if self.fix_attempts[error_key] >= max_attempts:
            return False, code, f"Max fix attempts ({max_attempts}) reached"
        
        self.fix_attempts[error_key] += 1
        
        system_prompt = """You are an expert code fixer.
Given an error and code, provide the corrected version of the code.
Return ONLY the fixed code, no explanations."""

        prompt = f"""Fix this code to resolve the error:

Error: {error_message}

Original Code:
```
{code}
```

Return the complete fixed code."""

        try:
            fixed_code = self.ai_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2
            )
            
            # Extract code from response
            if "```" in fixed_code:
                start = fixed_code.find("```")
                # Skip language identifier
                start = fixed_code.find("\n", start) + 1
                end = fixed_code.rfind("```")
                fixed_code = fixed_code[start:end].strip()
            
            return True, fixed_code, "Code fixed successfully"
            
        except Exception as e:
            return False, code, f"Auto-fix failed: {str(e)}"
    
    def validate_fix(self, original_code: str, fixed_code: str, 
                    test_function: Optional[callable] = None) -> Dict:
        """Validate that a fix doesn't break existing functionality"""
        
        validation_result = {
            "valid": False,
            "changes": [],
            "issues": []
        }
        
        # Compare code lengths as a basic check
        if len(fixed_code.strip()) < len(original_code.strip()) * 0.5:
            validation_result["issues"].append("Fixed code is significantly shorter - possible data loss")
            return validation_result
        
        # If test function provided, run it
        if test_function:
            try:
                test_function(fixed_code)
                validation_result["valid"] = True
            except Exception as e:
                validation_result["issues"].append(f"Test failed: {str(e)}")
                return validation_result
        else:
            # Basic validation - assume valid if no major issues
            validation_result["valid"] = True
        
        # Identify changes
        original_lines = original_code.split('\n')
        fixed_lines = fixed_code.split('\n')
        
        for i, (orig, fixed) in enumerate(zip(original_lines, fixed_lines)):
            if orig != fixed:
                validation_result["changes"].append({
                    "line": i + 1,
                    "original": orig,
                    "fixed": fixed
                })
        
        return validation_result
    
    def get_error_summary(self) -> Dict:
        """Get summary of errors encountered"""
        return {
            "total_errors": len(self.error_history),
            "error_types": self._count_error_types(),
            "most_common_error": self._get_most_common_error()
        }
    
    def _count_error_types(self) -> Dict:
        """Count errors by type"""
        types = {}
        for error in self.error_history:
            error_msg = error.get("error", "")
            error_info = self._parse_error(error_msg)
            error_type = error_info.get("type", "Unknown")
            types[error_type] = types.get(error_type, 0) + 1
        return types
    
    def _get_most_common_error(self) -> Optional[str]:
        """Get the most common error type"""
        types = self._count_error_types()
        if not types:
            return None
        return max(types, key=types.get)
