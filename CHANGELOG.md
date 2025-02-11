# Changelog - dnscacher

This document describes the changes that were made to the software for each
version. The changes are described concisely, to make it comprehensible for the
user. A change is always categorized based on the following types:

- Bug: a fault in the software is fixed.
- Feature: a functionality is added to the program.
- Improvement: a functionality in the software is improved.
- Task: a change is made to the repository that has no effect on the source code.
- Breaking: a change is made that is not backwards compatible.

## 0.1

### Features

- added --output ipset
- added counter that keeps its line
- added ipset command
- added support for files containing domains

### Bugs

- fix: args and options can now be parsed before and after the positionals
- fix: use comma to separate --output

### Improvements

- used pygeneral
- split the program into smaller subcommands
