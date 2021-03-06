# Tampio Interpreter
# Copyright (C) 2017 Iikka Hauhio

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os, sys, traceback, argparse, operator, re, readline, atexit
from voikko.libvoikko import Voikko, Token
from voikko.inflect_word import inflect_word

LANGUAGE = "fi-x-morpho"
ENCODING = "UTF-8"

voikko = Voikko(LANGUAGE)

CASES_LATIN = {
	"nimento": "nominatiivi",
	"omanto": "genetiivi",
	"osanto": "partitiivi",
	"olento": "essiivi",
	"tulento": "translatiivi",
	"ulkotulento": "allatiivi",
	"ulkoolento": "adessiivi",
	"ulkoeronto": "ablatiivi",
	"sisatulento": "illatiivi",
	"sisaolento": "inessiivi",
	"sisaeronto": "elatiivi",
	"vajanto": "abessiivi",
	"keinonto": "instruktiivi",
	"seuranto": "komitatiivi",
	"kerrontosti": "adverbi"
}

CASES_ENGLISH = {
	"nimento": "nominative",
	"omanto": "genitive",
	"osanto": "partitive",
	"olento": "essive",
	"tulento": "translative",
	"ulkotulento": "allative",
	"ulkoolento": "adessive",
	"ulkoeronto": "ablative",
	"sisatulento": "illative",
	"sisaolento": "inessive",
	"sisaeronto": "elative",
	"vajanto": "abessive",
	"keinonto": "instructive",
	"seuranto": "comitative",
	"kerrontosti": "adverb"
}

CASES_ABRV = {
	"": "*",
	"nimento": "N",
	"omanto": "G",
	"osanto": "P",
	"olento": "E",
	"tulento": "T",
	"ulkotulento": "U<",
	"ulkoolento": "U_",
	"ulkoeronto": "U>",
	"sisatulento": "S<",
	"sisaolento": "S_",
	"sisaeronto": "S>",
	"vajanto": "A",
	"keinonto": "I",
	"seuranto": "K",
	"kerrontosti": "D"
}

CASES_A = {
	"nimento": "",
	"omanto": ":n",
	"osanto": ":ta",
	"olento": ":na",
	"tulento": ":ksi",
	"ulkotulento": ":lle",
	"ulkoolento": ":lla",
	"ulkoeronto": ":lta",
	"sisatulento": ":han",
	"sisaolento": ":ssa",
	"sisaeronto": ":sta",
	"vajanto": ":tta",
	"keinonto": ":in",
	"seuranto": ":ineen",
	"kerrontosti": ":sti"
}

CASES_F = {
	"nimento": "",
	"omanto": ":n",
	"osanto": ":ää",
	"olento": ":nä",
	"tulento": ":ksi",
	"ulkotulento": ":lle",
	"ulkoolento": ":llä",
	"ulkoeronto": ":ltä",
	"sisatulento": ":ään",
	"sisaolento": ":ssä",
	"sisaeronto": ":stä",
	"vajanto": ":ttä",
	"keinonto": ":in",
	"seuranto": ":ineen",
	"kerrontosti": ":sti"
}

CASES_ELLIPSI = {
	"nimento": "",
	"omanto": ":n",
	"osanto": ":ä",
	"olento": ":nä",
	"tulento": ":ksi",
	"ulkotulento": ":lle",
	"ulkoolento": ":llä",
	"ulkoeronto": ":ltä",
	"sisatulento": ":iin",
	"sisaolento": ":ssä",
	"sisaeronto": ":stä",
	"vajanto": ":ttä",
	"keinonto": ":ein",
	"seuranto": ":eineen",
	"kerrontosti": ":sti"
}

CASE_REGEXES = {
	"singular": {
		"omanto": r"[^:]+:n",
		"osanto": r"[^:]+:(aa?|ää?|t[aä])",
		"olento": r"[^:]+:(n[aä])",
		"tulento": r"[^:]+:ksi",
		"ulkotulento": r"[^:]+:lle",
		"ulkoolento": r"[^:]+:ll[aä]",
		"ulkoeronto": r"[^:]+:lt[aä]",
		"sisatulento": r"[^:]+:(aan|ään|h[aeiouyäöå]n)",
		"sisaolento": r"[^:]+:ss[aä]",
		"sisaeronto": r"[^:]+:st[aä]",
		"vajanto": r"[^:]+:tt[aä]"
	},
	"plural": {
		"omanto": r"[^:]+:ien",
		"osanto": r"[^:]+:(ia?|iä?|it[aä])",
		"olento": r"[^:]+:(in[aä])",
		"tulento": r"[^:]+:iksi",
		"ulkotulento": r"[^:]+:ille",
		"ulkoolento": r"[^:]+:ill[aä]",
		"ulkoeronto": r"[^:]+:ilt[aä]",
		"sisatulento": r"[^:]+:(iin|ih[aeiouyäöå]n)",
		"sisaolento": r"[^:]+:iss[aä]",
		"sisaeronto": r"[^:]+:ist[aä]",
		"vajanto": r"[^:]+:itt[aä]",
		"keinonto": r"[^:]+:in",
		"seuranto": r"[^:]+:ine[^:]*"
	},
	"": {
		"kerrontosti": "[^:]+:sti"
	}
}

