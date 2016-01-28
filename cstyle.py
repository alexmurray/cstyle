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
    def __init__(self, Configfiles, files):
        config = ConfigParser.ConfigParser()
        config.read(Configfiles)
        rules = config_section_to_dict(config, 'Rules')

        kinds = {kind.name.lower(): kind
                 for kind in clang.cindex.CursorKind.get_all_kinds()}
        rules_db = {kinds[kind]: re.compile(Pattern)
                    for (kind, Pattern) in rules.items()}
        self.pointer_prefix = (None if not
                               config.has_option('Options', 'pointer_prefix')
                         else config.get('Options', 'pointer_prefix'))
        self.pointer_prefix_repeat = (False if not
                                      config.has_option('Options',
                                                        'pointer_prefix_repeat')
                         else config.getboolean('Options',
                                                'pointer_prefix_repeat'))
        self.prefer_goto = (False if not
                            config.has_option('Options', 'prefer_goto')
                  else config.getboolean('Options', 'prefer_goto'))
        self.rules_db = rules_db
        self.files = files
        self._n_returns = 0

    def local(self, node):
        """Check if node refers to a local file."""
        return node.location.file and node.location.file.name in self.files

    def invalid(self, node):
        """Check if node is invalid."""
        invalid = False
        reason = ''

        name = node.spelling
        if (self.pointer_prefix and
            (node.kind == clang.cindex.CursorKind.VAR_DECL or
             node.kind == clang.cindex.CursorKind.PARM_DECL) and
            node.type and (node.type.spelling.count('*') +
                           node.type.spelling.count('[')) > 0):
            prefix = self.pointer_prefix
            type_ = node.type.spelling
            count = len(prefix)
            if self.pointer_prefix_repeat:
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

        if self.prefer_goto:
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
                errors.append(('{files}:{Line}:{Column}: {reason}\n').
                                 format(files=node.location.file.name,
                                        Line=node.location.line,
                                        Column=node.location.column,
                                        reason=reason))
        return errors

def main():
    """Run cstyle"""
    parser = argparse.ArgumentParser(description='C Style Checker')
    parser.add_argument('--config', dest='config',
                        default=os.path.expanduser('~/.cstyle'),
                        help='configuration file')
    parser.add_argument('FILES', metavar='FILE', nargs='+',
                        help='files to check')
    args = parser.parse_args()
    errors = CStyle(args.config, args.FILES).check()
    for error in errors:
        sys.stderr.write(error)
    sys.exit(1 if len(errors) > 0 else 0)

if __name__ == '__main__':
    main()
