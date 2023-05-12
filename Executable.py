import sys
from Parser import Parser, Node

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

    
    def get_variable(self, lex):
        return self.variables[lex]
        
    def get_constant(self, lex):
        type = self.parser.constants[lex]
        if type == 'int':
            return int(lex)
        if type == "string":
            return lex[1:-1]

    
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

    def execute(self):
        if 'main' in self.parser.functions_ast:
            self.execute_node(self.parser.functions_ast['main'].childrens[0])
        else:
            semantical_error('undefined entry point')
