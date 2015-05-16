#!/usr/bin/env python3

class Bunch(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

class ParserError(Exception):
    pass

class ProgramRecursiveDescentParser(object):
    def __init__(self, tokens):
        self._tokens = tokens
        self._error = None
        self._operators = []
    def get_operators(self):
        return tuple(self._operators)
    def _err(self, text):
        raise ParserError('err: "{}", top_token="{}", tokens="{}"'.format(text, self._tokens[0] if self._tokens else '', self._tokens))
    def _is_on_top(self, term):
        return self._tokens and self._tokens[0] == term
    def _match_term(self, term):
        if self._is_on_top(term):
            return self._tokens.pop(0)
        self._err("term {} doesnt match with current stack top token".format(term))
    def _try_match(self, matcher):
        return self._tokens.pop(0) if self._tokens and matcher(self._tokens[0]) else None
    def _match(self, matcher):
        return self._try_match(matcher) or self._err('cant match by matcher {}'.format(matcher))
    def _try_parse_id(self):
        return self._try_match(lambda t: t.startswith('id_'))
    def _parse_id(self):
        return self._try_parse_id() or self._err('cant parse valid identificator')
    def _try_parse_constant(self):
        return self._try_match(lambda t: t.isdigit())
    def _parse_factor(self):
        if self._is_on_top('('):
            yield self._match_term('(')
            yield from self._parse_ar_expr()
            yield self._match_term(')')
        else:
            yield self._try_parse_id() or self._try_parse_constant() or self._err('invalid factor')
    def _parse_mul_op(self):
        return self._match(lambda t: t in ('*', '/'))
    def _parse_term_rest(self):
        yield self._parse_mul_op()
        yield from self._parse_factor()
        try:
            yield from self._parse_term_rest()
        except ParserError:
            pass
    def _parse_term(self):
        yield from self._parse_factor()
        try:
            yield from self._parse_term_rest()
        except ParserError:
            pass
    def _parse_add_op(self):
        return self._match(lambda t: t in ('+', '-'))
    def _parse_ar_expr_rest(self):
        yield self._parse_add_op()
        yield from self._parse_term()
        try:
            yield from self._parse_ar_expr_rest()
        except ParserError:
            pass
    def _parse_ar_expr(self):
        yield from self._parse_term()
        try:
            yield from self._parse_ar_expr_rest()
        except ParserError:
            pass
    def _try_parse_rel_op(self):
        return self._tokens.pop(0) if self._tokens and self._tokens[0] in ('==', '<=', '<>', '>=', '<', '>') else None
    def _parse_expr(self):
        yield from self._parse_ar_expr()
        rel_res = self._try_parse_rel_op()
        if rel_res:
            yield rel_res
            yield from self._parse_ar_expr()
    def _parse_op(self):
        if self._is_on_top('{'):
            return self._parse_block()
        lhs = self._parse_id()
        self._match_term('=')
        rhs = tuple(self._parse_expr())
        self._operators.append(Bunch(lhs=lhs, rhs=rhs))
    def _parse_op_tail(self):
        try:
            self._match_term(';')
            self._parse_op()
            self._parse_op_tail()
        except ParserError:
            pass
    def _parse_op_list(self):
        self._parse_op()
        self._parse_op_tail()
    def _parse_block(self):
        self._match_term('{')
        self._parse_op_list()
        self._match_term('}')
    def parse(self):
        return self._parse_block()

if __name__ == '__main__':
    import sys
    tokens = sys.stdin.read().split()
    parser = ProgramRecursiveDescentParser(tokens)
    try:
        parser.parse()
    except ParserError as e:
        #import traceback; traceback.print_exc()
        sys.exit(e)

    variables = {}
    for op in parser.get_operators():
        assert isinstance(op.lhs, str) and op.rhs
        variables[op.lhs] = eval(' '.join(op.rhs).replace(' <> ', ' != '), dict(variables))
    print('Variables:')
    for var, val in variables.items():
        print('{} = {}'.format(var, val))
