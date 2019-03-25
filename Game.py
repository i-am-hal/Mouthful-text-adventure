"""
"""
#Import Deconstructor so it can be used for the game
from Deconstructor import Deconstructor
from Tools import Room, Item, Container, Actor, Player #So I can make tests
from functools import reduce
from textwrap import wrap
import colorama #so I can use unicode characters
import sys

#All of the cardinal directions used in the engine
CARDINALS = ['north', 'south', 'east', 'west']


def nil_command(self): #When no verb is given
    """Raise error to user, there is no verb."""
    #Print out the error, and clear input areas
    self.raise_error(self.NO_VERB_ERROR)
    self.full_command = []
    self.command = []

#Allows for movement around rooms
def go_command(self):
    """Allows user to move from one room into another room."""
    verb = self.command[0] #Meat of the verb
    meat = self.command[1] #Main 'meat' (most of) the verb 

    if meat['obj'] != '<NIL>': #If there is some direction (hopefully)
        #Tell user we can't move in that direction
        if meat['obj'][0][0] not in CARDINALS:
            #Tell the user we can't move
            self.raise_error(self.NOT_MOVE_IN_DIR)
            self.error = False

        #If we can go north, do so
        elif meat['obj'][0][0] == 'north' and self.current_room.north != None:
            #If the way isn't locked
            if self.current_room.north.locked == False:
                self.current_room.player_here = False #Say player isn't here
                #Go north into the new room
                self.current_room = self.current_room.north.room
                self.enter_room() #Show dialog

            #Otherwise, the way is locked
            else:
                self.output_text(self.WAY_LOCKED)

        #Move south if possible
        elif meat['obj'][0][0] == 'south' and self.current_room.south != None:
            #If the way isn't locked
            if self.current_room.south.locked == False: 
                self.current_room.player_here = False #Say player isn't here
                self.current_room = self.current_room.south.room
                self.enter_room() #Show dialog

            else: #Otherwise, if locked, raise error
                self.output_text(self.WAY_LOCKED)

        #Move east if possible
        elif meat['obj'][0][0] == 'east' and self.current_room.east != None:
            #If the exit is not locked, continue
            if self.current_room.east.locked == False:
                self.current_room.player_here = False #Say player isn't here
                self.current_room = self.current_room.east.room
                self.enter_room() #Show dialog

            else: #Otherwise, if locked, raise error
                self.output_text(self.WAY_LOCKED)

        #Move west if possible
        elif meat['obj'][0][0] == 'west' and self.current_room.west != None:
            #If the entrance isn't locked, proceed to the next room
            if self.current_room.west.locked == False:
                self.current_room.player_here = False #Say player isn't here
                self.current_room = self.current_room.west.room
                self.enter_room() #Show dialog

            else: #Otherwise, the way is locked
                self.output_text(self.WAY_LOCKED)

        else: #cannot move
            self.raise_error(self.NOT_MOVE_IN_DIR)
            self.error = False

    else: #Cannot move at all
        self.raise_error(self.CANNOT_MOVE)
        self.error = False

def get_description(item): #returns description of a premade type in the engine
    type_name = type(item).__name__ #The type of the item

    if type_name == 'Item':
        return item.description

    #Give description + contents if open
    elif type_name == 'Container':
        return item.description + (item.tell_contents() if item.is_open == True else '')

    elif type_name == 'Actor':
        return item.description

#Allows for looking at objects / things in the environment
def see_command(self):
    """Allows user to look at an object / thing in a room, or look around room again."""
    verb_info = self.command[0] #Get the info relating to the verb
    phrase = self.command[1] #Get info relating to rest of phrase

    #If nothing or 'place' is given, give room description
    if phrase['obj'] == '<NIL>' or phrase['obj'][0][0] == 'place': 
        #Print out total info. about the room
        self.current_room.visited = False
        self.enter_room()

    elif phrase['obj'][0][0] == 'I': #Give description of self
        self.output_text(self.player.description.strip() + ' ' + self.player.tell_inventory())

    else: #Try to look at whatever was given
        #Get all of the items that share the same name
        items = get_items(self.current_room.items, phrase['obj'][0][0], phrase['obj'][1])

        #Assuming items has been reduced to ONE item, give info
        if len(items) == 1:
            self.output_text(get_description(items[0]))

        else: #Otherwise, say we don't see that
            self.output_text(self.DO_NOT_SEE_ITEM)

