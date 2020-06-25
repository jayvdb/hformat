#!python3
#-*- coding: utf-8 -*-
"""
	Human Readable String Formatter - Human Formatter

	This module presents the function hformat and the class HumanFormatter,
	which creates a human-readable pseudo-language that can substitute both
	str.format and f-strings.

	Its objective is to translate the current language, which is complex and
	usually difficult to understand and interprete. Moreover, you must know it
	in order to use it with its whole benefits. With hformat, you can forget
	about this, as it brings you a Python-like pseudo-language that uses logic
	functions which are understandable just by reading them.

	Aside from translating the usual 'format' function; 'hformat' also gives
	further useful extra functions to use, as it will be seen.

	FIXME: That does not really work...
	[[
	In order to achieve f-strings behavior, it uses the inspect module and the
	built-ins 'locals()' and 'globals()', although PEP498 discourages it.
	]]

	Check for further documentation at /projects/hformat/.

	Created:		27 Feb 2020
	Last modified:	25 Jun 2020
	TODO:
		- Adjust docstrings and type-check.
		- Allow limit without arguments that trims into width.
		- Try retrocompatibility with Python 2.7.
		- Allow some HTML and Markdown syntaxis, but just as literal conversions
		to hformat, without further specific code (v3).
"""
import sys
import inspect
import random
import yaml
from pprint import pprint

#
# Definitions and globals.
#
VERSION = "2.5"

#	User placeholders:
USER_PLACEHOLDERS = {
	'&sq;': "&';",
	'&dq;': '&";',
	'&c;': '&,;',
	'&op;': '&(;',
	'&cp;': '&);'
}

