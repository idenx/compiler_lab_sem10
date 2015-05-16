# -*- coding: utf-8 -*-

class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

class Gram(Bunch):
    def is_term(self, ch):
        return ch in self.terminals
    def is_nonterm(self, ch):
        return ch not in self.terminals
    def is_operator(self, ch):
        return ch in self.operators

EOF = '$'

def parse_rules(*rules_strs):
    rules = []
    i = [0]
    def get_and_inc_index():
        i[0] += 1
        return i[0] - 1
    for multi_rule in rules_strs:
        lhs, multi_rhs = multi_rule.split(' -> ')
        rules.extend([Bunch(lhs=lhs, rhs=rhs.split(' '), index=get_and_inc_index()) for rhs in multi_rhs.split(' | ')])
    return tuple(rules)

__gram_dict = {
    'operators': set(('<', '<=', '=', '==', '<', '>', '<>', '>=', '+', '-', '*', '/')),
    'terminals': set(('k', 'id', '<', '<=', '=', '==', '<', '>', '<>', '>=', '+', '-', '*', '/', ';', '{', '}', '(', ')', EOF)),
    'start_symbol': '<программа>',
    'rules': parse_rules(
        '<программа> -> <блок>',
        '<блок> -> { <список_операторов> }',
        '<список_операторов> -> <оператор> | <оператор> ; <список_операторов>',
        '<оператор> -> <идентификатор> = <выражение> | <блок>',
        '<выражение> -> <арифметическое_выражение> | ' +
                       ' | '.join('<арифметическое_выражение> {} <арифметическое_выражение>'.format(rel)
                                  for rel in ('<', '<=', '==', '<>', '>', '>=')),
        '<арифметическое_выражение> -> <арифметическое_выражение> + <терм> | <арифметическое_выражение> - <терм> | <терм>',
        '<терм> -> <терм> * <фактор> | <терм> / <фактор> | <фактор>',
        '<фактор> -> <идентификатор> | <константа> | ( <арифметическое_выражение> )',
        '<идентификатор> -> id',
        '<константа> -> k',
    )
}
'''
__gram_dict = {
    'terminals': set(('(', ')', '+', '*', 'a', EOF)),
    'start_symbol': 'E',
    'operators': set(('+', '*', '(', ')')),
    'rules': parse_rules(
        'E -> E + T | T',
        'T -> T * F | F',
        'F -> ( E ) | a',
    )
}
'''
test_grammar = Gram(**__gram_dict)
