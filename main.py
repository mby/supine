from lark import Lark, visitors
from sys import argv, exit

parser = Lark("""
    start: fn*

    fn:     "fn" WORD "(" fnargs ")" "{" stmts "}"
    fnargs: [WORD ("," WORD)*]

    stmts: stmt*

    ?stmt: let | ret

    let: "let" WORD "=" math ";"

    ret: "return" math ";"

    ?math: math "+" term -> add
         | math "-" term -> sub
         | term

    ?term: term "*" fact -> mul
         | term "/" fact -> div
         | fact

    ?fact: "(" math ")"
         | call
         | lit

    call:     WORD "(" callargs ")"
    callargs: [math ("," math)*]

    ?lit: name | num | str
    name: WORD
    num:  SIGNED_INT
    str:  ESCAPED_STRING

    %import common.WORD
    %import common.SIGNED_INT
    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
""", parser='lalr')

class FunctionReturn(Exception):
    def __init__(self, value):
        self.value = value

class MismatchingArgCount(Exception):
    pass

class Interpreter(visitors.Interpreter):
    def __init__(self):
        self.fns = {}
        self.stack = []

    def start(self, start):
        for fn in start.children:
            name = fn.children[0]
            self.fns[name] = fn

        main = self.fns["main"]
        if main == None:
            print("main function not found")
            exit(1)

        value = self.visit(main)
        return value

    def fn(self, fn, args = []):
        try:
            self.stack.append({})
            fnargs = fn.children[1].children

            if fnargs != [None] and len(fnargs) != len(args):
                raise MismatchingArgCount()

            if fnargs != [None]:
                for i in range(len(fnargs)):
                    argname = fnargs[i].value
                    argvalue = args[i]
                    self.stack[-1][argname] = argvalue

            fnbody = fn.children[2]
            self.visit(fnbody)
            self.stack.pop()
        except FunctionReturn as ret:
            self.stack.pop()
            return ret.value

    def stmts(self, stmts):
        self.visit_children(stmts)

    def let(self, let):
        value = self.visit(let.children[1])
        self.stack[-1][let.children[0].value] = value

    def ret(self, ret):
        value = self.visit(ret.children[0])
        raise FunctionReturn(value)

    def call(self, call):
        name = call.children[0]
        args = self.visit_children(call.children[1])
        fn = self.fns[name]
        value = self.fn(fn, args)
        return value

    def add(self, add):
        return self.visit(add.children[0]) + self.visit(add.children[1])

    def sub(self, sub):
        return self.visit(sub.children[0]) - self.visit(sub.children[1])

    def mul(self, mul):
        return self.visit(mul.children[0]) * self.visit(mul.children[1])

    def div(self, div):
        return self.visit(div.children[0]) / self.visit(div.children[1])

    def name(self, name):
        value = self.stack[-1][name.children[0].value]
        return value

    def num(self, num):
        return int(num.children[0].value)

    def str(self, str):
        return str.children[0].value[1:-1]

args = argv[1:]
for arg in args:
    source = open(arg).read()

    ast = parser.parse(source)
    print(ast.pretty())

    interpreter = Interpreter()
    result = interpreter.visit(ast)

    print(result)
