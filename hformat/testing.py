#!python3
#-*- coding: utf-8 -*-

from hformat import *

#
# Main (for testing purposes. Needs *termcolor*):
#
if __name__ == "__main__":

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

	out = hf("SPECS - ALIGN {:right, width(+5), fill(':-')}", 85)
	expect = "SPECS - ALIGN :-:-:85"
	cmp_test(out, expect)

	out = hf("SPECS - ALIGN {:left, width(10, #)}", 90)
	expect = "SPECS - ALIGN 90########"
	cmp_test(out, expect)

	out = hf("SPECS - ALIGN {:ralign(+6, _)}", 95)
	print(out, '\n')

	out = hf("SPECS - SIGN {+10:sign}")
	expect = "SPECS - SIGN +10"
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

	out = hf("SPECS - TYPE {1996.1512:float(&';, ',')}")
	expect = "SPECS - TYPE 1,996'151200"
	cmp_test(out, expect)

	out = hf("SPECS - TYPE {1996.1512:dec(4, &sq;, ',')}")
	expect = "SPECS - TYPE 1996'1512"
	cmp_test(out, expect)

	out = hf("SPECS - MISC {?fraselarga:width(+10, _), limit(5, .)}")
	expect = "SPECS - MISC fras._______________"
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

