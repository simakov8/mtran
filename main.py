from Lexer import Token, Lexer
from Parser import printTree, Parser

def main():
    lexer = Lexer()
    lexer.perfome_lexical_analysis('input.txt', True)
    lexer.all_tokens.append(Token('end'))

    #parser = Parser(lexer.all_tokens, lexer.variables, lexer.constants)
    #ast_tree = parser.parse()
    #printTree(ast_tree, 0)


if __name__ == '__main__':
    main()

