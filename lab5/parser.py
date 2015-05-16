class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
    def __repr__(self):
        return self.__dict__.__repr__()

from gram import EOF
EOF_TOKEN = Bunch(kind=EOF, value='', is_value=False)
CORE_AXIOM = 'S'
PREC_REL_LT = '<-'
PREC_REL_GT = '->'
PREC_REL_EQ = '='

def get_precedent_terms_set(gram, nonterm, rhs_filter):
    lookuped_nonterms = set((nonterm,))
    q = [nonterm]
    res = set()
    while q:
        lhs = q.pop(0)
        for rule in (r for r in gram.rules if r.lhs == lhs):
            rhs = rhs_filter(rule.rhs)
            if gram.is_term(rhs[0]):
                res.add(rhs[0])
                continue
            assert gram.is_nonterm(rhs[0])
            if len(rhs) >= 2 and gram.is_term(rhs[1]):
                res.add(rhs[1])
            if rhs[0] not in lookuped_nonterms:
                lookuped_nonterms.add(rhs[0])
                q.append(rhs[0])
    return res

def get_init_set(gram, nonterm):
    return get_precedent_terms_set(gram, nonterm, lambda rhs: rhs)
def get_tail_set(gram, nonterm):
    return get_precedent_terms_set(gram, nonterm, lambda rhs: list(reversed(rhs)))

class PrecedenceTable(object):
    def __init__(self, gram):
        self._pt = {}
        self._gram = gram
    def __setitem__(self, k, v):
        k1, k2 = k
        if self._pt.get(k1) is None:
            self._pt[k1] = {}
        if self._pt[k1].get(k2, v) != v:
            raise ValueError('invalid operator precedence grammar')
        self._pt[k1][k2] = v
    def __getitem__(self, k):
        if self._pt.get(k[0]) is None:
            return None
        return self._pt[k[0]].get(k[1])
    def dump(self):
        from sys import stdout
        stdout.write(' ' * 5)
        terms = tuple(sorted(self._gram.terminals))
        for term in terms:
            stdout.write('%5s' % term)
        print('\n' + '-' * 5 * (len(terms) + 1))
        for ut in terms:
            stdout.write('%3s |' % ut)
            for lt in terms:
                stdout.write('%5s' % (self[ut, lt] or ''))
            print('')
        print('\n' + '-' * 5 * (len(terms) + 1))
    @classmethod
    def from_grammar(cls, gram):
        pt = cls(gram)
        for rule in gram.rules:
            for i in range(len(rule.rhs)):
                rhs = rule.rhs[i:i+3]
                if len(rhs) == 1:
                    continue
                if gram.is_term(rhs[0]):
                    if gram.is_term(rhs[1]):
                        pt[rhs[0], rhs[1]] = PREC_REL_EQ
                        continue
                    assert gram.is_nonterm(rhs[1])
                    if len(rhs) == 3:
                        assert gram.is_term(rhs[2])
                        pt[rhs[0], rhs[2]] = PREC_REL_EQ
                    for term in get_init_set(gram, rhs[1]):
                        pt[rhs[0], term] = PREC_REL_LT
                    continue
                assert gram.is_nonterm(rhs[0]) and gram.is_term(rhs[1]), rhs
                for term in get_tail_set(gram, rhs[0]):
                    pt[term, rhs[1]] = PREC_REL_GT

        for term in get_init_set(gram, gram.start_symbol):
            pt[EOF, term] = PREC_REL_LT
        for term in get_tail_set(gram, gram.start_symbol):
            pt[term, EOF] = PREC_REL_GT

        return pt

class PrecedenceParser(object):
    def __init__(self, pt, core_gram):
        self._pt = pt
        self._core_gram = core_gram
    def _search_rule_pivot_to_reduce(self, stack):
        stack_terminals = [(i, e) for i, e in enumerate(stack) if e != CORE_AXIOM]
        for i in reversed(range(len(stack_terminals))):
            if i == 0:
                raise ValueError('cant find rule to reduce in the stack: {}'.format(stack))
            (prev_i, prev), (_, cur) = stack_terminals[i-1:i+1]
            prec_rel = self._pt[prev, cur]
            assert prec_rel is not None
            if prec_rel == PREC_REL_EQ:
                continue
            return prev_i + 1
    def parse(self, tokens):
        if not all(self._core_gram.is_term(t.kind) for t in tokens):
            raise ValueError('unknown terminals in input: {}'.format([t for t in tokens if self._core_gram.is_nonterm(t)]))
        stack, res, rpns, cur_rpn = [EOF], [], [], []
        while not (stack == [EOF, CORE_AXIOM] and tokens == [EOF_TOKEN]):
            print('stack: {}'.format(stack))
            stack_top, next_token = stack[-1], tokens[0]
            assert stack_top == CORE_AXIOM or self._core_gram.is_term(stack_top), stack
            if stack_top == CORE_AXIOM:
                stack_top = stack[-2]
            assert stack_top != CORE_AXIOM

            precedence_relation = self._pt[stack_top, next_token.kind]
            if precedence_relation is None:
                raise ValueError('cant parse grammar: no precedence relation between "{}" and "{}"'.format(stack_top, next_token.kind))
            if precedence_relation in (PREC_REL_LT, PREC_REL_EQ): # shift
                if next_token.is_value:
                    cur_rpn.append(next_token.value)
                stack.append(tokens.pop(0).kind)
                continue

            # reduce
            pivot_i = self._search_rule_pivot_to_reduce(stack)
            pivot = stack[pivot_i:]
            del stack[pivot_i:]
            reduce_rules = [r for r in self._core_gram.rules if r.rhs == pivot]
            if not reduce_rules:
                raise ValueError('cant reduce')
            assert len(reduce_rules) == 1, reduce_rules
            reduce_rule = reduce_rules[0]
            res.append(reduce_rule.index)
            stack.append(CORE_AXIOM)

            # rpn actions
            reduce_rule_operators = [t for t in reduce_rule.rhs if self._core_gram.is_operator(t)]
            if reduce_rule_operators:
                assert len(reduce_rule_operators) == 1 # current limitation: can't be > 1
                cur_rpn.append(reduce_rule_operators[0])
                if reduce_rule_operators[0] == '=':
                    rpns.append(cur_rpn)
                    cur_rpn = []
        return res, rpns

def tokenize(data):
    tokens = data.split()
    for token in tokens:
        if token == 'id' or token.startswith('id_'):
            yield Bunch(kind='id', value=token, is_value=True)
        elif token == 'k' or token.isdigit():
            yield Bunch(kind='k', value=token, is_value=True)
        else:
            yield Bunch(kind=token, value=token, is_value=False)
    yield EOF_TOKEN

def make_core_grammar(gram):
    def replace_by_start_symbol(rule):
        new_rhs = [e if gram.is_term(e) else CORE_AXIOM for e in rule.rhs]
        return Bunch(lhs=CORE_AXIOM, rhs=new_rhs, index=rule.index)

    core_rules = tuple(replace_by_start_symbol(r) for r in gram.rules if not (len(r.rhs) == 1 and gram.is_nonterm(r.rhs[0])))
    from gram import Gram
    return Gram(rules=core_rules, terminals=gram.terminals, operators=gram.operators, start_symbol=CORE_AXIOM)
