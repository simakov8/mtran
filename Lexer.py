import sys
import re
from prettytable import PrettyTable
from dataclasses import dataclass

@dataclass
class Token:
    lex: str
    line: int = 0
    pos: int = 0

class Lexer:
    keywords = [
        "int",
        "float",
        "string",
        "if",
        "else",
        "for",
        "while",
        "do",
        "continue",
        "break",
        "print",
        "cout",
        "return"
    ]
    simple_arith_operators = [
        "+",
        "-",
        "*",
        "/",
        "%"
    ]
    comparison_operators = [
        "==",
        "!=",
        "<=",
        ">=",
        "<",
        ">"
    ]
    all_arith_operators = [
        "+",
        "-",
        "*",
        "/",
        "%",
        "+=",
        "-=",
        "*=",
        "/=",
        "%=",
        "<<",
        ">>",
        "="
    ]
    separators = [
        "(",
        ")",
        ",",
        ";",
        "{",
        "}"
    ]

    i = 0
    line = 1
    pos = 0

    include_keywords = []
    include_separators = []
    include_operators = []
    include_constants = []
    variables = {}
    functions = {}
    constants = {}
    all_tokens = []

    def get_type(self, arg):
        number_regex = r"\d+(\.\d+)?"
        string_regex = r'"(.*?)"'
        if re.match(number_regex, arg):
            return 'int'
        elif re.match(string_regex, arg):
            return 'string'

    def perfome_lexical_analysis(self, file_name, output):
        f = open(file_name)
        source_code = f.read()
        keyword_table = PrettyTable()
        variable_table = PrettyTable()
        delimeter_table = PrettyTable()
        operator_table = PrettyTable()
        const_table = PrettyTable()
        func_table = PrettyTable()
        keyword_table.field_names = ["Keyword", "Description"]
        variable_table.field_names = ["Variable", "Description"]
        delimeter_table.field_names = ["Separator", "Description"]
        operator_table.field_names = ["Operator", "Description"]
        const_table.field_names = ["Constant", "Description"]
        func_table.field_names = ["Functions", "Description"]
        is_float = False

        # Regular expressions for each token type
        id_regex = r"[a-zA-Z_]\w*"
        number_regex = r"\d+(\.\d+)?"
        operator_regex = r"=|==|!=|<=|>=|<<|>>|<|>|[+\-*/%]=?|\+"
        string_regex = r'"(.*?)"'
        separator_regex = r"[(),;{}]"
        func_regex = r"([a-zA-Z_]+)\((.*)\)"
        whitespace_regex = r"\s+"

        # Combine all regular expressions into one
        pattern = re.compile(f"({'|'.join([func_regex, id_regex, number_regex, operator_regex, string_regex, separator_regex, whitespace_regex])})")

        state=''
        type = ''
        total_symbols_in_previos_lines = 0
        # Iterate over all matches in the source code
        for match in pattern.finditer(source_code):
            self.pos =  match.end() - total_symbols_in_previos_lines
            lex = match.group()
            if re.match(whitespace_regex, lex):
                if '\n' in lex:
                    self.line += lex.count('\n')
                    self.pos = 0
                    type = ''
                    total_symbols_in_previos_lines = match.end()
            elif m := re.match(func_regex, lex):
                func_name = m.group(1)
                func_args = m.group(2).split(',')
                if len(func_args) == 1 and func_args[0] == '':
                    func_args.clear()

                for arg in func_args:
                    if arg not in self.constants and func_name in self.functions:
                        self.constants[arg.strip()] = self.get_type(arg.strip()) 
                        const_table.add_row([arg, self.get_type(arg.strip())])
                if func_name not in self.functions: #function defenition
                    self.functions[func_name] = [[arg.strip().split(' ')[0], arg.strip().split(' ')[1]] for arg in func_args]
                self.all_tokens.append(Token(func_name, self.line, self.pos))
                [self.all_tokens.append(Token(arg.strip(), self.line, self.pos)) for arg in func_args]
            elif re.match(id_regex, lex):
                if lex in self.keywords:
                    if (lex not in self.include_keywords):
                        self.include_keywords.append(lex)
                        keyword_table.add_row([lex, "keyword"])
                    if lex == "int" or lex == "float" or lex == "string":
                        type = lex
                    else:
                        type = ""
                    self.all_tokens.append(Token(lex, self.line, self.pos))
                else:
                    if lex not in self.variables and type == "":
                        error_msg = " Unresolved reference"
                        state = "error"
                        break
                    if (lex not in self.variables):
                        self.variables[lex] = type
                        variable_table.add_row([lex, type])
                    self.all_tokens.append(Token(lex, self.line, self.pos))
            elif re.match(number_regex, lex):
                if is_float:
                    if lex not in self.constants:
                        self.constants[lex] = "float"
                        const_table.add_row([lex, "float"])
                    self.all_tokens.append(Token(lex, self.line, self.pos))
                    is_float = False
                else:
                    if lex not in self.constants:
                        self.constants[lex] = "int"
                        const_table.add_row([lex, "int"])
                    self.all_tokens.append(Token(lex, self.line, self.pos))
            elif re.match(operator_regex, lex):
                if lex in self.simple_arith_operators:
                    if lex not in self.include_operators:
                        self.include_operators.append(lex)
                        operator_table.add_row([lex, "simple arithmetic operator"])
                    self.all_tokens.append(Token(lex, self.line, self.pos))
                elif lex in self.comparison_operators:
                    if lex not in self.include_operators:
                        self.include_operators.append(lex)
                        operator_table.add_row([lex, "comparison operator"])
                    self.all_tokens.append(Token(lex, self.line, self.pos))
                elif lex in self.all_arith_operators:
                    if lex not in self.include_operators:
                        self.include_operators.append(lex)
                        operator_table.add_row([lex, "arithmetic operator"])
                    self.all_tokens.append(Token(lex, self.line, self.pos))
            elif re.match(string_regex, lex):
                if lex not in self.include_constants:
                    self.include_constants.append(lex)
                    self.constants[lex] = "string"
                    const_table.add_row([lex, "string"])
                self.all_tokens.append(Token(lex, self.line, self.pos))
            elif re.match(separator_regex, lex):
                if lex not in self.include_separators:
                    self.include_separators.append(lex)
                    delimeter_table.add_row([lex, "separator"])
                self.all_tokens.append(Token(lex, self.line, self.pos))
            else:
                error_msg = "Unknown token"
                state = "error"

        if state == "error":
            print(f"{error_msg} at line {self.line}, position {self.pos}: {lex}")
            sys.exit(1)

        if output:
            print(keyword_table)
            print(variable_table)
            print(delimeter_table)
            print(operator_table)
            print(const_table)