def inflect(word, case):
	case_latin = CASES_LATIN[case]
	if word[0] == "@":
		case_latin += "_mon"
	word = word[1:]
	
	if re.fullmatch(r"[0-9]+", word):
		if case == "sisatulento":
			if word[-1] in "123560":
				return word + ":een"
			elif word[-1] in "479":
				return word + ":ään"
			else: # 8
				return word + ":aan"
		elif word[-1] in "14579":
			return word + CASES_A[case].replace("a", "ä")
		else:
			return word + CASES_A[case]
	elif len(word) == 1:
		if word in "flmnrsx":
			return word + CASES_F[case]
		elif case == "sisatulento":
			if word in "aeiouyäöå":
				return word + ":h" + word + "n"
			elif word in "bcdgptvw":
				return word + ":hen"
			elif word in "hk":
				return word + ":hon"
			elif word == "j":
				return "j:hin"
			elif word == "q":
				return "q:hun"
			elif word == "z":
				return "z:aan"
		elif word in "ahkoquzå":
			return word + CASES_A[case]
		else:
			return word + CASES_A[case].replace("a", "ä")
	else:
		inflections = inflect_word(word)
		if case_latin not in inflections:
			return word + ":" + case
		return inflections[case_latin]
		

def lexLine(line):
	output = []
	if "#" in line:
		line = line[:line.index("#")]
	paragraph = line.strip()
	if paragraph == "":
		return []
	for token in voikko.tokens(paragraph):
		if token.tokenType != Token.WORD:
			continue
		word = token.tokenText
		
		cont = False
		for number in CASE_REGEXES:
			for case in CASE_REGEXES[number]:
				if re.fullmatch(CASE_REGEXES[number][case], word):
					output += [[Noun(word[:word.index(":")], case, number)]]
					cont = True
		if cont:
			continue
		
		analysisList = voikko.analyze(word)
		alternatives = []
		for analysis in analysisList:
			bf = analysis["BASEFORM"]
			cl = analysis["CLASS"]
			if cl in ["nimisana", "lyhenne", "lukusana", "laatusana", "nimisana_laatusana", "etunimi", "asemosana"]:
				case = analysis["SIJAMUOTO"]
				number = analysis["NUMBER"] if "NUMBER" in analysis else ""
				alternatives += [Noun(bf, case, number, "pronoun" if cl == "asemosana" else "noun")]
			elif cl == "seikkasana":
				alternatives += [Noun(bf, "nimento", "na")]
			elif cl in ["teonsana", "kieltosana"]:
				alternatives += [Verb(bf)]
			elif cl == "sidesana":
				alternatives += [Conj(bf)]
			elif debug:
				print("Unknown word:", bf, analysis)
		if len(alternatives) == 0:
			alternatives += [Noun(word, "nimento", "singular")]
		output += [alternatives]
	return output

class Noun:
	def __init__(self, bf, case, num, cl = "noun"):
		self.cl = cl
		self.bf = bf
		self.case = case
		self.num = num
	def str(self, nocase=False):
		num = "?" if self.cl == "pronoun" else "$" if self.num == "singular" else "@" if self.num == "plural" else "."
		case = CASES_ABRV[self.case]
		if nocase:
			return num + self.bf
		else:
			return num + self.bf + ":" + case

class Verb:
	def __init__(self, bf):
		self.cl = "verb"
		self.bf = bf
	def str(self):
		return "#" + self.bf

class Conj:
	def __init__(self, bf):
		self.cl = "conj"
		self.bf = bf
	def str(self, nocase=False):
		return "&" + self.bf

def nextWord(words):
	if len(words) == 0:
		fatalError("Syntax error: unexpected eof")
	w = words[0]
	del words[0]
	return as2w(w)

PROMOTE = [
	"yksi",
	"ehto"
]

def as2w(w):
	return sorted(w, key=lambda a: 2 if a.bf in PROMOTE else 1 if a.cl == "noun" else 0)[-1]

