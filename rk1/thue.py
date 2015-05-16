REPLACE_OPERATOR = '::='
END_OPERATOR = '!!!'
INPUT_GETTER_OPERATOR = ':::'

class Rule(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def __repr__(self):
        return '{} ::= {}'.format(self.lhs, self.rhs)

def parse_program(program_lines):
    memory = None
    rules = []
    input_lines = []
    end_of_rules_found = False
    end_found = False

    for line in program_lines:
        if not end_of_rules_found:
            if line == REPLACE_OPERATOR:
                end_of_rules_found = True
                continue
            rules.append(Rule(*line.split(' ::= ')))
        elif memory is None:
            memory = line
        elif not end_found:
            if line == END_OPERATOR:
                end_found = True
                continue
            input_lines.append(line)
        else:
            assert(False)

    assert(end_of_rules_found and memory is not None and end_found)
    return {'rules': rules, 'memory': memory, 'input_lines': input_lines}

def execute_program(rules, memory, input_lines):
    import random
    match_found = True
    while match_found:
        match_found = False
        random.shuffle(rules) # The searches are non-deterministic (search order does not matter)
        for rule in rules:
            if rule.lhs in memory:
                if rule.rhs == INPUT_GETTER_OPERATOR:
                    replacement = input_lines.pop(0) if input_lines else ''
                elif rule.rhs.startswith('~'):
                    output = rule.rhs[1:]
                    if output:
                        sys.stdout.write(output)
                    else:
                        print('')
                    replacement = ''
                else:
                    replacement = rule.rhs
                match_found = True
                memory = memory.replace(rule.lhs, replacement, 1)

if __name__ == '__main__':
    import sys
    lines = sys.stdin.read().splitlines()
    program = parse_program(lines)
    execute_program(**program)
