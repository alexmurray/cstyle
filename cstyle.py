#!/usr/bin/env python2
"""CStyle Checker based on libclang"""

import argparse
import ConfigParser
import clang.cindex
import ctypes.util
import os
import re
import sys

# try find and set libclang manually once
for Version in ([None] + ["-3.{Minor}".format(Minor=Minor)
                          for Minor in range(2, 8)]):
    LibName = 'clang'
    if Version is not None:
        LibName += Version
    LibFile = ctypes.util.find_library(LibName)
    if LibFile is not None:
        clang.cindex.Config.set_library_file(LibFile)
        break

def ConfigSectionToDict(Config, Section, Defaults=None):
    """Create a dict from a Section of Config"""
    Dict = {} if Defaults is None else Defaults
    try:
        for (Name, Value) in Config.items(Section):
            Dict[Name] = Value
    except ConfigParser.NoSectionError:
        pass
    return Dict

class CStyle(object):
    """CStyle checker"""
    def __init__(self, ConfigFile, Files):
        Config = ConfigParser.ConfigParser()
        Config.read(ConfigFile)
        Rules = ConfigSectionToDict(Config, 'Rules')

        Kinds = {Kind.name.lower(): Kind for Kind in clang.cindex.CursorKind.get_all_kinds()}
        RulesDB = {Kinds[Kind]: re.compile(Pattern) for (Kind, Pattern) in Rules.items()}
        self.PointerPrefix = (None if not Config.has_option('Options', 'pointer_prefix')
                         else Config.get('Options', 'pointer_prefix'))
        self.PointerPrefixRepeat = (False if not Config.has_option('Options', 'pointer_prefix_repeat')
                         else Config.getboolean('Options', 'pointer_prefix_repeat'))
        self.PreferGoto = (False if not Config.has_option('Options', 'prefer_goto')
                  else Config.getboolean('Options', 'prefer_goto'))
        self.RulesDB = RulesDB
        self.Files = Files
        self._NReturns = 0

    def Local(self, Node):
        """Check if Node refers to a local file."""
        return Node.location.file and Node.location.file.name in self.Files

    def Invalid(self, Node):
        """Check if Node is invalid."""
        Invalid = False
        Reason = ''

        Name = Node.spelling
        if (self.PointerPrefix and
            (Node.kind == clang.cindex.CursorKind.VAR_DECL or
             Node.kind == clang.cindex.CursorKind.PARM_DECL) and
            Node.type and (Node.type.spelling.count('*') +
                           Node.type.spelling.count('[')) > 0):
            Prefix = self.PointerPrefix
            Type = Node.type.spelling
            Count = len(Prefix)
            if self.PointerPrefixRepeat:
                Count = Type.count('*') + Type.count('[')
                Prefix = Prefix * Count
                Invalid = not Name.startswith(Prefix)
            if Invalid:
                FmtStr = '"{Name}" is invalid - expected pointer prefix "{Prefix}"'
                Reason = FmtStr.format(Name=Name, Prefix=Prefix)
                return Invalid, Reason
            else:
                # strip n prefix chars
                Name = Name[Count:]

        if self.PreferGoto:
            if Node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                self._NReturns = 0
            elif Node.kind == clang.cindex.CursorKind.RETURN_STMT:
                self._NReturns = self._NReturns + 1
            Invalid = self._NReturns > 1
            if Invalid:
                Reason = 'Only 1 return statement per function (prefer_goto)'
                return Invalid, Reason
        else:
            Invalid = (Node.kind == clang.cindex.CursorKind.GOTO_STMT)
            if Invalid:
                Reason = 'goto considered harmful'
                return Invalid, Reason

        # no point checking something which doesn't have a name (could be an
        # unnamed struct etc)
        if not Invalid and len(Name) > 0:
            Invalid = (Node.kind in self.RulesDB and
                       not self.RulesDB[Node.kind].match(Name))
            if Invalid:
                FmtStr = '"{Name}" is invalid - failed regexp check "{Regex}"'
                FmtStr.format(Name=Name, Regex=self.RulesDB[Node.kind].pattern)
        return Invalid, Reason

    def CheckStyle(self):
        """Check Files against RulesDB and report violations to stderr"""
        Errors = []
        for File in self.Files:
            Index = clang.cindex.Index.create()
            Unit = Index.parse(File)
            LocalNodes = [Node for Node in Unit.cursor.walk_preorder() if self.Local(Node)]
            InvalidNodes = []
            for Node in LocalNodes:
                Invalid, Reason = self.Invalid(Node)
                if Invalid:
                    InvalidNodes.append((Node, Reason))

            for (Node, Reason) in InvalidNodes:
                Errors.append(('{File}:{Line}:{Column}: {Reason}\n').
                                 format(File=Node.location.file.name,
                                        Line=Node.location.line,
                                        Column=Node.location.column,
                                        Reason=Reason))
        return Errors

def Main():
    """Run cstyle"""
    Parser = argparse.ArgumentParser(description='C Style Checker')
    Parser.add_argument('--config', dest='Config',
                        default=os.path.expanduser('~/.cstyle'),
                        help='configuration file')
    Parser.add_argument('FILES', metavar='FILE', nargs='+',
                        help='files to check')
    Args = Parser.parse_args()
    Errors = CStyle(Args.Config, Args.FILES).CheckStyle()
    for Error in Errors:
        sys.stderr.write(Error)
    sys.exit(1 if len(Errors) > 0 else 0)

if __name__ == '__main__':
    Main()
