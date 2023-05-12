import sys
import re

class Node:
    childrens = []

    def __init__(self, kind, value=None, childrens=None):
        self.kind = kind
        self.value = value
        self.childrens = childrens if childrens is not None else []


def printTree(x, depth=0):
    if x is None:
        return

    prefix = "|   " * depth
    if x.value is not None:
        print(f"{prefix}x---{x.value}")
    else:
        print(f"{prefix}x---{x.kind}")
    
    for child in x.childrens:
        printTree(child, depth + 1)

class Var:
    def __init__(self, lex, depth):
        self.lex = lex
        self.depth = depth

    def __eq__(self, other):
        return (self.lex == other.lex) and (self.depth <= other.depth)

class Parser:
    all_tokens = []
    variables = {}
    functions = {}
    asm_insertions = {}
    constants = []

    functions_ast = {}

    k = 0
    is_cycle = False
    is_assignment = False
    # is_cout = False

    open_brace = 0
    close_brace = 0
    new_var = []
    cur_depth = 0

    type = None

    def __init__(self, all_tokens, variables, constants, functions, asm_insertions):
        self.all_tokens = all_tokens
        self.variables = variables
        self.constants = constants
        self.functions = functions
        self.asm_insertions = asm_insertions

    def next_token(self):
        if (self.k != len(self.all_tokens) - 1):
            self.k += 1

    def check_token(self):
        if self.all_tokens[self.k].lex in ('int', 'string', 'float'):
            self.is_assignment = True
            self.type = self.all_tokens[self.k].lex
            self.next_token()

    def error(self, token, msg):
        if token.lex == 'end':
            token = self.all_tokens[self.k - 1]

        new_pos = token.pos - len(token.lex) - 1
        new_line = token.line if new_pos >= 0 else token.line - 1
        #new_pos = new_pos if new_pos >= 0 else len(self.lines[new_line-1]) + new_pos

        print(f'line: {new_line}. Parser error: {msg}')
        sys.exit(1)


    def semantical_error(self, token, msg):
        if token.lex == 'end':
            token = self.all_tokens[self.k - 1]

        new_pos = token.pos - len(token.lex) - 1
        new_line = token.line if new_pos >= 0 else token.line - 1
        new_pos = new_pos if new_pos >= 0 else len(self.lines[new_line-1]) + new_pos

        print(f'line: {new_line}, pos: {new_pos}. Semantical error: {msg}')
        sys.exit(1)

    def id(self):
        lex = self.all_tokens[self.k].lex
        if lex in self.variables:
            if self.is_assignment and Var(lex, self.cur_depth) in self.new_var:
                self.error(self.all_tokens[self.k], f'this variable already exists: {lex}')
            elif not self.is_assignment and Var(lex, self.cur_depth) not in self.new_var:
                self.error(self.all_tokens[self.k], f'this variable doesnt exist: {lex}')
            if self.type and self.variables[lex] != self.type:
                self.semantical_error(self.all_tokens[self.k], f"Incorrect type '{self.variables[lex]}', should be '{self.type}'")
            else:
                self.type = self.variables[lex]
            n = Node('variable', lex)
            if self.is_assignment:
                self.new_var.append(Var(lex, self.cur_depth))
            self.next_token()
            return n
        elif lex in self.constants:
            if self.is_assignment:
                self.error(self.all_tokens[self.k], 'must be a variable, not a constant')
            if self.type and self.constants[lex] != self.type:
                self.semantical_error(self.all_tokens[self.k], f"Incorrect type '{self.constants[lex]}', should be '{self.type}'")
            else:
                self.type = self.constants[lex]
            n = Node('constant', lex)
            self.next_token()
            return n
        elif lex in self.functions:
            n = Node('function', lex)
            args_num = len(self.functions[lex])
            for _ in range(args_num):
                self.next_token()
                type = self.all_tokens[self.k].lex
                if type in self.constants:
                    n.childrens.append(Node("constant", self.all_tokens[self.k].lex))
                if type in self.variables:
                    n.childrens.append(Node('variable', self.all_tokens[self.k].lex))
            self.next_token()
            return n
        else:
            return self.parenthesis_expression()

    def higher_priority_op(self):
        left = self.id()
        while True:
            op = self.all_tokens[self.k].lex
            if op not in ('*', '/', '%'):
                break
            self.next_token()
            right = self.id()
            left = Node(op, childrens=[left, right])
        return left

    def lower_priority_op(self):
        left = self.higher_priority_op()
        while True:
            op = self.all_tokens[self.k].lex
            if op not in ('+', '-'):
                break
            self.next_token()
            right = self.higher_priority_op()
            left = Node(op, childrens=[left, right])
        return left

    def comparison(self):
        operators = {'<': '<', '>': '>', '==': '==', '!=': '!=', '<=': '<=', '>=': '>='}
        n = self.lower_priority_op()
        token_lex = self.all_tokens[self.k].lex
        if self.is_assignment and token_lex in operators:
            self.error(self.all_tokens[self.k], 'incorrect expression')
        while token_lex in operators:
            self.next_token()
            n = Node(operators[token_lex], childrens=[n, self.lower_priority_op()])
            token_lex = self.all_tokens[self.k].lex
        return n


    def assignment(self):
        n = self.comparison()
        
        if n.kind != 'variable':
            return n
        
        if self.all_tokens[self.k].lex == '=':
            self.is_assignment = False
            self.next_token()
            n = Node('=', childrens=[n, self.lower_priority_op()])
        elif self.is_assignment and self.all_tokens[self.k].lex in ('/=', '*=', '+=', '-=', '%='):
            self.error(self.all_tokens[self.k], 'inccorrect expression')
        else:
            operators = {'/=': '/', '*=': '*', '+=': '+', '-=': '-', '%=': '/'}
            op = operators.get(self.all_tokens[self.k].lex)
            
            if op:
                self.next_token()
                n = Node(op + '=', childrens=[n, self.lower_priority_op()])
        
        return n

    def consume_token(self, lexeme):
        if self.all_tokens[self.k].lex != lexeme:
            self.error(self.all_tokens[self.k], f'Expected "{lexeme}"')
        token = self.all_tokens[self.k]
        self.next_token()
        return token

    def parenthesis_expression(self):
        token = self.consume_token('(')
        n = self.assignment()
        self.consume_token(')')
        return n

    def _if_statement(self):
        n = Node('if')
        self.next_token()
        p_exp = self.parenthesis_expression()
        if self.all_tokens[self.k].lex != '{':
            self.error(self.all_tokens[self.k], '"{" expected')
        self.type = None
        n.childrens = [p_exp, self.statement()]
        if self.all_tokens[self.k].lex == 'else':
            n.kind = 'if_else'
            self.next_token()
            if self.all_tokens[self.k].lex != '{':
                self.error(self.all_tokens[self.k], '"{" expected')
            self.type = None
            n.childrens.append(self.statement())
        return n

    def _while_statement(self):
        self.is_cycle = True
        n = Node('while')
        self.next_token()
        p_exp = self.parenthesis_expression()
        if self.all_tokens[self.k].lex != '{':
            self.error(self.all_tokens[self.k], '"{" expected')
        self.type = None
        n.childrens = [p_exp, self.statement()]
        return n

    def _do_statement(self):
        self.is_cycle = True
        n = Node('do')
        self.next_token()
        if self.all_tokens[self.k].lex != '{':
            self.error(self.all_tokens[self.k], '"{" expected')
        self.type = None
        n.childrens = [self.statement()]
        if self.all_tokens[self.k].lex != 'while':
            self.error(self.all_tokens[self.k], '"while" expected')
        self.next_token()
        n.childrens.append(self.parenthesis_expression())
        if self.all_tokens[self.k].lex != ';':
            self.error(self.all_tokens[self.k], '";" expected')
        self.type = None
        return n

    def _for_statement(self):
        self.is_cycle = True
        n = Node('for')
        self.next_token()
        if self.all_tokens[self.k].lex != '(':
            self.error(self.all_tokens[self.k], '"(" expected')
        self.next_token()
        self.check_token()
        n.childrens = [self.assignment()]
        if self.all_tokens[self.k].lex != ';':
            self.error(self.all_tokens[self.k], '";" expected')
        self.is_assignment = False
        self.type = None
        self.next_token()
        self.check_token()
        if (self.is_assignment):
            self.error(self.all_tokens[self.k], 'inccorrect expression')
        n.childrens.append(self.assignment())
        if self.all_tokens[self.k].lex != ';':
            self.error(self.all_tokens[self.k], '";" expected')
        self.type = None
        self.next_token()
        self.check_token()
        if (self.is_assignment):
            self.error(self.all_tokens[self.k], 'inccorrect expression')
        n.childrens.append(self.assignment())
        if self.all_tokens[self.k].lex != ')':
            self.error(self.all_tokens[self.k], '")" expected')
        self.next_token()
        if self.all_tokens[self.k].lex != '{':
            self.error(self.all_tokens[self.k], '"{" expected')
        self.type = None
        n.childrens.append(self.statement())
        return n
    
    def _loop_control_statement(self):
        if(self.is_cycle and self.all_tokens[self.k].lex == 'continue'):
            n = Node('continue')
            self.next_token()
            if self.all_tokens[self.k].lex != ';':
                self.error(self.all_tokens[self.k], '";" expected')
            self.type = None
        elif (self.is_cycle and self.all_tokens[self.k].lex == 'break'):
            n = Node('break')
            self.next_token()
            if self.all_tokens[self.k].lex != ';':
                self.error(self.all_tokens[self.k], '";" expected')
            self.type = None
        elif not self.is_cycle and self.all_tokens[self.k].lex == 'continue':
            self.error(self.all_tokens[self.k], 'a continue statement may only be used within a loop')
        elif not self.is_cycle and self.all_tokens[self.k].lex == 'break':
            self.error(self.all_tokens[self.k], 'a break statement may only be used within a loop')
        return n
    
    def _cout_statement(self):
        # self.is_cout = True
        self.type = None
        n = Node('cout')
        self.next_token()
        if (self.all_tokens[self.k].lex != '<<'):
            self.error(self.all_tokens[self.k], '<< expected')
        else:
            self.type = None
            self.next_token()
        n.childrens = [self.lower_priority_op()]
        while self.all_tokens[self.k].lex == '<<':
            self.type = None
            self.next_token()
            n.childrens.append(self.lower_priority_op())
        if self.all_tokens[self.k].lex != ';':
            self.error(self.all_tokens[self.k], '; expected')
        self.type = None
        # self.is_cout = False
        return n

    def _brace_statement(self):
        self.type = None
        self.open_brace += 1
        self.cur_depth += 1
        n = Node('body')
        self.next_token()
        if (self.all_tokens[self.k].lex == '}'):
            self.next_token()
            return n
        n.childrens = [self.statement()]
        while self.all_tokens[self.k].lex != '}':
            n.childrens.append(self.statement())
            if self.all_tokens[self.k].lex == 'end':
                self.error(self.all_tokens[self.k], '"}" expected')
        self.close_brace += 1
        self.cur_depth -= 1
        if (self.open_brace == self.close_brace):
            self.is_cycle = False
        self.next_token()
        return n


    def _return_token(self):
        n = Node('return')
        self.next_token()
        what_return = self.all_tokens[self.k].lex
        if what_return in self.constants:
            n.childrens.append(Node("constant", what_return))
        elif what_return in self.variables:
            n.childrens.append(Node("variable", what_return))
        self.next_token()
        return n


    inside_func = False
    all_done = False
    def statement(self):
        if self.all_tokens[self.k].lex == 'end' or self.k >= len(self.all_tokens):
            self.all_done = True
            return
        if (l := self.all_tokens[self.k].lex) in self.functions:
            if l not in self.functions_ast: # function declaration
                self.inside_func = True
                args_num = len(self.functions[l])
                for _ in range(args_num):
                    self.next_token()
                    t = self.all_tokens[self.k].lex
                    self.new_var.append(Var(self.all_tokens[self.k].lex.split(' ')[1], self.cur_depth))
                self.next_token()
                node = Node('o')
                node.childrens.append(self._brace_statement())
                self.functions_ast[l] = node
                self.inside_func = False
            else: # function invocation
                args_num = len(self.functions[l])
                node = Node("function", l)  
                for i in range(args_num):
                    self.next_token()
                    node.childrens.append(Node("argument", self.all_tokens[self.k].lex))
                self.next_token()
                return node
        if not self.inside_func:
            self.next_token()
            self.statement()
        if self.all_done:
            return

        current_insertion = self.all_tokens[self.k].lex
        if self.all_tokens[self.k].lex == 'if':
            return self._if_statement()
        elif self.all_tokens[self.k].lex == 'while':
            return self._while_statement()
        elif self.all_tokens[self.k].lex == 'do':
            return self._do_statement()
        elif self.all_tokens[self.k].lex == 'for':
            return self._for_statement()
        elif self.all_tokens[self.k].lex == 'continue' or self.all_tokens[self.k].lex == 'break':
            return self._loop_control_statement()
        elif self.all_tokens[self.k].lex == 'cout':
            return self._cout_statement()
        elif self.all_tokens[self.k].lex == 'return':
            return self._return_token()
        elif m := re.match(r"asm_insertion(.*)", current_insertion):
            cur_n = int(m.group(1))
            n = Node(current_insertion, self.asm_insertions[cur_n])
            self.next_token()
            return n
        elif self.all_tokens[self.k].lex == ';':
            n = None
            self.is_assignment = False
            self.type = None
            self.next_token()
        elif self.all_tokens[self.k].lex == '{':
            return self._brace_statement()
        elif self.all_tokens[self.k].lex == '}':
            self.error(self.all_tokens[self.k], '"{" expected')
        elif self.all_tokens[self.k].lex == 'int' or self.all_tokens[self.k].lex == 'string' or self.all_tokens[self.k].lex == 'float':
            n = None
            self.is_assignment = True
            self.type = self.all_tokens[self.k].lex
            self.next_token()
        else:
            n = self.assignment()
            if self.all_tokens[self.k].lex == ',':
                self.is_assignment = True
                self.next_token()
                if self.all_tokens[self.k].lex not in self.variables:
                    self.error(self.all_tokens[self.k], 'variable expected')
            elif self.all_tokens[self.k].lex != ';':
                self.error(self.all_tokens[self.k], '";" expected')
            else:
                self.is_assignment = False
                self.type = None
                self.next_token()
        return n

    def parse(self):
        self.statement()
        return self.functions_ast
