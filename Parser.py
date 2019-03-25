"""
This is a parser for the conlang Mouthful, which is made by
Alastar Slater. This will attempt to translate Mouthful sentences
into english sentences for use. 
Date: 3/1/19
Author: Alastar Slater
"""
from functools import reduce
from vocabParser import read_vocab #So we can read from vocab list ot get most vocab

WORD         = "WORD" #A random word in the language
NOUN         = "NOUN" #A noun in the language
ADJECTIVE    = "ADJECTIVE" #An adjective in this language
VERB         = "VERB" #A verb in this language
ADVERB       = "ADVERB" #An adverb in this language
CONJUNC      = "CONJUNC" #A conjunction in the language
INTERJECT    = "INTERJECT" #An interjection in the language
PHRASE       = "PHRASE" #A subsentence (or start of one)
QUOTE        = "QUOTE" #Start of a quotation
EOF          = "EOF" #End of file token

########################
#      DICTIONARY      #
########################

#Gets word list from dictionary file
def get_dict(name):
    words = {} #The list of words

    with open(name, 'r') as f:
        for line in (x.strip() for x in f.readlines() if x.strip() != ""):
            if line[0] != "#": #Isn't a comment
                word, defn = line.split(":") #Get the word and english definition
                words[word.strip()] = defn.strip()

    return words
            
vocab = read_vocab('vocab.txt') #Get the vocabulary
#List of conjunctions in the language
PHRASES = ["a"] #Notes start of a sub sentence
QUOTES = ["xae"] #Notes start of quotation
CONJUNCS = vocab['conjuncs']
NOUNS = vocab['nouns'] #Get the nouns
ADJECTIVES = vocab['adjectives'] #Get all the adjectives
VERBS = vocab['verbs'] #Get all of the verbs
ADVERBS = vocab['adverbs'] #Get all of the non-adjective derived adverbs
INTERJECTS = vocab['interjects'] #Get all of the interjections
#All of the alphabet, consonants and vowels
ALPHABET = vocab['alphabet']
CONSONANTS = vocab['consonants']
VOWELS = vocab['vowels']

###################
#      TOKEN      #
###################

class Token:
    def __init__(self, tok_type, value, line=0, column=0):
        self.type = tok_type #type of this particular token
        self.value = value #Token itself
        self.line = line #Line number position of this word
        self.column = column #Column position of this word

    def __str__(self):
        if self.column == self.line == 0: #If no positional information
            return f"Token({self.type}, {repr(self.value)})"

        #Otherwise give all of the information needed
        return f"Token({self.type}, {repr(self.value)}, L: {self.line}, C: {self.column})"

    def __repr__(self): return self.__str__()


###################
#      LEXER      #
###################

class Lexer:
    def __init__(self, sentence):
        self.text = sentence.lower()
        self.pos = 0 #position in the string
        #First character in the string
        self.current_char = None if sentence.strip() == "" else self.text[0]

        self.line = 1 #Starting line number
        self.column = 1 #Starting column number

        self.error = False #If an error occured

    #Raises an error
    def unrecognized_char(self, char, line, column):
        self.error = True
        self.advance()

    #Moves onto the next character
    def advance(self):
        self.pos += 1 #Move to next character

        if self.pos < len(self.text): #Update current character, line pos + column pos
            self.current_char = self.text[self.pos] #Get next character

            if self.current_char == '\n': #If new line, update column + line
                self.line += 1
                self.column = 1

            else: #Otherwise, just update the column
                self.column += 1

        else: #End of input
            self.current_char = None

    def skip_whitespace(self):
        #Skip over all of the whitespace characters
        while self.current_char != None and self.current_char.isspace():
            self.advance()

    def get_word(self): #Gets a single word from the input
        word = "" #The word to be collected

        #Collect all of the letters of the word
        while self.current_char != None and self.current_char in ALPHABET:
            word += self.current_char
            self.advance()

        return word

    def get_next_token(self):
        while self.current_char != None:
            #Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()

            #if this is a word
            elif self.current_char in ALPHABET:
                line, column = self.line, self.column 
                #Return the word token
                return Token(WORD, self.get_word(), line, column)

            else: #Not a recognized character
                self.unrecognized_char(self.current_char, self.line, self.column)

        #Return the EOF token (end of the input)
        return Token(EOF, EOF, self.line, self.column)

    def get_tokens(self):
        tokens = []

        tok = self.get_next_token()

        #Collect all the tokens besides an eof token
        while tok.type != EOF:
            tokens.append(tok)
            tok = self.get_next_token()

        #Return the list of tokens with an eof token at end
        return tokens + [self.get_next_token()]