#	Defines:
COLORS = ["gray", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
HIGHLIGHTS = ["on_"+color for color in COLORS]
STYLES = ["bold", "dark", "underline", "blink", "reverse", "canceled"]
CONTEXT_CHAR_ID = '@'
LITERAL_CHAR_ID = '?'
PARAM_CHAR_ID = '%'

#	Extern files:
FUNCTIONS_PATH = "./files/fcndefs.yml"

#	Placeholders:
COMMA_PLACEHOLDER = "$$$COMMA$$$"
FILL_PLACEHOLDER = chr(1500)
LITERAL_COMMA_PLACEHOLDER = "$$$LITERALCOMMA$$$"
LITERAL_POINTS_PLACEHOLDER = "$$$TWO$$$POINTS$$$"
LITERAL_OPENPAR_PLACEHOLDER = "$$$OPEN$$$PARENTHESIS$$$"
LITERAL_CLOSEPAR_PLACEHOLDER = "$$$CLOSE$$$PARENTHESIS$$$"
RFILL_PLACEHOLDER = chr(1501)

#	Intern keys:
CALLING_FRAME_KEY = "__cAlLiNg_MoDuLe__"
CONTEXT_KEY = "__cOnTeXt_KeY__"
FILL_KEY = "__FiLl__"
LITERAL_KEY = "__lItErAl__"
RFILL_KEY = "__rFiLl__"

#	Error messages:
ERROR_EXPECTED_ARG = "'{}' function requires positional argument at {}"
ERROR_EXPECTED_CLOSURE = "Expected '{}' before ending string"
ERROR_FUNCTION_SYNTAX = "Expected ')' for closing, or no openning '('"
ERROR_UNKNOWN_FUNCTION = "Unknown hformat function '{}' given"
ERROR_WIDTH_USES_INT = "width() argument must be integers or integers preceded"\
					   "by '+' char"
ERROR_WRONG_TYPED_ARG = "Positional argument {} of function '{}' expects type"\
						" '{}', not '{}'"
FATAL_ERROR_NO_ID = "- FATAL - Identificator key not found"
FATAL_ERROR_NO_TERMCOLOR = "- FATAL - Termcolor module must be installed in" \
						   "order to allow using coloring and style functions"


################################################################################

#
# Classes.
#
class HFFunction (object):
	"""Class that wraps hformat functions.
	Presents an easy-to-use system for handling those.
	"""
	def __init__ (self, key, args=list()):
		"""Constructor.
		 - 'key' identifies the calling function.
		 - 'args' is a list of dictionaries {arg_name: value}.
		"""
		self.key = key
		self.args = args
		self.last_arg = None	# Stores the last argument asked for.

	# Getters and setters:
	def add_arg (self, key, value):
		"""Appends an argument to the existing ones."""
		self.args.append({key: value})
		self.last_arg = self.args[-1][key]

	def get_arg (self, key=0):
		"""Returns an argument identified by:
		  - its position, if key is an integer.
		  - its name, if key is a string.
		Raises a SystemError if not found.
		"""
		if isinstance(key, int):
			return [v for v in self.args[key].values()][0]
		elif isinstance(key, str):
			for arg in self.args:
				if key in arg.keys():
					return arg[key]

	def has_arg (self, key):
		"""Returns True or False depending on having or not:
		  - required position, if key is an integer.
		  - required function name, if key is a string.
		Raises a SystemError if any error occurs.
		"""
		ret = False
		if isinstance(key, int):
			ret = key < len(self.args)
		elif isinstance(key, str):
			for arg in self.args:
				if key in arg.keys():
					ret = True

		if ret:
			self.last_arg = self.get_arg(key)
		return ret

	def __str__ (self):
		"""Printing content for debugging."""
		return f"Key: {self.key} - Args: {str(self.args)}"


class HumanFormatterError (Exception):
	"""Customizes and centralizes errors raised by HumanFormatter."""
	def __init__ (self, msg=""):
		super().__init__(msg)
		self.msg = msg

	def __str__ (self):
		return self.msg


class HumanFormatter (object):
	"""This class handles the main engine of hformat.
	It provides privates functions that achieve each part of the process.
	Those are:
	 1. Parsing the pseudo-language, identifying each {clause}.
	 2. Lexing each clause, identifying commands.
	 3. Interpreting and formatting each clause with its h-commands.
	"""
	HFCONFIG = {
		'error_on_unknown_function': False
	}

	def __init__ (self, line, *args, **kwargs):
		"""Receives the string, generates the formatted result."""
		self.original = line
		self.args = args
		self.kwargs = kwargs

		# Program user configuration.
		self.config = HumanFormatter.HFCONFIG

		# Program parameters.
		self.trans = list()
		self.hidden = list()

		# Control:
		self.__gi = 0		# Empty clauses identificator.
		self.__li = 0		# Literal identifiers index follower.
		self.__fi = 1500	# Random filling unique identificator index.
		self.__fill_dict = dict()	# Multi-char filling dictionary.
		self.__rfill_dict = dict()	# Random filling dictionary of chars.
		self.__limit_list = list()	# Limit char identifying list.
		self.__decsep = ''	# Decimal separator changer.
		self.__milsep = ''	# Thousands separator changer.

		# Obtaining calling module frame, for contextual identifiers:
		if CALLING_FRAME_KEY in self.kwargs:
			self.calling_frame = self.kwargs[CALLING_FRAME_KEY]
		else:
			self.calling_frame = inspect.stack()[1].frame

		# *** Starting program ***
		self.final = self.__parse(self.original, True)


	@staticmethod
	def config(*args, **kwargs):
		"""Changes user configuration."""
		for key, val in kwargs.items():
			if key in HumanFormatter.HFCONFIG.keys():
				HumanFormatter.HFCONFIG[key] = val


	def __parse (self, line, first=False):
		"""Parses a given string.
		Identifies every substring enclosed between parenthesis {} - clause.
		It is capable of distingish inner and outter clauses, and also ignores
		parentheses that are not clauses. It also provides the escape char '\'.
		'first' parameter identifies the first called instance, so when that one
		ends, it will mean the parsing and formatting has ended.

		It uses an spiral parsing, which means that everytime it identifies a
		clause, calls itself agains with this clause, identifying inner clauses.
		This way, everything in translated correctly.
		"""
		inside = False		# True when inside a clause.
		ignore = 0
		hop_next = False	# True when a {} char must be ignored.
		subline = ""
		for char in line:
			if inside:
				# This will include the closing '}', be careful.
				subline += char
			if hop_next and char in "}{":
				hop_next = False
				continue
			if char == '{':
				if inside is True:
					ignore += 1
				else:
					inside = True
			elif char == '}':
				if ignore == 0:
					# In order to identify inner clauses, __parse() is called
					# again until no more clauses are found. Only then the
					# secure translation is done.
					inside = False
					self.__parse(subline[:-1])
					subline = ""
				else:
					ignore = (ignore-1) if (ignore-1>=0) else ignore
			elif char == '\\':
				hop_next = True

		# Error handling:
		if inside is True:
			raise HumanFormatterError(ERROR_EXPECTED_CLOSURE)

		# Exiting the loop will mean that this subline must be translated,
		# or that the parsing has ended if it is the first instance:
		if first:
			# Replaces translations and applies format with __postproc.
			for ori, trans in self.trans:
				line = line.replace(ori, trans, 1)
			return line
		else:
			# Translates and formats the clause, saving it in the dict.
			self.__format(line)


	def __format (self, line):
		"""Translates and formats each given clause.
		It doesn't return anything, but saves both the original clause and its
		final formatted version in a dictionary so they can be replaced when
		all the formatting is made. This makes secure to use onion clauses.
		A lexer is used in order to identify what's inside a given clause.
		"""
		# Control variables:
		__replace_dict = dict()		# Replace every 'key' for its 'value'.
		__replace_list = list()		# For each cell, replaces (0) with (1).

		## Formatting what has been already translated:
		for ori, trans in self.trans:
			line = line.replace(ori, trans, 1)
		original = '{' + line[:] + '}'
		line = line.format(*self.args, **self.kwargs)

		## Lexing and setting up some lexer configuration.
		# For comfort, it builds a local class to handle the list of HFFunctions.
		aux = self.__lexer(line)
		class LocalFitems (object):
			def __init__ (self, fitems = aux):
				self.fitems = fitems
				self.fitem = None

			def get_fitem (self, key):
				for fitem in self.fitems:
					if fitem.key == key:
						self.fitem = fitem
						return fitem
				return None

			def add_fitem (self, key, args):
				self.fitems.append(HFFunction(key, args))

		fitems = LocalFitems()

		## Part 1: Translating identifiers.
		identifier = ""

		# - A. Autointerprete. Will try, in order: param, context and literal.
		#	If it finds what it is, it will include it so the following ifs
		#	catch them.
		if fitems.get_fitem("undef"):
			key = fitems.fitem.get_arg(0)
			try:
				# Try as param.
				_ = str('{'+key+'}').format(*self.args, **self.kwargs)
				fitems.add_fitem("param", [{'value': key}])
			except:
				# Try as contextual.
				try:
					_ = eval(key, {**self.calling_frame.f_locals,
					         	   **self.calling_frame.f_globals})
					fitems.add_fitem("context", [{'value': key}])
				except:
					# Set as literal.
					fitems.add_fitem("literal", [{'value': key}])


		# - 1.1. Empty (as str.format with {}):
		if fitems.get_fitem("noid"):
			identifier = str(self.__gi)
			self.__gi += 1

		# - 1.2. Literals:
		elif fitems.get_fitem("literal"):
			identifier = LITERAL_KEY
			self.kwargs[identifier] = fitems.fitem.get_arg()

		# - 1.3. Contextual (as f-strings):
		elif fitems.get_fitem("context"):
			identifier = CONTEXT_KEY
			self.kwargs[identifier] = eval(fitems.fitem.get_arg(),
			                               {**self.calling_frame.f_locals,
			                               **self.calling_frame.f_globals})

		# - 1.4. Parameter (as str.format()):
		elif fitems.get_fitem("param"):
			# That's the standard behavior.
			identifier = fitems.fitem.get_arg()

		else:
			raise SystemError(FATAL_ERROR_NO_ID)

		# - Trying to force casting of value, for numerics:
		try:
			self.kwargs[identifier] = eval(self.kwargs[identifier])
		except:
			pass


		## Part 2: Translating specs:
		fill = ""
		align = ""
		width = ""
		sign = ""
		alter = ""
		precision = ""
		limit_char = ""
		vtype = ""
		lmilsep = ""
		convert = ""
		open_char = close_char = ""
		do_color = False

		# - 2.1. Aligning:
		if fitems.get_fitem("align"):
			posdict = {"center": '^', "left": '<', "right": '>',
						"ralign": random.choice(['^','>','<'])}
			pos = fitems.fitem.get_arg()
			align = posdict[pos]

			if fitems.fitem.has_arg('width'):
				fitems.add_fitem("width", [{'size': fitems.fitem.last_arg}])

			if fitems.fitem.has_arg('fillchar'):
				fitems.add_fitem("fill", [{'fillchar': fitems.fitem.last_arg}])


		# - 2.2. Width:
		if fitems.get_fitem("width"):
			sizestr = fitems.fitem.get_arg()
			if sizestr.startswith('+'):
				# Handles relative width.
				width = int(sizestr[1:])
				aux_id = '{' + identifier + '}'
				aux = aux_id.format(*self.args, **self.kwargs)
				width += len(aux)
			else:
				width = int(sizestr)

			if fitems.fitem.has_arg("fillchar"):
				fitems.add_fitem("fill", [{'fillchar': fitems.fitem.last_arg}])


		# - 2.3. Filling:
		if fitems.get_fitem("fill"):
			align = align or '<'	# There must be alignment in order to fill.
			fill = fitems.fitem.get_arg()
			if len(fill) > 1:
				# Multichar filling - Placeholder and replacement system:
				fill = '{' + FILL_KEY + '}'
				self.kwargs[FILL_KEY] = FILL_PLACEHOLDER
				__replace_dict[FILL_PLACEHOLDER] = fitems.fitem.get_arg()

		elif fitems.get_fitem("rfill"):
			align = align or '<'
			# Random filling - Placeholder and replacement system:
			fill = '{' + RFILL_KEY + '}'
			self.kwargs[RFILL_KEY] = RFILL_PLACEHOLDER
			__replace_dict[RFILL_PLACEHOLDER] = fitems.fitem.get_arg()


		# - 2.4. Signing:
		if fitems.get_fitem("sign"):
			signdict = {"all":'+', "neg":'-', "sp":' ', "space":' '}
			try:
				sign = signdict[fitems.fitem.get_arg()]
			except:
				sign = '+'


		# - 2.5. Alternative representation.
		if fitems.get_fitem("alter"):
			alter = "#"

		# - 2.6. Precision.
		if fitems.get_fitem("decimal"):
			precision = '.' + str(fitems.fitem.get_arg())
			vtype = 'f'
			if fitems.fitem.has_arg("decsep"):
				fitems.add_fitem("decsep", [{'sep': fitems.fitem.last_arg}])

		elif fitems.get_fitem("limit"):
			precision = '.' + str(fitems.fitem.get_arg())
			if fitems.fitem.has_arg("endchar"):
				# Limiting ending char handling.
				limit_char = fitems.fitem.last_arg
				cropped = str('{'+f"{identifier}"+':'+f"{precision}"+'}'). \
					format(*self.args, **self.kwargs)
				__replace_list.append((cropped, cropped[:-1]+limit_char))

		# - 2.7. Type casting.
		#	- 2.7.1. Base:
		if fitems.get_fitem("base_cast"):
			basedict = {"bin": 'b', "oct": 'o', "octal": 'o',
						"hex": 'h', "Hex": 'H'}
			vtype = basedict[fitems.fitem.get_arg()]
			if fitems.fitem.get_arg("alter"):
				alter = '#'

		#	- 2.7.2. Raw casts:
		if fitems.get_fitem("raw_cast"):
			rawdict = {"char": 'c', "exp": 'e', "Exp": 'E', "round": 'g',
					   "Round": 'G', "per": '%'}
			vtype = rawdict[fitems.fitem.get_arg()]

		#	- 2.7.3. String conversions:
		if fitems.get_fitem("convert"):
			cnvdict = {"str": '!s', "repr": '!r'}
			convert = cnvdict[fitems.fitem.get_arg()]

		#	- 2.7.4. Integer conversions:
		if fitems.get_fitem("int"):
			vtype = 'd'
			if fitems.fitem.has_arg("milsep"):
				fitems.add_fitem("milsep", [{'sep': fitems.fitem.last_arg}])

		if fitems.get_fitem("float"):
			vtype = fitems.fitem.get_arg()[0]
			if fitems.fitem.has_arg("decsep"):
				fitems.add_fitem("decsep", [{'sep': fitems.fitem.last_arg}])
			if fitems.fitem.has_arg("milsep"):
				fitems.add_fitem("milsep", [{'sep': fitems.fitem.last_arg}])


		# - 2.8. Decimals separators.
		if fitems.get_fitem("decsep"):
			sep = fitems.fitem.get_arg()
			if sep == ',':
				sep = COMMA_PLACEHOLDER
			__replace_list.append(('.', sep))

		# - 2.9. Miles separator.
		if fitems.get_fitem("milsep"):
			lmilsep = ','
			__replace_list.append((',', fitems.fitem.get_arg()))


		# - 2.10. Surrounding (custom - [cow])
		if fitems.get_fitem("surround"):
			chars = fitems.fitem.get_arg()
			if len(chars) == 1:
				open_char = close_char = chars
			else:
				open_char = chars[:len(chars)//2]
				close_char = chars[len(chars)//2:]

		# - 2.12. Coloring and styling (custom) With Termcolor:
		set_color = set_hg = None
		set_style = list()
		if fitems.get_fitem("color"):
			set_color = fitems.fitem.get_arg()
			do_color = True
		if fitems.get_fitem("highlight"):
			set_hg = fitems.fitem.get_arg()
			do_color = True
		if fitems.get_fitem("style"):
			set_style = [fitems.fitem.get_arg()]
			do_color = True


		## Part 3: Formatting and post-procesing:
		frmt = '{' + identifier + convert + ':' + fill + align + sign + alter \
				+ str(width) + lmilsep + precision + vtype + '}'
		final = frmt.format(*self.args, **self.kwargs)

		for key, val in __replace_dict.items():
			if FILL_PLACEHOLDER == key:
				# Multi-char filling:
				total = len(val)
				for i in range(final.count(key)):
					final = final.replace(key, val[i%total], 1)
			elif RFILL_PLACEHOLDER == key:
				# Random-char filling:
				for _ in range(final.count(key)):
					final = final.replace(key, random.choice(val), 1)

		for key, val in __replace_list:
			# Limitters, decimal and milles separators.
			final = final.replace(key, val)

		final = final.replace(COMMA_PLACEHOLDER, ',')

		final = open_char + final + close_char

		if do_color:
			try:
				from termcolor import colored
				final = colored(final, color=set_color, on_color=set_hg,
				                attrs=set_style)
			except ImportError:
				# TODO: Do you want to import it?
				raise HumanFormatterError(FATAL_ERROR_NO_TERMCOLOR)

		# Part 4: Saving the formatted with its original line and returning:
		self.trans.append((original, final))
		return final


	def __lexer (self, line):
		"""Gathers the components of the given clause.
		It reads, identifies and transforms hformat functions into a list that
		the translator will be able to handle.
		It handles two different types of components:
			+ identifiers
			+ functions - Uses 'functions.yml' to recognise them.
		It returns a dictionary of HFFunction objects.
		"""
		cfg = list()
		## Loading YAML and setting up the functions dictionary:
		raw_yaml = yaml.load(open(FUNCTIONS_PATH, 'r'), Loader=yaml.FullLoader)
		ydict = dict()	# <name>: {<args>::list, <call>::str}
		for foo in raw_yaml:
			group = foo['def'] if isinstance(foo['def'], list) else [foo['def']]
			args = foo['args'] if ('args' in foo) else list()
			call = foo['call'] if ('call' in foo) else None
			for names in group:
				names = [n.strip() for n in names.split(',')]
				main_name = names[0]
				for name in names:
					ydict[name] = {
						'args': args,
						'call': call or main_name,
						'by_name': call is None
					}

		## Placeholding:
		# User-side placeholders:
		for key, val in USER_PLACEHOLDERS.items():
			line = line.replace(key, val)

		# Placeholding is done by identifying substring surrounded by an opening
		# and a closing char. Those are replaced with a random placeholder so
		# later they can be re-replaced. The format is:
		#	<open_char><close_char><placeholder_id><maintain_surrounders>
		phs = dict()
		rand_gen_key = lambda _id, _s: "$$$" + _id + '' \
			.join([str(random.randint(0,9)) for i in range(9)]) + _s + "$$$"
		for opcl in ("&;A-", "''Q+", '""Q+', '()P+'):
			open_char, close_char, ph_id, surr = opcl
			inside = False
			hide = ""		# String to placehold.
			ret_line = ""
			for char in line:
				if inside:
					hide += char
				if char == open_char and not inside:
					inside = True
				elif char == close_char and inside:
					inside = False
					# Adding 'hide' if not empty.
					if hide != close_char:
						phs[rand_gen_key(ph_id, surr)] = open_char + hide
					hide = ""
				ret_line += char

			if inside and (open_char == '('):
				raise HumanFormatterError(ERROR_EXPECTED_CLOSURE.format(close_char))

			# Replacing:
			for key, val in phs.items():
				ret_line = ret_line.replace(val, key)
			line = ret_line

		## Classification of elements of the line.
		MIXED = 0; ONLY_IDS = 1; ONLY_FOOS = 2
		lists = [list(), list(), list()]
		if ':' not in line:
			lists[MIXED] = line.split(',')
		else:
			lists[ONLY_IDS] = line.split(':')[0].split(',')
			lists[ONLY_FOOS] = line.split(':')[1].split(',')

		## Iteration through the three different lines:
		for which_list, content in enumerate(lists):
			for element in content:
				element = element.strip()
				fitem = None
				undef = True

				# Try to identify IDs.
				if which_list in (ONLY_IDS, MIXED):
					# The current format of identifiers should be:
					#	<[id_char][identifier]>
					if element.startswith(LITERAL_CHAR_ID):
						fitem = HFFunction("literal", [{'value': element[1:]}])
						undef = False
					elif element.startswith(CONTEXT_CHAR_ID):
						fitem = HFFunction("context", [{'value': element[1:]}])
						undef = False
					elif element.startswith(PARAM_CHAR_ID):
						fitem = HFFunction("param", [{'value': element[1:]}])
						undef = False
					elif (element == "") and (which_list == ONLY_IDS):
						fitem = HFFunction("noid")
						undef = False

				# Try identify functions.
				if (which_list in (ONLY_FOOS, MIXED)) and undef:
					# The current format of the function should be:
					#	<foo_name[args_placeholder]>
					# Which makes it easy to identify each component.
					for ph, orig in phs.items():
						if ph in element:
							# Function with args.
							fname = element[:element.find('$$$')]
							fargs = list()
							# Un-placeholding arguments.
							phargs = [arg.strip() for arg in orig[1:-1].split(',')]
							for pharg in phargs:
								if pharg in phs.keys():
									if pharg.endswith('-$$$'):
										fargs.append(phs[pharg][1:-1])
									elif pharg.endswith('+$$$'):
										fargs.append(phs[pharg])
								else:
									fargs.append(pharg)
							break
					else:
						# Function with no args.
						fname = element
						fargs = list()

					# Checking with YAML defined functions:
					if fname in ydict.keys():
						# Exists, proceeds to check if arguments are correct.
						undef = False
						fitem_args = list()
						for i, yarg in enumerate(ydict[fname]['args']):
							yarg_name, yarg_type, yarg_state = yarg.split(':')
							try:
								farg = fargs[i]
							except IndexError:
								# Can only happend if optional:
								if yarg_state == 'man':
									raise HumanFormatterError(ERROR_EXPECTED_ARG.format(fname, i))
								else:
									continue
							else:
								# Casting and evaluating arguments:
								eval_arg = ""
								if yarg_type == "any":
									eval_arg = farg
								elif yarg_type == "bool":
									eval_arg = bool(farg)
								elif yarg_type == "str" or yarg_type == 'chr':
									try:
										if farg.startswith('\'') and farg.endswith('\''):
											eval_arg = eval(farg)
										elif farg.startswith('"') and farg.endswith('"'):
											eval_arg = eval(farg)
										else:
											eval_arg = farg
									except:
										eval_arg = farg

									if (yarg_type=='chr') and (len(eval_arg)>1):
										raise HumanFormatterError(ERROR_WRONG_TYPED_ARG \
										.format(i, fname, yarg_type, type(eval_arg)))

								elif yarg_type in ("int", "float"):
									try:
										eval_arg = eval(f"{yarg_type}(farg)")
									except ValueError:
										raise HumanFormatterError(ERROR_WRONG_TYPED_ARG \
										.format(i, fname, yarg_type, type(eval_arg)))

								# Everything OK, create fitem argument dict:
								fitem_args.append({yarg_name: eval_arg})

						# Finally create function object and save.
						# It must be selected the way it must be call.
						key = ydict[fname]['call']
						if not ydict[fname]['by_name']:
							fitem_args = [{'name': fname}] + fitem_args

						fitem = HFFunction(key, fitem_args)

					else:
						# If name not in fnames, remain undef:
						undef = True

				# If nothing worked, set as undefined, or handle unid.
				if undef:
					if which_list == ONLY_FOOS:
						# Check config in order to pass or raise an error.
						if self.config['error_on_unknown_function']:
							raise HumanFormatterError(ERROR_UNKNOWN_FUNCTION.format(fname))
					else:
						# Packs everything in an 'undef' object.
						fitem = HFFunction("undef", [{'value': element}])

				# Appending created function object, if one given.
				if fitem is not None:
					cfg.append(fitem)

		return cfg


################################################################################

#
# Functions:
#
def hformat (line, *args, **kwargs):
	"""Function-style Human Formatter.
	It creates an object HumanFormatter, runs it, and returns the result.
	It also identifies the calling module.
	"""
	kwargs[CALLING_FRAME_KEY] = inspect.stack()[1].frame
	obj = HumanFormatter(line, *args, **kwargs)
	return obj.final

hf = hformat 	# Abbreviation, such as 'f' is for 'format'.

def hfprint (line, *args, **kwargs):
	"""Prints hformatted 'line'"""
	print(hformat(line, *args, **kwargs))

def hfconfig (*args, **kwargs):
	"""Changes the users general hformat configuration."""
	for key, val in kwargs.items():
			if key in HumanFormatter.HFCONFIG.keys():
				HumanFormatter.HFCONFIG[key] = val


################################################################################
