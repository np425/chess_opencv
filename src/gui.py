import tkinter as tk
from PIL import Image, ImageTk
from .game import HUMAN, ROBOT
import threading
import chess

robot_count = 0
game_thread = None
game_running = threading.Event()
game_stopped = threading.Event()

condition = threading.Condition()

def _stop_game():
    global game_thread, game_running, game_stopped

    game_running.set()
    if not game_thread:
        return

    while game_thread is not None or not game_stopped.is_set():
        # Wait for game to finish
        pass

    game_thread = None
    game_running.clear()
    game_stopped.clear()

    print('Stopped game...')

def stop_game():
    thread = threading.Thread(target=_stop_game)
    thread.start()
    return thread

def update_robot_win_count():
    global robot_count
    read_robot_count_from_file()
    robot_count += 1
    write_robot_count_to_file()
    update_count_label()


def write_robot_count_to_file():
    global robot_count
    with open("robot_win_count.txt", "w") as file:
        file.write(str(robot_count))

def read_robot_count_from_file():
    global robot_count
    try:
        with open("robot_win_count.txt", "r") as file:
            content = file.read()
            if content:
                robot_count = int(content)
                print(f"Robot wins: {robot_count}")
    except FileNotFoundError:
        robot_count = 0

def update_count_label():
    count_label.config(text=str(robot_count))


def clear_screen():
    for widget in root.winfo_children():
        if widget not in logo_widgets:
            widget.destroy()
