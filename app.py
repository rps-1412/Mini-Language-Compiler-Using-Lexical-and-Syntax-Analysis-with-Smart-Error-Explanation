# =============================================================
# app.py — Flask Web Server for the Mini Language Compiler
# =============================================================
# Routes:
#   GET  /          → Serve the HTML UI
#   POST /compile   → Accept source code, run compiler, return JSON
#
# CHANGES v2:
#   + compile_code() unpacks (tokens, lex_errors) from tokenize()
#   + Shares a single `errors` list across lexer + parser phases
#   + Returns `errors` (list) instead of `error` (single object)
#   + `success` is True only when errors list is empty
# =============================================================

import io
import contextlib

from flask import Flask, render_template, request, jsonify

from lexer         import tokenize, print_tokens
from parser        import Parser
from symbol_table  import SymbolTable
from error_handler import CompilerError

app = Flask(__name__)


# =============================================================
# compile_code()
# =============================================================

def compile_code(source: str) -> dict:
    """
    Run the full compiler front-end on the given source string.

    Returns a dict:
    {
        "success"     : bool,
        "errors"      : list of { type, line, message, suggestion },
        "tokens"      : list of { type, value, line },
        "parse_tree"  : str  (only populated on success),
        "symbol_table": list of { name, type, line },
        "token_count" : int
    }
    """
    result = {
        "success"      : False,
        "errors"       : [],          # ← now a LIST, not a single object
        "tokens"       : [],
        "parse_tree"   : "",
        "symbol_table" : [],
        "token_count"  : 0,
    }

    # ── Phase 1: Lexical Analysis ─────────────────────────────
    # tokenize() never raises; it returns (tokens, lex_errors).
    tokens, lex_errors = tokenize(source)

    # Pre-populate the shared errors list with any lexical errors
    errors: list[dict] = list(lex_errors)

    # Build token list for the UI table (even if there were lex errors)
    result["tokens"]      = [{"type": t.type, "value": t.value, "line": t.line} for t in tokens]
    result["token_count"] = len(tokens)

    # ── Phase 2: Syntax Analysis + Parse Tree ─────────────────
    sym    = SymbolTable()
    # Pass the shared errors list into the parser so it can append to it
    parser = Parser(tokens, sym, errors)

    try:
        tree = parser.parse_program()
    except CompilerError as e:
        # Unexpected top-level exception (shouldn't happen with recovery,
        # but kept as a safety net)
        errors.append(e.to_dict())
        result["errors"] = errors
        return result

    # parse_program() filled parser.errors via _collect() / _synchronize().
    # Our `errors` list IS parser.errors (same object), so it's up to date.

    result["errors"] = errors

    if errors:
        # There were errors — partial parse tree exists but we do not
        # expose it (it may be incomplete / misleading).
        result["success"] = False
        return result

    # ── Success — build outputs ───────────────────────────────
    tree_buffer = io.StringIO()
    with contextlib.redirect_stdout(tree_buffer):
        tree.print_tree(prefix="", is_last=True)
    result["parse_tree"] = tree_buffer.getvalue()

    result["symbol_table"] = [
        {"name": name, "type": info["type"], "line": info["line"]}
        for name, info in sym._table.items()
    ]
    result["success"] = True
    return result


# =============================================================
# Routes
# =============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/compile", methods=["POST"])
def compile_route():
    data   = request.get_json(force=True, silent=True) or {}
    source = data.get("code", "").strip()

    if not source:
        return jsonify({
            "success"      : False,
            "errors"       : [{
                "type"      : "Input",
                "line"      : 0,
                "message"   : "No source code provided.",
                "suggestion": "Type or paste your code into the editor and click Compile.",
            }],
            "tokens"       : [],
            "parse_tree"   : "",
            "symbol_table" : [],
            "token_count"  : 0,
        })

    output = compile_code(source)
    return jsonify(output)


# =============================================================
# Entry Point
# =============================================================

if __name__ == "__main__":
    print("Starting Mini Language Compiler Web Server...")
    print("Open your browser at:  http://127.0.0.1:5000")
    app.run(debug=True)
