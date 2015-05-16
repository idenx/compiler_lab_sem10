#!/usr/bin/env python3
import sys
import os

DEBUG = os.environ.get('DEBUG') == '1'

class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
    def __repr__(self):
        return self.__dict__.__repr__()

def list_tail_eq(a, b):
    """ Compare tail of list 'a' to the list 'b'
    >>> list_tail_eq([1, 2, 3], [2, 3])
    True
    >>> list_tail_eq([1, 2, 3], [1, 2])
    False
    """
    assert isinstance(a, list) and isinstance(b, list)
    assert a and b
    return len(a) >= len(b) and a[-len(b):] == b

def warn(str_):
    sys.stderr.write(str_ + '\n')

class BacktrackedBottomUpParser(object):
    def __init__(self, gram):
        self._gram = gram
    def _reduce_with_min_rule_index(self, cfg, min_rule_i):
        if not cfg.l1:
            return 'shift'
        last_l1_symbol = cfg.l1[-1]
        for i in range(min_rule_i, len(self._gram.rules)):
            rule = self._gram.rules[i]
            if last_l1_symbol == rule.rhs[-1] and list_tail_eq(cfg.l1, rule.rhs): # comparison optimization
                cfg.l1[-len(rule.rhs):] = [rule.lhs]
                assert not list_tail_eq(cfg.l1, rule.rhs)
                cfg.l2.append(i)
                if DEBUG:
                    print('reduced by rule {!r}'.format(rule))
                return 'reduce'
        if DEBUG:
            print('cant reduce')
        return 'shift'
    def _reduce(self, cfg):
        assert cfg.state == 'q'
        return self._reduce_with_min_rule_index(cfg, 0)
    def _shift(self, cfg, input_tokens):
        if cfg.pos == len(input_tokens):
            return 'verify'
        cfg.l1.append(input_tokens[cfg.pos])
        cfg.l2.append('s')
        cfg.pos += 1
        return 'reduce'
    def _verify(self, cfg, input_tokens):
        if cfg.pos == len(input_tokens) and cfg.l1 == [self._gram.start_symbol]:
            cfg.state = 't'
            return 'finish'
        return 'backtrack_change_state'
    def _backtrack_change_state(self, cfg, input_tokens):
        assert cfg.pos == len(input_tokens) and cfg.state == 'q'
        cfg.state = 'b'
        return 'backtrack'
    def _backtrack(self, cfg, input_tokens):
        if cfg.pos == 0:
            warn('backtracked to first symbol, error')
            return 'error'
        assert cfg.state == 'b'
        if isinstance(cfg.l2[-1], int): # 5 a, b, c
            j = cfg.l2.pop()
            rule = self._gram.rules[j]
            assert cfg.l1[-1] == rule.lhs
            cfg.l1.pop()
            cfg.l1.extend(rule.rhs)
            assert list_tail_eq(cfg.l1, rule.rhs)
            r = self._reduce_with_min_rule_index(cfg, j + 1) # try choose another rule
            if r == 'reduce': # 5a, found another rule
                cfg.state = 'q'
                return r
            assert r == 'shift' # rule wasn't found
            if cfg.pos == len(input_tokens): # 5b, nothing to shift: end of input
                return 'backtrack'
            cfg.state = 'q'
            return r # 5c, shift
        # 5d
        assert cfg.l2[-1] == 's' and cfg.l1[-1] == input_tokens[cfg.pos - 1]
        cfg.l1.pop()
        cfg.l2.pop()
        cfg.pos -= 1
        return 'backtrack'

    def parse(self, input_tokens):
        cfg = Bunch(state='q', pos=0, l1=[], l2=[])
        fsm = {
            'reduce': lambda: self._reduce(cfg),
            'shift': lambda: self._shift(cfg, input_tokens),
            'verify': lambda: self._verify(cfg, input_tokens),
            'backtrack_change_state': lambda: self._backtrack_change_state(cfg, input_tokens),
            'backtrack': lambda: self._backtrack(cfg, input_tokens)
        }
        fsm_state = 'reduce'
        i, MAX_ITER = 0, 1e9
        if DEBUG:
            warn('#{}: fsm_state={}, cfg={!r}'.format(i, fsm_state, cfg))
        while fsm_state not in ('finish', 'error') and i < MAX_ITER:
            fsm_state = fsm[fsm_state]()
            i += 1
            if DEBUG:
                warn('#{}: fsm_state={}, cfg={!r}'.format(i, fsm_state, cfg))
            if i % 1e5 == 0:
                warn('iter #{}'.format(i))
        if i == MAX_ITER:
            return 'iterations limit'
        if fsm_state != 'finish':
            return 'error occured'
        return cfg.l2

def parse_rules(*rules_strs):
    rules = []
    for multi_rule in rules_strs:
        lhs, multi_rhs = multi_rule.split(' -> ')
        rules.extend([Bunch(lhs=lhs, rhs=rhs.split(' ')) for rhs in multi_rhs.split(' | ')])
    return tuple(rules)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

    gram = {
        'start_symbol': '<выражение>',
        'rules': parse_rules(
            '<выражение> -> <арифметическое_выражение> <операция_отношения> <арифметическое_выражение> | <арифметическое_выражение>',
            '<арифметическое_выражение> -> <арифметическое_выражение> <операция_типа_сложения> <терм> | <терм>',
            '<терм> -> <терм> <операция_типа_умножения> <фактор> | <фактор>',
            '<фактор> -> <идентификатор> | <константа> | ( <арифметическое_выражение> )',
            '<операция_отношения> -> < | <= | = | <> | > | >=',
            '<операция_типа_сложения> -> + | -',
            '<операция_типа_умножения> -> * | /',
            '<идентификатор> -> id | id1 | id2',
            '<константа> -> k | k1 | k2',
        )
    }
    for i, rule in enumerate(gram['rules']):
        print('rule #{}: {} -> {}'.format(i, rule.lhs, ' '.join(rule.rhs)))
    print('')
    parser = BacktrackedBottomUpParser(Bunch(**gram))
    for line in sys.stdin.read().splitlines():
        r = parser.parse(tuple(line.split(' ')))
        print('{}: {}'.format(line, r))