#############################
#      WORD CLASSIFIER      #
#############################

#Uses closures to change a tokens value
def change_type(token):
    def __changer(tok_type):
        return Token(tok_type, token.value, token.line, token.column) 

    return __changer

#Returns true if any word in the dictionary is equal to or in this word
def word_isin(target, dictionary):
    return reduce(lambda a, b: a or b,
           (word in target
            for word in dictionary)
        )

#Returns true if any word in the dictionary exactly matches this word
def word_exact(target, dictionary):
    return reduce(lambda a, b: a or b,
           (word == target
            for word in dictionary)
    )

#Does inexact classification of words, given the word type as a string
#(and assuming it has a list of those words under <type>s, such as VERB -> VERBS)
def inexact_class(word_type, words):
    return (
        change_type(tok)(eval(word_type))
        if word_isin(tok.value, eval(word_type + 'S')) and tok.type == WORD
        else tok

        for tok in words
    )

#Allows for classification of a list of inexact word classifications
def inexact_classify(word_types, words):
    for word_type in word_types:
        words = inexact_class(word_type, words)

    return words #Return new set of words that have been classified w/ given types

#Classifies word types that don't have affixes
def exact_classify(word_types, words):
    for word_type in word_types:
        #Try to use every exact classification to classify these words
        words = (change_type(tok)(word_type)
                 if tok.value in eval(word_type + 'S')
                 else tok
                 for tok in words)

    return words #Return the words.

#Classifies a word as an adverb
def classify_adverbs(target): 
    for word in target:
        if word_isin(word.value, ADVERBS)or word_isin(word.value, ['sot']) and word_isin(word.value, ADJECTIVES):
            yield change_type(word)(ADVERB)

        else:
            yield word

#Classifies all the words in the sentence
def classify(sentence):
    lexer = Lexer(sentence) #Our lexer this time
    toks = lexer.get_tokens() #Gets tokens
    #toks = classify_conjuncs(toks)
    #toks = classify_adverbs(toks) #Classify adverbs first
    #Classify words without affixes
    toks = exact_classify(['INTERJECT', 'QUOTE'], toks)
    #Classify words that use affixes
    toks = inexact_classify(['NOUN', 'ADJECTIVE', 'VERB'], toks)

    #Make sure the grammar words are included
    toks = (change_type(tok)('PHRASE')
            if tok.value in PHRASES
            else tok
            for tok in toks)

    #because aparrently lists IN wordssss differently 
    toks = (change_type(tok)('CONJUNC')
            if tok.value in CONJUNCS
            else tok
            for tok in toks)

    #Infinitely return tokens
    def token_generator(lst):
        #Give back every other token
        for tok in lst:
            yield tok

        while True: #Infinitely give back the EOF token
            yield Token(EOF, EOF) 

    #print("TOKS : ", list(toks))

    return (x for x in toks), lexer.error
        
####################
#      PARSER      #
####################

#A full sentence in this language
class Sentence(object):
    def __init__(self):
        self.subject = None
        self.dir_object = None
        self.indir_object = None 
        self.quote = None #The potential quotation
        self.verb_phrase = None

#Connects two phrases by a conjunction
class Conjunction(object):
    def __init__(self, left_phrase, conjunc, right_phrase):
        self.left = left_phrase #Phrase left of conjunction
        self.conjunc = conjunc #Conjunction being used
        self.right = right_phrase #Phrase right of conjunction

    #Return type of conjoined brother
    def inner_type(self):
        if type(self.left).__name__ in ['NounPhrase', 'VerbPhrase']:
            return (('Noun' if type(self.left).__name__ == "NounPhrase" else 'Verb'),
                    (self.left.noun if type(self.left).__name__ == "NounPhrase" else self.left.verb))

        #If another conjunction, return their inner type
        elif type(self.left).__name__ == 'Conjunction':
            return self.left.inner_type()

        else:
            return type(self.left).__name__

#A noun phrase (Noun, possessor, adjectives)
class NounPhrase(object):
    def __init__(self):
        self.noun = None
        self.possessor = None
        self.adjectives = [] #List of adjectives
        self.split = False #If this noun phrase uses a conjunction

