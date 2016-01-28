# CStyle

[![License GPL 3](https://img.shields.io/badge/license-GPL_3-green.svg)](http://www.gnu.org/licenses/gpl-3.0.txt)
[![Build Status](https://travis-ci.org/alexmurray/cstyle.svg?branch=master)](https://travis-ci.org/alexmurray/cstyle)
[![Coverage Status](https://coveralls.io/repos/github/alexmurray/cstyle/badge.svg?branch=master)](https://coveralls.io/github/alexmurray/cstyle?branch=master)

CStyle is a simple tool to check the conformance of C/C++ coding against a
predefined style convention for variable / function naming etc.

CStyle uses libclang to parse and identify elements (variable declarations,
function names / parameters etc) and then simply checks each against a list of
rules.

## Configuration

CStyle is configured using a configuration file (see an example in
[config/cohda.cstyle](https://github.com/alexmurray/cstyle/blob/master/config/cohda.cstyle)). This
defaults to `~/.cstyle` but can be specified using the `--config` command-line
option.

The configuration file supports some basic options in the `Options` section:

 * `prefer_goto` - If enabled, will warn when multiple `return` statements exist
   in a single function. However, if disabled will warn about *any* use of
   `goto` at all.

 * `pointer_prefix` - If a variable is a pointer, this prefix is checked to
   exist at the start of the variable name. To disable simply remove this
   configuration option from the configuration file.

 * `pointer_prefix_repeat` - If set to `true` (and `pointer_prefix` is set),
   then the `pointer_prefix` is expected to be repeated by the depth of the
   pointer. i.e. for the argument `char **ppArgv`, `pointer_prefix` should be
   set to `p` and `pointer_prefix_repeat` should be `true`.

Rules for naming variables are specified in the `Rules` section - these specify
a libclang kind and the associated regular expression to validate the name. For
instance, `var_decl` is used to specify the regular expression for all variable
declarations.

For more information on the various libclang kinds see the
[libclang documentation](http://clang.llvm.org/doxygen/group__CINDEX.html#gaaccc432245b4cd9f2d470913f9ef0013)
for the `CursorKind` type. NOTE: In the cstyle configuration file, each kind is
specified as lowercase without the `CXCursor_` prefix, with the CamelCase suffix
written in snake_case.

## Requirements

* python2.7
* python-clang

## Emacs Integration

To integrate with Emacs there are two options - either standalone or via [flycheck](http://flycheck.org).

For standalone usage see [cstyle.el](https://github.com/alexmurray/cstyle.el).

To integrate with flycheck see [flycheck-cstyle](https://github.com/alexmurray/flycheck-cstyle).
