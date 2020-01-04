Mutable tester
==============

What is it ?
------------

This script provide the necessary command to use mutable testing on a C/C++ project.

Usage
-----

Edit the config file and setup the paths to your project and required commands to 
build and run the unit tests.

You also need to provide a coverage file so the script mutate only the covered lines.
You can get this file by compiling your project with the gcc coverage options:

```sh
gcc -O0 -fprofile-arcs -ftest-coverage
#run
lcov -o out.info -c -d .
```

Then just run the script.

```sh
./mutable-test-runner.py
```

Constrains
----------

This script does not parse the language, it only search pattern and replace them.
This is preferable to use code coverage profiles to eliminate comments which
might generate false negative.

It also consider spaces arround operators like `a == b` not `a==b`.

License
-------

This script is provide under CeCILL-C which is a LGPL like and compatible license.
