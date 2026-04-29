# Mini Language Compiler — v3 Visualization Edition

## What's New in v3
- **Level 1 — Error Distribution Chart** (donut chart via Chart.js): shows error counts by type (Lexical / Syntax / Validation / Unsupported) after every compile.
- **Level 2 — Drill-Down**: click any error type in the chart/legend to see a category breakdown (e.g., "Missing Semicolon", "Invalid Character").
- **Level 3 — Error Details**: click any category card to see individual error cards with line numbers, messages, and suggestions.
- 4 enhanced sample programs demonstrating all visualization paths.
- Modernized dark UI with smooth animations.

## Quick Start

### 1. Install dependencies
```bash
pip install flask
```

### 2. Run the server
```bash
cd compiler_web
python app.py
```

### 3. Open browser
```
http://127.0.0.1:5000
```

## How to Use
1. Type or paste source code into the editor (or load a Sample from the dropdown).
2. Click **▶ Compile** (or press `Ctrl+Enter`).
3. The **Error Distribution Chart** appears immediately.
4. Click a colored bar/legend row → **Category Breakdown** appears below.
5. Click a category card → **Individual Error Details** appear.
6. On success, browse **Tokens**, **Parse Tree**, and **Symbol Table** tabs.

## Sample Programs
| # | Description | Errors |
|---|-------------|--------|
| 1 | Small valid program (~28 lines) | 0 — chart shows clean |
| 2 | Large valid program (110+ lines) | 0 — full logic demo |
| 3 | Multi-error program | Lexical×2, Syntax×2, Validation×3 |
| 4 | Unsupported features | Unsupported×2 (function + array) |

## Compiler Supported Features
- Types: `int`, `float`, `char`
- Declarations with optional initializers
- Assignments
- `if` / `else`
- `while` loops
- `for` loops
- `printf` statements
- Arithmetic: `+ - * / %`
- Relational: `> < >= <= == !=`
- Logical: `&& ||`

## Project Structure
```
compiler_web/
├── app.py            ← Flask server + error grouping (v3)
├── lexer.py          ← Regex tokenizer (unchanged)
├── parser.py         ← Recursive descent parser (unchanged)
├── symbol_table.py   ← Variable tracking (unchanged)
├── error_handler.py  ← Structured error types (unchanged)
├── templates/
│   └── index.html    ← Full UI with Chart.js visualization (v3)
└── static/
    └── style.css     ← Dark theme styles (v3)
```
