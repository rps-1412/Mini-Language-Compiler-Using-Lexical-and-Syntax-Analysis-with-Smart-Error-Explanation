# =============================================================
# lexer.py — Lexical Analyser
# =============================================================
# Converts raw source code into a flat list of Token objects.
# Uses regex-based scanning with line-number tracking.
#
# CHANGES v2:
#   + tokenize() now returns (tokens, errors) — never raises.
#   + All lexical violations are collected and scanning continues.
#   + Added LBRACKET / RBRACKET tokens so the parser can detect
#     unsupported array syntax (int arr[5]) and report it cleanly.
# =============================================================

import re
from error_handler import CompilerError, lexical_error, unterminated_char_literal


# ── Token definition ────────────────────────────────────────

class Token:
    """A single lexical unit produced by the lexer."""

    def __init__(self, type_: str, value: str, line: int):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


# ── Keyword / operator tables ────────────────────────────────

KEYWORDS = {"int", "float", "char", "if", "else", "while", "for", "printf"}

TOKEN_SPEC = [
    # Whitespace and comments (discarded)
    ("COMMENT",        r'//[^\n]*'),
    ("NEWLINE",        r'\n'),
    ("WHITESPACE",     r'[ \t\r]+'),

    # Literals
    ("FLOAT_LITERAL",  r'\d+\.\d+'),
    ("INT_LITERAL",    r'\d+'),
    ("CHAR_LITERAL",   r"'.'"),
    ("STRING_LITERAL", r'"[^"]*"'),

    # Multi-character operators
    ("OP_AND",         r'&&'),
    ("OP_OR",          r'\|\|'),
    ("OP_GTE",         r'>='),
    ("OP_LTE",         r'<='),
    ("OP_EQ",          r'=='),
    ("OP_NEQ",         r'!='),

    # Single-character operators
    ("OP_GT",          r'>'),
    ("OP_LT",          r'<'),
    ("OP_ASSIGN",      r'='),
    ("OP_PLUS",        r'\+'),
    ("OP_MINUS",       r'-'),
    ("OP_MUL",         r'\*'),
    ("OP_DIV",         r'/'),
    ("OP_MOD",         r'%'),

    # Delimiters
    ("SEMICOLON",      r';'),
    ("COMMA",          r','),
    ("LPAREN",         r'\('),
    ("RPAREN",         r'\)'),
    ("LBRACE",         r'\{'),
    ("RBRACE",         r'\}'),
    # NEW: square brackets — tokenised so the parser can give a
    # clear "arrays not supported" message instead of a raw lexical error.
    ("LBRACKET",       r'\['),
    ("RBRACKET",       r'\]'),

    # Identifiers / keywords
    ("IDENTIFIER",     r'[A-Za-z_][A-Za-z0-9_]*'),

    # Catch-all for invalid characters
    ("UNKNOWN",        r'.'),
]

_MASTER_RE = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC)
)


# ── Public entry point ───────────────────────────────────────

def tokenize(source: str) -> tuple[list[Token], list[dict]]:
    """
    Scan *source* and return (tokens, errors).

    • tokens : list of Token objects (invalid characters are skipped).
    • errors  : list of error dicts  {"type", "line", "message", "suggestion"}
                collected during scanning — scanning never stops early.

    This replaces the old behaviour of raising on the first lexical error.
    """
    tokens: list[Token] = []
    errors: list[dict]  = []
    line = 1

    for mo in _MASTER_RE.finditer(source):
        kind  = mo.lastgroup
        value = mo.group()

        # ── Track line numbers ──────────────────────────────
        if kind == "NEWLINE":
            line += 1
            continue

        # ── Skip non-tokens ─────────────────────────────────
        if kind in ("WHITESPACE", "COMMENT"):
            continue

        # ── Invalid character — collect error, skip token ───
        if kind == "UNKNOWN":
            err = lexical_error(line, value)
            errors.append(err.to_dict())
            continue                   # ← do NOT raise; keep scanning

        # ── Validate char literals ──────────────────────────
        if kind == "CHAR_LITERAL":
            inner = value[1:-1]
            if len(inner) != 1:
                err = unterminated_char_literal(line)
                errors.append(err.to_dict())
                continue               # skip the bad literal

        # ── Promote identifiers that are keywords ───────────
        if kind == "IDENTIFIER" and value in KEYWORDS:
            kind = "KEYWORD"

        tokens.append(Token(kind, value, line))

    return tokens, errors


# ── Pretty-print helper ──────────────────────────────────────

def print_tokens(tokens: list[Token]) -> None:
    print(f"\n{'─'*50}")
    print(f"  {'TOKEN TYPE':<20} {'VALUE':<15} {'LINE'}")
    print(f"{'─'*50}")
    for tok in tokens:
        print(f"  {tok.type:<20} {tok.value:<15} {tok.line}")
    print(f"{'─'*50}\n")