def background():
    global logo_widgets, count_label
    logo_widgets = []

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    image1 = Image.open("images/fondas.png")
    image2 = Image.open("images/ku.png")
    image3 = Image.open("images/conexus.png")
    killcount = Image.open("images/killcount.png")

    target_height = 100

    def resize_image(image, target_height):
        aspect_ratio = image.width / image.height
        new_width = int(target_height * aspect_ratio)
        return image.resize((new_width, target_height), Image.Resampling.LANCZOS)

    image1 = resize_image(image1, target_height)
    image2 = resize_image(image2, target_height)
    image3 = resize_image(image3, target_height)
    killcount = resize_image(killcount, 150)

    image1 = ImageTk.PhotoImage(image1)
    image2 = ImageTk.PhotoImage(image2)
    image3 = ImageTk.PhotoImage(image3)
    killcount = ImageTk.PhotoImage(killcount)

    total_width = image1.width() + image2.width() + image3.width()
    spacing = (screen_width - total_width) // 5

    x1 = spacing
    x2 = x1 + image1.width() + spacing
    x3 = x2 + image2.width() + spacing
    x4 = 30

    label1 = tk.Label(root, image=image1, borderwidth=0, bg="#FFFFFF")
    label1.image = image1
    label1.place(x=x1, y=0)
    logo_widgets.append(label1)

    label2 = tk.Label(root, image=image2, borderwidth=0, bg="#FFFFFF")
    label2.image = image2
    label2.place(x=x2, y=0)
    logo_widgets.append(label2)

    label3 = tk.Label(root, image=image3, borderwidth=0, bg="#FFFFFF")
    label3.image = image3
    label3.place(x=x3, y=0)
    logo_widgets.append(label3)

    killcount_label = tk.Label(root, image=killcount, borderwidth=0, bg="#FFFFFF")
    killcount_label.image = killcount
    killcount_label.place(x=x4, y=150)
    logo_widgets.append(killcount_label)

    count_label = tk.Label(root, text=str(robot_count), bg="#FFFFFF", font=("Arial", 30), fg="black")
    count_label.place(x=x4 + killcount.width() // 2 - 20, y=230)
    logo_widgets.append(count_label)

#start_game: game_screen and a thread for game
def start_button():
    global button

    clear_screen()

    def start_game():
        game_screen(root)
  

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    image = Image.open("images/start.png")
    image = ImageTk.PhotoImage(image)
    button = tk.Button(root, image=image, command=start_game, borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    button.image = image

    x = (screen_width - image.width()) // 2
    y = (screen_height - image.height()) // 2

    button.place(x=x, y=y)

def chess_engine_thread():
    global game_running, game_stopped
    
    stop_game().join()

    while game_running.is_set():
        state = game.check_game_over()
        root.after(0, update_turn)

        if state != "*":
            root.after(0, win_lose_msg)
            break
    
        valid_move = None

        if game.player == ROBOT:
            valid_move = game.robot_makes_move()
        elif game.player == HUMAN:
            valid_move = game.player_made_move()

    game_stopped.set()
    stop_game().join()


#in level screen: game.depth=level
def level_screen():
    clear_screen()

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    def select_level(level_value):
        game.depth = level_value
        clear_screen()
        color_screen()
    def display_levels():
        choose_level = Image.open("images/choose_level.png")
        choose_level = ImageTk.PhotoImage(choose_level)
        choose_label = tk.Label(root, image=choose_level, borderwidth=0)
        choose_label.image = choose_level
        choose_label.place(x=(screen_width - choose_level.width()) // 2, y=(screen_height - choose_level.height()) // 2 - 200)

        level1_img = Image.open("images/beginner.png")
        level2_img = Image.open("images/intermediate.png")
        level3_img = Image.open("images/advanced.png")
        level4_img = Image.open("images/unbeatable.png")

        level1_img = ImageTk.PhotoImage(level1_img)
        level2_img = ImageTk.PhotoImage(level2_img)
        level3_img = ImageTk.PhotoImage(level3_img)
        level4_img = ImageTk.PhotoImage(level4_img)

        level1_button = tk.Button(root, image=level1_img, command=lambda: select_level(2), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
        level1_button.image = level1_img
        level1_button.place(x=(screen_width - level1_img.width()) // 2, y=(screen_height - choose_level.height()) // 2 - 50)

        level2_button = tk.Button(root, image=level2_img, command=lambda: select_level(4), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
        level2_button.image = level2_img
        level2_button.place(x=(screen_width - level2_img.width()) // 2, y=(screen_height - choose_level.height()) // 2 + 75)

        level3_button = tk.Button(root, image=level3_img, command=lambda: select_level(6), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
        level3_button.image = level3_img
        level3_button.place(x=(screen_width - level3_img.width()) // 2, y=(screen_height - choose_level.height()) // 2 + 200)

        level4_button = tk.Button(root, image=level4_img, command=lambda: select_level(10), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
        level4_button.image = level4_img
        level4_button.place(x=(screen_width - level4_img.width()) // 2, y=(screen_height - choose_level.height()) // 2 + 325)
    display_levels()
 

#in color screen/assign_color: game.board.perspective=color, game.reset_board()
 
def color_screen():
    clear_screen()

    def display_colors():
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        choose_color = Image.open("images/choose_color.png")
        choose_color = ImageTk.PhotoImage(choose_color)
        choose_label1 = tk.Label(root, image=choose_color, borderwidth=0)
        choose_label1.image = choose_color
        choose_label1.place(x=(screen_width - choose_color.width()) // 2, y=(screen_height - choose_color.height()) // 2 - 200)

        color1 = Image.open("images/white.png")
        color1 = ImageTk.PhotoImage(color1)
        button1 = tk.Button(root, image=color1, command=lambda: assign_color("white"), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
        button1.image = color1
        button1.place(x=(screen_width - color1.width()) // 2, y=(screen_height - color1.height()) // 2)

        color2 = Image.open("images/black.png")
        color2 = ImageTk.PhotoImage(color2)
        button2 = tk.Button(root, image=color2, command=lambda: assign_color("black"), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
        button2.image = color2
        button2.place(x=(screen_width - color2.width()) // 2, y=(screen_height - color2.height()) // 2 + 200)
    display_colors()

def assign_color(selected_color):
    if selected_color=='white':
        game.reset_board(perspective=chess.WHITE)
    elif selected_color=='black':
        game.reset_board(perspective=chess.BLACK)
    start_button()


#win lose msg: determined from both game.board.perspective and game.check_game_over()
def win_lose_msg():
    clear_screen()

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    back = Image.open("images/back.png")
    back = back.resize((200, 100), Image.Resampling.LANCZOS)
    back = ImageTk.PhotoImage(back)
    back_button = tk.Button(root, image=back, command=lambda: level_screen(), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    back_button.image = back
    back_button.place(x=(screen_width - back.width()) // 2, y=screen_height - back.height() - 50)

    game_over_image = Image.open("images/game_over.png")
    game_over_image = ImageTk.PhotoImage(game_over_image)
    game_over_label = tk.Label(root, image=game_over_image, borderwidth=0)
    game_over_label.image = game_over_image
    game_over_label.place(x=(screen_width - game_over_image.width()) // 2, y=(screen_height - game_over_image.height()) // 2 )

    def display_win_lose_messages():
        image_path = None
        state = game.check_game_over()

        if state == "resigned":
            return update_robot_win_count()

        if game.board.perspective==chess.WHITE:
            if state == "1-0":
                image_path = "images/you_won.png"
            elif state == "0-1":
                image_path = "images/you_lose.png"
                update_robot_win_count()
            elif state == "1/2-1/2":
                image_path = "images/draw.png"
        elif game.board.perspective==chess.BLACK:
            if state == "1-0":
                image_path = "images/you_lose.png"
                update_robot_win_count()
            elif state == "0-1":
                image_path = "images/you_won.png"
            elif state == "1/2-1/2":
                image_path = "images/draw.png"

        if image_path:
            game_over_label.destroy()
            win_lose_image = Image.open(image_path)
            win_lose_image = ImageTk.PhotoImage(win_lose_image)
            win_lose_label = tk.Label(root, image=win_lose_image, borderwidth=0)
            win_lose_label.image = win_lose_image
            win_lose_label.place(x=(screen_width - win_lose_image.width()) // 2, y=(screen_height - win_lose_image.height()) // 2)

    root.after(2000, display_win_lose_messages)

def update_turn():
    """ who plays right now """
    if game.player == ROBOT:
        robot_label.config(image=robot_turn_active)
        robot_label.image = robot_turn_active
        user_label.config(image=your_turn_inactive)
        user_label.image = your_turn_inactive
    elif game.player == HUMAN:
        robot_label.config(image=robot_turn_inactive)
        robot_label.image = robot_turn_inactive
        user_label.config(image=your_turn_active)
        user_label.image = your_turn_active
        #finished_button.place(x=(screen_width - finished_button.winfo_width()) // 2, y=650)

def resign_button_commands():
    clear_screen()
    win_lose_msg()

    #when HUMAN move is finished and button clicked game.player becomes ROBOT
def finished_functions():
    game.player==ROBOT
    update_turn()
    #finished_button.destroy()

#resign/ finished buttons
def game_screen(root):
    clear_screen()
    #screen setup
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    global robot_label, user_label, robot_turn_active,your_turn_inactive, robot_turn_inactive,your_turn_active
    turns = Image.open("images/turns.png")
    robot_turn_active = Image.open("images/robot_turn_active.png")
    robot_turn_inactive = Image.open("images/robot_turn_inactive.png")
    your_turn_active = Image.open("images/your_turn_active.png")
    your_turn_inactive = Image.open("images/your_turn_inactive.png")

    turns = ImageTk.PhotoImage(turns)
    robot_turn_active = ImageTk.PhotoImage(robot_turn_active)
    robot_turn_inactive = ImageTk.PhotoImage(robot_turn_inactive)
    your_turn_active = ImageTk.PhotoImage(your_turn_active)
    your_turn_inactive = ImageTk.PhotoImage(your_turn_inactive)

    turns_label = tk.Label(root, image=turns, borderwidth=0, bg="#FFFFFF")
    turns_label.image = turns
    x_turns = (screen_width - turns.width()) // 2
    y_turns = (screen_height) // 4
    turns_label.place(x=x_turns, y=y_turns)

    robot_label = tk.Label(root, image=robot_turn_inactive, borderwidth=0, bg="#FFFFFF")
    robot_label.image = robot_turn_inactive
    robot_label.place(x=x_turns, y=y_turns + 2 * turns.height() + 10)

    user_label = tk.Label(root, image=your_turn_inactive, borderwidth=0, bg="#FFFFFF")
    user_label.image = your_turn_inactive
    user_label.place(x=x_turns, y=y_turns + 3 * turns.height() + 10)

    resign = Image.open("images/resign.png")
    resign = resign.resize((200, 100), Image.Resampling.LANCZOS)
    resign = ImageTk.PhotoImage(resign)
    resign_button = tk.Button(root, image=resign, command=lambda: resign_button_commands(), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    resign_button.image = resign
    resign_button.place(x=screen_width - resign.width() - 50, y=screen_height - resign.height() - 50)

    # finished_move = Image.open("images/move_finished.png")
    # finished_move = finished_move.resize((300, 150), Image.Resampling.LANCZOS)
    # finished_move = ImageTk.PhotoImage(finished_move)
    # finished_button = tk.Button(root, image=finished_move, command=lambda: finished_functions(), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    # finished_button.image = finished_move

    global game_thread
    game_thread = threading.Thread(target=chess_engine_thread)
    game_thread.start()



def gui_main(game_obj):
    global root, game
    game=game_obj

    read_robot_count_from_file()

    root = tk.Tk()
    root.configure(bg="#FFFFFF")

    root.attributes('-fullscreen', True)
    root.attributes('-type', 'splash')

    background()
    level_screen()

    root.mainloop()