def isNext(words, s):
	if isinstance(s, list):
		return len(words) > 0 and as2w(words[0]).str() in s
	else:
		return len(words) > 0 and as2w(words[0]).str() == s

def checkCase(got, expected, place):
	if got != expected:
		fatalError("Syntax error: illegal case: expected " + CASES_ENGLISH[expected] + ", got " + CASES_ENGLISH[got] + " (" + place + ")")

class EqTree:
	def __init__(self, op, always, left, right, where):
		self.op = op
		self.always = always
		self.left = left
		self.right = right
		self.where = where
	def str(self):
		if self.query():
			return self.left.str()
		elif self.op == "#olla":
			return self.left.str() + " = " + self.right.str() + ("" if not self.where else ", where " + ", ".join([v + " = " + b.str() for v, b in self.where]))
		elif self.op == "#esittää":
			return self.left.str() + ' = "' + self.right.str() + '"'
	def query(self):
		return self.right == None

eqCounter = 0
def createEqName(counter):
	return VarTree("$<vaihe " + str(counter) + ">", "$funktio")

def makeArgChain(args):
	arg = args[-1]
	for a in args[-2::-1]:
		arg = CallTree(VarTree("&ja"), [a, arg], "", ("", ""))
	return arg

def parseWhen(words):
	global eqCounter
	eq = parseEq(words, False)
	if eq.op != "#olla" or not eq.always:
		return [eq]
	
	eqs = []
	variables = []
	while isNext(words, "&kun"):
		del words[0]
		eqCounter += 1
		
		when = parseEq(words, False)
		
		arg = makeArgChain([createEqName(eqCounter+1)] + variables)
		right = CallTree(VarTree("$liitetty"), [when.right, arg], "olento", ("", "sisatulento"))
		
		if len(eqs) == 0:
			eqs += [EqTree("#olla", True, eq.left, right, when.where)]
		else:
			name = createEqName(eqCounter)
			arg = makeArgChain([VarTree("$m")] + variables[1:])
			left = CallTree(name, [variables[0], arg], "olento", ("", "ulkotulento"))
			eqs += [EqTree("#olla", True, left, right, when.where)]
		
		if not isinstance(when.left, VarTree):
			fatalError("Syntax error: expected identifier after 'kun', got a more complex expression (" + when.left.inflect("nimento") + ")")
		variables = [when.left] + variables
	
	if len(eqs) == 0:
		return [eq]
	else:
		eqCounter += 1
		name = createEqName(eqCounter)
		arg = makeArgChain([VarTree("$m")] + variables[1:])
		left = CallTree(name, [variables[0], arg], "olento", ("", "ulkotulento"))
		eqs += [EqTree("#olla", True, left, eq.right, eq.where)]
		
		return eqs

def parseEq(words, allowQueries):
	c, left = parsePattern(words)
	checkCase(c, "nimento", left.inflect(c))
	
	if len(words) == 0 and allowQueries:
		return EqTree("", True, left, None, None)
	
	w = nextWord(words)
	if w.str() not in ["#olla", "#esittää"]:
		fatalError("Syntax error: expected 'on' or 'esitetään' (at " + w.str() + ")")
	
	always = True
	if isNext(words, ".epäpuhdas:D"):
		del words[0]
		always = False
	
	c, right = parsePattern(words)
	checkCase(c, "nimento", right.inflect(c))
	
	where = []
	if isNext(words, "?mikä:S_"):
		del words[0]
		
		var = nextWord(words)
		if var.cl != "noun":
			fatalError("Syntax error: expected noun (" + var.str() + ")")
		checkCase(var.case, "nimento", var.str())
		varName = var.str(nocase=True)
		
		w = nextWord(words)
		if w.str() != "#olla":
			fatalError("Syntax error: expected 'on' (at " + w.str() + ")")
		c, body = parsePattern(words)
		checkCase(c, "nimento", right.inflect(c))
		
		where += [(varName, body)]
		
		left = left.subs({varName: body})
	
	return EqTree(w.str(), always, left, right, where)

def parseVar(name):
	if magic and re.fullmatch(r"\$([1-9][0-9]*|0)", name):
		return NumTree(int(name[1:]))
	elif magic and name == "$nolla":
		return NumTree(0)
	else:
		return VarTree(name)

class AtomicTree:
	def __init__(self):
		pass
	def safeEq(self, tree, objects=None):
		return self == tree
	def match(self, tree):
		return False, {}
	def subs(self, subs, objects=None):
		return self
	def shouldReverseOrder(self):
		return True
	def containsFunctions(self):
		return self in FUNCTIONS

