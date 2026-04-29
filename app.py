# =============================================================
# app.py — Flask Web Server for the Mini Language Compiler
# =============================================================
import io, contextlib
from flask import Flask, render_template, request, jsonify
from lexer        import tokenize
from parser       import Parser
from symbol_table import SymbolTable
from error_handler import CompilerError

app = Flask(__name__)

# ── Error category mapping ────────────────────────────────────
def categorize_error(error: dict) -> str:
    msg   = (error.get("message")  or "").lower()
    etype = (error.get("type")     or "").lower()
    if etype == "lexical":
        if "unexpected character" in msg:   return "Invalid Character"
        if "unterminated" in msg:           return "Unterminated Literal"
        return "Lexical Error"
    if etype == "syntax":
        if "semicolon" in msg:              return "Missing Semicolon"
        if "'{'" in msg or "'}'" in msg:    return "Missing Brace"
        if "'('" in msg or "')'" in msg:    return "Missing Parenthesis"
        if "identifier" in msg:             return "Missing Identifier"
        if "relational operator" in msg:    return "Invalid Condition"
        if "unexpected token" in msg or "end of program" in msg: return "Unexpected Token"
        if "expression" in msg:             return "Invalid Expression"
        if "type keyword" in msg:           return "Missing Type Keyword"
        return "Syntax Error"
    if etype == "validation":
        if "already been declared" in msg:  return "Duplicate Declaration"
        if "used before" in msg:            return "Undeclared Variable"
        return "Validation Error"
    if etype == "unsupported":
        if "function" in msg:               return "Unsupported Functions"
        if "array" in msg:                  return "Unsupported Arrays"
        if "switch" in msg:                 return "Unsupported Switch"
        if "return" in msg:                 return "Unsupported Return"
        return "Unsupported Feature"
    return "Unknown Error"

def _build_summary_details(errors):
    summary, details = {}, {}
    for e in errors:
        t   = e.get("type", "Unknown")
        cat = categorize_error(e)
        summary[t] = summary.get(t, 0) + 1
        details.setdefault(t, {}).setdefault(cat, []).append(e)
    return summary, details

# ── Core compiler runner ──────────────────────────────────────
def compile_code(source: str) -> dict:
    result = {
        "success": False, "errors": [], "summary": {}, "details": {},
        "tokens": [], "parse_tree": "", "symbol_table": [], "token_count": 0,
    }
    tokens, lex_errors = tokenize(source)
    errors = list(lex_errors)
    result["tokens"]      = [{"type": t.type, "value": t.value, "line": t.line} for t in tokens]
    result["token_count"] = len(tokens)
    sym    = SymbolTable()
    parser = Parser(tokens, sym, errors)
    try:
        tree = parser.parse_program()
    except CompilerError as e:
        errors.append(e.to_dict())
        result["errors"]  = errors
        result["summary"], result["details"] = _build_summary_details(errors)
        return result
    result["errors"] = errors
    result["summary"], result["details"] = _build_summary_details(errors)
    if errors:
        return result
    tree_buf = io.StringIO()
    with contextlib.redirect_stdout(tree_buf):
        tree.print_tree(prefix="", is_last=True)
    result["parse_tree"]   = tree_buf.getvalue()
    result["symbol_table"] = [
        {"name": name, "type": info["type"], "line": info["line"]}
        for name, info in sym._table.items()
    ]
    result["success"] = True
    return result

# ── Routes ────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/compile", methods=["POST"])
def compile_route():
    data   = request.get_json(force=True, silent=True) or {}
    source = data.get("code", "").strip()
    if not source:
        empty_err = {"type":"Input","line":0,"message":"No source code provided.","suggestion":"Type or paste your code into the editor and click Compile."}
        return jsonify({"success":False,"errors":[empty_err],"summary":{"Input":1},"details":{"Input":{"Empty Input":[empty_err]}},"tokens":[],"parse_tree":"","symbol_table":[],"token_count":0})
    return jsonify(compile_code(source))

if __name__ == "__main__":
    print("Starting Mini Language Compiler Web Server...")
    print("Open your browser at:  http://127.0.0.1:5000")
    app.run(debug=True)
