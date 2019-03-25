"""
Parser for a minilang for making single files full of 
information relating to vocabulary of this game engine
for text based adventure games.
Author: Alastar Slater
Date: 3/10/19
"""
EOF    = "EOF" #End of file tag
WORD   = "WORD" #A word in this language
START   = "START" #Info tag for what information is given
COLON  = "COLON" #the character ':' for seperating word and translated word
SEMI   = "SEMI" #A semicolon for ending variable declarations
SET    = "SET" #Set command for declaring variables
EQUAL  = "EQUAL" #Equals sign for variable declarations
COMMA  = "COMMA" #the comma character for seperating multiple values
END    = "END" #end tag for the end of a type of information
STRING = "STRING" #String, used for names of types of information fields

#All of the commands for this language
COMMANDS = ["START", "END", "SET"]

class Token:
    def __init__(self, tok_type, value, line=0, column=0):
        self.type = tok_type
        self.value = value
        self.line = line
        self.column = column

    def __str__(self):
        #If no line, column information
        if self.line == self.column == 0:
            return f"Token({self.type}, {repr(self.value)})"

        #Give full set of information otherwise
        return f"Token({self.type}, {repr(self.value)}, L: {self.line}, C: {self.column})"

    def __repr__(self):
        return self.__str__()


class Lexer:
    def __init__(self, program):
        self.text = program
        self.pos = 0
        #Get the first character to look at
        self.current_char = None if self.pos == len(self.text) else self.text[self.pos]
        self.line = 1 #Start line and column positions
        self.column = 1

    def unrecognized_char(self, char):
        print("Unrecognized char: {}".format(char))
        print("Refer to line: {}, Column: {}".format(self.line, self.column))
        raise SystemExit

    def advance(self):
        self.pos += 1

        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]

            if self.current_char == '\n':
                self.line += 1
                self.column = 0

            else:
                self.column += 1

        else:
            self.current_char = None

    #Completely skip over whitespace
    def skip_whitespace(self):
        while self.current_char != None and self.current_char.isspace():
            self.advance()

    #Skips over a comment
    def remove_comment(self):
        while self.current_char != None and self.current_char != '\n':
            self.advance()
        self.advance()

    #Gets a string
    def get_string(self):
        if self.current_char == '"': #if start of string 
            self.advance()

        string = "" #The string being used

        while self.current_char != None and self.current_char != '"':
            string += self.current_char
            self.advance()

        if self.current_char == '"':
            self.advance()

        return string #Return the string

    def get_word(self):
        word = "" #To be returned word

        #Collect all of the characters that are in the alphabet
        while self.current_char != None and self.current_char.lower() in "abdegijklmnoprstx!":
            word += self.current_char
            self.advance()

        return word #return the word

    def get_next_token(self):
        while self.current_char != None:
            #Skip over all whitespace
            if self.current_char.isspace():
                self.skip_whitespace()

            elif self.current_char == '#': #Comment
                self.remove_comment()

            elif self.current_char == ':': #If the char is a colon
                tok = Token(COLON, COLON, self.line, self.column)
                self.advance()
                return tok

            elif self.current_char == '"': #Start of string
                line, column = self.line, self.column
                return Token(STRING, self.get_string(), line, column)

            elif self.current_char == ',': #if comma
                tok = Token(COMMA, COMMA, self.line, self.column)
                self.advance()
                return tok

            elif self.current_char == ';': #If semicolon
                tok = Token(SEMI, SEMI, self.line, self.column)
                self.advance()
                return tok

            elif self.current_char == '=': #If equals sign
                tok = Token(EQUAL, EQUAL, self.line, self.column)
                self.advance()
                return tok

            elif self.current_char.lower() in "abdegijklmnoprstx": #if word / command
                line, column = self.line, self.column
                word = self.get_word()

                #If a command (meaning, in FULL CAPS), return it as a command
                if word in COMMANDS:
                    return Token(word, word, line, column)

                #Otherwise, return it as a word
                return Token(WORD, word, line, column)

            #Uncrecognized character
            else:
                self.unrecognized_char(self.current_char)

        return Token(EOF, EOF, self.line, self.column) 
            
    def get_tokens(self):
        toks = []

        tok = self.get_next_token()

        while tok.type != EOF:
            toks.append(tok)
            tok = self.get_next_token()

        #Returns full list of tokens
        return toks + [self.get_next_token()]


