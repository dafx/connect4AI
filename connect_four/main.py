import copy
from kivy.config import Config
Config.set('graphics','resizable',0)
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.popup import Popup
from kivy.graphics import *
from kivy.properties import NumericProperty,ListProperty,ObjectProperty
import connect_four.agent as agent

def get_first_available(col):
    """
    Returns the index of the first space in a list that is 0,
    returns -1 if the value isn't found as False can evaluate
    to 0
    """
    for i in range(len(col)):
        if col[i] == 0:
            return i
    return False


def get_n_by_n(a, top_x, top_y, n):
    """
    Gets an n by n 2d list from another 2d list
    """
    out = []
    cols = a[top_x:top_x+n]
    for col in cols:
        out.append(col[top_y:top_y+n])

    return out


def rgb_max_1(rgb):
    return tuple([x/255 for x in rgb])


class Player(object):
    def __init__(self, name, col, hover_col, point_score):
        self.name = name
        self.col = col
        self.hover_col = hover_col
        self.point_score = point_score
        self.games_won = 0


class GameBoard(Widget):
    """
    Container widget for the Columns of the board
    """
    def __init__(self, **kwargs):
        super(GameBoard, self).__init__(**kwargs)

        self.columns = [None]*7
        for i in range(7):
            container = Widget()
            layout = RelativeLayout(size=(77, 460), pos=(248+78*i, 20))
            self.columns[i] = Column()
            self.columns[i].col_no = i
            layout.add_widget(self.columns[i])
            container.add_widget(layout)
            self.add_widget(container)


class ConnectFour(Widget):
    board = ListProperty([[0]*6 for _ in range(7)])
    cur_player = NumericProperty(0)
    players = ListProperty([])
    player_1_name = ObjectProperty(None)
    games_won_label = ObjectProperty(None)
    start_game_btn = ObjectProperty(None)
    game_board = ObjectProperty(None)

    def make_move(self, col_no, col_obj):
        """
        Makes a move on the board. Takes the column number and a
        reference to the column as parameters
        """
        if self.players == []:
            # Players haven't been initialised
            return False

        space_index = get_first_available(self.board[col_no])
        if space_index == False and isinstance(space_index,bool):
            # Column is full up
            return False

        # Set the board element
        self.board[col_no][space_index] = self.players[
                self.cur_player].point_score
        
        # Redraw that column with the new values
        col_obj.redraw(self.board[col_no],self.counter_cols)
        
        if self.check_win():
            self.game_end_popup("{} won".format(self.players[self.cur_player].name))
            return True
        else:
            # Check for draw
            self.draw = True
            for col in self.board:
                if 0 in col:
                    self.draw = False

            if self.draw:
               self.game_end_popup("Draw")


        # Change the current player
        # self.cur_player = int(not self.cur_player)
        return False
    
    def AI_make_move(self):
        """
        AI makes a move on the board. Takes a
        reference to the column as parameters
        """
        self.cur_player = 1
        
        if self.players == []:
            # Players haven't been initialised
            return False

        # AI chooses which column
        col_no = agent.get_move_1step(self.board)
        #col_no = agent.get_move_3step(self.board)

        space_index = get_first_available(self.board[col_no])
        if space_index == False and isinstance(space_index,bool):
            # Column is full up
            return False
        
        # Set the board element
        self.board[col_no][space_index] = self.players[
                self.cur_player].point_score

        # Redraw that column with the new values

        self.game_board.columns[col_no].redraw(self.board[col_no],self.counter_cols)

        if self.check_win():
            self.game_end_popup("The computer won")
            return True
        else:
            # Check for draw
            self.draw = True
            for col in self.board:
                if 0 in col:
                    self.draw = False

            if self.draw:
               self.game_end_popup("Draw")
        
        self.cur_player = 0
        return False        

    def make_hover(self, col_no, col_obj):
        """
        Implements a hovered state for the column. Does not affect the
        actual board used for win checking, etc
        """
        if self.players == []:
            # Players haven't been initialised
            return False

        if self.cur_player == 1:
            # AI's turn
            return False

        # Copy the game board so the hovered state doesn't affect the win checking
        temp_col = copy.copy(self.board[col_no])
        index = get_first_available(temp_col)

        if index == False and isinstance(index,bool):
            # Move can't be made
            return False
        temp_col[index] = self.players[self.cur_player].point_score*2
        col_obj.redraw(temp_col,self.counter_cols)

    def undo_hover(self, col_no, col_obj):
        """
        Undoes the hovered state of the column, by redrawing it
        """
        if self.players == []:
            # Players haven't been initialised
            return False
        col_obj.redraw(self.board[col_no],self.counter_cols)

    def game_end_popup(self, msg):
        """
        Create popup for the end of the game with a message, New game,
        and Reset game button
        """
        popup_content = BoxLayout(orientation="vertical", size=(250, 200))
        new_game_btn = Button(size_hint=(1, 0.3), text="New Game")
        reset_btn = Button(size_hint=(1, 0.3), text="Reset (New Players)")

        popup_content.add_widget(Label(size_hint=(1, 0.4), text="{}".format(
            msg)))
        popup_content.add_widget(new_game_btn)
        popup_content.add_widget(reset_btn)

        self.popup = Popup(title="Game Finished", size=(250, 200),
                           size_hint=(None, None), content=popup_content, auto_dismiss=False)
        new_game_btn.bind(on_press=self.new_game_handler)
        reset_btn.bind(on_press=self.reset_game_handler)
        self.popup.open()

    def new_game_handler(self, _=None):
        """
        Handle the New game button on the win popup, has *optional*
        parameter as the button instance is by default passed to it
        """
        self.popup.dismiss()

        if self.draw:
            for i in range(2):
                self.players[i].games_won += 1
        else:
            self.players[self.cur_player].games_won += 1
        self.games_won_label.text = "{} v {}".format(self.players[0].games_won, self.players[1].games_won)

        # Reset Board
        self.board = [[0]*6 for x in range(7)]
        # Loop through columns in GameBoard and redraw them
        for col in self.game_board.columns:
            col.redraw([0]*6)

        self.cur_player = 0

    def reset_game_handler(self, _=None):
        """
        Handle the reset game button on the win popup and main
        screen, has *optional* parameter as the button instance
        is passed to it
        """
        if hasattr(self,'popup'):
            self.popup.dismiss()
        if self.players == []:
            return False
        # Reset Board
        self.board = [[0]*6 for x in range(7)]
        for col in self.game_board.columns:
            col.redraw([0]*6)
        
        # Re-enable and clear text inputs
        self.set_inputs_state(False)
        self.player_1_name.text = ""
        self.games_won_label.text = "0 v 0"
        self.players = []
        self.cur_player = 0

    def start_game(self):
        """
        Handles the start game button and creates the player objects
        """
        # Create Players
        self.players = [Player(self.player_1_name.text, rgb_max_1((221, 63, 63)), rgb_max_1((221,141,141)), 1),
                        Player("Artificial Intelligence", rgb_max_1((50, 205, 50)), rgb_max_1((141,40,221)), -1)]
        self.counter_cols = {"1": self.players[0].col, "-1": self.players[1].col,
                             "2": self.players[0].hover_col, "-2": self.players[1].hover_col}
        # Disable text inputs and start game button
        self.set_inputs_state(True)

    def set_inputs_state(self, state):
        """
        Sets the disabled property to state for player name entries
        and start game button
        """
        self.player_1_name.disabled = state
        self.start_game_btn = state

    def check_win(self):
        """
        Check for wins by using a 4x4 box and moving that around
        """
        for top_y in range(3):
            for top_x in range(4):
                to_check = get_n_by_n(self.board,top_x,top_y,4)
                row_check = [0]*4
                # Left to right and right to left diagonal check
                diag_check = [0]*2
                # Check columns
                for y, col in enumerate(to_check):
                    # Calculate scores of rows
                    for x, space in enumerate(col):
                        row_check[x] += space
                        if x == y:
                            diag_check[0] += space
                        if x+y == 3:
                            diag_check[1] += space

                    if sum(col) == 4:
                        return self.players[0]
                    elif sum(col) == -4:
                        return self.players[1]

                # Check row_check scores
                for row in row_check:
                    if row == 4:
                        return self.players[0]
                    elif row == -4:
                        return self.players[1]

                for diag in diag_check:
                    if diag == 4:
                        return self.players[0]
                    elif diag == -4:
                        return self.players[1]
        return False