class VarTree(AtomicTree):
	def __init__(self, name, alias=None):
		super().__init__()
		self.name = name
		self.alias = alias
	def __eq__(self, tree):
		return type(tree) == VarTree and self.name == tree.name
	def __hash__(self):
		return hash(self.name) * 7
	def copy(self, objects=None):
		return VarTree(self.name)
	def str(self, objects=None):
		return self.name
	def match(self, tree):
		if re.fullmatch(r".[^0-9]", self.name):
			return True, {self.name: tree}
		if isinstance(tree, VarTree):
			return self.name == tree.name, {}
		elif isinstance(tree, NumTree):
			if self.name == "$nolla" and tree.num == 0:
				return True, {}
			return self.name == str(tree.num), {}
		return False, {}
	def inflect(self, case, objects=None):
		if self.alias is not None:
			return '"' + inflect(self.alias, case) + '"'
		else:
			return inflect(self.name, case)
	def subs(self, subs, objects=None):
		if self.name in subs:
			return subs[self.name]
		else:
			return self

class NumTree(AtomicTree):
	def __init__(self, num):
		super().__init__()
		self.num = num
	def __eq__(self, tree):
		return type(tree) == NumTree and self.num == tree.num
	def __hash__(self):
		return self.num * 7
	def copy(self, objects=None):
		return NumTree(self.num)
	def str(self, objects=None):
		if self.num == 0:
			return "$nolla"
		else:
			return "$" + str(self.num)
	def match(self, tree):
		if isinstance(tree, NumTree):
			return self.num == tree.num, {}
		elif isinstance(tree, VarTree):
			if self.num == 0 and tree.name == "$nolla":
				return True, {}
			return str(self.num) == tree.name, {}
		return False, {}
	def inflect(self, case, objects=None):
		if self.num == 0:
			return inflect("$nolla", case)
		else:
			return '"' + inflect("$" + str(self.num), case) + '"'

class WorldTree(AtomicTree):
	def __init__(self, counter):
		self.counter = counter
	def __eq__(self, tree):
		return type(tree) == WorldTree and self.counter == tree.counter
	def __hash__(self):
		return self.counter * 13
	def copy(self, objects=None):
		return WorldTree(self.counter)
	def nextWorld(self):
		return WorldTree(self.counter + 1)
	def str(self, objects=None):
		return "$maailma(" + str(self.counter) + ")"
	def inflect(self, case, objects=None):
		return '"' + inflect("$maailma", case) + '"'

