#!/usr/bin/env python
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

	In order to achieve f-strings behavior, it uses the inspect module and the
	built-ins 'locals()' and 'globals()', although PEP498 discourages it.

	Check for further documentation at /projects/hformat/.

	Created:		27 Feb 2020
	Last modified:	11 Mar 2020
		+ Added function 'hfprint' for printing.
		+ Arguments mini-menu added for version checking.
		+ Added surrounders and coloring.
	TODO:
		- Modify lexer behavior, so (v2.5):
			- It implements function identification, allowing multinaming and
			non-: clauses to be correctly interpreted.
			- It identifies the arguments of the function, and raise the errors
			itself, rather than letting the formatter do that.
			- Function definition is separated in another file, so brining news
			up should only modify this file and set up whatever it does.
		- Allow some HTML and Markdown syntaxis, but just as literal conversions
		to hformat, without further specific code (v3).
"""
import sys
import inspect
import random

# Definitions and globals.
VERSION = "2.2"
#	Defines:
COLORS = ["grey", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
HIGHLIGHTS = ["on_"+color for color in COLORS]
STYLES = ["bold", "dark", "underline", "blink", "reverse", "cancealed"]
CONTEXT_CHAR_ID = '@'
LITERAL_CHAR_ID = '?'
PARAM_CHAR_ID = '%'
#	Placeholders:
COMMA_PLACEHOLDER = "$$$COMMA$$$"
FILL_PLACEHOLDER = chr(1500)
RFILL_PLACEHOLDER = chr(1501)
#	Intern keys:
CALLING_FRAME_KEY = "__cAlLiNg_MoDuLe__"
CONTEXT_KEY = "__cOnTeXt_KeY__"
FILL_KEY = "__FiLl__"
LITERAL_KEY = "__lItErAl__"
RFILL_KEY = "__rFiLl__"
#	Error messages:
ERROR_EXPECTED_ARGS = "{}() function expects, at least, {} arguments"
ERROR_EXPECTED_CLOSURE = "Expected '}' before ending string"
ERROR_FUNCTION_SYNTAX = "Expected ')' for closing, or no openning '('"
ERROR_WIDTH_USES_INT = "width() argument must be integers or integers preceded"\
					   "by '+' char"
FATAL_ERROR_NO_ID = "- FATAL - Identificator key not found"
FATAL_ERROR_NO_TERMCOLOR = "- FATAL - Termcolor module must be installed in" \
						   "order to allow using coloring and style functions"
WARNING_SIGN_NOARGS = "Warning: sign() used without arguments will be ignored"


################################################################################


# Classes.
class HumanFormatter (object):
	"""This class handles the main engine of hformat.
	It provides privates functions that achieve each part of the process.
	Those are:
	 1. Parsing the pseudo-language, identifying each {clause}.
	 2. Lexing each clause, identifying commands.
	 3. Interpreting and formatting each clause with its h-commands.
	"""
	def __init__ (self, line, *args, **kwargs):
		"""Receives the string, generates the formatted result."""
		self.original = line
		self.args = args
		self.kwargs = kwargs

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
			raise SyntaxError(ERROR_EXPECTED_CLOSURE)

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

		# Formatting what has been already translated:
		for ori, trans in self.trans:
			line = line.replace(ori, trans, 1)
		original = '{' + line[:] + '}'
		line = line.format(*self.args, **self.kwargs)

		# Lexing and setting up some lexer configuration:
		params = self.__lexer(line)
		given_foos = [param['name'] for param in params]
		get_args = lambda name: \
			[param['args'] for param in params if param['name']==name][0]

		# Part 1: Translating identifiers.
		identifier = ""

		# - A. Autointerprete. Will try, in order: param, context and literal.
		#	If it finds what it is, it will include it so the following ifs
		#	catch them.
		if "undef" in given_foos:
			key = get_args("undef")[0]
			try:
				# Try as param.
				_ = str('{'+key+'}').format(*self.args, **self.kwargs)
				given_foos.append("param")
				params.append({'name':"param", 'args':[key]})
			except:
				# Try as contextual.
				try:
					_ = eval(key, {**self.calling_frame.f_locals,
					         	   **self.calling_frame.f_globals})
					given_foos.append("context")
					params.append({'name':"context", 'args':[key]})
				except:
					# Set as literal.
					given_foos.append("literal")
					params.append({'name':"literal", 'args':[key]})


		# - 1.1. Empty (as str.format with {}):
		if "noid" in given_foos:
			identifier = str(self.__gi)
			self.__gi += 1

		# - 1.2. Literals:
		elif "literal" in given_foos:
			identifier = LITERAL_KEY
			self.kwargs[identifier] = get_args("literal")[0]

		# - 1.3. Contextual (as f-strings):
		elif "context" in given_foos:
			identifier = CONTEXT_KEY
			aux_id = get_args("context")[0]
			self.kwargs[identifier] = eval(aux_id,
			                               {**self.calling_frame.f_locals,
			                               **self.calling_frame.f_globals})

		# - 1.4. Parameter (as str.format()):
		elif "param" in given_foos:
			# That's the standard behavior.
			identifier = get_args("param")[0]

		else:
			raise SystemError(FATAL_ERROR_NO_ID)

		# - Trying to force casting of value, for numerics:
		try:
			self.kwargs[identifier] = eval(self.kwargs[identifier])
		except:
			pass

		# Part 2: Translating specs:
		# [[fill]align][sign][alter][width][lmilsep][.precision][vtype]
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
		if "center" in given_foos:
			align = '^'
			args = get_args("center")
		elif "left" in given_foos:
			align = "<"
			args = get_args("left")
		elif "right" in given_foos:
			align = ">"
			args = get_args("right")
		elif "ralign" in given_foos:
			align = random.choice(['^','>','<'])
			args = get_args("ralign")
		if align != "" and args is not None:
			# Checking possible arguments of alignment functions.
			try:
				# First argument would be the width:
				if "width" not in given_foos:
					params.append({'name': "width", 'args': [args[0]]})
					given_foos.append("width")
			except IndexError:
				pass
			try:
				# Second would be the filling char:
				if "fill" not in given_foos:
					params.append({'name': "fill", 'args': [args[1]]})
					given_foos.append("fill")
			except IndexError:
				pass

		# - 2.2. Width:
		if ("width" in given_foos) or ("w" in given_foos):
			try:
				size = get_args("width")[0]
			except TypeError:
				raise ValueError(ERROR_EXPECTED_ARGS.format("width", 1))
			try:
				# Tries to get 'fill' argument if given:
				if "fill" not in given_foos:
					params.append({'name': "fill",
					              'args': [get_args("width")[1]]})
					given_foos.append("fill")
			except IndexError:
				pass
			try:
				if size.startswith('+'):
					# Handles relative width.
					width = int(size[1:])
					aux_id = '{' + identifier + '}'
					aux = aux_id.format(*self.args, **self.kwargs)
					width += len(aux)
				else:
					width = int(size)
			except TypeError:
				raise ValueError(ERROR_WIDTH_USES_INT)

		# - 2.3. Filling:
		if ("fill" in given_foos) or ("f" in given_foos):
			align = align or '<'	# There must be alignment in order to fill.
			fill = (get_args("fill") or [''])[0]
			if len(fill) > 1:
				# Multichar filling - Placeholder and replacement system:
				fill = '{' + FILL_KEY + '}'
				self.kwargs[FILL_KEY] = FILL_PLACEHOLDER
				__replace_dict[FILL_PLACEHOLDER] = get_args("fill")[0]
		elif "rfill" in given_foos:
			align = align or '<'
			# Random filling - Placeholder and replacement system:
			fill = '{' + RFILL_KEY + '}'
			self.kwargs[RFILL_KEY] = RFILL_PLACEHOLDER
			try:
				__replace_dict[RFILL_PLACEHOLDER] = get_args("rfill")[0]
			except TypeError:
				raise SyntaxError(ERROR_EXPECTED_ARGS.format("rfill", 1))

		# - 2.4. Signing:
		if "sign" in given_foos:
			try:
				which = get_args("sign")[0]
			except TypeError:
				which = None
			if which == "all":
				sign = '+'
			elif which == "neg":
				sign = '-'
			elif which == "sp" or which == "space":
				sign = ' '
			else:
				print(WARNING_SIGN_NOARGS)

		# - 2.5. Alternative representation.
		if "alter" in given_foos:
			alter = "#"

		# - 2.6. Precision.
		if "decimal" in given_foos:
			try:
				precision = '.' + get_args("decimal")[0]
				vtype = 'f'
			except TypeError:
				raise SyntaxError(ERROR_EXPECTED_ARGS.format("decimal", 1))
		elif ("limit" in given_foos) or ("l" in given_foos):
			try:
				precision = '.' + get_args("limit")[0]
			except TypeError:
				raise SyntaxError(ERROR_EXPECTED_ARGS.format("limit", 1))
			try:
				# Second argument could be Limit Mark Char.
				limit_char = get_args("limit")[1]
				cropped = str('{'+f"{identifier}"+':'+f"{precision}"+'}'). \
					format(*self.args, **self.kwargs)
				__replace_list.append((cropped, cropped[:-1]+limit_char))
			except IndexError:
				pass

		# - 2.7. Type.
		if "bin" in given_foos:
			vtype = 'b'
			alter = '#' if (len(get_args("bin")) > 0) else alter
		elif "int" in given_foos:
			vtype = 'd'
			try:
				given_foos.append("milsep")
				params.append({'name':"milsep", 'args':[get_args("int")[0]]})
			except TypeError:
				pass
		elif "char" in given_foos or "chr" in given_foos:
			vtype = 'c'
		elif "oct" in given_foos:
			vtype = 'o'
			alter = '#' if (len(get_args("oct")) > 0) else alter
		elif "hex" in given_foos:
			vtype = 'x'
			alter = '#' if (len(get_args("hex")) > 0) else alter
		elif "Hex" in given_foos:
			vtype = 'X'
			alter = '#' if (len(get_args("Hex")) > 0) else alter
		elif "exp" in given_foos:
			vtype = 'e'
		elif "Exp" in given_foos:
			vtype = 'E'
		elif "float" in given_foos:
			vtype = 'f'
			try:
				given_foos.append("decsep")
				params.append({'name':"decsep", 'args':[get_args("float")[0]]})
			except TypeError:
				pass
			try:
				given_foos.append("milsep")
				params.append({'name':"milsep", 'args':[get_args("float")[1]]})
			except TypeError:
				pass
		elif "Float" in given_foos:
			vtype = 'F'
			try:
				given_foos.append("decsep")
				params.append({'name':"decsep", 'args':[get_args("Float")[0]]})
			except TypeError:
				pass
			try:
				given_foos.append("milsep")
				params.append({'name':"milsep", 'args':[get_args("Float")[1]]})
			except TypeError:
				pass
		elif "round" in given_foos:
			vtype = 'g'
		elif "Round" in given_foos:
			vtype = 'G'
		elif "per" in given_foos:
			vtype = '%'

		# - 2.8. Decimals separators.
		if "decsep" in given_foos:
			try:
				__replace_list.append(('.', get_args("decsep")[0]))
			except TypeError:
				raise SyntaxError(ERROR_EXPECTED_ARGS.format("decsep", 1))

		# - 2.9. Miles separator.
		if "milsep" in given_foos:
			try:
				lmilsep = ','
				__replace_list.append((',', get_args("milsep")[0]))
			except TypeError:
				raise SyntaxError(ERROR_EXPECTED_ARGS.format("milsep", 1))

		# - 2.10. Conversion.
		if "convert" in given_foos:
			try:
				convert = '!' + get_args("convert")[0]
			except TypeError:
				raise SyntaxError(ERROR_EXPECTED_ARGS.format("convert", 1))

		# - 2.11. Surrounding (custom - [cow])
		if "surround" in given_foos or "surr" in given_foos:
			try:
				chars = get_args("surround")[0]
			except TypeError:
				raise SyntaxError(ERROR_EXPECTED_ARGS.format("surround", 1))
			if len(chars) == 1:
				open_char = close_char = chars
			else:
				open_char = chars[:len(chars)//2]
				close_char = chars[len(chars)//2:]

		# - 2.12. Coloring and styling (custom) With Termcolor:
		set_color = [color for color in COLORS if (color in given_foos)]
		set_hg = [hg for hg in HIGHLIGHTS if (hg in given_foos)]
		set_style = [attr for attr in STYLES if (attr in given_foos)]
		if (set_color + set_hg + set_style) != []:
			set_color = ((len(set_color)>0) and set_color[-1]) or None
			set_hg = ((len(set_hg)>0) and set_hg[-1]) or None
			set_style = ((len(set_style)>0) and set_style) or None
			do_color = True

		# Part 3: Formatting and post-procesing:
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

		final = open_char + final + close_char

		if do_color:
			try:
				from termcolor import colored
				final = colored(final, color=set_color, on_color=set_hg,
				                attrs=set_style)
			except ImportError:
				raise SyntaxError(FATAL_ERROR_NO_TERMCOLOR)

		# Part 4: Saving the formatted with its original line and returning:
		self.trans.append((original, final))
		return final


	def __lexer (self, line):
		"""Gathers the components of the given clause.
		It reads, identifies and transforms hformat functions into a list that
		the translator will be able to handle.
		It creates a list where each cell is a dictionary with {name, args}.
		"""
		cfg = list()

		# Getting identificator or expression:
		id_line = line.split(':')[0].strip()
		cfg.append(dict())
		if id_line == "":
			cfg[-1]['name'] = "noid"
			cfg[-1]['args'] = []
		elif id_line.startswith(LITERAL_CHAR_ID):
			cfg[-1]['name'] = "literal"
			cfg[-1]['args'] = [id_line[1:]]
		elif id_line.startswith(CONTEXT_CHAR_ID):
			cfg[-1]['name'] = "context"
			cfg[-1]['args'] = [id_line[1:]]
		elif id_line.startswith(PARAM_CHAR_ID):
			cfg[-1]['name'] = "param"
			cfg[-1]['args'] = [id_line[1:]]
		else:
			cfg[-1]['name'] = "undef"
			cfg[-1]['args'] = [id_line]

		if ':' in line:
			# Getting specs functions:
			specs_line = line[line.find(':')+1:].strip()
			# 	Saving in-brackets commas, which don't separate functions:
			inside = False
			clean_line = ""		# Here will be stored the cleaned line.
			for char in specs_line:
				if char == '(':
					inside = True
				elif char == ')':
					inside = False
				if char == ',' and inside:
					clean_line += COMMA_PLACEHOLDER
				else:
					clean_line += char
			# 	Separating each function using the commas. Getting args:
			if inside is not False:
				raise SyntaxError(ERROR_FUNCTION_SYNTAX)
			foos = clean_line.split(',')
			for foo in foos:
				cfg.append(dict())
				back = foo.replace(COMMA_PLACEHOLDER, ',').strip()
				if '(' in back:
					cfg[-1]['name'] = back[:back.find('(')]
					raw_args = back[back.find('(')+1:back.find(')')]
					args = list()
					for arg in raw_args.split(','):
						arg = arg.strip()
						if arg == '\'' or arg == '"':
							pass
						elif arg.startswith('\'') and arg.endswith('\''):
							arg = eval(arg)
						elif arg.startswith('"') and arg.endswith('"'):
							arg = eval(arg)
						args.append(arg)
					cfg[-1]['args'] = args[:] or None
				else:
					# Non-arguments function:
					cfg[-1]['name'] = back
					cfg[-1]['args'] = None

		return cfg


################################################################################


# Functions:
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


################################################################################


# Main:
if __name__ == "__main__":

	if len(sys.argv) > 1:
		if sys.argv[1] == "-v":
			print("HFormat Version {}".format(VERSION))
			sys.exit(0)
		elif sys.argv[1] == "-t":
			print(">> Testing mode")
		else:
			sys.exit(0)
	else:
		sys.exit(0)

	from termcolor import colored	# Just for testing.

	"""Testing purposes."""
	def cmp_test (a, b):
		"""Compares a and b. Presents the result."""
		print(" > " + a)
		print(colored("OK", "green", attrs=["reverse"]) if a==b else \
		      colored("FAILED", "red", attrs=["reverse"]))
		print()

	# Identifiers:
	out = hf("ID - EMPTY {}", 100)
	expect = "ID - EMPTY 100"
	cmp_test(out, expect)

	out = hf("ID - LITERAL UNDEF {patata}")
	expect = "ID - LITERAL UNDEF patata"
	cmp_test(out, expect)

	out = hf("ID - LITERAL DEF {?queso}")
	expect = "ID - LITERAL DEF queso"
	cmp_test(out, expect)

	ctx = 2001
	out = hf("ID - CONTEXT UNDEF {ctx}")
	expect = "ID - CONTEXT UNDEF 2001"
	cmp_test(out, expect)

	ctx2 = 2002
	out = hf("ID - CONTEXT DEF {@ctx2}")
	expect = "ID - CONTEXT DEF 2002"
	cmp_test(out, expect)

	out = hf("ID - PARAM UNDEF {prm}", prm=3.1415)
	expect = "ID - PARAM UNDEF 3.1415"
	cmp_test(out, expect)

	out = hf("ID - PARAM DEF {%prm}", prm=3.1415)
	expect = "ID - PARAM DEF 3.1415"
	cmp_test(out, expect)

	beta = 'HOLA'
	out = hf("ID - MIX {1} {%alfa} {?alfa} {beta} {fuera}", 1, 2, 3, alfa=4)
	expect = "ID - MIX 2 4 alfa HOLA fuera"
	cmp_test(out, expect)

	# Specs:
	out = hf("SPECS - ALIGN {:center, width(10), fill(#)}", 80)
	expect = "SPECS - ALIGN ####80####"
	cmp_test(out, expect)

	out = hf("SPECS - ALIGN {:right, width(+5), fill(:-)}", 85)
	expect = "SPECS - ALIGN :-:-:85"
	cmp_test(out, expect)

	out = hf("SPECS - ALIGN {:left, width(10, #)}", 90)
	expect = "SPECS - ALIGN 90########"
	cmp_test(out, expect)

	out = hf("SPECS - ALIGN {:ralign(+6, _)}", 95)

	out = hf("SPECS - SIGN {+10:sign}")
	expect = "SPECS - SIGN 10"
	cmp_test(out, expect)

	out = hf("SPECS - SIGN {+11:sign(all)}")
	expect = "SPECS - SIGN +11"
	cmp_test(out, expect)

	out = hf("SPECS - SIGN {+12:sign(neg)}")
	expect = "SPECS - SIGN 12"
	cmp_test(out, expect)

	out = hf("SPECS - SIGN {+13:sign(sp)}")
	expect = "SPECS - SIGN  13"
	cmp_test(out, expect)

	out = hf("SPECS - TYPE {3.141592:decimal(2)}")
	expect = "SPECS - TYPE 3.14"
	cmp_test(out, expect)

	out = hf("SPECS - MISC {?fraselarga:width(+10, _), limit(5, .)}")
	expect = "SPECS - MISC fras._______________"
	cmp_test(out, expect)

	out = hf("SPECS - MISC {1512.935:decimal(3),float(',' ')}")
	expect = "SPECS - MISC 1 512'935"
	cmp_test(out, expect)

	out = hf("SPECS - CONVERT {?conv:convert(r)}")
	expect = "SPECS - CONVERT 'conv'"
	cmp_test(out, expect)

	out = hf("SPECS - SURR {palabra:width(10),surround([])}")
	expect = "SPECS - SURR [palabra   ]"
	cmp_test(out, expect)

	out = hf("SPECS - COLOR {pikachu:yellow}")
	expect = "SPECS - SURR..."
	print(out)

	out = hf("{{?PIKACHU:center(+10),yellow,on_bc}:surround(|)}")
	expect = "SPECS - SURR..."
	print(out)
	print()

	out = hf("{{:underline,limit(18,.)}:left(20),surround(|  |)}",
	         "Bosnia y Herzegovina")
	print(out)