class Column(Widget):
    def __init__(self, **kwargs):
        super(Column, self).__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)
        # Draw Column with zeros, so the spaces will all be white on start
        self.redraw([0]*6, [None])
        self.hovered = False
        self.connectFourGame = None

    def get_game(self):
        """
        Finds the main ConnectFour widget if the property isn't set and returns it.
        Needed for hover states and mouse presses, to access the game board
        """
        if self.connectFourGame == None:
            # Get make move function from connectFourGame
            for child in self.get_root_window().children:
                if isinstance(child, ConnectFour):
                    self.connectFourGame = child
                    break
        return self.connectFourGame

    def on_touch_down(self, touch):
        if self.collide_point(touch.x,touch.y) and touch.button == "left":
            if not self.get_game().make_move(self.col_no,self):
                # AI makes move
                self.get_game().AI_make_move()

    def on_mouse_pos(self, *args):
        pos = args[1]
        if self.collide_point(*self.to_widget(*pos)):
            self.hovered = True
            # Hovered over this column
            self.get_game().make_hover(self.col_no,self)
        elif self.hovered:
            # Remove the hovered state as mouse is no longer on this col
            self.hovered = False
            self.get_game().undo_hover(self.col_no,self)

    def redraw(self, col_vals, cols=None):
        self.canvas.clear()
        with self.canvas:
            for i, space in enumerate(col_vals):
                if space == 0:
                    Color(0.9, 0.9, 0.9)
                else:
                    Color(*(cols[str(space)]))
                Ellipse(pos=(0, 78*i),size=(70, 70))


class ConnectFourApp(App):
    def build(self):
        self.title = "Connect Four"
        connectFourGame = ConnectFour()
        self.connectFourGame = connectFourGame
        Window.clearcolor=(0.9,0.9,0.9,1)
        Window.size=(800,500)
        return self.connectFourGame

    def start_game(self):
        self.connectFourGame.start_game()

    def restart_game(self):
        self.connectFourGame.reset_game_handler()


def main():
    ConnectFourApp().run()
