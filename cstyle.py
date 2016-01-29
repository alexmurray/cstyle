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
                          for minor in range(2, 8)]):
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

class CStyle(object):
    """CStyle checker"""
    def __init__(self, config_file=None, files=None):
        self.OPTIONS = {
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
            'prefer_goto': {
                'type': bool,
                'default': False,
                'doc': ('If set to `true`, will warn when multiple\n'
                        '`return` statements exist in a single function.\n'
                        'However, if set to `false` will warn about *any*\n'
                        'use of `goto` at all.')
            }
        }
        config = ConfigParser.ConfigParser()
        kinds = {kind.name.lower(): kind
                 for kind in clang.cindex.CursorKind.get_all_kinds()}
        if config_file is not None:
            config.read(config_file)
            rules = config_section_to_dict(config, 'Rules')
            self.rules_db = {kinds[kind]: re.compile(pattern)
                             for (kind, pattern) in rules.items()}
        else:
            self.rules_db = {kinds[kind]: re.compile('^.*$')
                             for kind in kinds.keys()}
        self.options = {}
        for name, option in self.OPTIONS.iteritems():
            if option['type'] is bool:
                self.options[name] = (option['default']
                                      if not config.has_option('Options', name)
                                      else config.getboolean('Options', name))
            elif option['type'] is str:
                self.options[name] = (option['default']
                                      if not config.has_option('Options', name)
                                      else config.get('Options', name))
            else:
                raise TypeError
        self.files = files if files is not None else []
        self._n_returns = 0

    def local(self, node):
        """Check if node refers to a local file."""
        return node.location.file and node.location.file.name in self.files

    def invalid(self, node):
        """Check if node is invalid."""
        invalid = False
        reason = ''

        name = node.spelling
        if (self.options['pointer_prefix'] != '' and
            (node.kind == clang.cindex.CursorKind.VAR_DECL or
             node.kind == clang.cindex.CursorKind.PARM_DECL) and
            node.type and (node.type.spelling.count('*') +
                           node.type.spelling.count('[')) > 0):
            prefix = self.options['pointer_prefix']
            type_ = node.type.spelling
            count = len(prefix)
            if self.options['pointer_prefix_repeat']:
                count = type_.count('*') + type_.count('[')
                prefix = prefix * count
                invalid = not name.startswith(prefix)
            if invalid:
                fmt = '"{name}" is invalid - expected pointer prefix "{prefix}"'
                reason = fmt.format(name=name, prefix=prefix)
                return invalid, reason
            else:
                # strip n prefix chars
                name = name[count:]

        if self.options['prefer_goto']:
            if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                self._n_returns = 0
            elif node.kind == clang.cindex.CursorKind.RETURN_STMT:
                self._n_returns = self._n_returns + 1
            invalid = self._n_returns > 1
            if invalid:
                reason = 'Only 1 return statement per function (prefer_goto)'
                return invalid, reason
        else:
            invalid = (node.kind == clang.cindex.CursorKind.GOTO_STMT)
            if invalid:
                reason = 'goto considered harmful'
                return invalid, reason

        # no point checking something which doesn't have a name (could be an
        # unnamed struct etc)
        if not invalid and len(name) > 0:
            invalid = (node.kind in self.rules_db and
                       not self.rules_db[node.kind].match(name))
            if invalid:
                fmt = '"{name}" is invalid - failed regexp check "{Regex}"'
                fmt.format(name=name, Regex=self.rules_db[node.kind].pattern)
        return invalid, reason

    def check(self):
        """Check files against rules_db and return errors"""
        errors = []
        for files in self.files:
            index = clang.cindex.Index.create()
            unit = index.parse(files)
            local_nodes = [node for node in unit.cursor.walk_preorder()
                           if self.local(node)]
            invalid_nodes = []
            for node in local_nodes:
                invalid, reason = self.invalid(node)
                if invalid:
                    invalid_nodes.append((node, reason))

            for (node, reason) in invalid_nodes:
                errors.append(('{files}:{line}:{column}: {reason}\n').
                                 format(files=node.location.file.name,
                                        line=node.location.line,
                                        column=node.location.column,
                                        reason=reason))
        return errors

    def generate_config(self):
        """Generate configuration and return as a string"""
        config = ''
        # Options
        config += '[Options]\n'
        for (name, option) in self.OPTIONS.iteritems():
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
    parser.add_argument('FILES', metavar='FILE', nargs='?',
                        help='files to check')
    args = parser.parse_args()
    if args.generate_config:
        sys.stdout.write(CStyle().generate_config())
        sys.exit(0)

    errors = CStyle(args.config, args.FILES).check()
    for error in errors:
        sys.stderr.write(error)
    sys.exit(1 if len(errors) > 0 else 0)

if __name__ == '__main__':
    main()
