import sys
from Parser import Parser, Node
import re

def semantical_error(msg):
    print(f'Semantical error: {msg}')
    sys.exit(1)

class Executable:
    def __init__(self, parser: Parser):
        self.parser = parser

    variables = {}
    def assign(self, node: Node):
        var = node.childrens[0].value
        value = self.execute_node(node.childrens[1])
        self.variables[var] = value
    
    def do_while(self, node: Node):
        return_value = self.execute_node(node.childrens[0])
        if return_value is not None:
            return return_value
        while (self.execute_node(node.childrens[1])):
            return_value = self.execute_node(node.childrens[0])
            if return_value is not None:
                return return_value

        
    def sum(self, node: Node):
        lhs = self.execute_node(node.childrens[0])
        rhs = self.execute_node(node.childrens[1])
        return lhs + rhs
    
    def multiply(self, node: Node):
        lhs = self.execute_node(node.childrens[0])
        rhs = self.execute_node(node.childrens[1])
        return lhs * rhs
    
    def mod(self, node: Node):
        lhs = self.execute_node(node.childrens[0])
        rhs = self.execute_node(node.childrens[1])
        return lhs % rhs

    def devide_assign(self, node: Node):
        old_value = self.variables[node.childrens[0].value]
        d = self.execute_node(node.childrens[1])
        new_value = old_value // d
        self.variables[node.childrens[0].value] = new_value

    def not_eq(self, node: Node):
        lhs = self.execute_node(node.childrens[0])
        rhs = self.execute_node(node.childrens[1])
        return lhs != rhs
    
    def cout(self, node: Node):
        for child in node.childrens:
            print(self.execute_node(child), end='')

    def func(self, node: Node):
        arg_num = 0
        for i in self.parser.functions[node.value]:
            var = i[1]
            value = self.execute_node(node.childrens[arg_num])
            arg_num += 1
            self.variables[var] = value
        return self.execute_node(self.parser.functions_ast[node.value].childrens[0])
    
    def ret(self, node: Node):
        return self.execute_node(node.childrens[0])

    
    def get_variable(self, lex):
        return self.variables[lex]
        
    def get_constant(self, lex):
        type = self.parser.constants[lex]
        if type == 'int':
            return int(lex)
        if type == "string":
            return lex[1:-1]
        
    def asm_insertion(self, asm_commands):
        supported_reg = ['ax', 'bx', 'cx', 'dx']
        mov_reg = r"^(mov (.*), (.*))"
        inc_reg = r"inc (.*)"
        reg_values = {}
        for command in asm_commands:
            if m := re.match(mov_reg, command):
                to_reg = False
                arg1 = m.group(2)
                arg2 = m.group(3)
                if (arg1 not in self.parser.variables and arg1 not in supported_reg) or (arg2 not in self.parser.variables and arg2 not in supported_reg):
                    semantical_error("neither supported reg or variable")
                if arg1 in supported_reg:
                    to_reg = True 
                
                if to_reg:
                    reg_values[arg1] = self.variables[arg2]
                else:
                    self.variables[arg1] = reg_values[arg2]
            elif m := re.match(inc_reg, command):
                arg = m.group(1)
                if arg not in supported_reg:
                    semantical_error("inc only applyed to register")
                reg_values[arg] += 1

    
    def execute_node(self, node: Node):
        if node.kind == 'body':
            for child in node.childrens:
                if child is None:
                    continue
                return_value = self.execute_node(child)
                if return_value is not None:
                    return return_value
            #return self.execute_node(node.ch)
        else:
            k = node.kind
            if node.kind == '=':
                self.assign(node)
            elif node.kind == 'do':
                self.do_while(node)
            elif node.kind == 'constant':
                return self.get_constant(node.value)
            elif node.kind == 'variable':
                return self.get_variable(node.value)
            elif node.kind == '+':
                return self.sum(node)
            elif node.kind == '*':
                return self.multiply(node)
            elif node.kind == '%':
                return self.mod(node)
            elif node.kind == '/=':
                return self.devide_assign(node)
            elif node.kind == '!=':
                return self.not_eq(node)
            elif node.kind == 'cout':
                self.cout(node)
            elif node.kind == 'function':
                return self.func(node)
            elif node.kind == 'return':
                return self.ret(node)
            elif m := re.match(r"asm_insertion(.*)", k):
                asm_n = m.group(1)
                return self.asm_insertion(self.parser.asm_insertions[int(asm_n)])

    def execute(self):
        if 'main' in self.parser.functions_ast:
            self.execute_node(self.parser.functions_ast['main'].childrens[0])
        else:
            semantical_error('undefined entry point')
