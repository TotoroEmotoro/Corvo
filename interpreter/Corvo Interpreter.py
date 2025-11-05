# Corvo Language and Runtime
# Copyright (c) 2025 Austin (GitHub: TotoroEmotoro)
# Licensed under the Corvo Source-Available License, Version 1.0.
#
# Permission is granted to use Corvo to write and distribute your own programs.
# You may view and study the Corvo source code for educational purposes.
# You may NOT modify or redistribute Corvo itself without written permission.
#
# See the LICENSE file for full license text.



from lark import Lark, Transformer
import sys
import csv

class CorvoInterpreter(Transformer):
    def __init__(self):
        self.vars = {}
        self.sections = {}

    def start(self, items):
        for item in items:
            if hasattr(item, 'children') and len(item.children) > 0:
                func = item.children[0]
                if callable(func):
                    try:
                        func()
                    except Exception as e:
                        print(f"Error executing statement: {e}")
                elif hasattr(func, 'data') and func.data == 'while':
                    # Handle while loop specially
                    try:
                        while_func = self.while_(func.children)
                        while_func()
                    except Exception as e:
                        print(f"Error executing while loop: {e}")
            elif callable(item):
                try:
                    item()
                except Exception as e:
                    print(f"Error executing statement: {e}")
        return items

    def STRING(self, token):
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

    def assignment(self, items):

        varname, value = items
        def assign():
            new_value = self.evaluate(value)
            self.vars[varname] = new_value
        return assign

    def display(self, items):
        expr = items[0]
        return lambda: print(self.evaluate(expr))

    def input(self, items):
        prompt, remember_as_token, varname = items
        def store_input():
            user_input = input(self.evaluate(prompt)).strip()
            try:
                if '.' in user_input:
                    user_input = float(user_input)
                else:
                    user_input = int(user_input)
            except ValueError:
                pass  
            self.vars[varname] = user_input
        return store_input
    
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
        if len(items) == 4:
            condition, then_stmt, otherwise_token, else_stmt = items
        elif len(items) == 3:
            condition, then_stmt, else_stmt = items
        else:
            print(f"ERROR: if_else expected 3 or 4 items but got {len(items)}")
            return lambda: None
        
        def run():
            if self.evaluate(condition):
                if hasattr(then_stmt, 'children') and len(then_stmt.children) > 0:
                    stmt_func = then_stmt.children[0]
                    if callable(stmt_func):
                        stmt_func()
                elif callable(then_stmt):
                    then_stmt()
            else:
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
            cond_result = self.evaluate(condition)
            if cond_result:
                for stmt in block:
                    stmt()
        return run

    def if_else_block(self, items):

        otherwise_index = -1
        for i, item in enumerate(items):
            if hasattr(item, 'type') and item.type == 'OTHERWISE':
                otherwise_index = i
                break
        
        if otherwise_index == -1:
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
        loops_token = items[1] 
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
        while_token = items[0]
        condition_tree = items[1] 
        do_token = items[2]
        statement_trees = items[3:] 
        block = []
        for stmt_tree in statement_trees:
            if hasattr(stmt_tree, 'children') and len(stmt_tree.children) > 0:
                block.append(stmt_tree.children[0])
            else:
                block.append(stmt_tree)
        
        def run():
            max_iterations = 10000
            iterations = 0
            
            while iterations < max_iterations:
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
            
            if iterations >= max_iterations:
                print("(Warning: While loop stopped after 10,000 iterations to prevent infinite loop)")
        
        return run


    def for_loop(self, items):
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
    def write(self, items):
        content, filename = items
        def write_file():
            with open(self.evaluate(filename), 'w') as f:
                f.write(str(self.evaluate(content)))
        return write_file

    def read(self, items):
        if len(items) == 3:
            if str(items[1]) == "remember as":
                filename, remember_as_token, varname = items
            else:
                read_from_token, filename, varname = items
        elif len(items) == 4:
            read_from_token, filename, remember_as_token, varname = items
        elif len(items) == 2:
            filename, varname = items
        else:
            filename = items[0]
            varname = items[-1]
            
        def read_file():
            try:
                with open(self.evaluate(filename), 'r') as f:
                    content = f.read().strip()
                    self.vars[varname] = content
            except FileNotFoundError:
                print(f"(Error: File {self.evaluate(filename)} not found.)")
                self.vars[varname] = ""
        return read_file
    

    def csv_read(self, items):
        read_csv_token, filename, remember_as_token, varname = items
        
        def read_csv_file():
            try:
                with open(self.evaluate(filename), 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    data = []
                    for row in reader:
                        data.append(row)
                    self.vars[varname] = data
            except FileNotFoundError:
                print(f"(Error: CSV file {self.evaluate(filename)} not found.)")
                self.vars[varname] = []
            except Exception as e:
                print(f"(Error reading CSV: {e})")
                self.vars[varname] = []
        return read_csv_file

    def csv_write(self, items):
        varname, to_csv_token, filename = items
        
        def write_csv_file():
            try:
                data = self.vars.get(varname, [])
                if not isinstance(data, list):
                    print(f"(Error: {varname} is not a list, cannot write to CSV)")
                    return
                    
                with open(self.evaluate(filename), 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for row in data:
                        if isinstance(row, list):
                            writer.writerow(row)
                        else:
                            writer.writerow([row]) 
            except Exception as e:
                print(f"(Error writing CSV: {e})")
        return write_csv_file

    def column_access(self, items):
        get_column_token, column_number, from_token, varname = items
        
        def get_column():
            data = self.vars.get(varname, [])
            if not isinstance(data, list):
                print(f"(Error: {varname} is not a list.)")
                return []
            
            col_idx = self.evaluate(column_number)
            if isinstance(col_idx, str):
                try:
                    col_idx = int(col_idx)
                except ValueError:
                    print(f"(Error: Column '{col_idx}' is not a valid number.)")
                    return []
            
            column = []
            for row in data:
                if isinstance(row, list) and 1 <= col_idx <= len(row):
                    column.append(row[col_idx - 1]) 
                else:
                    column.append("") 
            
            return column
        
        return get_column

    def csv_set(self, items):
        varname, row_token, row_number, column_token, column_number, new_value = items
        
        def set_cell():
            data = self.vars.get(varname, [])
            if not isinstance(data, list):
                print(f"(Error: {varname} is not a list.)")
                return
            
            row_idx = self.evaluate(row_number)
            col_idx = self.evaluate(column_number)
            
            if isinstance(row_idx, str):
                try:
                    row_idx = int(row_idx)
                except ValueError:
                    print(f"(Error: Row '{row_idx}' is not a valid number.)")
                    return
                    
            if isinstance(col_idx, str):
                try:
                    col_idx = int(col_idx)
                except ValueError:
                    print(f"(Error: Column '{col_idx}' is not a valid number.)")
                    return
            
            if not (1 <= row_idx <= len(data)):
                print(f"(Error: Row {row_idx} out of range. Data has {len(data)} rows.)")
                return
                
            target_row = data[row_idx - 1]  
            if not isinstance(target_row, list):
                print(f"(Error: Row {row_idx} is not a list.)")
                return
                
            if not (1 <= col_idx <= len(target_row)):
                print(f"(Error: Column {col_idx} out of range. Row {row_idx} has {len(target_row)} columns.)")
                return
            
            new_val = self.evaluate(new_value)
            data[row_idx - 1][col_idx - 1] = str(new_val)  
            
        return set_cell

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
                print(f"(Error: Section '{name}' not defined.)")
        return run

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
                print("(Error: Division by zero)")
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
                    print(f"(Error: Index '{idx}' is not a valid number.)")
                    return ""
            if not isinstance(lst, list):
                print(f"(Error: {varname} is not a list.)")
                return ""
            if not (1 <= idx <= len(lst)):
                print(f"(Error: Index {idx} out of range for list '{varname}'.)")
                return ""
            return lst[idx-1]
        return get_item

    def evaluate(self, func_or_value):
        if hasattr(func_or_value, 'children') and len(func_or_value.children) > 0:
            func_or_value = func_or_value.children[0]
        
        if callable(func_or_value):
            return func_or_value()
        elif isinstance(func_or_value, str):
            if func_or_value in self.vars:
                return self.vars[func_or_value]
            else:
                return func_or_value
        else:
            return func_or_value

def run_program(filename):
    with open(filename, 'r') as f:
        code = f.read()
    
    with open('grammar.lark', 'r') as f:
        grammar = f.read()
    
    try:
        parser = Lark(grammar, start='start')
        tree = parser.parse(code)
        interpreter = CorvoInterpreter()
        result = interpreter.transform(tree)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python interpreter.py <filename>")
        sys.exit(1)
    run_program(sys.argv[1])
