from Lexer import Token, Lexer
from Parser import printTree, Parser
from Executable import Executable

def main():
    lexer = Lexer()
    lexer.perfome_lexical_analysis('input.txt', True)
    lexer.all_tokens.append(Token('end'))

    parser = Parser(lexer.all_tokens, lexer.variables, lexer.constants, lexer.functions)
    ast_trees = parser.parse()
    for f_name in ast_trees:
        print(f_name)
        printTree(ast_trees[f_name])


    #executable = Executable(ast_tree)
    #executable.execute()


if __name__ == '__main__':
    main()

