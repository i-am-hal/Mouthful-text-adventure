"""
A full test game to try out all/most of the components
being developed. A recreation of a small text based game
I tried to make for a friend of mine.
Author: Alastar Slater
Date: 3/9/19
"""
from Game import GameEngine
from Tools import Actor, Item, Container, Room, Transistion, End, Exit, Player

game = GameEngine() #The game being used
player = Player('Unkown', "I'm wearing my pajamas.") #Starting player object

##################
#      MAP 1     #
##################

#Starting room
bedroom = Room('bedroom', "This is a simple and small room which was given to you for your use. It works fine enough for you. To the east is the hallway.", "  You awoke in a cold sweat. The reminents of whatever nightmare you had floated about your mind for a few more moments before you couldn't remember it anymore. It's late at night, and you know you most likely won't be able to go to sleep. Might as well try to find something to do.")

#Computer item in the room
computer = Item('computer', "An old computer that looks like it got plucked out of the 80s. It's currently not on.", room_name='computer')
computer.collectable = False

#The window in the room
window = Item('window', "It's dark outside. You can somewhat make out the outlines of the trees of in the distance. They seem to be swaying in the wind.", room_name='window')
window.collectable = False

#Add all of the items to the room
bedroom.add_items(computer, window)

hallway = Room('hallway', "A small narrow hallway which connects the bathroom door to the east, and the living room to the north. It's pretty dark in this hallway at this time of night.")

#Connect the bedroom to the hallway
bedroom.make_connect('e', hallway)
hallway.make_connect('n', Transistion()) #End of this map

#Add the first map
game.add_map(bedroom)

###################
#      MAP 2      #
###################

bedroom = Room('bedroom', "This is a small, dirty room which was given for you to use. It's cold in here.", "  You awoke in a cold sweat, your dream lingering for a few more moments until it faded once more. You can hear the rain pouring outside, your room is otherwise dark besides the soft green glow from your computer. There's no chance that you'll be able to go back to sleep, best to find something to do.")

#The computer object
computer = Item('computer', "An old computer that looks like it got plucked out of the 80s, it's currently on, a soft green light illuminating your dark room.", room_name='old computer')
computer.collectable = False #cannot be taken

window = Item('window', "It's dark outside, you can see the rain batter down against the window. You can somwhat see the trees swaying in the wind outside. Maybe there's a storm going on.", room_name='window')
window.collectable = False #cannot be taken

#Put the computer in the room
bedroom.add_items(computer, window) 

hallway = Room('hallway', "A narrow dark hallway that leads to the living room to the north. Your room is over to the west. It's very quiet in the house.")

bedroom.make_connect('e', hallway) #Connect bedroom to the hallway

#Last room in this map
livingroom = Room('livingroom', "The room is empty. The walls are bare, the paint on the walls seems to look old. To the south is the hallway, to the west is the front door.")
livingroom.make_connect('w', Transistion())

hallway.make_connect('n', livingroom) #Make connection to the livingroom

#Add the second map
game.add_map(bedroom)

###################
#      MAP 2      #
###################

#The starting room
bedroom = Room('bedroom', "To the north is the hallway.", "You hear thunder outside as you wake up again. Your room seems emptier then you remember it being.") 

#Words on the wall
words = Item('words', "Wake up.", room_name='words')

#Add all of the items for the bedroom
bedroom.add_items(words)

#The hallway connected to the bedroom
hallway = Room('hallway', "To the north is your room. To the south is your room. To the west is an exit.")

#Add the box which you can put items into
box = Container('item', "This is a small box. Looks like it could hold something.", ['empty'], 'item')
box.collectable = False

#Adds an exit for the user to go to the next room
def __give_user_exit(self, engine):
    engine.current_room.west.locked = False #Unlock the room

    #Add an exit to the west
    #engine.current_room.west = Transistion()
    #engine.current_room.description = 'The exit is to the west.'
    #Totally reshape the map so the user can't move
    #engine.current_room.south = None
    #engine.current_room.north = None
    #engine.maps[engine.map_index] = engine.current_room
    #engine.current_room.visited = False
    #engine.enter_room() #Bring name of room again, hint user to a change

#When the user puts the words in the box, add the exit
box.make_event(lambda self:words in self.items,  __give_user_exit)

hallway.add_items(box) #Add box to the room

hallway.make_connect('n', bedroom) #Conenct hallway to bedroom via north
hallway.make_connect('w', Transistion()) #Connect to exit
hallway.west.setup_lock(Item()) #Lock the exit to the west
bedroom.make_connect('n', hallway) #Connect bedroom to hallway via north

game.add_map(bedroom) #Add this new map


###################
#      MAP 3      #
###################

game.add_map(End("""
  You awoke finally from your dream. shades of pink and yellow
stream into your room as the early morning sun rises. What a
strange dream that was. It didn't even make any sense. You
shake your head for a few moments as you then rub your eyes
and get up from your bed. Best be time to get through the day.
"""))

#Startup the game
game.game_loop(player)
input('\n(Press enter when you are ready for the game to close)')
