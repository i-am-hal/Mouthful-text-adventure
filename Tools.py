"""
Contains a class for making rooms for text based adventure games.
Has all the basic components, such as the room superclass, item superclass.
These will be used for builting up smaller components of the game.
Author: Alastar Slater
Date: 3/6/19
"""
class Item: #Base class used in making more items
    def __init__(self, name="", description="", attributes=[], room_name=""):
        self.name = name
        self.description = description
        self.attributes = attributes #List of attributes / adjectives
        self.room_name = room_name #What the game says this object is in the room
        self.collectable = True #Can be collected by default
        self.events = [] #List of events for this item
        self.uses = {} #dict. of item:action pairs for when a particular item is used on this item

    def __hash__(self): #Return hash
        texts = -(hash(self.name) * hash(self.description) + hash(self.room_name)) + hash(self.collectable)
        events = sum(hash(x) for x in self.events)
        uses = sum(hash(x) for x in list(self.uses) + list(self.uses.values()))

        return uses * texts + events #return hash

    #Checks the events for this item
    def check_events(self, game_engine):
        for event in self.events: #Check every event
            #If condition is true, run function
            if event.__doc__(self) == True:
                event(self, game_engine)

    #Makes an event for this item
    def make_event(self, cond, event):
        """Adds an event. Condition takes only SELF, event is a function which takes SELF
        as well as taking the game engine being used. Condition returns a boolean, if 
        true then the event is triggered. """
        event.__doc__ = cond #save the condition as the doc-string
        self.events.append(event) #Add event to list of events

    def use(self, item, engine): #try to use this item on person
        """Attempts to use this item (given) to interact with this object."""
        if item in self.uses: #If there is an action associated with this item
            self.uses[item](self, engine) #Run action

        else: #Otherwise, cannot interact in this way
            engine.output_text(engine.CANNOT_USE_WITH_OBJ)

    #Adds a 'use' to this item
    def make_use(self, item, action):
        """Item is some item- or something that can be used to interact with the object.
        Action is a function taking self, and the game engine being used."""
        #If this item is used again, the action will be performed
        self.uses[item] = action

    def __eq__(self, other):
        #if types differ, return false
        if type(self) != type(other): return False

        #All of the information about this item
        self_info = (self.name, self.description, self.attributes, self.room_name, self.collectable)
        #info about the other item
        other_info =(other.name, other.description, other.attributes, other.room_name, other.collectable)

        #Return if these items are equal
        return self_info == other_info

#Makes output text less clunky with plurals
def last_item_plural(word):
    if word[-1] == 's': #Plural
        return word

    else: return 'a ' + word

class Container(Item):
    def __init__(self, name="", description="", attributes=[], room_name="", items=[]):
        #Put in the values for the item portion
        Item.__init__(self, name, description, attributes, room_name)
        self.items = items #all of the items contained within
        self.is_open = True #If the container is open (and things can be taken from it)
        self.update_state() #Check if this container is empty
        self.events = [] #All of the events to check
        self.uses = {} #Dict. of how certain items interact with this container

    def __hash__(self): #Return hash number
        #Text hash sum
        texts = hash(self.name) + hash(self.description) + hash(self.room_name)
        attr = sum(hash(x) for x in self.attributes) #attribute hash sum
        events = sum(hash(x) for x in self.events) #Event hash sum
        #Sum of uses hashes
        uses = sum(hash(x) for x in list(self.uses) + list(self.uses.values()))

        #Return hash
        return hash(self.is_open) * uses - events + attr + texts

    def use(self, item, engine):
        """Attempt to use this item (given) on this Container."""
        if item in self.uses: #Perform action if interactable
            self.uses[item](self, engine)

        else: #Otherwise, cannot use this item with this object
            engine.output_text(engine.CANNOT_USE_WITH_OBJ)

    def make_use(self, item, action):
        """Item is some object, action is a function that takes self and the game engine being used."""
        self.uses[item] = action

    def check_events(self, game_engine):
        #Checks every event
        for event in self.events:
            #If event should be triggered, does action
            if event.__doc__(self) == True:
                event(self, game_engine)

    def make_event(self, cond, event):
        """Condition takes only SELF, and event takes SELF and the game engine.
        Condition returns a boolean, if true, runs the event function."""
        event.__doc__ = cond
        self.events.append(event)

    #If the item has no items, add the 'empty' attribute
    def update_state(self):
        #If empty, add empty attribute
        if len(self.items) == 0: self.attributes.append('empty')
        else: #Otherwise, remove any empty attributes
            self.attributes = [a for a in self.attributes if a != 'empty']

    def tell_contents(self): #Gives contents of this container
        #The starting text on what item we are referring too
        text = ("{} contains: ".format(self.room_name)).capitalize()
        text = '\n' + text #add a new line

        #Say what each item contained is
        if len(self.items) > 1:
            text += ", ".join(i.room_name for i in self.items[:-1]) + ' and ' + self.items[-1].room_name + '. '

        elif len(self.items) == 1:
            text += self.items[0].room_name + '. '

        else: #if it contains nothing
            text += 'nothing. '

        return text

    def __eq__(self, other):
        #If types differ, return false
        if type(self) != type(other): return False

        #Information about this item
        self_info = (self.name, self.description, self.attributes, self.room_name,
                     self.collectable, self.items, self.is_open)

        #Information about the other value
        other_info = (other.name, other.description, other.attributes, other.room_name,
                      other.collectable, other.items, self.is_open)

        #Return if teh two values are equal
        return self_info == other_info