class CallTree:
	def __init__(self, head, args, headInfl, argInfls):
		self.head = head
		self.args = args
		self.headInfl = headInfl
		self.argInfls = argInfls
		if self.head and not freeMode and not isinstance(head, VarTree):
			fatalError("Syntax error: the head of the call must be a word in the restricted mode (" + self.inflect("nimento") + ")")
	def __eq__(self, tree):
		if type(tree) == CallTree:
			return self.headInfl == tree.headInfl and self.argInfls == tree.argInfls and self.head == tree.head and self.args == tree.args
		else:
			return False
	def safeEq(self, tree, objects=[]):
		if not isinstance(tree, CallTree):
			return False
		for obj in objects:
			if obj is self:
				return True
		objects += [self]
		return (len(self.args) == len(tree.args)
			and self.headInfl == tree.headInfl
			and self.argInfls == tree.argInfls
			and self.head.safeEq(tree.head, objects)
			and all([arg.safeEq(arg2, objects) for arg, arg2 in zip(self.args, tree.args)]))
	def copy(self, objects=[]):
		for obj, copy in objects:
			if obj is self:
				return copy
		copy = CallTree(None, None, self.headInfl, self.argInfls)
		objects = objects+[(self, copy)]
		copy.head = self.head.copy(objects)
		copy.args = [arg.copy(objects) for arg in self.args]
		return copy
	def headIs(self, tree, headInfl, argInfls):
		inflOk = self.headInfl == headInfl and self.argInfls == argInfls
		if isinstance(tree, str):
			return isinstance(self.head, VarTree) and self.head.name == tree
		else:
			return self.head == tree and inflOk
	def getHead(self):
		return (self.head, self.headInfl, self.argInfls)
	def str(self, objects=[]):
		for i in range(len(objects)):
			if objects[i] is self:
				return "\\" + str(i)
		objects = objects + [self]
		return self.head.str(objects) + ":" + CASES_ABRV[self.headInfl] + "(" + ", ".join([arg.str(objects) + ":" + CASES_ABRV[argInfl] for arg, argInfl in zip(self.args, self.argInfls)]) + ")"
	def match(self, tree):
		if isinstance(tree, CallTree):
			if self.headInfl != tree.headInfl:
				return False, {}
			
			ok, subs = self.head.match(tree.head)
			
			if not ok or len(tree.args) != len(self.args):
				return False, {}
			
			for arg, arg2, ai, ai2 in zip(self.args, tree.args, self.argInfls, tree.argInfls):
				if ai != ai2:
					return False, {}
				ok, subs2 = arg.match(arg2)
				for key in subs2:
					if key in subs:
						if not subs[key].safeEq(subs2[key]):
							return False, {}
				subs.update(subs2)
				if not ok:
					return False, {}
			return True, subs
		if isinstance(tree, NumTree) and tree.num > 0:
			if self.headIs("$seuraaja", "", ("omanto",)):
				return self.args[0].match(NumTree(tree.num - 1))
		return False, {}
	def subs(self, subs, objects=[]):
		for obj, copy in objects:
			if obj is self:
				return copy
		copy = CallTree(None, None, self.headInfl, self.argInfls)
		objects = objects+[(self, copy)]
		copy.head = self.head.subs(subs, objects)
		copy.args = [arg.subs(subs, objects) for arg in self.args]
		return copy
		#return CallTree(self.head.subs(subs), [arg.subs(subs) for arg in self.args], self.headInfl, self.argInfls)
	def inflect(self, case, objects=[]):
		for obj in objects:
			if obj is self:
				return "..." + CASES_ELLIPSI[case]
		objects = objects[:] + [self]
		if isinstance(self.head, VarTree) and self.head.str() in CONJUNCTIONS:
			return self.args[0].inflect(case, objects) + " " + self.head.name[1:] + " " + self.args[1].inflect(case, objects)
		if isinstance(self.head, VarTree) and self.head.str() in BINARY_OPERATORS:
			return self.args[0].inflect("nimento", objects) + " " + self.head.name[1:] + " " + self.args[1].inflect(case, objects)
		if self.headIs("$lisätty", "olento", ("", "sisatulento")):
			elements = [self.args[0]]
			tail = self.args[1]
			while isinstance(tail, CallTree) and tail.headIs("$lisätty", "olento", ("", "sisatulento")):
				elements += [tail.args[0]]
				tail = tail.args[1]
			tailString = "" if isinstance(tail, VarTree) and tail.str() == "$tyhjyys" else " ++ " + tail.inflect("nimento", objects)
			return '"%s" [%s]%s' % (
				inflect("$lista", case),
				", ".join([e.inflect("nimento", objects) for e in elements]),
				tailString)
		if self.headInfl == "olento":
			# TODO: entä jos tulevaisuudessa olisikin enemmän argumentteja???
			if case != "omanto" and len(self.args) == 2 and self.args[1].shouldReverseOrder():
				return (self.args[0].inflect(case, objects) + " "
					+ self.args[1].inflect(self.argInfls[1], objects) + " "
					+ self.head.inflect("olento", objects))
			a = self.args[0].inflect(case, objects) + " " + self.head.inflect("olento", objects)
			if len(self.args) == 2:
				a += " " + self.args[1].inflect(self.argInfls[1], objects)
			return a
		return self.args[0].inflect("omanto", objects) + " " + self.head.inflect(case, objects)
	def shouldReverseOrder(self):
		return self.headInfl != "olento" and (len(self.args) > 1 and self.args[-1].shouldReverseOrder())
	def containsFunctions(self):
		if self.getHead() in FUNCTIONS:
			return True
		for arg in self.args:
			if arg.containsFunctions():
				return True

BINARY_OPERATORS_CASE = [".ynnä:N", "$plus:N", "$miinus:N", "$modulo:N"]
BINARY_OPERATORS = [".ynnä", "$plus", "$miinus", "$modulo"]
CONJUNCTIONS = ["&ja", "&sekä", "&tai"]

def parsePattern(words):
	case, root = parseUnary(words)
	while len(words) != 0:
		w = as2w(words[0])
		if w.str() in (CONJUNCTIONS + BINARY_OPERATORS_CASE):
			del words[0]
			
			case2, arg = parseUnary(words)
			if w.str() in CONJUNCTIONS:
				checkCase(case2, case, w.str())
			case = case2
			
			root = CallTree(VarTree(w.str(nocase=True)), [root, arg], "", ("", ""))
		else:
			break
	return case, root

