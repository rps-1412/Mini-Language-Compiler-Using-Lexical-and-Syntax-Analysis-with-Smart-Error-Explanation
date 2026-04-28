# =============================================================
# parser.py — Recursive Descent Parser + Parse Tree Builder
# =============================================================
# Implements every grammar rule as a dedicated Python method.
# Simultaneously builds a parse tree (Node objects) and
# performs symbol-table validation (declarations / usage).
#
# CHANGES v2 — Multiple Error Handling:
#
#   Parser.__init__ now accepts an `errors` list (shared with
#   app.py so lexical errors are already in it before parsing).
#
#   parse_stmt_list() wraps each statement in try/except and
#   calls _synchronize() on error → parsing continues after
#   each bad statement, collecting ALL errors.
#
#   _synchronize() skips tokens (brace-depth-aware) until it
#   finds a safe restart point: ';', a type/control keyword,
#   or a closing '}' at the top level.
#
#   Unsupported feature detection (NEW):
#     • Functions  — detected in parse_decl when TYPE ID ( ...
#     • Arrays     — detected in parse_decl when TYPE ID [ ...
#     • switch     — detected in parse_stmt when IDENTIFIER=='switch'
#
#   parse_program() adds any leftover-token error to the list
#   instead of raising, so ALL errors are returned together.
# =============================================================

from lexer         import Token
from symbol_table  import SymbolTable
from error_handler import (
    CompilerError,
    syntax_error,
    missing_semicolon,
    unexpected_token,
    unsupported_feature,
)


# ── Parse-tree node ──────────────────────────────────────────

class Node:
    def __init__(self, label: str, children: list = None):
        self.label    = label
        self.children = children if children is not None else []

    def add(self, child: "Node") -> "Node":
        if child is not None:
            self.children.append(child)
        return self

    def print_tree(self, prefix: str = "", is_last: bool = True) -> None:
        connector = "└── " if is_last else "├── "
        print(prefix + connector + self.label)
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(self.children):
            child.print_tree(child_prefix, i == len(self.children) - 1)

    def __repr__(self):
        return f"Node({self.label!r}, children={len(self.children)})"


# ── Parser ───────────────────────────────────────────────────

