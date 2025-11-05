# Corvo Browser Runtime
# Copyright (c) 2025 Austin (GitHub: TotoroEmotoro)
# Licensed under the Corvo Source-Available License, Version 1.0.
# See LICENSE for full terms.
#
# This module is a browser-safe interpreter for Corvo.
# It is designed to run inside Pyodide (Python in the browser),
# and be loaded dynamically by the Corvo-Coder playground.
#
# Key differences from the desktop interpreter:
# - All output is captured into a buffer instead of using print().
# - Blocking input() is stubbed out.
# - File and CSV I/O are stubbed or simulated instead of touching the local filesystem.
# - A hard iteration cap protects against infinite loops in while-loops.
#
# Public API:
#     run_corvo(source_code: str) -> tuple[str, str]
#         Returns (program_output, debug_info_string)

from lark import Lark, Transformer
import csv
RUNTIME_ID = "Corvo Browser Runtime 2025-11-05"


CORVO_GRAMMAR = r"""
start: statement*

statement: assignment
         | display
         | input
         | conditional
         | repeat
         | while
         | for_loop
		 | repeat
         | write
         | read
         | csv_read
         | csv_write
         | csv_set
         | section_def
         | list_append
         | list_remove
         | section_call

assignment: "the" WORD "is" expr

display: "display" expr

input: "ask" expr REMEMBER_AS WORD

conditional: "if" condition "then" statement OTHERWISE statement  -> if_else
           | "if" condition "then" statement                     -> if_only
           | "if" condition "then" ":" "[" statement* "]" OTHERWISE ":" "[" statement* "]"  -> if_else_block
           | "if" condition "then" ":" "[" statement* "]"         -> if_only_block

condition: base_condition
         | condition AND condition  -> and_
         | condition OR condition   -> or_

base_condition: expr comparator expr

repeat: "repeat" expr LOOPS statement                              -> repeat_single
      | "repeat" expr LOOPS ":" "[" statement* "]"                 -> repeat_block

while: WHILE condition DO ":" "[" statement* "]"

for_loop: "for" "each" WORD "in" WORD ":" "[" statement* "]"

write: "write" expr "to" expr

read: READ_FROM expr REMEMBER_AS WORD

csv_read: READ_CSV expr REMEMBER_AS WORD

csv_write: "write" WORD TO_CSV expr

csv_set: "set" WORD ROW expr COLUMN expr "to" expr

section_def: SECTION WORD "is" "[" statement* "]"

list_append: "append" expr "to" WORD

list_remove: "remove" expr "from" WORD

section_call: WORD

expr: list
    | length
    | count
    | concat
    | math_expr
    | index_access
    | column_access
    | STRING
    | NUMBER
    | WORD

list: "[" [expr ("," expr)*] "]"

length: LENGTH_OF expr

count: COUNT_OF WORD

concat: expr PLUS expr

math_expr: expr MINUS expr        -> subtract
         | expr TIMES expr        -> multiply
         | expr DIVIDED_BY expr   -> divide

index_access: WORD AT expr

column_access: GET_COLUMN expr FROM WORD

comparator: IS_EQUAL_TO
          | IS_GREATER_THAN
          | IS_LESS_THAN

%import common.WS
COMMENT: /#[^\r\n]*/
COUNT_OF.10: "count of"
LOOPS.10: "loops"
WHILE.10: "while"
DO.10: "do"
AT.10: "at"
AND.10: "and"
OR.10: "or"
OTHERWISE.10: "otherwise"
PLUS.10: "plus"
MINUS.10: "minus"
TIMES.10: "times"
SECTION.10: "section"
IS_EQUAL_TO.10: "is equal to"
IS_GREATER_THAN.10: "is greater than"
IS_LESS_THAN.10: "is less than"
REMEMBER_AS.10: "remember as"
READ_FROM.10: "read from"
READ_CSV.10: "read csv"
TO_CSV.10: "to csv"
GET_COLUMN.10: "get column"
FROM.10: "from"
ROW.10: "row"
COLUMN.10: "column"
LENGTH_OF.10: "length of"
DIVIDED_BY.10: "divided by"
%import common.CNAME -> WORD
%import common.ESCAPED_STRING -> STRING
%import common.NUMBER
%ignore WS
%ignore COMMENT

"""