def parseUnary(words, allowReverseWordOrder=True):
	w = nextWord(words)
	if w.cl != "noun":
		fatalError("Syntax error: expected noun (at " + w.str() + ")")
	root = parseVar(w.str(nocase=True))
	root = parseEssive(root, words, False)
	while isinstance(w, Noun) and w.case == "omanto":
		w = nextWord(words)
		root = CallTree(parseVar(w.str(nocase=True)), [root], "", ("omanto",))
	if not isinstance(w, Noun):
		fatalError("Syntax error: expected noun, got " + w.str())
	if w.case != "nimento" and w.case != "omanto" and isNext(words, CONJUNCTIONS):
		words2 = words[:]
		conj = as2w(words[0]).str()
		del words[0]
		#if w.case == "omanto":
			# ... TODO
		#else:
		case, arg = parseUnary(words)
		if case == w.case:
			root = CallTree(parseVar(conj), [root, arg], "", ("", ""))
		else:
			del words[:]
			words += words2
	else:
		root = parseEssive(root, words, allowReverseWordOrder)
	return w.case, root

def parseEssive(root, words, allowReverseWordOrder, allowFullPattern=True):
	while len(words) != 0:
		w = as2w(words[0])
		if w.cl == "noun":
			owners = []
			if allowFullPattern:
				words2 = words[:]
				del words[0]
				while w.case == "omanto":
					owners += [w]
					w = nextWord(words)
			#print([o.str() for o in owners])
			if w.case == "olento":
				args = []
				argInfls = []
				if len(words) != 0:
					if as2w(words[0]).cl == "noun":
						words3 = words[:]
						case, arg = parseUnary(words, False)
						if case in ["nimento", "omanto", "olento"]:
							del words[:]
							words += words3
						else:
							args += [arg]
							argInfls += [case]
				root2 = applyOwners(parseVar(w.str(nocase=True)), owners)
				root = CallTree(root2, [root]+args, "olento", tuple([""]+argInfls))
			elif allowReverseWordOrder and w.case not in ["nimento", "omanto"]:
				case = w.case
				arg = applyOwners(parseVar(w.str(nocase=True)), owners)
				
				if isNext(words, CONJUNCTIONS):
					c = nextWord(words)
					owners, w = parseOwners(words)
					checkCase(w.case, case, w.str() + ", after " + arg.inflect(case) + " " + c.str()[1:])
					arg2 = applyOwners(parseVar(w.str(nocase=True)), owners)
					arg = CallTree(VarTree(c.str(nocase=True)), [arg, arg2], "", ("", ""))
				
				owners, w = parseOwners(words)
				checkCase(w.case, "olento", w.str() + ", after " + arg.inflect(case))
				root2 = applyOwners(parseVar(w.str(nocase=True)), owners)
				
				root = CallTree(root2, [root, arg], "olento", ("", case))
			elif allowFullPattern:
				del words[:]
				words += words2
				return root
		else:
			break
	return root

def parseOwners(words):
	owners = []
	w = nextWord(words)
	while w.case == "omanto":
		owners += [w]
		w = nextWord(words)
	return owners, w

def applyOwners(root, owners):
	for o in owners[::-1]:
		root = CallTree(root, [parseVar(o.str(nocase=True))], "", ("omanto",))
	return root

stack = []

def fatalError(msg):
	sys.stderr.write(msg + "\n")
	raise(StopEvaluation())

class StopEvaluation(Exception):
	pass

# Prints stack traces
def printStack():
	sys.stderr.write("Stack:\n")
	for val in stack:
		sys.stderr.write("  " + val.str() + "\n")
	if debug:
		sys.stderr.write("Defs:\n")
		for defi in DEFS:
			sys.stderr.write("  " + defi.str() + "\n")
	raise(StopEvaluation())

# Fully evaluates an expression
def evals(tree):
	a = evals_(tree)
	c = a.copy()
	while True:
		if visualize:
			print(a.inflect("nimento"))
		b = evals_(a)
		if c.safeEq(b):
			break
		a = b
		c = a.copy()
	if debug and verbosity >= 1:
		print("\x1b[1;4;31mEnd:\x1b[0m " + a.str())
	return a

