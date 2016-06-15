# Loktar, the hybrid Continuous Integration

## Intro

Loktar is a Continuous Integration project who can managed microservices environment and hybrid environment (python, java ...).

User side :
 * Install Loktar CI
 * Add a loktar.json file at the root of your repository

loktar.json :
```
```

Technologies supported for test:
 * Makefile (with a `ci` and `clean` rules)

Artifact type in output:
 * Docker image
 * Wheel package
 * Debian package


## Contributing to Loktar

All contributions, bug reports, bug fixes, documentation improvements, enhancements and ideas are welcome.

### Working with the code

Now that you have an issue you want to fix, enhancement to add, or documentation to improve, you need to learn how to work with GitHub.
We use the [Github Flow](https://guides.github.com/introduction/flow/).

Finally, commit your changes to your local repository with an explanatory message, Loktar uses a convention for commit message prefixes.
Here are some common prefixes along with general guidelines for when to use them:
 * ENH: Enhancement, new functionality
 * BUG: Bug fix
 * DOC: Additions/updates to documentation
 * TST: Additions/updates to tests
 * BLD: Updates to the build process/scripts
 * PERF: Performance improvement
 * CLN: Code cleanup
 * NOBUILD: special tag to skip test & build

