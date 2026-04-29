# =============================================================
# error_handler.py — Smart Error Explanation Module
# =============================================================
# Provides structured, user-friendly error messages for:
#   - Lexical errors     (invalid tokens / unknown characters)
#   - Syntax errors      (grammar violations)
#   - Validation errors  (duplicate/undeclared variable use)
#   - Unsupported errors (features outside the CFG)
#
# CHANGES v2:
#   + Added unsupported_feature() factory function
#   + Added CompilerError.to_dict() for clean JSON serialisation
# =============================================================

class CompilerError(Exception):
    """Base exception for all compiler errors."""

    def __init__(self, error_type: str, line: int, message: str, suggestion: str = ""):
        self.error_type  = error_type   # "Lexical" | "Syntax" | "Validation" | "Unsupported"
        self.line        = line
        self.message     = message
        self.suggestion  = suggestion
        super().__init__(self._format())

    def _format(self) -> str:
        width = 60
        bar   = "=" * width
        lines = [
            bar,
            f"  [{self.error_type.upper()} ERROR]  —  Line {self.line}",
            bar,
            f"  Description : {self.message}",
        ]
        if self.suggestion:
            lines.append(f"  Suggestion  : {self.suggestion}")
        lines.append(bar)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialise this error to a JSON-friendly dict."""
        return {
            "type"       : self.error_type,
            "line"       : self.line,
            "message"    : self.message,
            "suggestion" : self.suggestion,
        }

    def __str__(self):
        return self._format()


# ── Factory functions ──────────────────────────────────────

def lexical_error(line: int, char: str) -> CompilerError:
    return CompilerError(
        error_type="Lexical", line=line,
        message=f"Unexpected character '{char}' found.",
        suggestion=(
            "Remove or replace the invalid character. "
            "Identifiers must start with a letter or underscore."
        ),
    )

def unterminated_char_literal(line: int) -> CompilerError:
    return CompilerError(
        error_type="Lexical", line=line,
        message="Unterminated or multi-character char literal.",
        suggestion="Char literals must contain exactly one character, e.g. 'a'.",
    )

def syntax_error(line: int, expected: str, found: str) -> CompilerError:
    return CompilerError(
        error_type="Syntax", line=line,
        message=f"Expected {expected}, but found '{found}'.",
        suggestion=_syntax_suggestion(expected),
    )

def missing_semicolon(line: int, context: str = "") -> CompilerError:
    hint = f" after {context}" if context else ""
    return CompilerError(
        error_type="Syntax", line=line,
        message=f"Missing semicolon{hint}.",
        suggestion="Every declaration, assignment, and print statement must end with ';'.",
    )

def unexpected_token(line: int, token: str) -> CompilerError:
    return CompilerError(
        error_type="Syntax", line=line,
        message=f"Unexpected token '{token}' encountered.",
        suggestion=(
            "Check that the statement follows the grammar. "
            "Statements must start with a type keyword, identifier, "
            "'if', 'while', 'for', or 'printf'."
        ),
    )

def duplicate_declaration(line: int, var_name: str) -> CompilerError:
    return CompilerError(
        error_type="Validation", line=line,
        message=f"Variable '{var_name}' has already been declared.",
        suggestion=(
            f"Remove the duplicate declaration of '{var_name}', "
            "or rename the variable."
        ),
    )

def undeclared_variable(line: int, var_name: str) -> CompilerError:
    return CompilerError(
        error_type="Validation", line=line,
        message=f"Variable '{var_name}' is used before it was declared.",
        suggestion=(
            f"Declare '{var_name}' before using it, "
            f"e.g.  int {var_name};  or  int {var_name} = 0;"
        ),
    )

def unsupported_feature(line: int, feature: str, detail: str = "") -> CompilerError:
    """Raised for constructs outside the CFG: functions, arrays, switch-case."""
    msg = f"Unsupported feature: {feature}."
    if detail:
        msg += f" {detail}"
    return CompilerError(
        error_type="Unsupported", line=line,
        message=msg,
        suggestion=(
            "This compiler supports: int/float/char declarations, assignments, "
            "if-else, while, for, and printf statements only."
        ),
    )


# ── Internal helpers ────────────────────────────────────────

def _syntax_suggestion(expected: str) -> str:
    table = {
        "'('":                "Opening parenthesis '(' is required here.",
        "')'":                "Closing parenthesis ')' is missing. Check your expression.",
        "'{'":                "Opening brace '{' is required to start a block.",
        "'}'":                "Closing brace '}' is missing. Every '{' needs a matching '}'.",
        "';'":                "Semicolon ';' is required to end this statement.",
        "'='":                "Assignment operator '=' expected.",
        "identifier":         "An identifier (variable name) is expected here.",
        "expression":         "A valid expression (number, variable, or arithmetic) is expected.",
        "type keyword":       "A type keyword ('int', 'float', or 'char') is expected.",
        "relational operator":"A relational operator (>, <, >=, <=, ==, !=) is required in a condition.",
    }
    return table.get(expected, f"Review the grammar rule that requires {expected}.")