# Evaluates an expression lazily (ie. evaluates the uppermost calls, but not arguments)
def evals_(tree, objects=[]):
	for obj in objects:
		if obj is tree:
			return tree
	objects = objects + [tree]
	global stack
	stack += [tree]
	try:
		if magic:
			for opt in OPTIMIZATIONS:
				if opt.match(tree):
					if debug and verbosity >= 1:
						print(" "*len(stack) + "\x1b[1;4;31mMatch:\x1b[0m " + tree.str() + " \x1b[1;33m(opt)\x1b[0m")
					return opt.optimize(tree)
			for bi in BUILTINS:
				if bi.match(tree):
					if debug and verbosity >= 1:
						print(" "*len(stack) + "\x1b[1;4;31mMatch:\x1b[0m " + tree.str() + " \x1b[1;33m(builtin)\x1b[0m")
					return bi.eval(tree)
		for defi in DEFS:
			ok, subs = defi.left.match(tree)
			if ok:
				for var, body in defi.where[::-1]:
					if var in subs:
						sys.stderr.write("Error: Illegal redefinition of " + var + "\n")
						raise(StopEvaluation())
					subs[var] = body.subs(subs)
				rightsubs = defi.right.subs(subs) if len(subs) > 0 or (defi.always and (impure or not freeMode)) else defi.right
				if debug and verbosity >= 1:
					print(" "*len(stack) + "\x1b[1;4;31mMatch:\x1b[0m " + tree.str() + " \x1b[1;4;34m==\x1b[0m " + defi.left.str() + " \x1b[1;4;34m->\x1b[0m " + rightsubs.str())
				return rightsubs
			elif debug and verbosity >= 2:
				print(" "*len(stack) + "\x1b[1;4;31mNO MATCH:\x1b[0m " + tree.str() + " \x1b[1;4;34m!=\x1b[0m " + defi.left.str() + " \x1b[1;33m(def)\x1b[0m")
		if isinstance(tree, CallTree):
			tree.head = evals_(tree.head, objects)
			tree.args = [evals_(arg, objects) for arg in tree.args]
		return tree
	except StopEvaluation as e:
		raise(e)
	except KeyboardInterrupt:
		traceback.print_exc(file=sys.stderr)
		sys.stderr.write(str(e) + "\n")
		printStack()
	except Exception as e:
		traceback.print_exc(file=sys.stderr)
		sys.stderr.write(str(e) + "\n")
		printStack()
	finally:
		del stack[-1]

DEFS = []
FUNCTIONS = set()

def evalFile(filename):
	with open(filename) as lines:
		try:
			while True:
				line = next(lines)
				if line == "\n":
					continue
				while line[-2] == "\\":
					line = line[:-2]
					line += next(lines)
				try:
					evalLine(line)
				except StopEvaluation:
					pass
		except StopIteration:
			pass

def evalLine(line, allowQueries=False):
	global DEFS
	output = lexLine(line)
	if not output:
		return
	if debug and verbosity >= 0:
		print(" ".join(["|".join(set([a.str() for a in alternatives])) for alternatives in output]))
	if not allowQueries:
		eqs = parseWhen(output)
	else:
		eqs = [parseEq(output, True)]
	for eq in eqs:
		if debug and verbosity >= 0:
			print(eq.str())
		if eq.query():
			return evals(eq.left)
		elif eq.op == "#olla":
			DEFS += [eq]
			if not freeMode:
				if isinstance(eq.left, CallTree):
					FUNCTIONS.add(eq.left.getHead())
				else:
					FUNCTIONS.add(eq.left)

def evalExpression(string):
	output = lexLine(string)
	eq = parseEq(output, True)
	if not eq.query():
		fatalError("Syntax error: expected expression, got declaration")
	return evals(eq.left)

# In the restricted mode, pattern matching against functions is forbidden.
# This function checks if there are any such forbidden patterns and
# reports the errors.
def checkFunctionMatching():
	a = True
	if not freeMode:
		for defi in DEFS:
			if isinstance(defi.left, CallTree):
				if defi.left.head.containsFunctions():
					functionMatchingError(defi.left)
					a = False
				for arg in defi.left.args:
					if arg.containsFunctions():
						functionMatchingError(defi.left)
						a = False
						break
	return a

def functionMatchingError(left):
	sys.stderr.write("Error: pattern matching against functions is forbidden in the restricted mode (" + left.inflect("nimento") + ")\n")

# This class represents an optimization of a operator handling numbers
# It allows together with NumTree efficient calculations even though
# the standard library implementation of integers is very unefficient.
class OptimizeOperator:
	def __init__(self, operator, opcase, argcases, ok, fun):
		self.operator = operator
		self.opcase = opcase
		self.argcases = argcases
		self.ok = ok
		self.fun = fun
	def match(self, tree):
		if isinstance(tree, CallTree) and tree.headIs(self.operator, self.opcase, self.argcases):
			if all([isinstance(arg, NumTree) for arg in tree.args]):
				return self.ok(*[arg.num for arg in tree.args])
	def optimize(self, tree):
		return NumTree(self.fun(*[arg.num for arg in tree.args]))