#An actor is any NPC (and user potentially) in the game
class Actor:
    def __init__(self, name="", description="", attributes=[], room_name="", items=[]):
        self.name = name
        self.description = description
        self.room_name = room_name #Referred to in the room
        self.collectable = False #Cannot take a person
        self.accept_items = True #Actor will accept items from user
        self.loose_grip = True #If items can freely be taken from this actor
        self.items = items #The items this actor possessess
        self.attributes = attributes #Adjectives
        self.uses = {} #Dict. of ways items interact with the actor

    def __hash__(self): #Returns hash value of this actor
        texts = hash(self.name) + hash(self.description) + hash(self.room_name) #Sum of text sum
        #Sum of all boolean values
        bools = hash(self.collectable) + hash(self.accept_items) + hash(self.loose_grip)
        items = sum(hash(x) for x in self.items) #Sum of all item hashes
        attrs = sum(hash(x) for x in self.attributes) #Sum of all attribute hashes
        #Sum of all of the use hashes
        uses = sum(hash(x) for x in list(self.uses) + list(self.uses.values()))

        #Return total hashes
        return bools + texts * items + attrs - uses

    def use(self, item, engine):
        """Attempts to use this item on this actor."""
        if item in self.uses: #Perform the action associated
            self.uses[item](self, engine)

        else: #Otherwise, cannot interact
            engine.output_text(engine.CANNOT_USE_WITH_OBJ)

    def make_use(self, item, action):
        """Item is some item in the game, action is a function taking self and the game engine."""
        self.uses[item] = action

    def __eq__(self, other):
        #If types differ, automatically NO
        if type(self) != type(other): return False

        #This item's information
        self_info = (self.name, self.description, self.room_name, self.collectable,
                     self.accept_items, self.loose_grip, self.items, self.attributes)

        #Other item's information
        other_info = (other.name, other.description, other.room_name, other.collectable,
                      other.accept_items, other.loose_grip, other.items, other.attributes)

        #Return if these items are equal
        return self_info == other_info

    def __str__(self):
        return f"Actor(Name:{self.name}, R-Name:{self.room_name}, Attr:{self.attributes})"

    def __repr__(self):
        return self.__str__()

#The player object for the game
class Player:
    def __init__(self, name="", description="", inventory=[]):
        self.name = name
        self.description = description
        self.inventory = inventory #List of items owned
        self.collectable = False #The player cannot collect themself

    def tell_inventory(self): #Returns with text saying what the player has
        text = "I have: "

        if len(self.inventory) > 1: #More than one item
            text += ", ".join(i.room_name for i in self.inventory[:-1]) + ' and ' + self.inventory[-1].room_name 

        elif len(self.inventory) == 1: #Use just teh one items name
            text += self.inventory[0].room_name

        else: #No items
            text += 'nothing. '

        return text #return the following text

#Mostly just denotes the end of the game, should be ideally, it's own map
class End:
    def __init__(self, end_text=""):
        self.end_text = end_text

    def __hash__(self): return hash(self.end_text) * 7

#An empty node which tells the engine to move to the next map
class Transistion:
    def __hash__(self): return 79

#An exit in a room
class Exit:
    def __init__(self, room):
        self.room = room #The room connected to
        self.locked = False #If the room is locked or not
        self.key = None #The key we are looking for 
        self.uses = {} #Dict. of how items interact with this

    def __hash__(self):
        #Get the sum as the uses hash
        uses_sum = sum(hash(x) for x in list(self.uses) + list(self.uses.values()))
        #Return this hash by taking the sum of all of these parts
        return hash(self.room) - hash(self.locked) + hash(self.key) - uses_sum

    def make_use(self, item, action):
        """Makes an antry on what this item does to this obj."""
        self.uses[item] = action

    def use(self, item, engine):
        #Perform action if there is a pairing
        if item in self.uses:
            self.uses[item](self, engine)

        else: #Tell user they can't use this item on this object
            engine.output_text(engine.CANNOT_USE_WITH_OBJ)

    #Setup exit to be locked
    def setup_lock(self, key):
        self.locked = True
        self.key = key
        #Setup key to change the state of the door
        self.make_use(key, lambda self, engine: self.change_lock_state(key))

    #Changes the door to it's opposite state
    def change_lock_state(self, key):
        #Change state of the exit
        if self.locked == False:
            state = self.lock(key)

        else:
            state = self.unlock(key)

        if state == 1: #Tell the user it worked
            print("Success.")

        elif state == -1: #Tell user it failed
            print("Failed.")

    #Returns number, 1 = succesfful lock, 0 = was locked, -1 = unsuccessful lock
    def lock(self, test_key):
        if self.locked == False and self.key == test_key:
            self.locked = True #Lock room
            return 1

        elif self.locked == True: #If already locked
            return 0

        else: #Unsuccessful lock
            return -1

    #Returns number, 1 is now unlocked, 0 was unlocked, -1 unseccessful unlock
    def unlock(self, test_key):
        if self.locked == True and self.key != None and self.key == test_key:
            self.locked = False #Unlock room
            return 1

        #Just say it is unlocked
        elif self.locked == False:
            return 0

        #Otherwise, unseccessful
        else: return -1

