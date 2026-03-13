import sys
import math
import random
import os
import re as _re

try:
    import readline
except ImportError:
    pass

class MaySonLangError(Exception):
    def __init__(self, message, line=None):
        self.line = line
        prefix = f"Line {line}: " if line else ""
        super().__init__(f"{prefix}{message}")

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class BreakSignal(Exception):
    pass

class ContinueSignal(Exception):
    pass

class Token:
    __slots__ = ("line", "indent", "content")

    def __init__(self, line, indent, content):
        self.line    = line
        self.indent  = indent
        self.content = content

    def __repr__(self):
        return f"Token(line={self.line}, indent={self.indent}, content={self.content!r})"


def tokenize(source: str) -> list:
    tokens = []
    for lineno, raw in enumerate(source.splitlines(), 1):
        stripped = raw.rstrip()
        text     = stripped.lstrip()
        if not text or text.startswith("#"):
            continue
        indent = len(stripped) - len(text)
        tokens.append(Token(lineno, indent, text))
    return tokens

def _arg_split(s):
    parts = []; cur = ""; depth = 0; in_str = False; str_ch = ""
    for ch in s:
        if in_str:
            cur += ch
            if ch == str_ch: in_str = False
        elif ch in ('"', "'"):
            in_str = True; str_ch = ch; cur += ch
        elif ch in ("(", "["): depth += 1; cur += ch
        elif ch in (")", "]"): depth -= 1; cur += ch
        elif ch == "," and depth == 0:
            parts.append(cur.strip()); cur = ""
        else:
            cur += ch
    if cur.strip(): parts.append(cur.strip())
    return parts


def _find_op(expr: str, op: str) -> int:
    depth = 0; in_str = False; str_ch = ""
    i = 0
    while i < len(expr):
        ch = expr[i]
        if in_str:
            if ch == str_ch and (i == 0 or expr[i-1] != "\\"): in_str = False
        elif ch in ('"', "'"): in_str = True; str_ch = ch
        elif ch in ("(", "["): depth += 1
        elif ch in (")", "]"): depth -= 1
        elif depth == 0 and expr[i:i+len(op)] == op: return i
        i += 1
    return -1


def _split_keyword(expr: str, kw: str):
    pat = f" {kw} "
    parts = []; cur = ""; depth = 0; in_str = False; str_ch = ""; i = 0
    while i < len(expr):
        ch = expr[i]
        if in_str:
            cur += ch
            if ch == str_ch and (i == 0 or expr[i-1] != "\\"): in_str = False
            i += 1; continue
        if ch in ('"', "'"): in_str = True; str_ch = ch; cur += ch; i += 1; continue
        if ch in ("(", "["): depth += 1; cur += ch; i += 1; continue
        if ch in (")", "]"): depth -= 1; cur += ch; i += 1; continue
        if depth == 0 and expr[i:i+len(pat)] == pat:
            parts.append(cur.strip()); cur = ""; i += len(pat); continue
        cur += ch; i += 1
    parts.append(cur.strip())
    return parts if len(parts) > 1 else None


def _arith_tokenize(expr: str):
    toks = []; cur = ""; depth = 0; in_str = False; str_ch = ""; found = False
    i = 0
    while i < len(expr):
        ch = expr[i]
        if in_str:
            cur += ch
            if ch == str_ch and (i == 0 or expr[i-1] != "\\"): in_str = False
            i += 1; continue
        if ch in ('"', "'"): in_str = True; str_ch = ch; cur += ch; i += 1; continue
        if ch in ("(", "["): depth += 1; cur += ch; i += 1; continue
        if ch in (")", "]"): depth -= 1; cur += ch; i += 1; continue
        if depth == 0:
            two = expr[i:i+2]
            if two == "//":
                toks.append(cur.strip()); cur = ""; toks.append("//"); found = True; i += 2; continue
            if ch in ("+", "-", "*", "/", "%", "^"):
                # treat as unary minus if nothing accumulated yet
                if ch == "-" and cur.strip() == "" and (not toks or toks[-1] in ("+","-","*","/","//","%","^")):
                    cur += ch; i += 1; continue
                toks.append(cur.strip()); cur = ""; toks.append(ch); found = True; i += 1; continue
        cur += ch; i += 1
    toks.append(cur.strip())
    if not found: return None
    if any(t == "" for t in toks[::2]): return None
    return toks


