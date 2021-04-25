# TODO

### Bugs

What if the user aborts the cherry-pick? Currently we're still left with the
commit on the template branch. This will mess up future attempts to update the
project. (Would it help to create a plumbing interface, to clarify the logic?)

`cutty update` is somewhat of a misnomer, the command will happily downgrade
when passed an out-of-date version. Furthermore, it just applies a diff to
whatever it finds on the template branch. If that happens to be some weird
snapshot, even importing an up-to-date release will produce strange results.

## Next

- Error handling: Check for usable git
- Use temporary directory for instance worktree
- Logging
- Integration testing
- Unit testing

## Proposed

### Uncategorized

- Add assignment abstraction
- Remove config (expand only built-in abbreviations for compatibility)
- Use `git describe --always`

### Important

- Use immutable types for all parameters
- Survey should not modify `variables`
- Serialization schema for config

### Nice to have

- Rewrite paths in exceptions to be relative to the template (or instance) repository
- Hide git output
- create: pass variables
- Command classes
- Extend cache interface (offline, list, view, configure)
- Plumbing commands
- Better prompting UI
- Offline mode
- Command for listing cached templates
- Command for viewing a cached template (location, version, sha1, variables)
- Command for configuring template variables
- Command for searching templates
- Command for removing a cached template
- Command for pruning the cache
- Show tracebacks of uncaught exceptions with Rich.
- Progress reporting (clone)
- Support template branches?
  - Use case: Try out template PR in project, without updating main template branch.

### Security

- Ensure --directory is a relative path without `..`
- Ensure templated filenames do not contain slash and are neither `..` nor `.`

### Features

- It should be possible to use third-party Jinja extensions.

### Cookiecutter

#### Merged PRs

- #992 Add option `--accept-hooks=yes|ask|no`

#### Open PRs

- #907 Add option `--strip`

#### Open Issues

- #1415 Arbitrary code execution in Jinja templates

# Related tools

- https://github.com/zillow/battenberg
- https://github.com/rmedaer/milhoja
- https://github.com/senseyeio/cupper
- https://github.com/timothycrosley/cruft
- https://github.com/copier-org/copier

# Test Corpus

https://github.com/search?q=filename%3A.cookiecutter.json&type=Code&ref=advsearch&l=&l=
