# Human Formatter
___
This module implements a group of functions that allow to use Python's `str.format()` and f-strings with a whole new language created to be human-understandable. It uses a system of Python-like functions to configure and set the format just as you would do with `str.format()` or similar. 

It includes the following functions:

* `hformat(line, *args, **kwargs)`
* `hf(line, *args, **kwargs)`. Same as `hformat`, but shortened.
* `hfprint(line, *args, **kwargs)`; Printing function that, before, calls `hformat`.

And a class, which is the one that does all the magic:

* `HumanFormatter`. You can also use it as if you called `hformat`, and the result will be saved in the attribute `final`.

This separation between functions and classes is done like that in order to follow the same system as Python's `format`does.

You can modify some of the HumanFormatter behavior by using the function `hfconfig(**kwargs)`; which currently has the following options:

* `error_on_unknown_function`: If True, raises an error if an used function does not exists or is not recognized.

HumanFormatter also provides its custom Exception, `HumanFormatterError`, which handles syntax and format errors and problems.

Check 'language.md' to learn how to use `hformat` custom language.
