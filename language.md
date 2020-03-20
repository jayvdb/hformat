# Human Formatter Language
## Introduction
Mainly, _HumanFormatter_ follows the same syntax as Python's formatter, which is:

	{[identifier][:specs]}

Where 'specs' will be a list of functions separated by commas [,].

You don't really need to make a differentiation between 'identifier' and 'specs' using the two points [:]. In this case, you will be able to arrange the functions and identifier in the order you choose, and the formatter will automatically recognize each component.


&nbsp;
## A. Placeholders
Placeholders are used in order to allow some special characters to be used without causing conflicts with the formatter syntax. Most of the times this will be solved by surrounding those characters with quotes, but if this is also not an option, the following placeholding system is given:

	&<chars>;

Where 'chars' can be from the literal character wanted to placehold, to a keyword that identifies some typical conflicting chars:

* `&sq;` Simple quote ['].
* `&dq;` Double quote ["].
* `&c;` Comma [,].
* `&op;` Opening parentheses [(].
* `&cp;` Closing parentheses [)].


&nbsp;
## B. Identificators
Identificators are the strings the system uses to identify what needs to be printed. It would be what is before the two points (**:**) when it is separated from specs. _HumanFormatter_ allows all the possible systems from `str.format()` and f-strings, and more:

* _**Parameters:**_ As in `str.format()`, the identifier will be the name of the parameter given as an argument to the function. You can force it by prefixing the name with **%**.
* _**Contextual:**_ As it would be with f-strings. It will try to evaluate whatever line is given as an identifier, so you can use from local-defined variables to some simple operations. You can force it prefixing with **@**.
* _**Literals:**_ It will interpret the id as an string or a numeric, and represent it directly. You can force it with **?**.
* _**Integers:**_ It will act as `str.format()` does. You cannot force it (although you can use '%' as with parameters).
* _**Empty:**_ If an empty string is given, it will act like `str.format()`, getting the given positional argument corresponding to it's position in the string.

If the identificator is not recognized, two situation may happen. If the separation between identificator and specs is made, it will try to force it to the other types, or interpret it as a literal if it fails. But if no separation is made, it will first try to interpret it as a function, and only if that fails, will treat it as a literal.

&nbsp;
## C. Specs
Specs is the name given to the functions that configure the formatting. Most of them will be just like `str.format()`, but there are some minor changes and more possible different operations. They all have the Python-function format "_<fooname\>([<args...\>],)_", but there are some changes:

* You don't have to use quotes to write strings, as there are no variables nor definitions that could cause conflict. You just **must** use them when you want to write strings arguments that contain commas (,), parentheses () or double points (:).
* When you use a function with no arguments, you don't have to write the parentheses ().


The following list includes all the currently available functions and how to use them (version 2.5):
### C.1. Alignment.
Alignment places the string in different sides of the given space.

* `center|cnt([width], [fill])` places the string in the center of the available space. As in every other alignment function, _width_ and _fill_ arguments can be set in order to configure width and filling char. See their own functions below for further information.
* `left|lft([width], [fill])` places in the left side.
* `right|rgt([width], [fill])` places in the right side.
* `ralign([width], [fill])` aligns the string in a random place from center, left or right.

### C.2. Width
Width sets up the minimum space where the string must be placed. That space left will be filled by spaces, or by the filling char (check _fill_ function).

* `width|w(size, [fill])`. 'size' can be set as an absolute value, with a normal integer; or as a relative one, prefixing the integer with a '+'. Absolute values will set the size ignoring the string to be placed (just as normal f-strings), while relative ones will count from the actual length of the string. Also, setting the width to 0 will represent 0 before any number. The 'fill' argument can be set in order to specify a filling char different from a space. Check _fill_ function for more.

### C.3. Filling
Substitutes the simple space char as a width filler. It needs an alignment to be set, by default would be _left_.

* `fill|f([with])` substitutes the spaces with the argument given. If there is none, the space will remain. You can use more than one char to fill, and those will be adjust to the existing space.
* `rfill|rf([which])` chooses, for each space to be filled, one of the given characters from 'which', randomly.

### C.4. Signing
Chooses the way the signs of numeric values must be shown.

* `sign([arg])`. Its argument can be one of the following:
	* _all_ -- Represent both + and - signs. Also default if no args passed.
	* _neg_ -- Represent only - sign.
	* _sp_ or _space_ -- Represent - sign and a space when the number is positive.

### C.5. Altering
Shows the alternative representation of some variable-types such as binaries or hexadecimals.

* `alter`

### C.6. Precision
Handles the precision or limiting of the string given to represent. It acts differently between numerics and strings, so two functions are given:

* `decimal|dec(limit, [decsep])` limits the number of decimal digits to be represented, to the argument given. It also forces the variable type to be float, so it can work with integers too. 'decsep' can be given in order to change the decimals separator char.
* `limit|l(size, [end])` limits the number of chars from a string to be shown, to 'size'. 'end' argument can be a char that will be putted as final char of the representation. Have in mind that this ending char won't increase the limiting size, so if you use it, your string will be limited to (size-1), leaving the on space for the char.

### C.7. Number separators.
Changes the characters used to separate decimals and miles. Remind that if you want to use commas (,) as a part of you arguments, you must surround it with quotes.

* `decsep(new)` changes the default decimal separator (,) to 'new'.
* `milsep(new)` changes the default miles separator (None) to 'new'.

### C.8. Type casters.
Forces the element to be printed to cast into the selected format.

* `bin([alter])` casts a numeric value to bin. Whenever 'alter' is an available argument, it will mean that it represents its alternative form (as using _alter_ function).
* `int([milsep])` casts a numeric value to integer. A miles separator can be specified.
* `char` casts to char, even numeric values.
* `oct([alter])` casts a numeric value to octal.
* `hex([alter]); Hex([alter])` casts a numeric value to hexadecimal. Case difference defines whenever to use 'x' or 'X' as hex symbol.
* `exp([alter]); Exp([alter])` represents a floating value with exponential format.
* `float([decsep], [milsep]); Float([decsep], [milsep])` represents a numeric value as a floating.
* `round; Round` uses 'g' or 'G' to represent a numeric value.
* `per` represents a numeric value as a percentage with two decimals.
* `str` represents using _str()_.
* `repr` represents using _repr()_.

### C.9. Surrounding.
Surrounds what is to be print with the selected characters.

* `surround|surr([chars])`. _chars_ can be every string of characters. The first half of them (+1 if odd) will open the print, and the other half will close it.

&nbsp;
## D. Style and Coloring
The following functions are used in order to modify the coloring, background and style of the print. You __must__ have the `termcolor` module installed in order to use this functionality. You can download it with `pip install termcolor`, and should work in every OS.

Mind that what this function does is surround the print with some special characters, which means they can be removed or cut off with some other function as `limit`. Use them with caution.

None of those functions use arguments, and they have the same names as the ones used by the function `colored` from `termcolor`. Those are:

* _For coloring:_ gray, red, green, yellow, blue, magenta, cyan, white.
* _For background:_ on\_gray, on\_red, on\_green, on\_yellow, on\_blue, on\_magenta, on\_cyan, on\_white.
* _For styling:_ bold, dark, underline, blink, reverse, canceled.

&nbsp;
## Examples
A simple example could be:

	{?Hello World!:center, width(+10), fill(*)}

Which would be the same as, in Python's format:

	{"Hello World!":*^22}

And will output:

	*****Hello World!*****

As you can see, whereas the _hformat_ is way larger than Python's, but it is also way more understandable.

Notice that, with Python style, you won't be able to use the relative width; and, also, you wouldn't be able to use `str.format()` on that line, as identificators evaluation is only available with f-strings, which, also, are only available on Python 3.6+. _HumanFormatter_, on the other side, can run even in Python 2!
