# =============================================================
# symbol_table.py — Symbol Table  (UNCHANGED from v1)
# =============================================================
# Tracks declared variables and their types.
# Raises Validation CompilerErrors — the Parser catches them.
# =============================================================

from error_handler import duplicate_declaration, undeclared_variable


class SymbolTable:
    def __init__(self):
        self._table: dict[str, dict] = {}

    def declare(self, name: str, var_type: str, line: int) -> None:
        if name in self._table:
            raise duplicate_declaration(line, name)
        self._table[name] = {"type": var_type, "line": line}

    def check_usage(self, name: str, line: int) -> None:
        if name not in self._table:
            raise undeclared_variable(line, name)

    def lookup(self, name: str) -> dict | None:
        return self._table.get(name)

    def is_declared(self, name: str) -> bool:
        return name in self._table

    def display(self) -> None:
        if not self._table:
            print("  (symbol table is empty)")
            return
        print(f"\n{'─'*40}")
        print(f"  {'VARIABLE':<15} {'TYPE':<10} {'DECLARED AT'}")
        print(f"{'─'*40}")
        for name, info in self._table.items():
            print(f"  {name:<15} {info['type']:<10} line {info['line']}")
        print(f"{'─'*40}\n")

    def __len__(self):
        return len(self._table)

    def __repr__(self):
        return f"SymbolTable({list(self._table.keys())})"