#With a list of items, an item name and list of attributes, returns a list of corresponding items
def get_items(items_list, name, attributes):
    #Get all items with a matching name
    items = [item for item in items_list if item.name == name]

    if len(items) > 1: #More than one item, use attributes
        #Get the items with no attributes
        if attributes == []:
            items = [item for item in items if item.attributes == []]

        else: #Otherwise, get item with all matching attributes
            items = [item
                     for item in items
                     if reduce(lambda a,b:a and b,
                               [a in item.attributes for a in attributes]) == True]

    return items

#Allows for taking items from the room
def take_command(self):
    """Allows the user to take an item from the room that can be collected."""
    verb = self.command[0] #Verb info
    phrase = self.command[1] #Rest of the command

    #If we only have an object, it must be in the room
    if phrase['indir obj'] == '<NIL>' and phrase['obj'] != '<NIL>':
        items = get_items(self.current_room.items, phrase['obj'][0][0], phrase['obj'][1])

        #if we have only one item (that's collectable), add it to inventory
        if len(items) == 1 and items[0].collectable == True: 
            self.player.inventory.append(items[0])
            #Remove this item from the list of items
            self.current_room.items = [item for item in self.current_room.items if item != items[0]]
            self.output_text("Taken.") #Tell the user the item has been taken

        #if the user cannot take this item at all
        elif len(items) == 1 and items[0].collectable == False:
            self.output_text(self.CANNOT_TAKE)

        else: #Couldn't find the item
            self.output_text(self.DO_NOT_SEE_ITEM)

    #If we have an indirect object (to take from) and an item to take
    #Note that we will immediatly start loking for containers
    elif phrase['indir obj'] != '<NIL>' and phrase['obj'] != '<NIL>':
        #Start looking through all of the containers
        sources = [i for i in self.current_room.items if type(i).__name__ == 'Container']
        #Get potential sources to get the item from
        sources = get_items(sources, phrase['indir obj'][0][0], phrase['indir obj'][1]) 

        #If we cannot find this source
        if len(sources) == 0 or len(sources) > 1:
            self.output_text(self.GRAMMAR_ERROR)
            return

        #Get (hopefully only one) item for use
        items = get_items(sources[0].items, phrase['obj'][0][0], phrase['obj'][1])

        #If we have more than one item
        if len(items) == 0 or len(items) > 1:
            self.output_text(self.GRAMMAR_ERROR)
            return

        #Add the item to the user's inventory
        self.player.inventory.append(items[0])
        #Remove the item put in the user's inventory
        sources[0].items = [item for item in sources[0].items if item != items[0]]
        sources[0].update_state() #Check if the item is empty now
        self.output_text("Taken.") #Text displayed when user gets the item

    else: #Say we don't understand
        self.output_text(self.GRAMMAR_ERROR)