class Parser:
    """
    Recursive Descent Parser for the mini language.

    Parameters
    ----------
    tokens       : Token list produced by the lexer.
    symbol_table : SymbolTable instance shared with the caller.
    errors       : Shared list; lexical errors are pre-loaded here
                   by app.py before the parser runs.  All syntax
                   and validation errors are appended here too.
    """

    # Keywords that mark a safe restart point after an error
    _SYNC_KEYWORDS = {"int", "float", "char", "if", "while", "for", "printf"}

    def __init__(self, tokens: list[Token], symbol_table: SymbolTable,
                 errors: list[dict] | None = None):
        self.tokens = tokens
        self.pos    = 0
        self.sym    = symbol_table
        # Shared error list — populated by lexer before we start,
        # then extended here as we parse.
        self.errors: list[dict] = errors if errors is not None else []

    # ── Token navigation helpers ─────────────────────────────

    def _current(self) -> Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _peek_type(self) -> str:
        tok = self._current()
        return tok.type if tok else "EOF"

    def _peek_val(self) -> str:
        tok = self._current()
        return tok.value if tok else "EOF"

    def _line(self) -> int:
        tok = self._current()
        return tok.line if tok else 0

    def _advance(self) -> Token:
        tok = self._current()
        self.pos += 1
        return tok

    def _expect(self, token_type: str, token_value: str = None,
                expected_label: str = None) -> Token:
        tok   = self._current()
        label = expected_label or (f"'{token_value}'" if token_value else f"'{token_type}'")
        if tok is None:
            raise syntax_error(self._line(), label, "EOF")
        type_match  = (tok.type  == token_type)
        value_match = (token_value is None) or (tok.value == token_value)
        if not (type_match and value_match):
            raise syntax_error(tok.line, label, tok.value)
        return self._advance()

    def _is_type_keyword(self) -> bool:
        return self._peek_type() == "KEYWORD" and self._peek_val() in ("int", "float", "char")

    # ── Error recovery helpers ───────────────────────────────

    def _collect(self, err: CompilerError) -> None:
        """Append a CompilerError to the shared error list."""
        self.errors.append(err.to_dict())

    def _synchronize(self) -> None:
        """
        Skip tokens until a safe restart point is found.

        Rules (depth = how many '{' we are inside):
        • depth == 0 and SEMICOLON  → consume it and stop.
        • depth == 0 and a type/control keyword → stop (leave token).
        • depth == 0 and RBRACE → stop (leave '}' for caller).
        • LBRACE → increment depth, consume.
        • RBRACE at depth > 0 → decrement depth, consume.
        • Everything else → consume and continue.

        This lets us skip entire function bodies { ... } cleanly.
        """
        depth = 0
        while self._current() is not None:
            tok = self._current()

            if tok.type == "LBRACE":
                depth += 1
                self._advance()
                continue

            if tok.type == "RBRACE":
                if depth > 0:
                    depth -= 1
                    self._advance()
                    continue
                else:
                    return  # unmatched '}' — let caller handle it

            if depth == 0:
                if tok.type == "SEMICOLON":
                    self._advance()   # consume the semicolon, then stop
                    return
                if tok.type == "KEYWORD" and tok.value in self._SYNC_KEYWORDS:
                    return            # leave keyword for next parse_stmt call

            self._advance()

    def _skip_block(self) -> None:
        """
        Consume a complete { ... } block (with nested braces).
        Called only when _peek_type() == 'LBRACE'.
        """
        if self._peek_type() != "LBRACE":
            return
        self._advance()   # consume {
        depth = 1
        while self._current() is not None and depth > 0:
            if self._peek_type() == "LBRACE":
                depth += 1
            elif self._peek_type() == "RBRACE":
                depth -= 1
            self._advance()

    # ==========================================================
    # Grammar rules — each returns a Node
    # ==========================================================

    # ── PROGRAM → STMT_LIST ───────────────────────────────────

    def parse_program(self) -> Node:
        root = Node("PROGRAM")
        root.add(self.parse_stmt_list())
        # Any remaining tokens at EOF → syntax error (collect, don't raise)
        if self._current() is not None:
            tok = self._current()
            self.errors.append({
                "type"      : "Syntax",
                "line"      : tok.line,
                "message"   : f"Unexpected token '{tok.value}' at end of program.",
                "suggestion": (
                    "Check for an extra '}' or tokens that appear outside "
                    "any statement. Every block must be properly closed."
                ),
            })
        return root

    # ── STMT_LIST → STMT STMT_LIST | ε ───────────────────────
    #
    # KEY CHANGE: each statement is wrapped in try/except.
    # On CompilerError we collect the error and call _synchronize()
    # so the next statement can still be parsed.

    def parse_stmt_list(self) -> Node:
        node = Node("STMT_LIST")
        while self._current() is not None and self._peek_val() != "}":
            try:
                stmt = self.parse_stmt()
                node.add(stmt)
            except CompilerError as e:
                self._collect(e)
                self._synchronize()
        return node

    # ── STMT → DECL | ASSIGN | IFSTMT | WHILESTMT | FORSTMT | PRINTSTMT

    def parse_stmt(self) -> Node:
        tok = self._current()
        if tok is None:
            return None

        # ── Unsupported: switch statement ───────────────────
        if tok.type == "IDENTIFIER" and tok.value == "switch":
            raise unsupported_feature(
                tok.line,
                "switch-case statements are not supported",
                "Use if-else chains instead.",
            )

        # ── Unsupported: return statement ───────────────────
        if tok.type == "IDENTIFIER" and tok.value == "return":
            raise unsupported_feature(
                tok.line,
                "'return' is not supported",
                "Functions and return statements are outside the supported grammar.",
            )

        if self._is_type_keyword():
            return self.parse_decl()

        if tok.type == "KEYWORD":
            if tok.value == "if":
                return self.parse_ifstmt()
            if tok.value == "while":
                return self.parse_whilestmt()
            if tok.value == "for":
                return self.parse_forstmt()
            if tok.value == "printf":
                return self.parse_printstmt()

        if tok.type == "IDENTIFIER":
            return self.parse_assign()

        raise unexpected_token(tok.line, tok.value)

    # ── DECL → TYPE ID INIT ; ─────────────────────────────────

    def parse_decl(self) -> Node:
        node     = Node("DECL")
        type_tok = self._advance()               # consume TYPE keyword
        node.add(Node(f"TYPE:{type_tok.value}"))

        id_tok = self._expect("IDENTIFIER", expected_label="identifier")
        node.add(Node(f"ID:{id_tok.value}"))

        # ── Unsupported: function declaration ───────────────
        # Pattern: TYPE ID ( ...
        if self._peek_type() == "LPAREN":
            # Skip parameters and body so the next statement parses cleanly
            while self._current() and self._peek_type() not in ("LBRACE", "SEMICOLON", "EOF"):
                if self._peek_type() == "RBRACE":
                    break
                self._advance()
            if self._peek_type() == "LBRACE":
                self._skip_block()
            raise unsupported_feature(
                id_tok.line,
                f"functions are not supported",
                f"Found '{type_tok.value} {id_tok.value}(...)'. "
                "Remove the function definition and inline its logic.",
            )

        # ── Unsupported: array declaration ──────────────────
        # Pattern: TYPE ID [ ...
        if self._peek_type() == "LBRACKET":
            # Skip to the end of the declaration
            while self._current() and self._peek_type() not in ("SEMICOLON", "LBRACE", "RBRACE"):
                self._advance()
            if self._peek_type() == "SEMICOLON":
                self._advance()   # consume ;
            raise unsupported_feature(
                id_tok.line,
                f"arrays are not supported",
                f"Found '{type_tok.value} {id_tok.value}[...]'. "
                "Declare individual variables instead: int x; int y; int z;",
            )

        # ── Normal declaration ───────────────────────────────
        self.sym.declare(id_tok.value, type_tok.value, id_tok.line)
        node.add(self.parse_init())

        if self._peek_type() != "SEMICOLON":
            raise missing_semicolon(self._line(), f"declaration of '{id_tok.value}'")
        self._advance()
        node.add(Node(";"))
        return node

    # ── INIT → = EXPR | ε ─────────────────────────────────────

    def parse_init(self) -> Node:
        node = Node("INIT")
        if self._peek_type() == "OP_ASSIGN":
            self._advance()
            node.add(Node("="))
            node.add(self.parse_expr())
        return node

    # ── ASSIGN → ID = EXPR ; ──────────────────────────────────

    def parse_assign(self) -> Node:
        node   = Node("ASSIGN")
        id_tok = self._expect("IDENTIFIER", expected_label="identifier")
        node.add(Node(f"ID:{id_tok.value}"))
        self.sym.check_usage(id_tok.value, id_tok.line)
        self._expect("OP_ASSIGN", "=", expected_label="'='")
        node.add(Node("="))
        node.add(self.parse_expr())
        if self._peek_type() != "SEMICOLON":
            raise missing_semicolon(self._line(), f"assignment to '{id_tok.value}'")
        self._advance()
        node.add(Node(";"))
        return node

    # ── IFSTMT → if ( COND ) BLOCK ELSE_PART ─────────────────

    def parse_ifstmt(self) -> Node:
        node = Node("IFSTMT")
        self._expect("KEYWORD", "if")
        node.add(Node("if"))
        self._expect("LPAREN", "(")
        node.add(Node("("))
        node.add(self.parse_cond())
        self._expect("RPAREN", ")", expected_label="')'")
        node.add(Node(")"))
        node.add(self.parse_block())
        node.add(self.parse_else_part())
        return node

    # ── ELSE_PART → else BLOCK | ε ───────────────────────────

    def parse_else_part(self) -> Node:
        node = Node("ELSE_PART")
        if self._peek_type() == "KEYWORD" and self._peek_val() == "else":
            self._advance()
            node.add(Node("else"))
            node.add(self.parse_block())
        return node

    # ── WHILESTMT → while ( COND ) BLOCK ─────────────────────

    def parse_whilestmt(self) -> Node:
        node = Node("WHILESTMT")
        self._expect("KEYWORD", "while")
        node.add(Node("while"))
        self._expect("LPAREN", "(")
        node.add(Node("("))
        node.add(self.parse_cond())
        self._expect("RPAREN", ")", expected_label="')'")
        node.add(Node(")"))
        node.add(self.parse_block())
        return node

    # ── FORSTMT → for ( (DECL|ASSIGN) COND ; ASSIGN ) BLOCK ──

    def parse_forstmt(self) -> Node:
        node = Node("FORSTMT")
        self._expect("KEYWORD", "for")
        node.add(Node("for"))
        self._expect("LPAREN", "(")
        node.add(Node("("))

        if self._is_type_keyword():
            node.add(self.parse_decl())
        else:
            node.add(self.parse_assign())

        node.add(self.parse_cond())
        self._expect("SEMICOLON", ";", expected_label="';'")
        node.add(Node(";"))
        node.add(self._parse_assign_no_semi())
        self._expect("RPAREN", ")", expected_label="')'")
        node.add(Node(")"))
        node.add(self.parse_block())
        return node

    def _parse_assign_no_semi(self) -> Node:
        node   = Node("ASSIGN")
        id_tok = self._expect("IDENTIFIER", expected_label="identifier")
        node.add(Node(f"ID:{id_tok.value}"))
        self.sym.check_usage(id_tok.value, id_tok.line)
        self._expect("OP_ASSIGN", "=", expected_label="'='")
        node.add(Node("="))
        node.add(self.parse_expr())
        return node

    # ── BLOCK → { STMT_LIST } ─────────────────────────────────

    def parse_block(self) -> Node:
        node = Node("BLOCK")
        self._expect("LBRACE", "{", expected_label="'{'")
        node.add(Node("{"))
        node.add(self.parse_stmt_list())
        self._expect("RBRACE", "}", expected_label="'}'")
        node.add(Node("}"))
        return node

    # ── PRINTSTMT → printf ( ARG ) ; ─────────────────────────

    def parse_printstmt(self) -> Node:
        node = Node("PRINTSTMT")
        self._expect("KEYWORD", "printf")
        node.add(Node("printf"))
        self._expect("LPAREN", "(", expected_label="'('")
        node.add(Node("("))
        if self._peek_type() == "STRING_LITERAL":
            node.add(Node(self._advance().value))
        else:
            node.add(self.parse_expr())
        self._expect("RPAREN", ")", expected_label="')'")
        node.add(Node(")"))
        if self._peek_type() != "SEMICOLON":
            raise missing_semicolon(self._line(), "printf statement")
        self._advance()
        node.add(Node(";"))
        return node

    # ── COND → LOGIC_EXPR ────────────────────────────────────

    def parse_cond(self) -> Node:
        node = Node("COND")
        node.add(self.parse_logic_expr())
        return node

    def parse_logic_expr(self) -> Node:
        node = Node("LOGIC_EXPR")
        node.add(self.parse_rel_expr())
        node.add(self.parse_logic_expr_prime())
        return node

    def parse_logic_expr_prime(self) -> Node:
        node = Node("LOGIC_EXPR'")
        if self._peek_type() in ("OP_AND", "OP_OR"):
            op = self._advance()
            node.add(Node(op.value))
            node.add(self.parse_rel_expr())
            node.add(self.parse_logic_expr_prime())
        return node

    def parse_rel_expr(self) -> Node:
        node = Node("REL_EXPR")
        node.add(self.parse_expr())
        node.add(self.parse_relop())
        node.add(self.parse_expr())
        return node

    _RELOP_TYPES = {"OP_GT", "OP_LT", "OP_GTE", "OP_LTE", "OP_EQ", "OP_NEQ"}

    def parse_relop(self) -> Node:
        if self._peek_type() not in self._RELOP_TYPES:
            raise syntax_error(self._line(), "relational operator", self._peek_val())
        op = self._advance()
        return Node(f"RELOP:{op.value}")

    def parse_expr(self) -> Node:
        node = Node("EXPR")
        node.add(self.parse_term())
        node.add(self.parse_expr_prime())
        return node

    def parse_expr_prime(self) -> Node:
        node = Node("EXPR'")
        if self._peek_type() in ("OP_PLUS", "OP_MINUS"):
            op = self._advance()
            node.add(Node(op.value))
            node.add(self.parse_term())
            node.add(self.parse_expr_prime())
        return node

    def parse_term(self) -> Node:
        node = Node("TERM")
        node.add(self.parse_factor())
        node.add(self.parse_term_prime())
        return node

    def parse_term_prime(self) -> Node:
        node = Node("TERM'")
        if self._peek_type() in ("OP_MUL", "OP_DIV", "OP_MOD"):
            op = self._advance()
            node.add(Node(op.value))
            node.add(self.parse_factor())
            node.add(self.parse_term_prime())
        return node

    def parse_factor(self) -> Node:
        node = Node("FACTOR")
        tok  = self._current()

        if tok is None:
            raise syntax_error(self._line(), "expression", "EOF")

        if tok.type == "IDENTIFIER":
            self._advance()
            self.sym.check_usage(tok.value, tok.line)
            node.add(Node(f"ID:{tok.value}"))

        elif tok.type == "INT_LITERAL":
            self._advance()
            node.add(Node(f"INT:{tok.value}"))

        elif tok.type == "FLOAT_LITERAL":
            self._advance()
            node.add(Node(f"FLOAT:{tok.value}"))

        elif tok.type == "CHAR_LITERAL":
            self._advance()
            node.add(Node(f"CHAR:{tok.value}"))

        elif tok.type == "LPAREN":
            self._advance()
            node.add(Node("("))
            node.add(self.parse_expr())
            self._expect("RPAREN", ")", expected_label="')'")
            node.add(Node(")"))

        elif tok.type == "OP_MINUS":    # unary minus
            self._advance()
            node.add(Node("-"))
            node.add(self.parse_factor())

        else:
            raise syntax_error(tok.line, "expression", tok.value)

        return node
