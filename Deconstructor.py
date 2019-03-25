"""
Uses the Parser to get the AST of the sentences,
but then boils down the sentence into the direct object,
indirect object, ect.
This makes it so it should be exceedinly easy to write code
that looks at the statements and executes them.
Author: Alastar Slater
Date: 3/6/19
"""
#Import parser and all of the import dictionaries
from Parser import Parser, NOUNS, VERBS, ADJECTIVES, ADVERBS, CONJUNCS, vocab

#The opposite definitions of verbs
VERB_INVERSES = vocab['verb inverses']

class Deconstructor:
    def __init__(self, text=""):
        #Get the full abstract syntax tree
        self.parser = Parser(text)
        self.ast = self.parser.parse_all() #Try to parse sentence
        self.error = self.parser.error #get error state

    def err_visit(self, node):
        print("Visit {} method not implemented!!".format(type(node).__name__))
        raise SystemExit

    #Visits that specific node
    def visit(self, node):
        func_name = 'visit_' + type(node).__name__
        visitor = getattr(self, func_name, self.err_visit)
        return visitor(node)

    def visit_Conjunction(self, phrase): 
        if phrase.conjunc.lower() == "al": #'Combine' both terms in an and
            ret = [] #Return a list of all of the conjoined values

            left = self.visit(phrase.left) #Get the left part of the conjunction
            right = self.visit(phrase.right) #Get right part of the conjunction

            ret.append(left) #Add the left portion

            #Add all the elements from the right portion
            if type(right).__name__ == "list":
                ret.extend(right)

            else: #Otherwise add right portion
                ret.append(right)
            
            return ('and', ret)

    #'Unpacks' a full on sentence so it can be used
    def visit_Sentence(self, phrase):
        #Discard the subject, keep the verb, direct object,
        #indirect object, any quote or any sub sentence
        dir_obj = '<NIL>' if phrase.dir_object == None else self.visit(phrase.dir_object)
        indir_obj = '<NIL>' if phrase.indir_object == None else self.visit(phrase.indir_object)
        quote = '<NIL>' if phrase.quote == None else self.visit(phrase.quote)
        verb = ('<NIL>', '<NIL>') if phrase.verb_phrase == None else self.visit(phrase.verb_phrase)

        #Return the 'unpacked' version of the statement
        ret = (verb, {'obj': dir_obj, 'quote': quote, 'indir obj': indir_obj})

        return ret
    
    def visit_VerbPhrase(self, phrase): #Gets info from this phrase
        return self.visit(phrase.verb)

    def visit_Verb(self, phrase): #Gets needed info from verb
        verb = VERBS[phrase.verb] #Get the action

        if phrase.neg == True: #Negate the verb
            verb = VERB_INVERSES[verb] #Get negated verb

        statement_type = phrase.type #Type of statement that this is

        return (verb, statement_type) #Good enough info

    #Give back the noun, and the atrributes / adjectives and owner
    def visit_NounPhrase(self, phrase):
        noun = self.visit(phrase.noun) #The noun itself
        adjectives = [self.visit(x) for x in phrase.adjectives] #Get adjectives

        #Return the noun, the attributes, and the name of who owns it
        return (noun, adjectives)

    #Return the noun itself
    def visit_Noun(self, phrase):
        word = NOUNS[phrase.noun] #get english word
        poss = None if phrase.poss == None else ( #possession (who owns this)
            {'gi':'your', 'ge':'my', 'go':'our', 'ga':'their',
             'goa':'his', 'goe':'hers'}.get(phrase.poss.lower())
        )

        #Add plural marker onto the noun
        if phrase.plural != None and phrase.plural.lower() == "ni":
            word += 's'

        #Return the noun and the pronoun for whomever owns it
        return (word, poss)

    #Simply gives back the adjective
    def visit_Adjective(self, phrase):
        adjective = ADJECTIVES[phrase.word] #Get the adjective used

        if phrase.intensifier > 0: #Positive intensifier
            adjective = "very " + adjective

        elif phrase.intensifier < 0: #Negative intensifier
            adjective = "not so " + adjective

        return adjective

    #Returns the quote
    def visit_Quote(self, phrase):
        #Get all of the sentences needed
        sentences = [self.visit(sentence)
                     for sentence in phrase.sentences]

        return ('quote', sentences)

    def deconstruct(self):
        #If we have and error tell the user
        if self.error == True:
            return []

        #Return the list of statements to execute
        return [self.visit(x) for x in self.ast] 