class Parser: #Parses it into a dictionary
    def __init__(self, program):
        self.lexer = Lexer(program) #tokenize program
        self.current_token = self.lexer.get_next_token() #Get token
        self.line = self.current_token.line
        self.column = self.current_token.column

    def eat(self, tok_type, err='default'):
        #Get next token if types match
        if tok_type == self.current_token.type:
            self.current_token = self.lexer.get_next_token()
            self.line = self.current_token.line
            self.column = self.current_token.column

        else: #Otherwise, raise an error
            if err=='default':
                print("An error occured, expected token of type: {}".format(tok_type))
                print("Instead, got type: {}".format(self.current_token.type))
                print("Refer to Line: {}, Column: {}".format(self.line, self.column))
                raise SystemExit

            else:
                print(err)
                print("Refer to Line: {}, Column: {}".format(self.line, self.column))
                raise SystemExit

    def program(self):
        """
        program: statement_list
        statement_list: statement+
        """
        ret = {} #Return dictionary

        #Combine result with result of the statement
        while self.current_token.type != EOF:
            ret = {**ret, **self.statement()}

        return ret #return the program

    def statement(self):
        """
        statement: variable_declr
                 | info_field
        """
        tok_type = self.current_token.type #Type of current token

        if tok_type == SET: #Variable declaration
            return self.variable_declaration()

        elif tok_type == START: #information field
            return self.info_field()

        else: #Raise an error
            print("Syntax Error: UNKNOWN STATMENT")
            print("Expected a VARIABLE DECLARATION or INFORMATION FIELD at this time.")
            print("Refer to Line: {}, Column: {}".format(self.line, self.column))
            raise SystemExit

    def variable_declaration(self):
        """
        variable_declr: SET string '=' WORD ';'
        """
        self.eat(SET) #remove set token
        name = self.current_token.value #Get name of variable

        #Remove the variable name and equals sign
        self.eat(STRING, "Syntax Error: Expected a STRING at this time as variable name")
        self.eat(EQUAL, "Syntax Error: Expected equals sign ('=') after variable name (string)")

        word = self.current_token.value #Get the word this variable is equal to

        #Remove the value and then semicolon ending the declration
        self.eat(WORD, "Synatx Error: Expected a WORD as the meaning of this variable.")
        self.eat(SEMI, "Syntax Error: Expected a semi colon to end variable declaration")

        #Return the result
        return {name: word}

    def info_field(self):
        """
        info_field: START string ':' WORD ':' STRING (',' WORD ':' STRING)* END
        """
        self.eat(START) #remove start token
        field_name = self.current_token.value #name of the information field

        #Remove string token and colon token
        self.eat(STRING, "Syntax Error: Expected a string as the name of this field")
        self.eat(COLON, "Synatx Error: Expected a colon (':') to note start of information in field")

        words = {} #Word-meaning pairings in this field

        word = self.current_token.value #get word in the language

        #Remove the word token
        if self.current_token.type == WORD:
            self.eat(WORD, "Syntax Error: Expected a WORD for start of WORD : MEANING pair in field")
        else:
            self.eat(STRING, "Syntax Error: Expected a STRING for start of WORD : MEANING pair in field")

        self.eat(COLON, "Syntax Error: Expected a COLON to seperate WORD and MEANING in pair")

        meaning = self.current_token.value #Get the meaning of the word
        #Removes the string
        self.eat(STRING, "Synatx Error: Expected a STRING for end of WORD : MEANING pair in field")

        words[word] = meaning #Enter in word and the meaning

        while self.current_token.type == COMMA: #While we have more pairs, add them
            self.eat(COMMA)
            word = self.current_token.value #get word in the language
            #Remove the word token
            if self.current_token.type == WORD:
                self.eat(WORD, "Syntax Error: Expected a WORD for start of WORD : MEANING pair in field")
            else:
                self.eat(STRING, "Syntax Error: Expected a STRING for start of WORD : MEANING pair in field")

            self.eat(COLON, "Syntax Error: Expected a COLON to seperate WORD and MEANING in pair")
            meaning = self.current_token.value #Get the meaning of the word
            #Removes the string
            self.eat(STRING, "Synatx Error: Expected a STRING for end of WORD : MEANING pair in field")
            words[word] = meaning #Enter in word - meaning pair

        self.eat(END, "Syntax Error: Expected the END keyword to denote end of field")

        return {field_name: words} #Return field

    def parse(self):
        return self.program()

#Reads a vocabulary file
def read_vocab(file_name):
    try:
        #Try to read the file
        contents = open(file_name, 'r').read()

    except FileNotFoundError:
        print("--Couldn't locate file {} in current directory--".format(file_name))
        raise SystemExit

    else: #Otherwise, return the parsed file
        return Parser(contents).parse()