def _fn_call_pattern(expr: str):
    if not expr.endswith(")"): return None
    p = expr.index("(")
    name = expr[:p].strip()
    if not name.isidentifier(): return None
    return name, expr[p+1:-1]


def _index_pattern(expr: str):
    if not expr.endswith("]"): return None
    b = expr.index("[")
    name = expr[:b].strip()
    if not name.isidentifier(): return None
    return name, expr[b+1:-1]


def resolve_var(name: str, scope: dict, line=None):
    if name == "true":  return True
    if name == "false": return False
    if name in ("null", "nothing"): return None
    if name in scope:   return scope[name]
    raise MaySonLangError(f"Undefined variable: '{name}'", line)


def eval_expr(expr: str, scope: dict, functions: dict, line=None):
    expr = expr.strip()
    if not expr: return None

    if expr[0] in ('"', "'"):
        ch = expr[0]; j = 1
        while j < len(expr):
            if expr[j] == "\\" and j+1 < len(expr): j += 2; continue
            if expr[j] == ch:
                if j == len(expr) - 1:
                    return expr[1:j].replace("\\n", "\n").replace("\\t", "\t")
                break
            j += 1

    if expr.startswith("call "):
        inner = expr[5:].strip()
        fm = _fn_call_pattern(inner)
        if fm:
            args = [eval_expr(a, scope, functions, line) for a in _arg_split(fm[1])]
            return _call_function(fm[0], args, scope, functions, line)

    if expr == "true":  return True
    if expr == "false": return False
    if expr in ("null", "nothing"): return None

    try: return int(expr)
    except ValueError: pass
    try: return float(expr)
    except ValueError: pass

    if expr.startswith("[") and expr.endswith("]"):
        inner = expr[1:-1].strip()
        if not inner: return []
        return [eval_expr(a, scope, functions, line) for a in _arg_split(inner)]

    if expr.startswith("(") and expr.endswith(")"):
        return eval_expr(expr[1:-1], scope, functions, line)

    or_parts = _split_keyword(expr, "or")
    if or_parts: return any(eval_expr(p, scope, functions, line) for p in or_parts)
    and_parts = _split_keyword(expr, "and")
    if and_parts: return all(eval_expr(p, scope, functions, line) for p in and_parts)
    if expr.startswith("not "):
        return not eval_expr(expr[4:].strip(), scope, functions, line)

    for op in (">=", "<=", "!=", " is not ", " is ", "==", ">", "<"):
        idx = _find_op(expr, op)
        if idx != -1:
            L = eval_expr(expr[:idx].strip(),       scope, functions, line)
            R = eval_expr(expr[idx+len(op):].strip(), scope, functions, line)
            if op in ("==", " is "):     return L == R
            if op in ("!=", " is not "): return L != R
            if op == ">":  return L > R
            if op == "<":  return L < R
            if op == ">=": return L >= R
            if op == "<=": return L <= R

    at = _arith_tokenize(expr)
    if at is not None:
        vals = [eval_expr(t, scope, functions, line) for t in at[::2]]
        ops  = at[1::2]
        i = len(ops) - 1
        while i >= 0:
            if ops[i] == "^":
                vals[i] = vals[i] ** vals[i+1]; del vals[i+1]; del ops[i]
            i -= 1
        i = 0
        while i < len(ops):
            op = ops[i]
            if op in ("*", "/", "//", "%"):
                if op == "*":  r = vals[i] * vals[i+1]
                elif op == "/":
                    if vals[i+1] == 0: raise MaySonLangError("Division by zero", line)
                    r = vals[i] / vals[i+1]
                elif op == "//":
                    if vals[i+1] == 0: raise MaySonLangError("Division by zero", line)
                    r = int(vals[i] // vals[i+1])
                elif op == "%": r = vals[i] % vals[i+1]
                vals[i] = r; del vals[i+1]; del ops[i]
            else:
                i += 1
        result = vals[0]
        for k, op in enumerate(ops):
            a, b = result, vals[k+1]
            if op == "+":
                result = (str(a) + str(b)) if isinstance(a, str) or isinstance(b, str) else a + b
            elif op == "-":
                result = a - b
        return result

    fm = _fn_call_pattern(expr)
    if fm:
        args = [eval_expr(a, scope, functions, line) for a in _arg_split(fm[1])]
        return _call_function(fm[0], args, scope, functions, line)

    im = _index_pattern(expr)
    if im:
        arr = resolve_var(im[0], scope, line)
        idx = eval_expr(im[1], scope, functions, line)
        try: return arr[idx]
        except IndexError: raise MaySonLangError(f"Index {idx} out of range for '{im[0]}'", line)

    if expr.isidentifier():
        return resolve_var(expr, scope, line)

    raise MaySonLangError(f"Cannot evaluate: {expr!r}", line)


# ─────────────────────────────────────────────────────────────────────────────
#  BUILT-IN FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

BUILTINS = {
    "len":       lambda a, **_: len(a[0]),
    "type":      lambda a, **_: type(a[0]).__name__,
    "number":    lambda a, **_: float(a[0]) if "." in str(a[0]) else int(a[0]),
    "text":      lambda a, **_: str(a[0]),
    "round":     lambda a, **_: round(a[0], int(a[1]) if len(a) > 1 else 0),
    "floor":     lambda a, **_: math.floor(a[0]),
    "ceil":      lambda a, **_: math.ceil(a[0]),
    "abs":       lambda a, **_: abs(a[0]),
    "sqrt":      lambda a, **_: math.sqrt(a[0]),
    "max":       lambda a, **_: max(a),
    "min":       lambda a, **_: min(a),
    "sum":       lambda a, **_: sum(a[0]) if len(a) == 1 else sum(a),
    "random":    lambda a, **_: random.random(),
    "randint":   lambda a, **_: random.randint(int(a[0]), int(a[1])),
    "upper":     lambda a, **_: str(a[0]).upper(),
    "lower":     lambda a, **_: str(a[0]).lower(),
    "title":     lambda a, **_: str(a[0]).title(),
    "strip":     lambda a, **_: str(a[0]).strip(),
    "replace":   lambda a, **_: str(a[0]).replace(str(a[1]), str(a[2])),
    "split":     lambda a, **_: str(a[0]).split(str(a[1])) if len(a) > 1 else str(a[0]).split(),
    "join":      lambda a, **_: str(a[1]).join(str(x) for x in a[0]),
    "contains":  lambda a, **_: a[1] in a[0],
    "startswith":lambda a, **_: str(a[0]).startswith(str(a[1])),
    "endswith":  lambda a, **_: str(a[0]).endswith(str(a[1])),
    "range":     lambda a, **_: (list(range(int(a[0]))) if len(a) == 1
                                 else list(range(int(a[0]), int(a[1]))) if len(a) == 2
                                 else list(range(int(a[0]), int(a[1]), int(a[2])))),
    "sort":      lambda a, **_: sorted(a[0]),
    "reverse":   lambda a, **_: list(reversed(a[0])),
    "unique":    lambda a, **_: list(dict.fromkeys(a[0])),
    "first":     lambda a, **_: a[0][0],
    "last":      lambda a, **_: a[0][-1],
    "slice":     lambda a, **_: a[0][int(a[1]):int(a[2])],
    "input":     lambda a, **_: input(str(a[0]) if a else ""),
    "exit":      lambda a, **_: sys.exit(0),
}


def _call_function(name: str, args: list, scope: dict, functions: dict, line=None):
    if name in BUILTINS:
        try:
            return BUILTINS[name](args, scope=scope, functions=functions)
        except MaySonLangError:
            raise
        except Exception as e:
            raise MaySonLangError(f"Error in built-in '{name}': {e}", line)

    if name not in functions:
        raise MaySonLangError(f"Unknown function: '{name}'", line)

    fn = functions[name]
    if len(args) != len(fn["params"]):
        raise MaySonLangError(
            f"'{name}' expects {len(fn['params'])} arg(s), got {len(args)}", line)

    fn_scope = {**fn["closure"], **dict(zip(fn["params"], args))}
    interp = Interpreter.__new__(Interpreter)
    interp.functions  = functions
    interp.call_depth = fn.get("call_depth", 0) + 1
    if interp.call_depth > 500:
        raise MaySonLangError("Maximum recursion depth exceeded", line)
    try:
        interp.execute(fn["body"], fn_scope)
    except ReturnSignal as ret:
        return ret.value
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  INTERPRETER
# ─────────────────────────────────────────────────────────────────────────────

class Interpreter:
    def __init__(self):
        self.functions  = {}
        self.call_depth = 0

    # ── helpers ───────────────────────────────────────────────────────────────

    def _eval(self, expr, scope, line=None):
        return eval_expr(expr, scope, self.functions, line)

    def _cond(self, cond, scope, line=None):
        return bool(self._eval(cond, scope, line))

    def _group_block(self, tokens, start, base_indent):
        block = []; i = start
        while i < len(tokens) and tokens[i].indent > base_indent:
            block.append(tokens[i]); i += 1
        return block, i

    def _display(self, val):
        if val is None:           return "nothing"
        if isinstance(val, bool): return "true" if val else "false"
        if isinstance(val, list): return "[" + ", ".join(self._display(v) for v in val) + "]"
        if isinstance(val, float) and val == int(val): return str(int(val))
        return str(val)

    # ── entry points ──────────────────────────────────────────────────────────

    def run(self, source: str):
        self.execute(tokenize(source), {})

    def execute(self, tokens, scope, start=0, base_indent=-1):
        i = start
        while i < len(tokens):
            tok = tokens[i]
            if base_indent >= 0 and tok.indent <= base_indent:
                break
            i = self._exec_stmt(tok, tokens, i, scope)

    # ── statement dispatcher ──────────────────────────────────────────────────

    def _exec_stmt(self, tok, tokens, i, scope):
        c  = tok.content
        ln = tok.line

        # ── say / show ────────────────────────────────────────────────────────
        if c in ("say", "show") or c.startswith(("say ", "show ")):
            expr = _re.sub(r"^(say|show)\s*", "", c)
            val  = self._eval(expr, scope, ln) if expr else ""
            print(self._display(val))
            return i + 1

        # ── set x to expr  /  set x[idx] to expr ─────────────────────────────
        m = _re.match(r"^set\s+(.+?)\s+to\s+(.+)$", c)
        if m:
            target, expr = m.group(1), m.group(2)
            val = self._eval(expr, scope, ln)
            im  = _index_pattern(target)
            if im:
                arr = resolve_var(im[0], scope, ln)
                arr[self._eval(im[1], scope, ln)] = val
            else:
                scope[target.strip()] = val
            return i + 1

        # ── increase x by N  (x += N) ────────────────────────────────────────
        m = _re.match(r"^increase\s+([A-Za-z_][A-Za-z0-9_]*)\s+by\s+(.+)$", c)
        if m:
            name, expr = m.group(1), m.group(2)
            old = resolve_var(name, scope, ln)
            scope[name] = old + self._eval(expr, scope, ln)
            return i + 1

        # ── decrease x by N  (x -= N) ────────────────────────────────────────
        m = _re.match(r"^decrease\s+([A-Za-z_][A-Za-z0-9_]*)\s+by\s+(.+)$", c)
        if m:
            name, expr = m.group(1), m.group(2)
            old = resolve_var(name, scope, ln)
            scope[name] = old - self._eval(expr, scope, ln)
            return i + 1

        # ── multiply x by N  (x *= N) ────────────────────────────────────────
        m = _re.match(r"^multiply\s+([A-Za-z_][A-Za-z0-9_]*)\s+by\s+(.+)$", c)
        if m:
            name, expr = m.group(1), m.group(2)
            old = resolve_var(name, scope, ln)
            scope[name] = old * self._eval(expr, scope, ln)
            return i + 1

        # ── divide x by N  (x /= N) ──────────────────────────────────────────
        m = _re.match(r"^divide\s+([A-Za-z_][A-Za-z0-9_]*)\s+by\s+(.+)$", c)
        if m:
            name, expr = m.group(1), m.group(2)
            old = resolve_var(name, scope, ln)
            divisor = self._eval(expr, scope, ln)
            if divisor == 0: raise MaySonLangError("Division by zero", ln)
            scope[name] = old / divisor
            return i + 1

        # ── add x to list ─────────────────────────────────────────────────────
        m = _re.match(r"^add\s+(.+)\s+to\s+([A-Za-z_][A-Za-z0-9_]*)$", c)
        if m:
            val_expr, lst_name = m.group(1), m.group(2)
            lst = resolve_var(lst_name, scope, ln)
            if not isinstance(lst, list):
                raise MaySonLangError(f"'{lst_name}' is not a list", ln)
            lst.append(self._eval(val_expr, scope, ln))
            return i + 1

        # ── remove x from list ────────────────────────────────────────────────
        m = _re.match(r"^remove\s+(.+)\s+from\s+([A-Za-z_][A-Za-z0-9_]*)$", c)
        if m:
            val_expr, lst_name = m.group(1), m.group(2)
            lst = resolve_var(lst_name, scope, ln)
            v = self._eval(val_expr, scope, ln)
            if v in lst: lst.remove(v)
            return i + 1

        # ── make fn(params): ──────────────────────────────────────────────────
        m = _re.match(r"^make\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*:?$", c)
        if m:
            fname, param_str = m.group(1), m.group(2)
            params = [p.strip() for p in param_str.split(",") if p.strip()]
            block, next_i = self._group_block(tokens, i + 1, tok.indent)
            self.functions[fname] = {
                "params": params, "body": block,
                "closure": dict(scope), "call_depth": self.call_depth
            }
            return next_i

        # ── call fn(args) statement ───────────────────────────────────────────
        m = _re.match(r"^call\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)$", c)
        if m:
            fname, args_str = m.group(1), m.group(2)
            args = [self._eval(a.strip(), scope, ln) for a in _arg_split(args_str)]
            _call_function(fname, args, scope, self.functions, ln)
            return i + 1

        # ── return ────────────────────────────────────────────────────────────
        if c.startswith("return"):
            expr = c[6:].strip()
            raise ReturnSignal(self._eval(expr, scope, ln) if expr else None)

        # ── break / continue ──────────────────────────────────────────────────
        if c == "break":    raise BreakSignal()
        if c == "continue": raise ContinueSignal()

        # ── if  (primary keyword; 'check' is accepted as alias) ──────────────
        m = _re.match(r"^(?:if|check)\s+(.+?)\s*:?$", c)
        if m:
            cond = m.group(1)
            then_block, after_then = self._group_block(tokens, i + 1, tok.indent)
            else_block, after_else = self._collect_else(tokens, after_then, tok.indent, scope)

            if self._cond(cond, scope, ln):
                self._run_block(then_block, scope)
            elif else_block:
                self._run_block(else_block, scope)
            return after_else

        # ── else / otherwise (top-level: already consumed by if) ─────────────
        if (_re.match(r"^(else|otherwise)\s*:?$", c) or
                _re.match(r"^(else if|else check|otherwise if|otherwise check)\s+", c)):
            _, next_i = self._group_block(tokens, i + 1, tok.indent)
            return next_i

        # ── repeat N times: ───────────────────────────────────────────────────
        #    'N' can be a variable — it is evaluated ONCE before the loop,
        #    but if the variable changes inside the loop, repeat re-reads it
        #    each iteration so `repeat x times` works with a changing x.
        m = _re.match(r"^repeat\s+(.+?)\s+times?\s*:?$", c)
        if m:
            count_expr = m.group(1).strip()
            block, next_i = self._group_block(tokens, i + 1, tok.indent)
            iteration = 0
            while True:
                # Re-evaluate count from scope each iteration (supports
                # "repeat x times" where x changes inside the block).
                count = int(self._eval(count_expr, scope, ln))
                if iteration >= count:
                    break
                loop_scope = {**scope, "i": iteration}
                broke = False
                try:
                    self._run_block(block, loop_scope)
                except BreakSignal:
                    broke = True
                except ContinueSignal:
                    pass
                # ── IMPORTANT: flush ALL loop_scope mutations back to outer scope
                for k, v in loop_scope.items():
                    scope[k] = v
                if broke:
                    break
                iteration += 1
            return next_i

        # ── repeat for each item in list ─────────────────────────────────────
        m = _re.match(r"^repeat\s+for\s+each\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+?)\s*:?$", c)
        if m:
            var_name, list_expr = m.group(1), m.group(2)
            lst = self._eval(list_expr, scope, ln)
            if not isinstance(lst, list):
                raise MaySonLangError(f"Expected list, got {type(lst).__name__}", ln)
            block, next_i = self._group_block(tokens, i + 1, tok.indent)
            for item in lst:
                loop_scope = {**scope, var_name: item}
                broke = False
                try:
                    self._run_block(block, loop_scope)
                except BreakSignal:
                    broke = True
                except ContinueSignal:
                    pass
                for k, v in loop_scope.items():
                    scope[k] = v
                if broke:
                    break
            return next_i

        # ── while ─────────────────────────────────────────────────────────────
        m = _re.match(r"^while\s+(.+?)\s*:?$", c)
        if m:
            cond = m.group(1)
            block, next_i = self._group_block(tokens, i + 1, tok.indent)
            guard = 0
            while self._cond(cond, scope, ln):
                guard += 1
                if guard > 100_000:
                    raise MaySonLangError("Infinite loop detected (>100,000 iterations)", ln)
                loop_scope = {**scope}
                broke = False
                try:
                    self._run_block(block, loop_scope)
                except BreakSignal:
                    broke = True
                except ContinueSignal:
                    pass
                for k, v in loop_scope.items():
                    scope[k] = v
                if broke:
                    break
            return next_i

        # ── bare expression (e.g. standalone function call) ───────────────────
        try:
            self._eval(c, scope, ln)
            return i + 1
        except MaySonLangError:
            raise
        except Exception as e:
            raise MaySonLangError(str(e), ln)

    # ── else / otherwise chain collector ──────────────────────────────────────

    def _collect_else(self, tokens, start, base_indent, scope):
        """
        Collect an optional else / else if chain after an if block.
        Returns (block_to_run, next_index).
        """
        if start >= len(tokens):
            return [], start
        tok = tokens[start]
        if tok.indent != base_indent:
            return [], start
        c = tok.content

        # plain else / otherwise
        if _re.match(r"^(else|otherwise)\s*:?$", c):
            block, next_i = self._group_block(tokens, start + 1, tok.indent)
            return block, next_i

        # else if / else check / otherwise if / otherwise check
        m = _re.match(r"^(?:else if|else check|otherwise if|otherwise check)\s+(.+?)\s*:?$", c)
        if m:
            cond = m.group(1)
            then_block, after_then = self._group_block(tokens, start + 1, tok.indent)
            else_block, after_else = self._collect_else(tokens, after_then, base_indent, scope)
            if self._cond(cond, scope, tok.line):
                return then_block, after_else
            return else_block, after_else

        return [], start

    def _run_block(self, block, scope):
        self.execute(block, scope, 0, -1)


# ─────────────────────────────────────────────────────────────────────────────
#  REPL + CLI
# ─────────────────────────────────────────────────────────────────────────────

BANNER = """\
╔══════════════════════════════════════════════════════════╗
║         MaySonLang Interpreter                           ║
║  Type 'help' for syntax reference  |  'exit' to quit     ║
╚══════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
MaySonLang SYNTAX REFERENCE
═══════════════════════════════════

  Output
    say "Hello, World!"
    say "Value: " + x

  Variables
    set x to 5
    set name to "Alice"
    set nums to [1, 2, 3]
    set nums[0] to 99

  Variable Update Shorthands
    increase x by 3          → x = x + 3
    decrease x by 1          → x = x - 1
    multiply x by 2          → x = x * 2
    divide x by 4            → x = x / 4
    (or use:  set x to x + 3)

  Arithmetic
    + - * / // % ^
    set result to (x + y) * 2

  Conditionals
    if x > 0:
      say "positive"
    else if x < 0:
      say "negative"
    else:
      say "zero"

  Loops
    repeat 5 times:           ← i = current index (0-based)
      say i

    repeat x times:           ← x is re-read each iteration;
      decrease x by 1           changes inside the loop take effect

    repeat for each item in nums:
      say item

    while x > 0:
      decrease x by 1

  Functions
    make greet(name):
      return "Hello, " + name

    say call greet("World")

  Lists
    set nums to [1, 2, 3]
    add 4 to nums
    remove 2 from nums
    say nums[0]
    say len(nums)

  Logic
    and  or  not
    is   is not   ==  !=  >  <  >=  <=

  Built-in Functions
    len(x)  type(x)  number(x)  text(x)
    round(x)  floor(x)  ceil(x)  abs(x)  sqrt(x)
    max(...)  min(...)  sum(lst)
    random()  randint(a, b)
    upper(s)  lower(s)  title(s)  strip(s)
    replace(s, old, new)  split(s, sep)  join(lst, sep)
    contains(s, sub)  startswith(s, pre)  endswith(s, suf)
    range(n)  range(a, b)  sort(lst)  reverse(lst)
    first(lst)  last(lst)  slice(lst, a, b)
    input("prompt")

  Comments
    # This is a comment

  Control flow
    break
    continue
    return x

Type 'example' to run a sample program.
"""

EXAMPLE = """\
# ── MaySonLang Example ──────────────────────
set name to "MaySonLang"
say "Welcome to " + name + "!"

# ── Variable updates ────────────────────────
set x to 10
say "x starts at: " + x

increase x by 5
say "After increase x by 5: " + x

decrease x by 3
say "After decrease x by 3: " + x

multiply x by 2
say "After multiply x by 2: " + x

divide x by 4
say "After divide x by 4: " + x

# ── Conditionals (now use 'if') ───────────────────
set score to 85
if score >= 90:
  say "Grade: A"
else if score >= 80:
  say "Grade: B"
else if score >= 70:
  say "Grade: C"
else:
  say "Grade: F"

# ── repeat x times (x mutates each loop) ─────────
say "Counting down from 5:"
set count to 5
repeat count times:
  say "  count = " + count
  decrease count by 1

# ── repeat N times (i = loop index) ──────────────
say "Squares:"
repeat 5 times:
  say "  " + i + "^2 = " + (i * i)

# ── while loop ───────────────────────────────────
set n to 3
while n > 0:
  say "n = " + n
  decrease n by 1

# ── Lists ─────────────────────────────────────────
set fruits to ["apple", "banana", "cherry"]
add "mango" to fruits
say "Fruits: " + fruits
repeat for each fruit in fruits:
  say "  - " + upper(fruit)

# ── Functions & recursion ─────────────────────────
make factorial(n):
  if n <= 1:
    return 1
  return n * call factorial(n - 1)

say "5! = " + call factorial(5)
say "10! = " + call factorial(10)
"""


def repl():
    print(BANNER)
    interp = Interpreter()
    scope  = {}
    buffer = []
    in_block = False

    while True:
        try:
            prompt = "... " if (buffer or in_block) else ">>> "
            line   = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        stripped = line.strip()
        if not buffer:
            if stripped == "exit":  print("Bye!"); break
            if stripped == "help":  print(HELP_TEXT); continue
            if stripped == "example":
                print("Running example...\n")
                _run_source(interp, scope, EXAMPLE)
                continue

        buffer.append(line)
        text = "\n".join(buffer)
        last = line.rstrip()

        if last.endswith(":") or (buffer and last.startswith("  ")):
            in_block = True
            continue

        if in_block and stripped == "":
            in_block = False
        elif not last.startswith(" ") and not last.startswith("\t"):
            in_block = False

        if not in_block:
            _run_source(interp, scope, text)
            buffer.clear()


def _run_source(interp, scope, source):
    try:
        tokens = tokenize(source)
        interp.execute(tokens, scope)
    except MaySonLangError as e:
        print(f"\033[91mError: {e}\033[0m")
    except ReturnSignal:
        pass
    except Exception as e:
        print(f"\033[91mUnexpected error: {e}\033[0m")


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) == 1:
        repl()
    elif len(sys.argv) == 2:
        path = sys.argv[1]
        if not os.path.exists(path):
            print(f"Error: file not found: {path}")
            sys.exit(1)
        with open(path) as f:
            source = f.read()
        interp = Interpreter()
        try:
            interp.run(source)
        except MaySonLangError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print("Usage: python MaySonLang.py [file.sl]")
        sys.exit(1)


if __name__ == "__main__":
    main()