def give_command(self):
    """Allows the user to give items to other things / actors."""
    verb = self.command[0] #Verb portion of the command
    phrase = self.command[1] #Phrase portion of the command

    #In this case, infer that we are 'dropping' the item
    if phrase['obj'] != '<NIL>' and phrase['indir obj'] == '<NIL>':
        items = get_items(self.player.inventory, phrase['obj'][0][0], phrase['obj'][1])

        #tell the user that we don't understand
        if len(items) == 0 or len(items) > 1:
            self.output_text(self.DO_NOT_SEE_ITEM)
            return

        #Add the item that the user is giving to the rooms list of items
        self.current_room.items.append(items[0])
        #Remove the item from the user's inventory
        self.player.inventory = [i for i in self.player.inventory if i != items[0]]
        print("Dropped.") #Tell the user that they dropped the item

    #If we have something to give the item to
    elif phrase['obj'] != '<NIL>' and phrase['indir obj'] != '<NIL>':
        #Get the item to give from the user
        items = get_items(self.player.inventory, phrase['obj'][0][0], phrase['obj'][1])

        #Tell user there was a problem
        if len(items) == 0 or len(items) > 1:
            self.output_text(self.DO_NOT_SEE_ITEM)
            return

        #Get the potential subject that we will give our 'gift' to
        targets = get_items(self.current_room.items, phrase['indir obj'][0][0], phrase['indir obj'][1])

        #Tell user we don't understand
        if len(targets) == 0 or len(items) > 1:
            self.output_text(self.DO_NOT_SEE_ITEM)
            return

        #If the target actor accepts items, give them the item
        if type(targets[0]).__name__ == 'Actor' and targets[0].accept_items == False:
            self.output_text(self.ACTOR_NOT_ACCEPT_GIFT)
            return

        #If the container cannot take in any 'gifts'
        elif type(targets[0]).__name__ == 'Container' and targets[0].is_open == False: 
            self.output_text(self.CONTAINER_CLOSED)
            return

        #Add this item to the target's item list
        targets[0].items.append(items[0])

        #Check if the item is now not empty
        if type(targets[0]).__name__ == 'Container': targets[0].update_state()

        #Remove this item from the player's inventory
        self.player.inventory = [i for i in self.player.inventory if i != items[0]]
        print("Given.") #Tell the user that it has been given

    else: #Otherwise, tell user there is a problem
        self.output_text(self.GRAMMAR_ERROR)

#Effect an exit in some form or another
def cause_exit(self):
    phrase = self.command[1]
    direct = phrase['obj'][0][0] #Get the direction

    #Get the exit we'll effect
    if direct == 'north': direct = self.current_room.north
    elif direct == 'south': direct = self.current_room.south
    elif direct == 'east': direct = self.current_room.east
    elif direct == 'west': direct = self.current_room.west

    if direct == None: #If this is not a direction we can effect
        self.output_text(self.NOT_EXIT)
        return

    if phrase['indir obj'] == '<NIL>': #Save the indir obj
        items = ['<NIL>'] #The item

    else: #Otherwise, get the item
        #Get the items
        items = get_items(self.player.items, phrase['indir obj'][0][0], phrase['indir obj'][1])

        #If the item is not in the user's inventory, raise error
        if len(items) == 0 or len(items) > 1:
            self.output_text(self.NOT_IN_INVENTORY)
            return

    #Try to use this item on this exit
    direct.use(items[0], self) 

#Basically 'use', dir obj is thing we want to effect, indir obj is thing we effect it with
def cause_command(self):
    """Allows user to USE items on objects / actors in the room (or exits)."""
    verb = self.command[0] #Get the verb portion
    phrase = self.command[1] #Get the phrase portion

    if phrase['obj'] == '<NIL>': #Raise an error
        self.output_text(self.INTERACT_NO_OBJ)

    elif phrase['obj'][0][0] in CARDINALS: #Need to effect an exit
        cause_exit(self) #Do all that is needed to interact with exits

    elif phrase['indir obj'] == '<NIL>': #Not using any object
        #Get name and list of attributes of the item
        name, attr = phrase['obj'][0][0], phrase['obj'][1]

        #Try to get the wanted item
        items = get_items(self.current_room.items, name, attr)

        #If more than one item, tell user we don't see it
        if len(items) == 0 or len(items) > 1:
            self.output_text(self.DO_NOT_SEE_ITEM)
            return

        #Use NOTHING, and pass reference to engine
        items[0].use('<NIL>', self)

    else: #We have indirect object and direct object 
        #Get the items in the room
        room_items = get_items(self.current_room.items, phrase['obj'][0][0], phrase['obj'][1])

        #If the item in the room couldn't be seen
        if len(room_items) == 0 or len(room_items) > 1:
            self.output_text(self.DO_NOT_SEE_ITEM)
            return 

        #Go through the items in the user's inventory
        inven_items = get_items(self.player.items, phrase['indir obj'][0][0], phrase['indir obj'][1])

        #Go through user's items to see if the user has one item to use here
        if len(inven_items) == 0 or len(inven_items) > 1:
            self.output_text(self.NOT_IN_INVENTORY)
            return

        #Try to use the user's item on this object
        room_items[0].use(inven_items[0], self)

def quit_command(self): #Quits the game without saving
    self.playing = False #Stops the game

