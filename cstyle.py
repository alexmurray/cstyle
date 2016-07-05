#!/usr/bin/env python
"""cstyle C/C++ style checker based on libclang"""

import argparse
import ConfigParser
import clang.cindex
import ctypes.util
import os
import re
import sys

# try find and set libclang manually once
for version in ([None] + ["-3.{minor}".format(minor=minor)
                          for minor in range(2, 9)]):
    lib_name = 'clang'
    if version is not None:
        lib_name += version
    lib_file = ctypes.util.find_library(lib_name)
    if lib_file is not None:
        clang.cindex.Config.set_library_file(lib_file)
        break

def config_section_to_dict(config, section, defaults=None):
    """Create a dict from a section of config"""
    _dict = {} if defaults is None else defaults
    try:
        for (name, value) in config.items(section):
            _dict[name] = value
    except ConfigParser.NoSectionError:
        pass
    return _dict

def node_is_variable(node):
    """Is node a variable / param declaration?"""
    return (node.kind == clang.cindex.CursorKind.VAR_DECL or
            node.kind == clang.cindex.CursorKind.PARM_DECL)

def node_is_pointer(node, arrays_are_pointers):
    """Is node a pointer?"""
    return (node_is_variable(node) and
            node.type and (node.type.spelling.count('*') +
                           (node.type.spelling.count('[')
                            if arrays_are_pointers else 0)) > 0)

