import six
import sys
import traceback

EMPTY_SYMBOL = '__empty__'

class CfgRule(object):
    def __init__(self, lhs, rhs):
        assert lhs and rhs
        assert isinstance(lhs, six.string_types), lhs
        assert isinstance(rhs, list)
        self.lhs = lhs
        self.rhs = rhs
    @classmethod
    def from_string(cls, s):
        lhs, rhs = s.split(' -> ')
        rhs = rhs.split(' ')
        return cls(lhs, rhs)
    def to_string(self):
        assert self.lhs and self.rhs
        return '{} -> {}'.format(self.lhs, ' '.join(self.rhs))
    def __hash__(self):
        return hash(self.to_string())
    def __repr__(self):
        return self.to_string()
    def __eq__(self, v):
        return self.to_string() == v.to_string()

class Cfg(object): # context-free grammar
    def __init__(self, terminals, nonterminals, start_symbol, rules):
        assert terminals and nonterminals and start_symbol and rules
        self.terminals = terminals
        self.nonterminals = nonterminals
        self.start_symbol = start_symbol
        self.rules = rules
    @classmethod
    def from_string(cls, string):
        lines = string.splitlines()
        n = int(lines.pop(0))
        assert n > 0
        nonterminals = lines.pop(0).split(' ')
        assert n == len(nonterminals)
        n = int(lines.pop(0))
        assert n > 0
        terminals = lines.pop(0).split(' ')
        assert n == len(terminals)
        n = int(lines.pop(0))
        assert n > 0
        symbols = nonterminals + terminals + [EMPTY_SYMBOL]
        rules = []
        for line in lines[:n]:
            rule = CfgRule.from_string(line)
            assert rule.lhs in nonterminals
            assert all(s in symbols for s in rule.rhs)
            rules.append(rule)
        del lines[:n]
        start_symbol = lines.pop(0)
        assert not lines
        return cls(terminals, nonterminals, start_symbol, rules)
    def to_string(self):
        ret = []
        assert self.nonterminals
        ret.append(str(len(self.nonterminals)))
        ret.append(' '.join(sorted(self.nonterminals)))
        assert self.terminals
        ret.append(str(len(self.terminals)))
        ret.append(' '.join(sorted(self.terminals)))
        assert self.rules
        ret.append(str(len(self.rules)))
        for rule in sorted(self.rules, key=lambda v: v.lhs):
            ret.append(rule.to_string())
        ret.append(self.start_symbol)
        return '\n'.join(ret)

def transform_cfg_to_chomsky_normal_form(cfg):
    new_rules = set()
    new_nonterminals = set()

    for rule in cfg.rules:
        new_nonterminals.add(rule.lhs)
        if len(rule.rhs) == 1:
            assert rule.rhs[0] in cfg.terminals or rule.rhs[0] == EMPTY_SYMBOL
            new_rules.add(rule)
            continue

        def make_nonterminal(s):
            if s in cfg.nonterminals:
                return s
            ret = s + "'"
            assert ret not in cfg.nonterminals
            new_nonterminals.add(ret)
            new_rules.add(CfgRule(ret, [s]))
            return ret

        if len(rule.rhs) == 2:
            new_rhs = list(map(make_nonterminal, rule.rhs))
            new_rules.add(CfgRule(rule.lhs, new_rhs))
            continue

        assert len(rule.rhs) > 2
        cur_lhs, cur_rhs = rule.lhs, rule.rhs
        while len(cur_rhs) >= 2:
            rest_symbols = cur_rhs[1:]
            new_nonterminal = '<{}>'.format(' '.join(rest_symbols)) if len(cur_rhs) > 2 else make_nonterminal(rest_symbols[0])
            new_rule = CfgRule(cur_lhs, [make_nonterminal(cur_rhs[0]), new_nonterminal])
            new_nonterminals.add(new_nonterminal)
            new_rules.add(new_rule)
            cur_lhs = new_nonterminal
            cur_rhs.pop(0)
    return Cfg(cfg.terminals, new_nonterminals, cfg.start_symbol, new_rules)

def validate_cfg_reduced_form(cfg):
    assert cfg.rules
    for rule in cfg.rules:
        assert rule.lhs and rule.rhs
        if len(rule.rhs) == 1 and rule.rhs[0] in cfg.nonterminals:
            return False
        if EMPTY_SYMBOL in rule.rhs:
            if len(rule.rhs) != 1:
                return False
            if rule.lhs != cfg.start_symbol:
                return False
            if any(cfg.start_symbol in r.rhs for r in cfg.rules):
                return False
    return True

if __name__ == '__main__':
    try:
        input_file = sys.argv[1] if len(sys.argv) == 2 else sys.stdin
        if len(sys.argv) == 2:
            with open(filename) as f:
                input_str = f.read()
        else:
            input_str = sys.stdin.read()
    except:
        sys.exit('bad input file!')

    try:
        cfg = Cfg.from_string(input_str)
    except:
        traceback.print_exc()
        sys.exit('invalid input data format!')

    if not validate_cfg_reduced_form(cfg):
        sys.exit('input CFG should be in reduced form!')

    nf_cfg = transform_cfg_to_chomsky_normal_form(cfg)
    print(nf_cfg.to_string())