#Superclass for gaming a game
class GameEngine(object):
    def __init__(self):
        colorama.init() #Startup colorama

        #List of room graphs, in the order they should be ran.
        #(First room graph is loaded first..)
        self.maps = []
        self.map_index = 0 #The map we will load / are using
        self.current_room = None #Current room we are in
        self.playing = True #if we are playing the game
        self.player = None #player object
        self.score = 0 #How well the user is doing
        self.moves = 0 #How many actions the user has done

        #=[PROMPTS]=
        self.PROMPT = ">" #Prompt for getting user import
        self.ROOM_NAME = "\t\t\t   -=[{}]=-" #Way the room name is printed
        self.START_TEXT = "" #Text put in the very beginning as intro

        #=[ERRORS]=
        self.error = False #Error flag
        #Error raised to user when there is some sort of error
        self.GRAMMAR_ERROR = "I'm sorry, I don't understand."
        #The error brought up if there is no verb
        self.NO_VERB_ERROR = "Uhmm.. kinda need to know what I AM doing."
        #Error raised when user gives an unknown/unsupported verb
        self.UNKNOWN_VERB = "I don't know the verb '{}'."
        #Error raised when teh exit in the given direction is locked
        self.WAY_LOCKED = "The exit is locked."
        #Error raised when user can't go in a direction
        self.NOT_MOVE_IN_DIR = "I can't go in that direction."
        #If there is not an exit in a certain direction
        self.NOT_EXIT = "There isn't an exit there."
        #The message given if the user can't even move
        self.CANNOT_MOVE = "Well, I can't move."
        #When the user tries to look at something that doesn't exist in this room
        self.DO_NOT_SEE_ITEM = "I don't see that here."
        #When an item isn't in the user's inventory
        self.NOT_IN_INVENTORY = "I don't own that."
        #When the user tries to grab something they cannot grab
        self.CANNOT_TAKE = "I can't take that."
        #What is printed when the user can't use item with object
        self.CANNOT_USE_WITH_OBJ = "I can't use this with that."
        #What is printed when there IS NOTHING GIVEN TO INTERACT WITH
        self.INTERACT_NO_OBJ = "I don't know what I'm interacting with."
        #What is printed when an actor won't accept a gift
        self.ACTOR_NOT_ACCEPT_GIFT = "They won't accept my gift."
        #If the container we are trying to give the gift to is closed / locked
        self.CONTAINER_CLOSED = "I can't, it's closed."

        #=[COMMANDS]=
        self.full_command = [] #Current command to execute (all of it)
        self.command = [] #Current (single) command
        #Executes some code for a specific verb / word
        self.execute = {'<NIL>': nil_command, 'go': go_command, 'see': see_command,
                        'take': take_command, 'give': give_command, 'quit': quit_command,
                        'cause': cause_command} 

    def raise_error(self, err):
        """Prints out some error message, and says we have an error."""
        self.output_text(err)
        self.error = True

    #Prints every nicely fitted line of text
    def output_text(self, text):
        """Wraps the text to ~80 chars per row, then prints."""
        for line in wrap(text):
            print(line + '\x1b[0m')

    #Startup total play of next map
    def load_next_map(self):
        self.select_next_map()
        self.load_map()
        self.enter_room()

    #Loads the current map
    def load_map(self):
        self.current_room = self.maps[self.map_index]

        #Print out exit text, and stop the engine
        if type(self.current_room).__name__ == 'End':
            self.output_text(self.current_room.end_text)
            self.playing = False

    #Sets up map index to load next map
    def select_next_map(self):
        if self.map_index < len(self.maps):
            self.map_index += 1

    def enter_room(self):
        """Prints out all the text for the room (if new to room, otherwise, just name."""

        #Load the next map
        if type(self.current_room).__name__ == 'Transistion':
            self.load_next_map()

        #Otherwise, deal with room description stuff
        elif type(self.current_room).__name__ == 'Room': 
            self.current_room.player_here = True #Note thet the player is here
            #If the room has a name, print it out
            if self.current_room.name.strip() != "":
                self.output_text(self.ROOM_NAME.format(self.current_room.name))

            if self.current_room.visited == False: #If a new room, print description
                self.current_room.visited = True

                #Printout this start-up text only once if there is any
                if self.current_room.room_start_text.strip() != "" and self.current_room.start_text_shown == False:
                    self.current_room.start_text_shown = True #We've now shown this text
                    self.output_text(self.current_room.room_start_text) #Print out the text
                    print()

                self.output_text(self.current_room.get_description()) #Give description

    def delete_last_line(self):
        """Deletes last outputted line of text."""
        sys.stdout.write("\x1b[1A") #Move cursor up one
        sys.stdout.write("\x1b[1K") #Erase the line

    def unrecognized_verb(self, verb):
        """Raises an error because this verb is unknown / unsupported."""
        self.error = True #Note we have an error
        #Print out the error
        self.output_text(self.UNKNOWN_VERB.format(verb))

    def consume_input(self):
        """Use up all the input and execute each of them in sequence (or try to)."""

        i = 0 #Command index
        for command in self.full_command:

            #If the object uses a conjunction, extend it into multiple commands
            #(since it'll do the same thing, and make it easier for programming actions)
            if command[1]['obj'][0] == "and":
                #Template rest of the sentence
                template = {'obj':'CHANGE', 'indir obj':command[1]['indir obj'], 'quote':command[1]['quote']}
                n = i + 1
                for obj in command[1]['obj'][1][1:]:
                    #Setup the template for this sub type
                    new_tem = eval(str(template))
                    new_tem['obj'] = obj
                    #Add in the sub-command
                    self.full_command.insert(n, (command[0], new_tem)) 
                    n += 1

                command[1]['obj'] = command[1]['obj'][1][0] 

            #Load up the current command to be run
            self.command = command

            verb = command[0][0] #Get just the verb itself

            #Tell the user we don't know that verb
            if verb not in self.execute:
                self.raise_error(self.UNKNOWN_VERB.format(verb))
                self.error = False
                break

            else: #Otherwise, this verb is defined
                self.execute[verb](self)
                self.moves += 1 #Note taht we've done an action
                i += 1 #Note we're going to next command

        #Make sure input buffers are cleared out
        self.full_command = []
        self.command = []

    def prompt(self):
        """Gets input from the user and then consumes input."""
        #Get input from the user on what they want to do next
        print() #Extra spacing in input
        line = input(self.PROMPT)

        #Continue getting input until something is given
        while line.strip() == "":
            self.delete_last_line()
            line = input(self.PROMPT)

        #The deconstructor-- will give us usable versions of sentences
        decon = Deconstructor(line)
        #Attempt to deconstruct the user's input
        full_command = decon.deconstruct()

        if decon.error == True: #If an error occured, don't save input, tell user
            self.output_text(self.GRAMMAR_ERROR) #Print out that an error occured
            return [] #Return full command

        return full_command #What the total command is

    #Add this map to the list of maps to be loaded
    def add_map(self, graph):
        """Adds a gamemap to the list of maps to load in order."""
        self.maps.append(graph)

    def add_command(self, verb, function):
        """Adds a command for the gameplay, a verb which is the command,
        and a function (which takes only self) to then have access to self.command
        to perform the action needed."""
        self.execute[verb] = function

    def game_loop(self, player=Player()):
        """Main game loop. Keep running until 'end condition' (i.e. self.playing == False).
        Player must be fed into this function for game to properly start (otherwise, an 'empty'
        player is used, no attributes, name or description."""

        self.player = player #Save player object for gameplay

        if len(self.maps) == 0: #Raise error, can't start
            print("RUNTIME ERROR: NO MAPS IN GAME, GAME COULDN'T LOAD ANYTHING AND START")
            raise SystemExit

        #print out whatever introduction there is
        self.output_text(self.START_TEXT)
        #Add padding to text if the start isn't NOTHING
        if self.START_TEXT.strip() != "":
            print() #Adds new line to intro

        #Load the first map (first room, really)
        self.current_room = self.maps[self.map_index]

        self.enter_room() #Give room name and description

        #keep going while we are 'playing'
        while self.playing:
            self.current_room.check_events(self) #Check events for this room
            self.full_command = self.prompt() #Get input
            self.consume_input() #Use up whatever input is given
