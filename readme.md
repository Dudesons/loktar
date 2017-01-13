# Loktar, the hybrid Continuous Integration

[![Coverage Status](https://coveralls.io/repos/github/Dudesons/loktar/badge.svg?branch=try-travis)](https://coveralls.io/github/Dudesons/loktar?branch=try-travis)
[![Build Status](https://travis-ci.org/Dudesons/loktar.svg?branch=master)](https://travis-ci.org/Dudesons/loktar)

## Intro

Loktar is a Continuous Integration project who can managed microservices environment and hybrid environment (python, java, golang ...).
This project is composed by the loktar framework and some services around for running a distributed CI server.
The loktar framework permits you to create your CI pipeline with the python language.


Architecture:


User side :
 * Install Loktar CI
 * Add a loktar.json file at the root of your repository

loktar.json :
```
{
  "packages": [
    {
      "pkg_type": "docker",
      "pkg_name": "pet_api",
      "test_type": "make",
      "type": "service",
      "pkg_dir": "rest_services/pet_api",
      "build_info": {
        "build_type": "url",
        "registry_type": "quay",
        "storage_type": "s3"
      }
    },
    {
      "pkg_type": "docker",
      "pkg_name": "web-front",
      "test_type": "make",
      "type": "service",
      "build_info": {
        "build_type": "url",
        "registry_type": "quay",
        "storage_type": "s3"
      }
    },
    {
      "pkg_type": "whl",
      "pkg_name": "awesome_lib",
      "test_type": "make",
      "type": "library"
    }
  ]
}
```

repository topology:
```
/
|---- webfront
|---- awesome_lib
|---- rest_services/
                   |---- pet_api
                   |---- stock_api
```

Here all services / lib in this reposity will be integrated in the Loktar except the `stock_api` because it's not referenced in in the loktar.json.


Technologies supported for test:
 * Makefile (with a `ci` and `clean` rules)

Artifact type in output:
 * Docker Registry (Quay)
 * Wheel package
 * Debian package
 * Jar for EMR (Elastic Map Reduce from aws ) with S3
 
SCM provider:
 * Github
 
Storage Provider:
 * S3
 
Notification:
 * Slack
 * Github
 

## What's in this repo ?

 * loktar: this is the framework of the project
 * api_gateway (experimental) : this is the api gateway who expose internal rest apis
 * job (experimental): this is a rest service who prepares the CI run, get informations about jobs ...
 * worker_manager (experimental): this is a mq service who manages the launch of jobs following the dep graph
 * executor (experimental): this is a mq service who wait information from the worker_manager and executes CI job
 * storage_proxy: this is a rest service who provide a reverse proxy for storage like S3
 * loktar_prototypes (experimental): This is some prototypes for celery workers
 * utils: Some stuff who can help to build service/dev, for example there is docker base image for loktar

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
 * RFR: Refactor
 * NOBUILD: special tag to skip test & build

