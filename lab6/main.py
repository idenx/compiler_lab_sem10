#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir)))
import numpy as np

from lab5.parser import PrecedenceParser, PrecedenceTable
from lab5.parser import PREC_REL_LT, PREC_REL_GT, PREC_REL_EQ
from lab5.parser import make_core_grammar, tokenize

class CompactPrecedenceTable(object):
    VAL_EMPTY = -2
    VAL_LT = -1
    VAL_GT = 1
    VAL_EQ = 0

    def __init__(self, f, g):
        self._f = f
        self._g = g
    def __getitem__(self, k):
        f, g = self._f[k[0]], self._g[k[1]]
        if f < g:
            return PREC_REL_LT
        if f == g:
            return PREC_REL_EQ
        return PREC_REL_GT
    def dump(self):
        def print_fg(name, d):
            print('{}:'.format(name))
            for term, max_path in sorted(d.items(), key=lambda v: v[0]):
                print("%5s => %d" % (term, max_path))
            print('')
        print_fg('f', self._f)
        print_fg('g', self._g)

        def print_table(self):
            from sys import stdout
            stdout.write(' ' * 5)
            terms = tuple(sorted(k for k, _ in self._f.iteritems()))
            for term in terms:
                stdout.write('%5s' % term)
            print('\n' + '-' * 5 * (len(terms) + 1))
            for ut in terms:
                stdout.write('%3s |' % ut)
                for lt in terms:
                    stdout.write('%5s' % self[ut, lt])
                print('')
            print('\n' + '-' * 5 * (len(terms) + 1))
        print_table(self)

    @staticmethod
    def _precedence_table_to_matrix(pt, gram_terminals):
        matr = np.empty(shape=(len(gram_terminals), len(gram_terminals)), dtype=np.int8)
        matr.fill(CompactPrecedenceTable.VAL_EMPTY)
        terminals = {t: i for i, t in enumerate(sorted(gram_terminals))}
        for k1, subdict in pt._pt.iteritems():
            for k2, v in subdict.iteritems():
                i, j = terminals[k1], terminals[k2]
                if v == PREC_REL_EQ:
                    matr[i, j] = CompactPrecedenceTable.VAL_EQ
                elif v == PREC_REL_LT:
                    matr[i, j] = CompactPrecedenceTable.VAL_LT
                elif v == PREC_REL_GT:
                    matr[i, j] = CompactPrecedenceTable.VAL_GT

        def print_matrix():
            print('Precedence matrix:')
            sys.stdout.write(' ' * 5)
            terms = tuple(sorted(gram_terminals))
            for term in terms:
                sys.stdout.write('%5s' % term)
            print('\n' + '-' * 5 * (len(terms) + 1))
            for ut in terms:
                sys.stdout.write('%3s |' % ut)
                for lt in terms:
                    sys.stdout.write('%5s' % matr[terminals[ut], terminals[lt]])
                print('')
            print('\n' + '-' * 5 * (len(terms) + 1))

        print_matrix()
        return matr

    @staticmethod
    def _squash_precedence_matrix(terminals, matr):
        def squash_rows(m):
            row2term = {}
            for i, t in terminals:
                row = tuple(m[i])
                if row2term.get(row) is None:
                    row2term[row] = {'index': i, 'terms': []}
                row2term[row]['terms'].append(t)

            squashed_rows = []
            row_terminals = []
            for row, row_info in sorted(row2term.iteritems(), key=lambda v: v[1]['index']):
                row_terminals.append(row_info['terms'])
                squashed_rows.append(row)
            print(squashed_rows)
            return row_terminals, np.array(squashed_rows)

        row_terminals, squashed_rows_matrix = squash_rows(matr)
        col_terminals, squashed_cols_matrix = squash_rows(squashed_rows_matrix.T)
        squashed_matr = squashed_cols_matrix.T

        def print_squashed_matrix(matrix):
            print('Squashed precedence matrix:')
            w = 12
            sys.stdout.write(' ' * w)
            for terms in col_terminals:
                sys.stdout.write('%{}s'.format(w) % ', '.join(terms))
            print('\n' + '-' * w * (len(row_terminals) + 1))
            for i, row_terms in enumerate(row_terminals):
                sys.stdout.write('%{}s |'.format(w - 3) % ', '.join(row_terms))
                for j, _ in enumerate(col_terminals):
                    sys.stdout.write('%{}s'.format(w) % matrix[i, j])
                print('')
            print('\n' + '-' * w * (len(row_terminals) + 1))

        print_squashed_matrix(squashed_matr)
        return row_terminals, col_terminals, squashed_matr

    class GraphNode(object):
        def __init__(self, data, successors=None):
            self.successors = successors or []
            self.data = data
        def __repr__(self):
            return 'GraphNode(data={}, successors_n={})'.format(self.data, len(self.successors))

    @staticmethod
    def _build_precedence_graph(row_terminals, col_terminals, squashed_matr):
        f_nodes = [CompactPrecedenceTable.GraphNode(data={'f_terms': rt, 'kind':'f'}) for rt in row_terminals]
        g_nodes = [CompactPrecedenceTable.GraphNode(data={'g_terms': ct, 'kind':'g'}) for ct in col_terminals]
        zero_elems = zip(*np.where(squashed_matr == 0))
        print(squashed_matr)
        print(zero_elems)
        for index_pair in zero_elems:
            i, j = index_pair
            print(i)
            f_nodes[i] = g_nodes[j] = CompactPrecedenceTable.GraphNode(data=
                {'f_terms': f_nodes[i].data['f_terms'], 'g_terms': g_nodes[j].data['g_terms'], 'kind': 'fg'})
        for i in range(len(f_nodes)):
            for j in range(len(g_nodes)):
                v = squashed_matr[i, j]
                if v in (CompactPrecedenceTable.VAL_EMPTY, CompactPrecedenceTable.VAL_EQ):
                    continue
                assert v in (CompactPrecedenceTable.VAL_LT, CompactPrecedenceTable.VAL_GT), v
                if v == CompactPrecedenceTable.VAL_GT:
                    f_nodes[i].successors.append(g_nodes[j])
                else:
                    g_nodes[j].successors.append(f_nodes[i])
        return set(f_nodes + g_nodes)

    @staticmethod
    def _does_graph_contain_loops(nodes):
        import copy
        nodes = copy.deepcopy(nodes)
        while nodes:
            final_node = next((n for n in nodes if not n.successors), None)
            if final_node is None: # loop found
                return True
            nodes.remove(final_node)
            for node in nodes:
                if final_node in node.successors:
                    node.successors.remove(final_node)
        return False

    @staticmethod
    def _mark_longest_paths_in_precedence_graph(nodes):
        for node in nodes:
            node.data['max_path'] = 0
        have_changes = True
        while have_changes:
            have_changes = False
            for node in nodes:
                old_val = node.data['max_path']
                if not node.successors:
                    continue
                node.data['max_path'] = max(s.data['max_path'] for s in node.successors) + 1
                have_changes = have_changes or (node.data['max_path'] != old_val)

    @classmethod
    def from_grammar(cls, gram):
        pt = PrecedenceTable.from_grammar(gram)
        matrix = cls._precedence_table_to_matrix(pt, gram.terminals)
        terminals = tuple(enumerate(sorted(gram.terminals)))
        row_terminals, col_terminals, squashed_matr = cls._squash_precedence_matrix(terminals, matrix)
        assert row_terminals and col_terminals

        nodes = cls._build_precedence_graph(row_terminals, col_terminals, squashed_matr)
        assert nodes
        if cls._does_graph_contain_loops(nodes):
            raise ValueError('precedence graph contains loops, cant buld compact precedence grammar')
        cls._mark_longest_paths_in_precedence_graph(nodes)

        f_nodes = [n for n in nodes if 'f' in n.data['kind']]
        g_nodes = [n for n in nodes if 'g' in n.data['kind']]

        f, g = {}, {}
        for _, term in terminals:
            term_f_nodes = [n for n in f_nodes if term in n.data['f_terms']]
            assert len(term_f_nodes) == 1, (term, term_f_nodes)
            f[term] = term_f_nodes[0].data['max_path']

            term_g_nodes = [n for n in g_nodes if term in n.data['g_terms']]
            assert len(term_g_nodes) == 1, (term, term_g_nodes)
            g[term] = term_g_nodes[0].data['max_path']

        return cls(f=f, g=g)

if __name__ == '__main__':
    from lab5.gram import test_grammar
    for i, rule in enumerate(test_grammar.rules):
        print('rule #{}: {} -> {}'.format(i, rule.lhs, ' '.join(rule.rhs)))
    print('')

    cpt = CompactPrecedenceTable.from_grammar(test_grammar)
    cpt.dump()
    parser = PrecedenceParser(cpt, make_core_grammar(test_grammar))
    parse_rules, rpns = parser.parse(list(tokenize(sys.stdin.read())))
    print('parse rules: {}'.format(parse_rules))
    print('RPNs: \n{}'.format('\n'.join(' '.join(rpn) for rpn in rpns)))