#A single noun (uses affixes for information)
class Noun(object):
    def __init__(self, token):
        self.token = token #Token this is built from
        self.noun = None #Word (root) itself
        self.prep = None #Prepositional affix
        self.poss = None #Possession pronoun
        self.plural = None #Plurality/number affix
        self.use = 'subject' #If it is subject / dir obj / indir obj

class Adjective(object):
    def __init__(self, token):
        self.token = token #The token this is from
        self.word = None  #The word this is based on
        self.intensifier = 0  #1 = INTENSE, -1 = DIMINISH, 0 = NONE
        self.neg = False  #If the adjective is negated or not

#Makes an entire verb phrase
class VerbPhrase(object):
    def __init__(self):
        self.verb = None #The verb being used
        self.adverbs = [] #List of adverbs

#A single verb (uses affixes for information)
class Verb(object):
    def __init__(self, token):
        self.token = token #Token this is built from
        self.verb = None #Word (root) being done (action)
        self.able = False #Able to do that action
        self.infin = False #If this is being used in the infinitive form
        self.neg = False #If this verb is being logically negated (give -> take)
        self.type = 'statement' #If it is a statement, question, or command
        self.intense = False #If verb is intensified
        self.tense = 'present' #If this is the present / past / future tense

#A quote- some text either said or written. 
class Quote(object):
    def __init__(self, token):
        self.token = token #Token this is built from
        self.sentences = [] 

#A single adverb
class Adverb(object):
    def __init__(self, token):
        self.token = token
        self.word = None
        self.neg = False #If the word is negated
        self.from_adjective = False #If this is derived from an adjective
        self.adjective = None #Adjective this is made from

class NoOp(object):
    pass