class CorvoInterpreter(Transformer):
    """
    CorvoInterpreter walks the parsed syntax tree and executes Corvo code.

    This version is adapted for browser use:
    - Stores variables in self.vars
    - Stores defined sections (your "functions") in self.sections
    - Appends output to self._stdout instead of printing
    - Stubs blocking features (input, file I/O) so the browser sandbox is safe
    """

    def __init__(self):
        self.vars = {}
        self.sections = {}
        self._stdout = []
        self._max_loop_iterations = 10000  # safety against infinite loops

    # ========== helpers ==========

    def _print(self, value):
        """Append text to output buffer instead of printing to console."""
        self._stdout.append(str(value))

    def evaluate(self, func_or_value):
        """
        Your original interpreter sometimes returns callables (lambdas),
        sometimes raw values, sometimes tree nodes with .children.

        This normalize step is basically the same logic you already wrote.
        """
        if hasattr(func_or_value, 'children') and len(func_or_value.children) > 0:
            func_or_value = func_or_value.children[0]

        if callable(func_or_value):
            return func_or_value()
        elif isinstance(func_or_value, str):
            # variable lookup fallback
            if func_or_value in self.vars:
                return self.vars[func_or_value]
            else:
                return func_or_value
        else:
            return func_or_value

    # ========== program start ==========

    def start(self, items):
        """
        Runs each top-level statement or block in sequence.
        Mirrors your start() method, but uses _print() for errors.
        """
        for item in items:
            if hasattr(item, 'children') and len(item.children) > 0:
                func = item.children[0]
                if callable(func):
                    try:
                        func()
                    except Exception as e:
                        self._print(f"Error executing statement: {e}")
                elif hasattr(func, 'data') and func.data == 'while':
                    # handle while loops specially
                    try:
                        while_func = self.while_(func.children)
                        while_func()
                    except Exception as e:
                        self._print(f"Error executing while loop: {e}")
            elif callable(item):
                try:
                    item()
                except Exception as e:
                    self._print(f"Error executing statement: {e}")
        return items

    # ========== literals / terminals ==========

    def STRING(self, token):
        # Return a callable that yields the string contents without quotes.
        return lambda: str(token)[1:-1]

    def NUMBER(self, token):
        token_str = str(token)
        try:
            if '.' in token_str:
                value = float(token_str)
            else:
                value = int(token_str)
        except ValueError:
            value = 0
        return lambda: value

    def WORD(self, token):
        return str(token)

    # ========== assignments, display, input ==========

    def assignment(self, items):
        varname, value = items
        def assign():
            new_value = self.evaluate(value)
            self.vars[varname] = new_value
        return assign

    def display(self, items):
        expr = items[0]
        return lambda: self._print(self.evaluate(expr))

    def input(self, items):
        """
        Desktop version:
            ask "Enter age:" remember as age
        Browser version:
            we can't prompt() in pure Pyodide without JS bridge,
            so we just set empty string.
        """
        prompt, remember_as_token, varname = items
        def store_input():
            # Stub: no interactive input in browser yet.
            self.vars[varname] = ""
        return store_input

    # ========== conditionals ==========

    def if_only(self, items):
        condition_tree, statement_tree = items
        condition = condition_tree.children[0] if hasattr(condition_tree, 'children') else condition_tree
        stmt = statement_tree.children[0] if hasattr(statement_tree, 'children') else statement_tree
        def run():
            cond_result = self.evaluate(condition)
            if cond_result:
                stmt()
        return run

    def if_else(self, items):
        # Support both forms you already handle (3 or 4 elements)
        if len(items) == 4:
            condition, then_stmt, otherwise_token, else_stmt = items
        elif len(items) == 3:
            condition, then_stmt, else_stmt = items
        else:
            def noop():
                pass
            return noop

        def run():
            if self.evaluate(condition):
                # execute "then" branch
                if hasattr(then_stmt, 'children') and len(then_stmt.children) > 0:
                    stmt_func = then_stmt.children[0]
                    if callable(stmt_func):
                        stmt_func()
                elif callable(then_stmt):
                    then_stmt()
            else:
                # execute "else" branch
                if hasattr(else_stmt, 'children') and len(else_stmt.children) > 0:
                    stmt_func = else_stmt.children[0]
                    if callable(stmt_func):
                        stmt_func()
                elif callable(else_stmt):
                    else_stmt()
        return run

    def if_only_block(self, items):
        condition_tree = items[0]
        statement_trees = items[1:]
        condition = condition_tree.children[0] if hasattr(condition_tree, 'children') else condition_tree
        block = [tree.children[0] if hasattr(tree, 'children') else tree for tree in statement_trees]
        def run():
            if self.evaluate(condition):
                for stmt in block:
                    stmt()
        return run

    def if_else_block(self, items):
        # You scan for OTHERWISE in your code. We'll replicate it.
        otherwise_index = -1
        for i, item in enumerate(items):
            if hasattr(item, 'type') and item.type == 'OTHERWISE':
                otherwise_index = i
                break

        if otherwise_index == -1:
            # if-without-else
            condition_tree = items[0]
            statement_trees = items[1:]
            condition = condition_tree.children[0] if hasattr(condition_tree, 'children') else condition_tree
            block = [tree.children[0] if hasattr(tree, 'children') else tree for tree in statement_trees]
            def run():
                if self.evaluate(condition):
                    for stmt in block:
                        stmt()
            return run
        else:
            # if ... otherwise ...
            condition = items[0]
            then_statements = items[1:otherwise_index]
            else_statements = items[otherwise_index + 1:]

            then_block = []
            for stmt_tree in then_statements:
                if hasattr(stmt_tree, 'children') and len(stmt_tree.children) > 0:
                    then_block.append(stmt_tree.children[0])
                else:
                    then_block.append(stmt_tree)

            else_block = []
            for stmt_tree in else_statements:
                if hasattr(stmt_tree, 'children') and len(stmt_tree.children) > 0:
                    else_block.append(stmt_tree.children[0])
                else:
                    else_block.append(stmt_tree)

            def run():
                if self.evaluate(condition):
                    for stmt in then_block:
                        if callable(stmt):
                            stmt()
                else:
                    for stmt in else_block:
                        if callable(stmt):
                            stmt()
            return run

    # ========== boolean / comparisons ==========

    def and_(self, items):
        left_tree, and_token, right_tree = items
        left = left_tree.children[0] if hasattr(left_tree, 'children') else left_tree
        right = right_tree.children[0] if hasattr(right_tree, 'children') else right_tree
        def cond():
            return self.evaluate(left) and self.evaluate(right)
        return cond

    def or_(self, items):
        left_tree, or_token, right_tree = items
        left = left_tree.children[0] if hasattr(left_tree, 'children') else left_tree
        right = right_tree.children[0] if hasattr(right_tree, 'children') else right_tree
        def cond():
            return self.evaluate(left) or self.evaluate(right)
        return cond

    def base_condition(self, items):
        left, op, right = items
        def cond():
            l_val = self.evaluate(left)
            r_val = self.evaluate(right)

            if hasattr(op, 'children') and len(op.children) > 0:
                op_str = op.children[0]
            else:
                op_str = op

            if op_str == "is equal to":
                result = l_val == r_val
            elif op_str == "is greater than":
                result = l_val > r_val
            elif op_str == "is less than":
                result = l_val < r_val
            else:
                result = False

            return result
        return cond

    def IS_EQUAL_TO(self, token):
        return "is equal to"

    def IS_GREATER_THAN(self, token):
        return "is greater than"

    def IS_LESS_THAN(self, token):
        return "is less than"

    # ========== loops ==========

    def repeat_single(self, items):
        times_tree, loops_token, stmt_tree = items
        times = times_tree.children[0] if hasattr(times_tree, 'children') else times_tree
        stmt = stmt_tree.children[0] if hasattr(stmt_tree, 'children') else stmt_tree
        def run():
            times_val = self.evaluate(times)
            if isinstance(times_val, str):
                try:
                    times_val = int(times_val)
                except ValueError:
                    times_val = 0
            for _ in range(times_val):
                stmt()
        return run

    def repeat_block(self, items):
        times_tree = items[0]
        # items[1] is e.g. "loops"
        statement_trees = items[2:]
        times = times_tree.children[0] if hasattr(times_tree, 'children') else times_tree
        block = [tree.children[0] if hasattr(tree, 'children') else tree for tree in statement_trees]

        def run():
            times_val = self.evaluate(times)
            if isinstance(times_val, str):
                try:
                    times_val = int(times_val)
                except ValueError:
                    times_val = 0

            for _ in range(times_val):
                for stmt in block:
                    if callable(stmt):
                        stmt()
        return run

    def while_(self, items):
        # items: [while_token, condition_tree, do_token, ...block...]
        condition_tree = items[1]
        statement_trees = items[3:]
        block = []
        for stmt_tree in statement_trees:
            if hasattr(stmt_tree, 'children') and len(stmt_tree.children) > 0:
                block.append(stmt_tree.children[0])
            else:
                block.append(stmt_tree)

        def run():
            max_iter = self._max_loop_iterations
            iterations = 0

            while iterations < max_iter:
                condition_func = condition_tree
                if hasattr(condition_tree, 'children') and len(condition_tree.children) > 0:
                    condition_func = condition_tree.children[0]

                condition_result = self.evaluate(condition_func)
                if not condition_result:
                    break

                for stmt in block:
                    if callable(stmt):
                        stmt()

                iterations += 1

            if iterations >= max_iter:
                self._print("(Warning: While loop stopped after max iterations)")
        return run

    def for_loop(self, items):
        # You support both:
        #   for each item in list : [ ... ]
        # and a slightly looser variant
        if len(items) >= 6:
            var = items[2]
            list_name = items[4]
            statement_trees = items[6:]
        else:
            var = items[0]
            list_name = items[1]
            statement_trees = items[2:]

        block = []
        for stmt_tree in statement_trees:
            if hasattr(stmt_tree, 'children') and len(stmt_tree.children) > 0:
                block.append(stmt_tree.children[0])
            else:
                block.append(stmt_tree)

        def run():
            lst = self.vars.get(list_name, [])
            for item in lst:
                self.vars[var] = item
                for stmt in block:
                    if callable(stmt):
                        stmt()
        return run

    # ========== file / CSV features (stubbed for browser) ==========

    def write(self, items):
        content, filename = items
        def write_file():
            # can't write to arbitrary local files in browser sandbox
            self._print(f"(File write skipped in browser: {self.evaluate(filename)})")
        return write_file

    def read(self, items):
        def read_file():
            self._print("(File read skipped in browser)")
        return read_file

    def csv_read(self, items):
        def read_csv_file():
            self._print("(CSV read skipped in browser)")
        return read_csv_file

    def csv_write(self, items):
        def write_csv_file():
            self._print("(CSV write skipped in browser)")
        return write_csv_file

    def column_access(self, items):
        def get_column():
            # browser runtime doesn't have persistent CSV tables yet
            return []
        return get_column

    def csv_set(self, items):
        def set_cell():
            self._print("(CSV cell edit skipped in browser)")
        return set_cell

    # ========== sections (your "functions") ==========

    def section_def(self, items):
        section_token = items[0]
        name_func = items[1]
        statement_trees = items[2:]

        block = []
        for tree in statement_trees:
            if hasattr(tree, 'children') and len(tree.children) > 0:
                block.append(tree.children[0])
            else:
                block.append(tree)

        name = self.evaluate(name_func) if callable(name_func) else name_func
        self.sections[name] = block
        return lambda: None

    def section_call(self, items):
        name_func = items[0]
        def run():
            name = self.evaluate(name_func) if callable(name_func) else name_func
            if name in self.sections:
                for stmt in self.sections[name]:
                    stmt()
            else:
                self._print(f"(Error: Section '{name}' not defined.)")
        return run

    # ========== lists, arithmetic, indexing ==========

    def list_append(self, items):
        item, list_name = items
        def append_item():
            if list_name not in self.vars:
                self.vars[list_name] = []
            if isinstance(self.vars[list_name], list):
                self.vars[list_name].append(self.evaluate(item))
        return append_item

    def list_remove(self, items):
        item, list_name = items
        def remove_item():
            if list_name in self.vars and isinstance(self.vars[list_name], list):
                try:
                    self.vars[list_name].remove(self.evaluate(item))
                except ValueError:
                    pass
        return remove_item

    def list(self, items):
        return lambda: [self.evaluate(item) for item in items]

    def length(self, items):
        _, expr = items
        return lambda: len(str(self.evaluate(expr)))

    def count(self, items):
        _, varname = items
        return lambda: len(self.vars.get(varname, []))

    def concat(self, items):
        left, plus_token, right = items
        def operation():
            left_val = self.evaluate(left)
            right_val = self.evaluate(right)

            # try to coerce numeric strings so "5 plus 7" = 12
            if isinstance(left_val, str) and left_val.replace('.', '').replace('-', '').isdigit():
                try:
                    left_val = float(left_val) if '.' in left_val else int(left_val)
                except ValueError:
                    pass

            if isinstance(right_val, str) and right_val.replace('.', '').replace('-', '').isdigit():
                try:
                    right_val = float(right_val) if '.' in right_val else int(right_val)
                except ValueError:
                    pass

            if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
                return left_val + right_val
            else:
                return str(left_val) + str(right_val)
        return operation

    def subtract(self, items):
        left, minus_token, right = items
        def operation():
            left_val = self.evaluate(left)
            right_val = self.evaluate(right)
            return left_val - right_val
        return operation

    def multiply(self, items):
        left, times_token, right = items
        def operation():
            left_val = self.evaluate(left)
            right_val = self.evaluate(right)
            return left_val * right_val
        return operation

    def divide(self, items):
        left, divided_by_token, right = items
        def operation():
            left_val = self.evaluate(left)
            right_val = self.evaluate(right)
            if right_val == 0:
                self._print("(Error: Division by zero)")
                return 0
            return left_val / right_val
        return operation

    def index_access(self, items):
        varname_func, at_token, index = items
        def get_item():
            varname = self.evaluate(varname_func) if callable(varname_func) else varname_func
            lst = self.vars.get(varname)
            idx = self.evaluate(index)

            if isinstance(idx, str):
                try:
                    idx = int(idx)
                except ValueError:
                    self._print(f"(Error: Index '{idx}' is not a valid number.)")
                    return ""

            if not isinstance(lst, list):
                self._print(f"(Error: {varname} is not a list.)")
                return ""

            if not (1 <= idx <= len(lst)):
                self._print(f"(Error: Index {idx} out of range for list '{varname}'.)")
                return ""

            return lst[idx-1]
        return get_item


# -------------------------------------------------
# 2. Public entry point for the browser
# -------------------------------------------------

def run_corvo(source_code: str):
    """
    Run a Corvo program and return (program_output, debug_info).

    program_output: text that should show in the "Program Output" panel.
    debug_info: text that should show in the "Debug" panel.
    """

    # Build parser from embedded grammar. IMPORTANT:
    # Make sure the start rule name here ('start') matches grammar.lark.
    parser = Lark(CORVO_GRAMMAR, start='start')

    # Parse Corvo source into a tree
    tree = parser.parse(source_code)

    # Transform+execute using CorvoInterpreter
    interp = CorvoInterpreter()
    interp.transform(tree)

    # Gather output and debug info
    program_output = "\n".join(interp._stdout)
    debug_info = "Parsed program successfully.\n" + tree.pretty()

    return program_output, debug_info