class Room:
    def __init__(self, name="", description="", room_start_text=""):
        #All of the ajoined rooms
        self.north = None
        self.east = None
        self.west = None
        self.south = None
        self.visited = False #If this room has been visited
        self.start_text_shown = False #If startup text is shown
        self.player_here = False #If the player is currently here

        self.name = name #Name of the room
        self.description = description 
        #Only shown at the start of this room / map
        self.room_start_text = room_start_text

        self.items = [] #list of items in room
        self.events = [] #List of events and things to do

    def __hash__(self): #Returns hash of this value
        #Sum of all direction nodes
        dirs = hash(self.north) + hash(self.south) + hash(self.east) + hash(self.west)
        #Sym of all text hashes
        texts = hash(self.name) + hash(self.description) + hash(self.room_start_text)
        item_sum = sum(hash(x) for x in self.items) #Sum of items
        event_sum = sum(hash(x) for x in self.events) #Sum of events
        #Sum of the rest of the values
        rest = hash(self.visited) + hash(self.start_text_shown) + hash(self.player_here)

        #return hashed values
        return dirs - texts + item_sum - event_sum * rest

    def get_description(self): #Returns discription + room description of objects
        text = ""
        
        if len(self.items) > 0:
            #If we have more than one thing
            if len(self.items) >= 2:
                #Collect all of the room names in a nice way.
                text = ", ".join(x.room_name for x in self.items[:-1]) + ", and " + last_item_plural(self.items[-1].room_name)
                #Add this text to make it more cohesive.
                text = "There is also: " + text + "."

            else: #Otherwise, use only that item
                text = "There is " + last_item_plural(self.items[0].room_name) + ' here.'

            #Check for open containers, get their contents
            if 'Container' in [type(x).__name__ for x in self.items]:
                #Say contents of every item in each open container
                for container in [i for i in self.items if type(i).__name__ == 'Container' and i.is_open == True]:
                    text += container.tell_contents()

        #Return the description and items present in the room
        return self.description + ' ' + text

    #Adds an event to the list of events to check
    #(an event is just a function to call)
    def make_event(self, cond, event):
        """
        An event is something that occurs based on some certain condition
        in a room. An event has a CONDITION, and an EVENT (action).
        The CONDITION is a function (that only takes self) and returns 
        a Boolean (true if the event will occur, false otherwise). The
        EVENT is the function that takes only self and preforms some action.
        """
        event.__doc__ = cond 
        self.events.append(event)

    #Check if any events have happened et
    def check_events(self, game_engine):
        """Checks if any events are ready to be triggered."""
        #If the vent is true, then we will execute the event
        for event in self.events:
            if event.__doc__(self) == True:
                event(self)

        #Check the evnts of every item
        for item in self.items:
            item.check_events(game_engine)

    #Gives cardinal direction
    def __simple_dir(self, direct):
        if direct.lower() in ['west', 'w']: return 'west'
        elif direct.lower() in ['south', 's']: return 'south'
        elif direct.lower() in ['east', 'e']: return 'east'
        elif direct.lower() in ['north', 'n']: return 'north'

    #Makes a connection to this new node that is given
    def make_connect(self, direct, node):
        """Makes a connection to another room via some cardinal direction."""
        direct = self.__simple_dir(direct) #Get the direction

        if direct == 'north':
            self.north = Exit(node) #North of this room is the new room
            self.north.room.south = Exit(self) #Allow for backtracking

        elif direct == 'south':
            self.south = Exit(node)
            self.south.room.north = Exit(self)

        elif direct == 'east':
            self.east = Exit(node)
            self.east.room.west = Exit(self)

        elif direct == 'west':
            self.west = Exit(node)
            self.west.room.east = Exit(self)

    #Adds the items to the list of items in this room
    def add_items(self, *items):
        """Adds 1+ items to the list of items in this room."""
        #Add all of the items
        if type(items).__name__ in ['tuple', 'list']:
            self.items.extend(items)

        else: #Otherwise add the single item
            self.items.append(items)
