#!/usr/bin/env python

if __name__ == '__main__':
    from gram import test_grammar
    for i, rule in enumerate(test_grammar.rules):
        print('rule #{}: {} -> {}'.format(i, rule.lhs, ' '.join(rule.rhs)))
    print('')

    from parser import PrecedenceTable, PrecedenceParser
    from parser import make_core_grammar, tokenize
    pt = PrecedenceTable.from_grammar(test_grammar)
    pt.dump()
    parser = PrecedenceParser(pt, make_core_grammar(test_grammar))
    from sys import stdin
    parse_rules, rpns = parser.parse(list(tokenize(stdin.read())))
    print('parse rules: {}'.format(parse_rules))
    print('RPNs: \n{}'.format('\n'.join(' '.join(rpn) for rpn in rpns)))