class Parser:
    def __init__(self, sentence):
        #The list of tokens to use, and current error state
        self.tokens, self.error = classify(sentence)
        self.current_token = next(self.tokens) #Get first token
        self.line = self.current_token.line #get line number
        self.column = self.current_token.column #Get column number

    #Raises an error
    def raise_error(self, err=""):
        self.error = True
        return NoOp()

    def eat(self, tok_type, err='default'):
        #If the types match, consume current token and get next one
        if self.current_token.type == tok_type:
            #Get the next token
            self.current_token = next(self.tokens)
            self.line = self.current_token.line #Get new line number and column number
            self.column = self.current_token.column

            if self.current_token.type == WORD: #Unclassified word, stop prematurely
                self.raise_error()

        else: #Raise an error
            self.raise_error()
            #if err == 'default': #Default error
            #    self.raise_error( #Tells the user we didn't expect this type of word
            #        "Sorry, we didn't expect a {} at this time..".format(self.current_token.type)
            #    )

            #else: #Raises the error given explicitly
            #    self.raise_error(err)

    #Returns true if this word starts with this string
    def starts_with(self, word, start):
        return word[:len(start)] == start

    #Returns true if thsi word ends with this string
    def ends_with(self, word, end):
        return word[len(word) - len(end):] == end 

    #Returns the english meaning of the word
    def meaning(self, word, word_type):
        return word_type[word]

    #Checks that there is isn't more than one affix type
    def check_affixes(self, max_num, affixes, word, token, err='default'):
        #Number of times an affix appeared
        times = {n: 0 for n in range(max_num + 1)}

        for affix in affixes:
            times[affix[1]] += 1 #incriment this type


            if times[affix[1]] > 1: #If there is more than one of this type, raise error
                self.raise_error()
                #if err == 'default': #Default error
                #    print("There is a grammatical error in terms of the word '{}'".format(word))
                #    print("You've used multiple affixes relating to one thing all on this word.")
                #    print("(Example, using more than one possession affix on a noun.)")
                #    print("Look at the word on Line {}, Column {}".format(token.line, token.column))
                #    raise SystemExit

                #else: #use custom error message
                #    print("Relating to the word '{}' ..".format(word))
                #    print(err)
                #    print("Look at the word on Line {}, Column {}".format(token.line, token.column))
                #    raise SystemExit

    def prefix_removal(self, word, affixes): #collects and removes all affixes on the front
        affix_list = [] #list of all collected affixes
        i = 0
        while i < len(affixes):
            affix = affixes[i]
            #Try taking off the prefix and potential result
            #prefix, result = remove_front(word)

            prefix = word[: len(affix)] #The potential prefix
            result = word[len(affix):] #potential result

            #Save the removed affix
            if prefix == affix[0].lower():
                affix_list.append(affix)
                word = result
                continue #Make sure there isn't a copy

            else:  #Move to next affix
                i += 1

        #Return list of affixes and the word
        return affix_list, word

    def suffix_removal(self, word, affixes): #Collects and removes all suffixes 
        affixes = affixes[::-1] #Reverse list

        affix_list = [] #List of affixes that where there
        i = 0
        while i < len(affixes):
            affix = affixes[i] #Current affix
            result = word[0: len(word) - len(affix)] #Get potential result
            real_affix = word[len(result):] #get the potential affix

            if affix[0].lower() == real_affix: #If they match, add it
                affix_list.append(affix)
                word = result #update the result
                continue #Make sure there isn't a copy

            else: #Otherwise, go to the next affix
                i += 1

        return affix_list, word 

    #Collects and removes the prefixes and suffixes, returns resulting word + affix list
    def affix_removal(self, prefixes, word, suffixes):
        #Remove all of the prefixes from the word
        affix_list, word = self.prefix_removal(word, prefixes)
        #Remove all the suffixes from the word
        affix_list2, word = self.suffix_removal(word, suffixes)

        #Return the root word and the list of affixes
        return word, affix_list + affix_list2

    def parse_all(self): #Parses EVERYTHING and sticks it into a paragraph (list)
        """
        text: sentence+
        """
        paragraph = []

        #Not end of file? Keep parsing..
        while self.current_token.type != EOF and self.error == False:
            paragraph.append(self.sentence()) #Add sentence

        return paragraph

    def sentence(self): #An entire sentence 
        """
        sentence: (np_sub)* (quote) verb_phrase (conjunc sentence)
        """
        node = Sentence()

        noun_phrase_num = 3 #Can only be three noun phrases MAX

        #While we have either a noun or sub sentence, add it
        while self.current_token.type in [NOUN, PHRASE]:
            if noun_phrase_num == 0: #Raise an error if there were to many
                self.raise_error("This sentence has wayy to many noun phrases/sub sentences.\nCouln't break down sentence.")

            part = self.np_sub()
            part_type = type(part).__name__ #name of this part of the sentence

            #If we have something that is the subject of the sentence
            if part_type == "NounPhrase" and part.noun.use == 'subject' or\
               part_type == 'Conjunction' and part.inner_type()[0] == "Noun" and part.inner_type()[1].use == 'subject':
                node.subject = part

            #If something is the direct object of the sentence
            elif part_type == "NounPhrase" and part.noun.use == 'dir obj' or part_type == "Sentence" or\
                 part_type=='Conjunction' and part.inner_type()[0] == 'Noun' and part.inner_type()[1].use == 'dir obj':
                node.dir_object = part

            #If something is the indirect object of the sentence
            elif part_type == "NounPhrase" and part.noun.use == 'indir obj' or part_type == 'Conjunction' or\
                 part.inner_type()[0] == "Noun" and part.inner_type()[1].use == "indir obj":
                node.indir_object = part

            noun_phrase_num -= 1 #Decrease number of noun phrases

        #If we have a quotation up next
        if self.current_token.type == QUOTE:
            node.quote = self.quote()

        #If there is a verb, get it
        if self.current_token.type == VERB:
            #Add the verb phrase of this sentence
            node.verb_phrase = self.verb_phrase()

        if self.current_token.type == CONJUNC: #Another sentence to add
            conjunc_type = self.current_token.value #Save the word itself
            self.eat(CONJUNC) #remove the conjunction

            #Return the conjunction
            return Conjunction(node, conjunc_type, self.sentence)

        return node #return the sentence we had before otherwise

    def quote(self): #A quotation- some dialogue to be used in a sentence
        """
        quote: xau (sentence)+ VERB
        """
        node = Quote(self.current_token) #The token we'll be returning
        #Remove the start of the quote
        self.eat(QUOTE, "Couldn't break up sentence at this point, expected the word 'xau' for the start of a quotation.")

        sentences = [] #The full dialogue
        while self.current_token.type != EOF: #Keep collecting sentences while possible
            #Stop if we have something that would indicate that we are at the end
            if self.current_token.type == VERB and self.meaning(self.current_token.value, VERBS) in ['write', 'say']:
                break

            sentences.append(self.sentence())

        node.sentences = sentences #Save the sentences

        return node

    def verb_phrase(self): #Parses a verb phrase
        """
        verb_phrase: verb adverbs*
        """
        node = VerbPhrase() #The verb phrase we'll end up returning

        node.verb = self.verb() #Get the verb of this phrase

        adverbs = [] #All of the adverbs modifying this verb
        #While we have adverbs, collect them
        while self.current_token.type == ADVERB:
            adverbs.append(self.adverb()) 

        node.adverbs = adverbs

        return node #Return this verb phrase

    def verb(self): #a single verb
        """
        verb: (XI-) (KO-) (LO-) VERB (-BI) (-BO | -BE)  (-LA | -LE)  
        
        Affix key:
        0 -> Able to do the action
        1 -> Infinitive affix
        2 -> logical negation (give -> take)
        3 -> Intensifier 
        4 -> Command / Question affixes
        5 -> Future / Past tense
        """
        node = Verb(self.current_token) #Make the node we'll return
        #Remove the verb
        self.eat(VERB, "Couldn't break down sentence, expected a verb at this time.")

        #Get the root word and the list of affixes
        word, affixes = self.affix_removal(
            [("XI", 0), ("KO", 1), ("LO", 2)], #Prefixes
            node.token.value,
            [("BI", 3), ("BO", 4), ("BE", 4), ("LA", 5), ("LE", 5)] #suffixes
            )

        node.verb = word #Save the root verb

        #Checks the affixes for any errors
        self.check_affixes(5, affixes, word, node.token, "You've used multiple affixes that relate to the same thing (for example, using both \nfuture and past tense affixes). Please revise this verb so that translation can continue.")

        for affix in affixes: #Go through each affix and save info.
            if affix[1] == 5: #Past / Future marker
                node.tense = 'future' if affix[0] == "LA" else 'past' 

            elif affix[1] == 4: #Question / command
                node.type = 'question' if affix[0] == "BO" else 'command'

            elif affix[1] == 3: #Intensifier
                node.intense = True

            elif affix[1] == 2: #Logically negates the meaning
                node.neg = True

            elif affix[1] == 1: #Infinitive
                node.infin = True

            elif affix[1] == 0: #Able to do
                node.able = True

        return node

    def adverb(self): #A single adverb
        """
        adverb: (LO-) ADVERB | (LO-) SOT- ADJECTIVE
        """
        node = Adverb(self.current_token) #The node we'll return
        self.eat(ADVERB, "Couldn't break down sentence correctly, expected an Adverb at this time.\nPlease fix the error so translation can continue.")

        #Get the step word and affix list
        word, affixes = self.affix_removal(
            [("LO", 0)],
            node.token.value,
            []
        )

        #Check for affix repeats
        self.check_affixes(1, affixes, word, node.token, "You've used more than one 'LO' prefix most likey, please reduce \nthe number to just one, so that translation can be successful.")

        if len(affixes) > 0: #Note that we have negation being used
            node.neg = True

        if self.starts_with(word, 'sot') == True: #if we have an adjective derived adverb
            node.from_adjective = True #Note that we have derived meaning from adjectives

            if node.neg == True: #If we had used a negation prefix, raise an error
                print("Refering to the word '{}' ..".format(node.token.value))
                print("This is an adjective-derived adverb, because of this, you shouldn't use the negation affix")
                print("'lo-' on the adverb form, since the needed meaning can be gained from the adjective.")
                print("Look at the word on Line {}, Column {}".format(node.token.line, node.token.column))
                raise SystemExit

            stem_word = word #The stem
            sot_num = 0
            while self.starts_with(stem_word, 'sot'):
                stem_word = stem_word[len('sot'): ]
                sot_num += 1

            if sot_num > 1: #Raise an error
                print("In reference to '{}' ..".format(word))
                print("You used the prefix 'sot-' more than one time in your adjective-derived adverb.")
                print("Please just have only one use of the 'sot-' prefix on your adjective.")
                print("Look at the adjective on line {}, column {}".format(node.token.line, node.token.column))
                raise SystemExit

            #Raw token for this adjective to parse
            raw_tok = Token(ADJECTIVE, stem_word, node.token.line, node.token.column)

            small_parser = Parser("")
            small_parser.current_token = raw_tok #Setup this adjective for parsing

            #Parse the adjective and save the resulting node
            node.adjective = small_parser.adjective()

            return node #Return the node now

        return node #Return raw adverb

    def np_sub(self): #Either a noun_phrase or sub sentence
        """
        np_sub: noun_phrase | 'a' sentence
        """
        
        if self.current_token.type == PHRASE: #Sub sentence, then return a full sentence
            self.eat(PHRASE) #Remove phrase token
            return self.sentence() #Return the parsed sentence

        elif self.current_token.type == NOUN: #This is a noun, parse it
            return self.noun_phrase()

    def noun_phrase(self): #A single noun phrase
        """
        noun_phrase: noun (noun) adjective* (conjunc noun_phrase)
        """
        node = NounPhrase() #The noun phrase we'll return

        node.noun = self.noun() #Get the noun that is the core of this phrase

        #if self.current_token.type == NOUN: #Possessor noun
        #    node.possesor = self.noun()

        #print("POSSESSOR :", node.possessor)

        adjectives = [] #get all of the adjectives

        #Add all of the adjectives that we have for this noun
        while self.current_token.type == ADJECTIVE:
            adjectives.append(self.adjective()) 

        #Save all of the adjectives for this noun
        node.adjectives = adjectives
        
        #A connected noun phrase, connect it
        if self.current_token.type == "CONJUNC":
            conjunc_type = self.current_token.value #Save word
            self.eat(CONJUNC) #Remove conjunction

            #Return the compound noun_phrase
            ret = Conjunction(node, conjunc_type, self.noun_phrase())
            ret.split = True #Note that there is a conjunction in this

            return ret

        return node #return the original noun phrase 

    def adjective(self):
        """
        adjective: (LO-) (BI- | BA-) ADJECTIVE
        
        AFFIX KEY:
        0 -> Negation affix
        1 -> Intensifier / Diminisher affixes
        """
        node = Adjective(self.current_token) #The node we'll return
        #Remove the adjective
        self.eat(ADJECTIVE, "Couldn't break down sentence correctly, expected an Adjective at this time.")

        #Get the base word and affixes being used
        word, affixes = self.affix_removal(
            [("LO", 0), ("BI", 1), ("BA", 1)],
            node.token.value,
            []
        )

        node.word = word #Save the base word

        self.check_affixes(1, affixes, word, node.token, "You used more than one adjective affixes. So you if you have like both 'bi-' and 'ba-',\njust remove one of them, or if you have more than one 'lo-', just have one of them.")

        #Go through every affix to get all of the info.
        for affix in affixes:
            if affix[1] == 0: node.neg = True #Mark that the adjective is negated

            elif affix[0] == "BI": #Note that we have a positive intensifier
                node.intensifier = 1 

            elif affix[0] == "BA": #note that we have a negative intensifier (diminsher)
                node.intensifier = -1

        return node #return the node

    def noun(self): #A single noun
        """
        noun: (PREP.) NOUN (DET.) (POSSES.) (NOUN-MARKER)
        
        AFFIX KEY:
        0 -> Prepositional affix
        1 -> Determiner / Number affix
        2 -> Possession affix
        3 -> Noun marker / role
        """
        node = Noun(self.current_token) #The noun node we're working on
        #Remove the noun
        self.eat(NOUN, "Couldn't break down sentence correctly, expected a noun at this point in the sentence.")

        #Get the root word and the list of affixes
        word, affixes = self.affix_removal(
            #All of the prefixes for this noun
            [("RE",0),("RA",0),("RI",0),("RO",0),("TI",0),("TA",0)], 

            node.token.value,

            #All of the suffixes for the noun
            [("NI",1), ("NO",1), ("GA", 2), ("GI", 2), ("GO", 2),
             ("GE",2), ("GOA",2), ("GOE",2), ("KA",3), ("KE",3) ]
            )

        #Checks that multiple affixes of the same type weren't used
        self.check_affixes(3, affixes, word, node.token, "You've used multiple affixes relating to nouns (such as prepositional affixes, possession affixes, \nor role markers). Please fix your mistake and try again so translation can comtinue.")

        node.noun = word #Save what the 'root' word is

        #Now go through every affix so we can record the relevant information
        for affix in affixes: 
            if affix[1] == 0: #If we have a prepositional affix, save it
                node.prep = affix[0] #Save the preposition itself

            elif affix[1] == 1: #If we have a word for gram. number
                node.plural = affix[0]

            elif affix[1] == 2: #If we have a word for possession
                node.poss = affix[0]

            elif affix[1] == 3: #If we have a word for placement
                #Mark if the noun is the direct or indirect object
                node.use = 'dir obj' if affix[0] == "KA" else 'indir obj'

        return node #finally return the node

    def parse(self): return self.sentence() #Parses the sentence