class CStyle(object):
    """CStyle checker"""
    def __init__(self, config_file=None, files=None):
        self.options_map = {
            'pointer_prefix': {
                'type': str,
                'default': '',
                'doc': ('If a variable is a pointer, this prefix is checked\n'
                        'to exist at the start of the variable name.')
            },
            'pointer_prefix_repeat': {
                'type': bool,
                'default': False,
                'doc': ('If set to `true` (and `pointer_prefix` is set),\n'
                        'then the `pointer_prefix` is\n'
                        'expected to be repeated by the depth of the\n'
                        'pointer. i.e. for the argument `char **ppArgv`,\n'
                        '`pointer_prefix` should be set to `p` and\n'
                        '`pointer_prefix_repeat` should be `true`.)')
            },
            'arrays_are_pointers': {
                'type': bool,
                'default': False,
                'doc': ('If a variable is an array, treat it as a pointer\n'
                'for `pointer_prefix` and related checks.')
            },
            'prefer_goto': {
                'type': bool,
                'default': False,
                'doc': ('If set to `true`, will warn when multiple\n'
                        '`return` statements exist in a single function.\n'
                        'However, if set to `false` will warn about *any*\n'
                        'use of `goto` at all.')
            }
        }
        # checks to perform on each node in this order
        self.checks = [self.check_pointer_prefix,
                       self.check_prefer_goto,
                       self.check_goto_harmful,
                       self.check_rules]
        kinds = {kind.name.lower(): kind
                 for kind in clang.cindex.CursorKind.get_all_kinds()}
        config = ConfigParser.ConfigParser()
        if config_file is not None:
            config.read(config_file)
            rules = config_section_to_dict(config, 'Rules')
            self.rules_db = {kinds[kind]: re.compile(pattern)
                             for (kind, pattern) in rules.items()}
        else:
            self.rules_db = {kinds[kind]: re.compile('^.*$')
                             for kind in kinds.keys()}
        self.options = self.parse_options(config)
        self.files = files if files is not None else []
        self._n_returns = 0

    def parse_options(self, config):
        """Parse Options section of config."""
        options = {}
        for name, option in self.options_map.iteritems():
            get = 'get'
            if option['type'] is bool:
                get = 'getboolean'
            options[name] = (option['default']
                             if not config.has_option('Options', name)
                             else getattr(config, get)('Options', name))
        return options

    def local(self, node):
        """Check if node refers to a local file."""
        return node.location.file and node.location.file.name in self.files

    def check_pointer_prefix(self, node, name):
        """Do pointer_prefix related checks on node."""
        invalid = False
        reason = ''
        if (self.options['pointer_prefix'] != '' and
            node_is_pointer(node, self.options['arrays_are_pointers'])):
            prefix = self.options['pointer_prefix']
            type_ = node.type.spelling
            count = len(prefix)
            if self.options['pointer_prefix_repeat']:
                count = type_.count('*')
                if self.options['arrays_are_pointers']:
                    count +=  type_.count('[')
                prefix = prefix * count
            invalid = not name.startswith(prefix)
            if invalid:
                fmt = ('"{name}" is invalid - expected pointer prefix '
                       '"{prefix}"')
                reason = fmt.format(name=name, prefix=prefix)
                return invalid, reason, name
            # strip n prefix chars
            name = name[count:]
        return invalid, reason, name

    def check_goto_harmful(self, node, name):
        """Check on any use of goto for node."""
        invalid = False
        reason = ''
        if not self.options['prefer_goto']:
            invalid = (node.kind == clang.cindex.CursorKind.GOTO_STMT)
            if invalid:
                reason = 'goto considered harmful'
        return invalid, reason, name

    def check_prefer_goto(self, node, name):
        """Perform prefer_goto check on node."""
        invalid = False
        reason = ''
        if self.options['prefer_goto']:
            if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                self._n_returns = 0
            elif node.kind == clang.cindex.CursorKind.RETURN_STMT:
                self._n_returns = self._n_returns + 1
            invalid = self._n_returns > 1
            if invalid:
                reason = 'Only 1 return statement per function (prefer_goto)'
        return invalid, reason, name

    def check_rules(self, node, name):
        """Check rules on node with name."""
        # no point checking something which doesn't have a name (could be an
        # unnamed struct etc)
        invalid = False
        reason = ''
        if len(name) > 0:
            invalid = (node.kind in self.rules_db and
                       not self.rules_db[node.kind].match(name))
            if invalid:
                fmt = '"{name}" is invalid - failed pattern check "{pattern}"'
                reason = fmt.format(name=name,
                                    pattern=self.rules_db[node.kind].pattern)
        return invalid, reason, name

    def invalid(self, node):
        """Check if node is invalid."""
        invalid = False
        reason = ''
        name = node.spelling

        for check in self.checks:
            invalid, reason, name = check(node, name)
            if invalid:
                return invalid, reason
        return invalid, reason

    def check_unit(self, unit):
        """Check the translation unit."""
        errors = []
        for node in [node for node in unit.cursor.walk_preorder()
                     if self.local(node)]:
            invalid, reason = self.invalid(node)
            if invalid:
                errors.append({'file': node.location.file.name,
                               'line': node.location.line,
                               'column': node.location.column,
                               'reason': reason})
        return errors

    def check(self):
        """Check files against rules_db and return errors"""
        errors = []
        for files in self.files:
            errors += self.check_unit(clang.cindex.Index.create().parse(files))
        return errors

    def generate_config(self):
        """Generate configuration and return as a string"""
        config = ''
        # Options
        config += '[Options]\n'
        for (name, option) in self.options_map.iteritems():
            default = option['default']
            if option['type'] is bool:
                default = str(default).lower()
            doc = option['doc'].replace('\n', '\n# ')
            config += '# {doc}\n'.format(doc=doc)
            config += '{name}: {default}\n'.format(name=name,
                                                   default=default)
            config += '\n'
        config += '[Rules]\n'
        for (kind, pattern) in self.rules_db.iteritems():
            config += '{kind}: {pattern}\n'.format(kind=kind.name.lower(),
                                                   pattern=pattern.pattern)
        return config

def main():
    """Run cstyle"""
    parser = argparse.ArgumentParser(description='C Style Checker')
    parser.add_argument('--generate-config', action='store_true',
                        help='generate a configuration file')
    parser.add_argument('--config', dest='config',
                        default=os.path.expanduser('~/.cstyle'),
                        help='configuration file')
    parser.add_argument('--msg-template', dest='template',
                        default='{file}:{line}:{column}: {reason}',
                        help='Set the template used to display messages.')
    parser.add_argument('FILES', metavar='FILE', nargs='*',
                        help='files to check')
    args = parser.parse_args()
    if args.generate_config:
        sys.stdout.write(CStyle().generate_config())
        return 0

    if len(args.FILES) == 0:
        parser.print_help()
        return 0

    errors = CStyle(args.config, args.FILES).check()
    for error in errors:
        sys.stderr.write(args.template.format(file=error['file'],
                                              line=error['line'],
                                              column=error['column'],
                                              reason=error['reason']) + '\n')
    return 1 if len(errors) > 0 else 0

if __name__ == '__main__':
    sys.exit(main())