OPTIMIZATIONS = [
	OptimizeOperator("$seuraaja", "", ("omanto",), lambda x: True, lambda x: x + 1),
	OptimizeOperator("$plus", "", ("", ""), lambda x, y: True, lambda x, y: x + y),
	OptimizeOperator("$miinus", "", ("", ""), lambda x, y: x >= y, lambda x, y: x - y),
	OptimizeOperator("$kerrottu", "olento", ("", "ulkoolento"), lambda x, y: True, lambda x, y: x * y),
	OptimizeOperator("$jaettu", "olento", ("", "ulkoolento"), lambda x, y: y != 0, lambda x, y: x // y),
	OptimizeOperator("$modulo", "", ("", ""), lambda x, y: True, lambda x, y: x % y)
]

class Builtin:
	def __init__(self, operator, opcase, argcases, ok, fun):
		self.operator = operator
		self.opcase = opcase
		self.argcases = argcases
		self.ok = ok
		self.fun = fun
	def match(self, tree):
		if isinstance(tree, CallTree) and tree.headIs(self.operator, self.opcase, self.argcases):
			return self.ok(*tree.args)
	def eval(self, tree):
		return self.fun(*tree.args)

worldCounter = 0

def checkWorld(w):
	global worldCounter
	if w.counter != worldCounter:
		fatalError("Error: impossible time travel")
	worldCounter += 1
	return w.nextWorld()

def createPair(output, w):
	return CallTree(VarTree("$pari"), [output, checkWorld(w)], "olento", ("", "ulkotulento"))

def writeOutput(tree, w):
	print(evals(tree).inflect("nimento"))
	return createPair(VarTree("$tyhjyys"), w)

BUILTINS = [
	Builtin("$luettu", "olento", ("", "sisaeronto"),
		lambda l, w: isinstance(w, WorldTree),
		lambda l, w: createPair(evalExpression(input(l.inflect("nimento") + "> ")), w)
	),
	Builtin("$tulostettu", "olento", ("", "sisatulento"),
		lambda l, w: isinstance(w, WorldTree),
		writeOutput
	)
]

debug = False
visualize = False
verbosity = 0
magic = True
freeMode = False
impure = False

TAMPIO_VERSION = "1.8"
INTERPRETER_VERSION = "2.5.1"

VERSION_STRING = "Tampio %s Interpreter v%s" % (TAMPIO_VERSION, INTERPRETER_VERSION)

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
STD_LIB = os.path.join(SCRIPT_DIR, 'std.suomi')

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Interprets Tampio code.')
	parser.add_argument('filename', type=str, nargs='?', help='source code file')
	parser.add_argument('-v', '--version', help='show version number and exit', action='store_true')
	
	free = parser.add_mutually_exclusive_group()
	free.add_argument('-i', '--free-impure', help='enable impure free mode', action='store_true')
	free.add_argument('-p', '--free-pure', help='enable pure free mode', action='store_true')
	parser.add_argument('--io', help='evaluate "maailman tulos" instead of "tulos"', action='store_true')
	parser.add_argument('--no-magic', help='disable all optimizations and builtins', action='store_true')
	
	debugOptions = parser.add_argument_group('debug options')
	debugOptions.add_argument('--debug', help='enable debug mode', action='store_true')
	debugOptions.add_argument('-V', '--verbosity', help='verbosity level of debug information', action='count', default=0)
	debugOptions.add_argument('--visualize', help='enable inflected debug mode', action='store_true')
	args = parser.parse_args()
	
	if args.version:
		print(VERSION_STRING)
		sys.exit(0)
	
	freeMode = args.free_impure or args.free_pure
	impure = args.free_impure
	debug = args.debug
	magic = not args.no_magic
	verbosity = args.verbosity
	visualize = args.visualize
	
	evalFile(STD_LIB)
	
	if not checkFunctionMatching():
		sys.exit(1)
	
	if args.filename:
		evalFile(args.filename)
		if args.io:
			print(evals(CallTree(VarTree("$tulos"), [WorldTree(worldCounter)], "", ("omanto",))).inflect("nimento"))
		else:
			print(evals(parseVar("$tulos")).inflect("nimento"))
	else:
		
		histfile = os.path.join(os.path.expanduser("~"), ".tampio_history")
		try:
			readline.read_history_file(histfile)
			readline.set_history_length(1000)
		except FileNotFoundError:
			pass
		atexit.register(readline.write_history_file, histfile)
		
		print(VERSION_STRING + """
Copyright (C) 2017 Iikka Hauhio
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Read the LICENSE file for details.""")
		while True:
			try:
				line = input(">>> ")
			except KeyboardInterrupt:
				pass
			except EOFError:
				print()
				break
			try:
				out = evalLine(line, True)
				if out:
					print(out.inflect("nimento"))
				else:
					checkFunctionMatching()
			except StopEvaluation:
				continue
