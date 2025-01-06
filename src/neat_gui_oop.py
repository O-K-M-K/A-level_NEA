# GUI Related imports
import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as tk1
from PIL import Image, ImageTk
from datetime import datetime
from emojiKeyboardPackage import emojiKeyboard
import re

# File manipulation imports
from pathlib import Path
import os

# Networking Imports
import neat_secure_client as secure_client


# Asset management
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / \
    Path(r"C:\Users\orank\OneDrive\Desktop\Computer Science\A-level NEA\build\assets\frame0")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


class UIController(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)

        # Creating main app
        self.geometry("745x504")
        app_frame = tk.Frame(self)
        app_frame.pack(side="top", fill="both", expand=True)
        app_frame.grid_rowconfigure(0, weight=1)
        app_frame.grid_columnconfigure(0, weight=1)

        self.client = secure_client.Client()

        self.screen_name = None

        # Creating the different pages/frames
        self.frames = {}

        for F in (LoginPage, CreateAccountPage, ChatPage, AddFriendPage, SettingsPage):

            frame = F(self, app_frame, self.client)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        # Connect to server and display first frame
        if self.client.connect():
            self.client.establish_inital_contact()
        self.show_frame(LoginPage)

        self.ChatPage = self.frames[ChatPage]
        self.AddFriendPage = self.frames[AddFriendPage]

        self.client.ChatPage = self.ChatPage
        self.client.AddFriendPage = self.AddFriendPage

    def show_frame(self, new_frame: object):
        """Raises the frame in the paremeter: new_frame"""

        frame = self.frames[new_frame]
        # on_show acts like the __init__ class but for when a frame is shown instead
        frame.on_show()
        frame.tkraise()

    def on_close(self, account_deletion=False):
        """Function called when the user closes the entire app"""
        try:
            self.client.stop_listen()
            self.client.send_disconnect_message()
            print('[-] CLOSING APP...')
        except Exception as e:
            print(e)
        self.destroy()
        self.client.close_db_connection()
        if account_deletion:
            self.client.delete_directory()
        self.client.close_client()


class LoginPage(tk.Frame):
    def __init__(self, parent, window, client: secure_client.Client):
        self.controller = parent
        self.client = client
        tk.Frame.__init__(self, window)

    def on_show(self):
        """Function called when frame is shown"""
        self.create_and_place()
        self.check_client_connection()

    def create_and_place(self):
        """Creates and places all tkinter objects onto the frame"""

        self.canvas = tk.Canvas(
            self,
            bg="#0A0C10",
            height=504,
            width=745,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        login_header_text = self.canvas.create_text(
            316.0,
            30.0,
            anchor="nw",
            text="Login",
            fill="#E3E7ED",
            font=("MontserratRoman Bold", 40 * -1)
        )

        self.login_entry_image = tk.PhotoImage(
            file=relative_to_assets("login_entry.png"))

        # USERNAME ENTRY
        username_entry_text = self.canvas.create_text(
            252.0,
            118.0,
            anchor="nw",
            text="USERNAME",
            fill="#E3E7ED",
            font=("MontserratRoman Regular", 16 * -1)
        )
        username_entry_bg = self.canvas.create_image(
            372.0,
            156.5,
            image=self.login_entry_image
        )
        self.username_entry = tk.Entry(
            self,
            bd=0,
            bg="#617998",
            fg="#000716",
            highlightthickness=0
        )
        self.username_entry.place(
            x=255.5,
            y=140.0,
            width=233.0,
            height=33.0
        )

        # PASSWORD ENTRY
        password_entry_text = self.canvas.create_text(
            252.0,
            223.0,
            anchor="nw",
            text="PASSWORD",
            fill="#E3E7ED",
            font=("MontserratRoman Regular", 16 * -1)
        )
        password_entry_bg = self.canvas.create_image(
            372.0,
            261.5,
            image=self.login_entry_image
        )
        self.password_entry = tk.Entry(
            self,
            bd=0,
            bg="#617998",
            fg="#000716",
            highlightthickness=0,
            show='*'
        )
        self.password_entry.place(
            x=255.5,
            y=245.0,
            width=233.0,
            height=33.0
        )
        self.password_entry.bind(
            '<Return>', lambda e: self.login())

        # CREATE ACCOUNT BUTTON
        self.create_account_button_image = tk.PhotoImage(
            file=relative_to_assets("login_create_account_button.png"))

        create_account_button = tk.Button(
            self,
            image=self.create_account_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.controller.show_frame(CreateAccountPage),
            relief="flat",
            activebackground='#0A0C10'
        )
        create_account_button.place(
            x=271.0,
            y=415.0,
            width=203.0,
            height=25.0
        )

        # LOGIN BUTTON
        # self is required because as soon as the function finishes the variable is destroyed
        self.login_button_image = tk.PhotoImage(
            file=relative_to_assets("login_login_button.png"))

        self.login_button = tk.Button(
            self,
            image=self.login_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.login(),
            relief="flat",
            activebackground='#0A0C10'
        )
        self.login_button.place(
            x=311.0,
            y=328.0,
            width=123.0,
            height=39.0
        )

        # TOGGLE PASSWORD VISABILITY BUTTON
        self.eye_open_image = tk.PhotoImage(
            file=relative_to_assets("login_eye_open.png"))
        self.eye_closed_image = tk.PhotoImage(
            file=relative_to_assets("login_eye_closed.png"))

        self.toggle_password_button = tk.Button(
            self,
            image=self.eye_closed_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.show_hide_password(),
            relief="flat",
            background='#0A0C10',
            activebackground='#0A0C10'
        )
        self.toggle_password_button.place(
            x=519.0,
            y=237.0,
            width=51.0,
            height=51.0
        )

        # ERROR MESSAGE
        self.error_message = self.canvas.create_text(
            257.0,
            384.0,
            anchor="nw",
            text='',
            fill="#FF4747",
            font=("MontserratRoman Bold", 20 * -1),
            state='hidden'
        )

        # CONNECTION ERROR MESSAGE
        self.connection_error_message = self.canvas.create_text(
            225.0,
            80.0,
            anchor="nw",
            text='Client unable to connect to server',
            fill="#FF4747",
            font=("MontserratRoman Bold", 20 * -1),
            state='hidden'
        )

    def check_client_connection(self):
        """
        Checks the connection status of the client. 

        If client is NOT connected it disables all UI reponsiveness
        """
        if self.client.connected == False:
            self.canvas.itemconfig(
                self.connection_error_message, state='normal'
            )
            for w in self.winfo_children():
                # disable all widgets on login frame
                # prevents user loging in when server is down
                w.configure(state="disabled")

    def login(self):
        username_value = self.username_entry.get()
        password_value = self.password_entry.get()
        self.canvas.itemconfig(self.error_message, state='hidden')
        if username_value == '' or password_value == '':
            self.canvas.itemconfig(
                self.error_message, text='Please fill in required fields')
            self.canvas.moveto(self.error_message, 257.0, 384.0)
            self.canvas.itemconfig(self.error_message, state='normal')
        else:
            valid_password = self.client.login(username_value, password_value)
            if valid_password:
                self.password_entry.unbind('<Return>')
                self.client.handel_logged_in_client()
                self.controller.show_frame(ChatPage)
            else:
                print("Invalid Password")
                self.canvas.itemconfig(
                    self.error_message, text='Incorrect username or password')
                self.canvas.moveto(self.error_message, 230.0, 384.0)
                self.canvas.itemconfig(self.error_message, state='normal')

    def show_hide_password(self):
        print('{BUTTON CLICKED} toggle_password_button')
        if self.password_entry.cget('show') == '':
            self.password_entry.config(show='*')
            self.toggle_password_button.config(image=self.eye_closed_image)
        else:
            self.password_entry.config(show='')
            self.toggle_password_button.config(image=self.eye_open_image)

        # Try block as function used by CreateAccountPage too
        try:
            if self.comfirm_password_feild.cget('show') == '':
                self.comfirm_password_feild.config(show='*')
                self.toggle_password_button.config(image=self.eye_closed_image)
            else:
                self.comfirm_password_feild.config(show='')
                self.comfirm_password_feild.config(image=self.eye_open_image)
        except:
            pass


class CreateAccountPage(tk.Frame):
    def __init__(self, parent, window, client: secure_client.Client):
        self.controller = parent
        self.client = client
        tk.Frame.__init__(self, window)

    def on_show(self):
        # self.client.get_screen_name()
        self.create_and_place()

    def create_and_place(self):
        self.canvas = tk.Canvas(
            self,
            bg="#0A0C10",
            height=504,
            width=745,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        self.create_account_entry_image = tk.PhotoImage(
            file=relative_to_assets("create_account_entry.png"))

        # USERNAME ENTRY
        username_entry_bg = self.canvas.create_image(
            205.5,
            149.5,
            image=self.create_account_entry_image
        )
        self.username_entry_feild = tk.Entry(
            self,
            bd=0,
            bg="#617998",
            fg="#000716",
            highlightthickness=0
        )
        self.username_entry_feild.place(
            x=87.5,
            y=133.0,
            width=236.0,
            height=33.0
        )
        self.canvas.create_text(
            85.0,
            110.0,
            anchor="nw",
            text="USERNAME",
            fill="#E3E7ED",
            font=("MontserratRoman Regular", 16 * -1)
        )

        # SCREEN NAME ENTRY
        screen_name_entry_bg = self.canvas.create_image(
            205.5,
            217.5,
            image=self.create_account_entry_image
        )
        self.screen_name_entry_feild = tk.Entry(
            self,
            bd=0,
            bg="#617998",
            fg="#000716",
            highlightthickness=0
        )
        self.screen_name_entry_feild.place(
            x=87.5,
            y=201.0,
            width=236.0,
            height=33.0
        )
        self.canvas.create_text(
            85.0,
            178.0,
            anchor="nw",
            text="SCREEN NAME",
            fill="#E3E7ED",
            font=("MontserratRoman Regular", 16 * -1)
        )

        # PASSWORD ENTRY
        self.password_entry_image = tk.PhotoImage(
            file=relative_to_assets("create_account_password_entry.png"))

        password_entry_bg = self.canvas.create_image(
            515.5,
            149.5,
            image=self.password_entry_image
        )
        self.password_entry = tk.Entry(
            self,
            bd=0,
            bg="#617998",
            fg="#000716",
            highlightthickness=0,
            show='*'
        )
        self.password_entry.place(
            x=422.5,
            y=133.0,
            width=186.0,
            height=33.0
        )

        self.canvas.create_text(
            421.0,
            110.0,
            anchor="nw",
            text="PASSWORD",
            fill="#E3E7ED",
            font=("MontserratRoman Regular", 16 * -1)
        )

        # CONFIRM PASSWORD ENTRY
        confirm_password_bg = self.canvas.create_image(
            540.5,
            217.5,
            image=self.create_account_entry_image
        )
        self.comfirm_password_feild = tk.Entry(
            self,
            bd=0,
            bg="#617998",
            fg="#000716",
            highlightthickness=0,
            show='*'
        )
        self.comfirm_password_feild.place(
            x=422.5,
            y=201.0,
            width=236.0,
            height=33.0
        )

        self.canvas.create_text(
            421.0,
            178.0,
            anchor="nw",
            text="CONFIRM PASSWORD",
            fill="#E3E7ED",
            font=("MontserratRoman Regular", 16 * -1)
        )

        # CREATE ACCOUNT HEADER
        self.canvas.create_text(
            227.0,
            35.0,
            anchor="nw",
            text="Create Account",
            fill="#E3E7ED",
            font=("MontserratRoman Bold", 40 * -1)
        )

        # ERROR MESSAGE
        self.error_message = self.canvas.create_text(
            240.0,
            422.0,
            anchor="nw",
            text="",
            fill="#FF4747",
            font=("MontserratRoman Bold", 20 * -1),
            state='hidden'
        )

        # SUBMIT BUTTON
        self.submit_button_image = tk.PhotoImage(
            file=relative_to_assets("create_account_submit.png"))

        submit_button = tk.Button(
            self,
            image=self.submit_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.create_new_account(),
            relief="flat",
            activebackground='#0A0C10'
        )
        submit_button.place(
            x=293.0,
            y=266.0,
            width=149.0,
            height=43.0
        )

        # LOGIN OPTION BUTTON
        self.login_option_image = tk.PhotoImage(
            file=relative_to_assets("create_account_login_option.png"))

        login_option_button = tk.Button(
            self,
            image=self.login_option_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.controller.show_frame(LoginPage),
            relief="flat",
            activebackground='#0A0C10'
        )
        login_option_button.place(
            x=227.0,
            y=342.0,
            width=286.0,
            height=48.0
        )

        # TOGGLE PASSWORD VISABILITY BUTTON
        self.eye_open_image = tk.PhotoImage(
            file=relative_to_assets("login_eye_open.png"))
        self.eye_closed_image = tk.PhotoImage(
            file=relative_to_assets("login_eye_closed.png"))
        self.toggle_password_button = tk.Button(
            self,
            image=self.eye_closed_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: LoginPage.show_hide_password(self),
            relief="flat",
            background='#0A0C10',
            activebackground='#0A0C10'
        )
        self.toggle_password_button.place(
            x=633.0,
            y=125.0,
            width=51.0,
            height=51.0
        )

    def secure_password(self, password: str):
        valid = False
        special_char = re.compile('[@_!$%^&*()<>?/\|}{~:]#')
        general_patern = re.compile(
            '^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).{8,64}$')

        if special_char.search(password) == None and re.match(general_patern, password):
            valid = True
        return valid

    def create_new_account(self):
        """Creates new account OR shows error messasge if feilds not filled in correctly"""
        print("{BUTTON CLICKED} submit_button")
        self.canvas.itemconfig(self.error_message, state='hidden')

        # getting relevant values
        username_value = self.username_entry_feild.get()
        screen_name_value = self.screen_name_entry_feild.get()
        password_value = self.password_entry.get()
        password_confirm_value = self.comfirm_password_feild.get()

        if username_value == '' or screen_name_value == '' or password_value == '' or password_confirm_value == '':
            self.canvas.itemconfig(
                self.error_message, text='Please fill in required fields')
            self.canvas.moveto(self.error_message, 250.0, 422.0)
            self.canvas.itemconfig(self.error_message, state='normal')
        elif password_value != password_confirm_value:
            self.canvas.itemconfig(
                self.error_message, text='Your entered passwords do not match')
            self.canvas.moveto(self.error_message, 207.0, 422.0)
            self.canvas.itemconfig(self.error_message, state='normal')
        elif not self.secure_password(password_value):
            self.canvas.itemconfig(
                self.error_message, text='Password is not secure enough')
            self.canvas.moveto(self.error_message, 240.0, 422.0)
            self.canvas.itemconfig(self.error_message, state='normal')

        else:  # actually send data to client
            unique_userID, account_created = self.client.create_account(
                username_value, password_value, screen_name_value)
            if unique_userID and account_created:
                self.client.handel_logged_in_client()
                self.controller.show_frame(ChatPage)
                print('{ACCOUNT CREATED}')
            elif unique_userID != True:
                self.canvas.itemconfig(
                    self.error_message, text='Username taken. Please try a different username'
                )
                self.canvas.moveto(self.error_message, 157.0, 422.0)
                self.canvas.itemconfig(self.error_message, state='normal')
            else:
                self.canvas.itemconfig(
                    self.error_message, text='Something went wrong when creating your account, please try again later'
                )
                self.canvas.moveto(self.error_message, 157.0, 422.0)
                self.canvas.itemconfig(self.error_message, state='normal')


class ChatPage(tk.Frame):
    def __init__(self, parent, window, client: secure_client.Client):
        self.controller = parent
        self.client = client
        tk.Frame.__init__(self, window)
        self.current_friend_message_history = None
        self.active_chat_user_details = None
        self.last_selected = None
        self.list_of_buttons = []
        self.friend_screen_name = None
        self.send_image_data = None
        self.images = []

    def on_show(self):
        self.client.get_friend_list()
        self.create_and_place()
        self.add_temp_text()
        self.show_friends()
        self.client.listen()
        self.disable_message_buttons()

    def add_temp_text(self):
        self.add_temp_text_to_message_entry()
        if len(self.client.friend_list) == 0:
            self.canvas.itemconfig(
                self.recipient, text='Add a friend to start chatting')
        else:
            self.canvas.itemconfig(
                self.recipient, text='Click on a friend to start chatting')

    def create_and_place(self):

        self.canvas = tk.Canvas(
            self,
            bg="#0A0C10",
            height=504,
            width=745,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )

        self.canvas.place(x=0, y=0)
        self.side_bar_rectangle = self.canvas.create_rectangle(
            0.0,
            0.0,
            190.0,
            504.0,
            fill="#2A3441",
            outline="",
            tags='rectangle')

        self.canvas.create_text(
            9.0,
            14.0,
            anchor="nw",
            text="Chats",
            fill="#E3E7ED",
            font=("MontserratRoman Bold", 24 * -1)
        )

        self.message_display_box = tk.Text(
            self,
            bd=0,
            bg="#12161C",
            fg="#E3E7ED",
            highlightthickness=0,
            font=("MontserratRoman", 14, 'normal'),
            state='disabled'
        )
        self.message_display_box.place(
            x=199.0,
            y=54.0,
            width=533.0,
            height=393.0
        )

        self.message_entry_box_image = tk.PhotoImage(
            file=relative_to_assets("entry_2.png"))
        message_entry_box_bg = self.canvas.create_image(
            485.0,
            477.0,
            image=self.message_entry_box_image
        )

        self.message_entry_box = tk.Entry(
            self,
            bd=0,
            bg="#617998",
            fg="#E3E7ED",
            highlightthickness=0,
            font=("MontserratRoman")
        )
        self.message_entry_box.place(
            x=292.0,
            y=463.0,
            width=386.0,
            height=28.0
        )

        self.message_entry_box.bind(
            '<FocusIn>', lambda e: self.remove_temp_text_from_message_entry())
        self.message_entry_box.bind(
            '<FocusOut>', lambda e: self.add_temp_text_to_message_entry())

        self.message_entry_box.bind(
            '<Return>', lambda e: self.send_message(self.message_entry_box.get()))

        # -------------------------

        self.recipient = self.canvas.create_text(
            199.0,
            14.0,
            anchor="nw",
            text="",
            fill="#E3E7ED",
            font=("MontserratRoman Bold", 24 * -1)
        )

        self.screen_name_text = self.canvas.create_text(
            10.0,
            466.0,
            anchor="nw",
            text=self.client.screen_name,
            fill="#E3E7ED",
            font=("MontserratRoman Bold", 24 * -1)
        )

        self.settings_image = tk.PhotoImage(
            file=relative_to_assets("settings_button.png"))

        settings_button = tk.Button(
            self,
            image=self.settings_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.controller.show_frame(SettingsPage),
            relief="flat",
            bg='#2A3441',
            activebackground='#2A3441'
        )
        settings_button.place(
            x=151.0,
            y=463.0,
            width=30.0,
            height=30.0
        )
        self.add_friend_image = tk.PhotoImage(
            file=relative_to_assets("add_friend_button.png"))
        add_friend_button = tk.Button(
            self,
            image=self.add_friend_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.controller.show_frame(AddFriendPage),
            relief="flat",
            bg='#2A3441',
            activebackground='#2A3441'
        )
        add_friend_button.place(
            x=151.0,
            y=15.0,
            width=30.0,
            height=30.0
        )

        self.send_message_image = tk.PhotoImage(
            file=relative_to_assets("send_message_button.png"))
        self.send_message_button = tk.Button(
            self,
            image=self.send_message_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.send_message(
                self.message_entry_box.get()),
            relief="flat",
            bg='#0A0C10',
            activebackground='#0A0C10'
        )
        self.send_message_button.place(
            x=702.0,
            y=463.0,
            width=30.0,
            height=30.0
        )

        self.attachment_button_image = tk.PhotoImage(
            file=relative_to_assets("attachment_button.png"))
        self.attachment_button = tk.Button(
            self,
            image=self.attachment_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=self.handel_getting_image,
            relief="flat",
            bg='#0A0C10',
            activebackground='#0A0C10'
        )
        self.attachment_button.place(
            x=199.0,
            y=463.0,
            width=30.0,
            height=30.0
        )

        self.emoji_keyboard_image = tk.PhotoImage(
            file=relative_to_assets("emoji_button.png"))

        self.emoji_keyboard_button = tk.Button(
            self,
            image=self.emoji_keyboard_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.open_emoji_keyboard(),
            relief="flat",
            bg='#0A0C10',
            activebackground='#0A0C10'
        )
        self.emoji_keyboard_button.place(
            x=238.0,
            y=463.0,
            width=30.0,
            height=30.0
        )


# FRIENDS LIST CODE

        self.friend_list_area = tk.Text(
            self,
            bd=0,
            bg="#12161C",
            fg="#E3E7ED",
            highlightthickness=0,
            cursor='arrow',
            state='disabled'
        )
        self.friend_list_area.place(
            x=0.0,
            y=93.0,
            width=190,
            height=356
        )
        sb = tk.Scrollbar(self.friend_list_area,
                          command=self.friend_list_area.yview, width=20)
        sb.pack(side='right', fill=tk.Y)
        self.friend_list_area.configure(yscrollcommand=sb.set)
        self.active_chat_user_details = tk.StringVar(self.friend_list_area)

    def disable_message_buttons(self):
        self.message_entry_box.config(state='disabled')
        self.send_message_button.config(state='disabled')
        self.emoji_keyboard_button.config(state='disabled')
        self.attachment_button.config(state='disabled')


# ----------EMOJI KEYBOARD LOGIC----------

    def open_emoji_keyboard(self):
        print('Opening keyboard')
        # self.newWindow = tk.Toplevel(self.controller)
        emoji_keyboard = emojiKeyboard.Keyboard(self)

    def insert_emoji(self, emojis: str):
        self.message_entry_box.focus_set()
        self.remove_temp_text_from_message_entry()
        self.message_entry_box.insert('end', emojis)

# ----------SENDING IMAGE LOGIC----------

    def handel_getting_image(self):
        self.client.client_get_image_path()
        if self.client.image_path:
            self.send_image_data = self.client.get_image_data(
                self.client.image_path)
            image_name = self.client.image_path.split('/')[-1]
            self.remove_temp_text_from_message_entry()
            self.add_specific_temp_text_to_msg_entery(image_name)

            self.message_entry_box.config(state='disabled')


# ----------FRIEND LIST LOGIC---------------

    def add_new_friend_to_UI(self, friend_screen_name: str, friend_details: str, status: str, specifier_id: str):

        state = 'normal'
        colour = '#2A3441'
        active = '#12161C'
        if status == 'blk' and specifier_id == self.client.user_id:  # you have blocked them
            colour = '#FF4747'
            active = '#612a2a'
        elif (status == 'blk' and specifier_id != self.client.user_id) or ('deleted account' in friend_screen_name):  # they have blocked you
            state = 'disabled'

        # when clicked self.active_chat_user_details is set to value
        # text is the text shown on the button value itself
        btn = tk.Radiobutton(self.friend_list_area,
                             text=friend_screen_name,
                             variable=self.active_chat_user_details,
                             value=friend_details,
                             indicatoron=0,
                             bg=colour,
                             height=2,
                             width=23,
                             relief='flat',
                             fg='#E3E7ED',
                             selectcolor=active,
                             command=lambda: self.friend_chat_btn_press(btn),
                             borderwidth=0,
                             font=("MontserratRoman", 9, 'normal'),
                             state=state
                             )
        self.list_of_buttons.append(btn)
        self.friend_list_area.window_create('end', window=btn)
        self.friend_list_area.insert('end', '\n')

    def friend_chat_btn_press(self, btn: tk.Radiobutton):
        if self.active_chat_user_details.get() != self.last_selected:
            # getting details
            friend_details = self.active_chat_user_details.get().split(' ')
            friend_user_id = friend_details[0]
            friend_public_key = friend_details[1]
            self.friend_screen_name = btn.cget("text")

            # updating UI
            self.canvas.itemconfig(
                self.recipient, text=self.friend_screen_name)
            self.last_selected = self.active_chat_user_details.get().split(' ')

            self.message_display_box.config(state='normal')
            self.message_display_box.delete(1.0, 'end')

            # insert message history here
            self.client.decrypt_message_history(
                self.active_chat_user_details.get().split(' ')[0])
            self.show_message_history()

            if btn.cget('bg') == '#FF4747':
                self.message_entry_box.config(state='disabled')
                self.send_message_button.config(state='disabled')
                self.emoji_keyboard_button.config(state='disabled')
                self.attachment_button.config(state='disabled')
            else:
                self.message_entry_box.config(state='normal')
                self.send_message_button.config(state='normal')
                self.emoji_keyboard_button.config(state='normal')
                self.attachment_button.config(state='normal')
                self.message_entry_box.focus_set()
                self.message_entry_box.delete(0, 'end')

    def show_friends(self):
        for friend in self.client.friend_list:
            friend_screen_name = friend[2]
            friend_details = friend[0:2]
            status = friend[3]
            specifier_id = friend[4]
            self.add_new_friend_to_UI(
                friend_screen_name, friend_details, status, specifier_id)

    def update_friend_list(self):
        for btn in self.list_of_buttons:
            btn.destroy()
        self.show_friends()


# ---------SEND MESSAGE LOGIC----------------------


    def show_message_history(self):
        for message_data in self.client.current_message_history:
            formatted_message = self.format_stored_message_for_display(
                message_data)
            self.client.image_path = formatted_message['message']
            self.display_message(
                self.format_stored_message_for_display(message_data))

    def handel_sending_message_or_image(self, message: str):
        pass

    def send_message(self, message: str):
        """Executes procedure to display message and send message to the server"""
        if len(message) != 0:
            is_image = 0
            msg = message
            image_name_and_format = ''

            if self.message_entry_box.cget('state') == 'disabled':
                print('[-] SENDING IMAGE')
                is_image = 1
                msg = self.send_image_data
                image_name_and_format = self.client.image_name_and_format

            date, time = self.get_timestamp()
            formatted_message = self.format_message(
                self.client.screen_name, date, time, msg, is_image, image_name_and_format)
            self.client.handel_send_message(formatted_message)
            self.display_message(formatted_message)
            if is_image:
                os.remove(self.client.image_path)

    def get_timestamp(self):
        """Gets current data and time"""
        now = datetime.now()
        date = now.strftime("%d/%m/%Y")
        time = now.strftime("%H:%M:%S")
        return date, time

    def format_stored_message_for_display(self, message_data):
        decrypted_message = message_data[0]
        date = message_data[1]
        time = message_data[2]
        from_me = message_data[3]
        is_image = message_data[4]

        if from_me:
            screen_name = self.client.screen_name
        else:
            screen_name = self.friend_screen_name

        return self.format_message(screen_name, date, time, decrypted_message, is_image)

    def format_message(self, screen_name, date, time, message, is_image, image_name_and_format=''):
        """Turns message into dict"""
        user_data = {
            'type': 'message',
            'recipient': self.active_chat_user_details.get().split(' ')[0],
            'config': 'message',
            'sender_user_id': self.client.user_id,
            'sender_screen_name': screen_name,
            'date': date,
            'time': time,
            'message': message,
            'is_image': is_image,
            'image_name_and_format': image_name_and_format
        }
        return user_data

    def display_message(self, formatted_message: dict):
        """Displays message with appropriate formatting onto screen"""

        self.message_display_box.tag_add(
            'timestamp_formatting', '1.0', '1.end')
        self.message_display_box.tag_config('timestamp_formatting', font=(
            'MontserratRoman', 10, 'italic'))

        # formatting text
        if formatted_message['is_image'] == False:
            self.display_message_text(formatted_message)
        else:
            self.display_message_image(formatted_message)
        self.message_entry_box.delete(0, 'end')

    def display_message_image(self, formatted_message: dict):
        dt = f"{formatted_message['date']} {formatted_message['time']}"
        screen_name = f"{formatted_message['sender_screen_name']}"
        timestamp = f"\n<{screen_name} {dt}>\n"
        image_path = self.client.image_path

        # global image
        unprocessed_image = Image.open(image_path)

        image = ImageTk.PhotoImage(unprocessed_image)
        self.images.append(image)

        self.message_display_box.config(state='normal')
        self.message_display_box.insert(
            'end', timestamp, 'timestamp_formatting')
        self.message_display_box.image_create(tk.END, image=image)
        self.message_display_box.insert('end', '\n')
        self.message_display_box.see('end')
        self.message_display_box.config(state='disabled')
        self.message_entry_box.config(state='normal')

    def display_message_text(self, formatted_message: dict):
        dt = f"{formatted_message['date']} {formatted_message['time']}"
        screen_name = f"{formatted_message['sender_screen_name']}"
        timestamp = f"\n<{screen_name} {dt}>\n"
        message = f"{formatted_message['message']}\n"

        # displaying message
        self.message_display_box.config(state='normal')
        self.message_display_box.insert(
            'end', timestamp, 'timestamp_formatting')
        self.message_display_box.insert('end', message)
        self.message_display_box.see('end')
        self.message_display_box.config(state='disabled')

    def add_temp_text_to_message_entry(self):
        if len(self.message_entry_box.get()) == 0:
            self.message_entry_box.delete(0, 'end')
            self.message_entry_box.config(fg='#2a3441')
            self.message_entry_box.insert(0, 'Type your message...')

    def remove_temp_text_from_message_entry(self):
        self.message_entry_box.config(fg='#E3E7ED')
        if self.message_entry_box.get() == 'Type your message...':
            print('REMOVING TEMP TEXT')
            self.message_entry_box.config(fg='#E3E7ED')
            self.message_entry_box.delete(0, 'end')

    def add_specific_temp_text_to_msg_entery(self, text: str):
        self.message_entry_box.config(fg='#2a3441')
        self.message_entry_box.insert(0, text)


class AddFriendPage(tk.Frame):
    def __init__(self, parent, window, client: secure_client.Client):
        self.controller = parent
        self.client = client
        tk.Frame.__init__(self, window)

        self.active_friend_button = None
        self.active_request_button = None

    def on_show(self):
        """Function called when frame is shown"""
        self.client.stop_listen()
        self.client.get_friend_list()
        self.client.get_friend_request_list()
        self.client.get_pending_friends_list()
        self.create_and_place()
        self.add_text()
        self.add_radio_buttons()

    def create_and_place(self):
        """Creates and places all tkinter objects onto the frame"""
        self.canvas = tk.Canvas(
            self,
            bg="#0A0C10",
            height=504,
            width=745,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )

        self.canvas.place(x=0, y=0)
        self.canvas.create_rectangle(
            0.0,
            0.0,
            745.0,
            32.0,
            fill="#12161C",
            outline="")

        page_header = self.canvas.create_text(
            8.0,
            6.0,
            anchor="nw",
            text="Friends",
            fill="#FFFFFF",
            font=("MontserratRoman Bold", 16 * -1)
        )

        self.back_to_chats_button_image = tk.PhotoImage(
            file=relative_to_assets("back_to_chats_button.png"))
        back_to_chats_button = tk.Button(
            self,
            image=self.back_to_chats_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.controller.show_frame(ChatPage),
            relief="flat"
        )
        back_to_chats_button.place(
            x=640.0,
            y=61.0,
            width=95.0,
            height=87.0
        )

        friends_friend_code_entry_text = self.canvas.create_text(
            8.0,
            121.0,
            anchor="nw",
            text="Enter your friend’s code to invite them to chat",
            fill="#FFFFFF",
            font=("MontserratRoman Bold", 16 * -1)
        )

        personal_friend_code_entry_text = self.canvas.create_text(
            9.0,
            38.0,
            anchor="nw",
            text="Your Friend Code",
            fill="#FFFFFF",
            font=("MontserratRoman Bold", 16 * -1)
        )

        self.friend_code_error_message = self.canvas.create_text(
            8.0,
            208.0,
            anchor="nw",
            text="",
            fill="#FF4747",
            font=("MontserratRoman Bold", 13 * -1),
            state='hidden'
        )

        self.personal_friend_code_entry_image = tk.PhotoImage(
            file=relative_to_assets("add_friend_personal_friend_code_entry.png"))
        personal_friend_code_entry_bg = self.canvas.create_image(
            169.5,
            84.0,
            image=self.personal_friend_code_entry_image
        )

        self.friends_friend_code_entry_image = tk.PhotoImage(
            file=relative_to_assets("add_friend_friends_friend_code_entry.png"))
        entry_bg_2 = self.canvas.create_image(
            169.5,
            171.0,
            image=self.friends_friend_code_entry_image
        )
        self.friends_friend_code_entry = tk.Entry(
            self,
            bd=0,
            bg="#617998",
            fg="#E3E7ED",
            highlightthickness=0
        )
        self.friends_friend_code_entry.place(
            x=30.0,
            y=150.0,
            width=279.0,
            height=40.0
        )

        self.copy_button_image = tk.PhotoImage(
            file=relative_to_assets("add_friend_copy_button.png"))
        copy_button = tk.Button(
            self,
            image=self.copy_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.copy_user_id_to_clipboard(),
            relief="flat"
        )
        copy_button.place(
            x=352.0,
            y=63.0,
            width=105.0,
            height=42.0
        )

        self.add_friend_submit_button_image = tk.PhotoImage(
            file=relative_to_assets("add_friend_submit_button.png"))
        add_friend_submit_button = tk.Button(
            self,
            image=self.add_friend_submit_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.send_friend_request(),
            relief="flat"
        )
        add_friend_submit_button.place(
            x=352.0,
            y=150.0,
            width=105.0,
            height=42.0
        )

        self.personal_friend_code = self.canvas.create_text(
            19.0,
            75.0,
            anchor="nw",
            text="",
            fill="#FFFFFF",
            font=("MontserratRoman Bold", 16 * -1)
        )

        # ----------incoming friend request area---------

        friend_request_box_header_text = self.canvas.create_text(
            31.0,
            264.0,
            anchor="nw",
            text=" Friend Requests",
            fill="#FFFFFF",
            font=("MontserratRoman Bold", 16 * -1)
        )

        self.friend_request_area = tk.Text(
            self,
            bd=0,
            bg="#2A3441",
            fg="#2A3441",
            highlightthickness=0,
            cursor='arrow',
            state='disabled'
        )

        self.friend_request_area.place(
            x=9.0,
            y=294.0,
            width=190,
            height=201
        )

        sb = tk.Scrollbar(self.friend_request_area,
                          command=self.friend_request_area.yview, width=20)
        sb.pack(side='right', fill=tk.Y)
        self.friend_request_area.configure(yscrollcommand=sb.set)
        self.incoming_request_value = tk.StringVar(self.friend_request_area)

        # accept button
        self.accept_button_image = tk.PhotoImage(
            file=relative_to_assets("add_friend_accept_button.png"))
        accept_button = tk.Button(
            self,
            image=self.accept_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.accept_friend_request(),
            relief="flat"
        )
        accept_button.place(
            x=213.0,
            y=294.0,
            width=119.23919677734375,
            height=42.0
        )

        # reject button

        self.reject_button_image = tk.PhotoImage(
            file=relative_to_assets("add_friend_reject_button.png"))
        reject_button = tk.Button(
            self,
            image=self.reject_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.reject_friend_request(),
            relief="flat"
        )
        reject_button.place(
            x=213.0,
            y=453.0,
            width=119.23919677734375,
            height=42.0
        )

        # -----------current friends area-----------

        current_friends_box_header_text = self.canvas.create_text(
            468.0,
            264.0,
            anchor="nw",
            text="Friends",
            fill="#FFFFFF",
            font=("MontserratRoman Bold", 16 * -1)
        )

        self.friend_list_area = tk.Text(
            self,
            bd=0,
            bg="#2A3441",
            fg="#2A3441",
            highlightthickness=0,
            cursor='arrow',
            state='disabled'
        )
        self.friend_list_area.place(
            x=405,
            y=294.0,
            width=190,
            height=201
        )

        sb = tk.Scrollbar(self.friend_list_area,
                          command=self.friend_list_area.yview, width=20)
        sb.pack(side='right', fill=tk.Y)
        self.friend_list_area.configure(yscrollcommand=sb.set)
        self.friend_list_value = tk.StringVar(self.friend_list_area)

        # block button
        self.add_friend_block_button_image = tk.PhotoImage(
            file=relative_to_assets("add_friend_block_button.png"))
        add_friend_block_button = tk.Button(
            self,
            image=self.add_friend_block_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.block_friend(),
            relief="flat"
        )
        add_friend_block_button.place(
            x=609.0,
            y=294.0,
            width=119.23919677734375,
            height=42.0
        )

        # unblock button

        self.add_friend_unblock_button_image = tk.PhotoImage(
            file=relative_to_assets("add_friend_unblock_button.png"))
        add_friend_unblock_button = tk.Button(
            self,
            image=self.add_friend_unblock_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.unblock_friend(),
            relief="flat"
        )
        add_friend_unblock_button.place(
            x=609.0,
            y=450.0,
            width=119.23919677734375,
            height=42.0
        )

        # outgoing friend requests

        pending_friend_request_box_header = self.canvas.create_text(
            505.0,
            38.0,
            anchor="nw",
            text="Pending",
            fill="#FFFFFF",
            font=("MontserratRoman Bold", 16 * -1)
        )

        self.pending_friends_area = tk.Text(
            self,
            bd=0,
            bg="#2A3441",
            fg="#2A3441",
            highlightthickness=0,
            cursor='arrow',
            state='disabled'
        )
        self.pending_friends_area.place(
            x=474,
            y=63.0,
            width=135,
            height=145
        )

        pending_friend_scrollbar = tk.Scrollbar(self.pending_friends_area,
                                                command=self.pending_friends_area.yview, width=20)
        pending_friend_scrollbar.pack(side='right', fill=tk.Y)
        self.pending_friends_area.configure(
            yscrollcommand=pending_friend_scrollbar.set)

    def send_friend_request(self):
        friend_code = self.friends_friend_code_entry.get()
        self.canvas.itemconfig(self.friend_code_error_message, state='hidden')
        self.canvas.itemconfig(self.friend_code_error_message, fill='#FF4747')

        if friend_code == '' or friend_code == self.client.user_id:
            self.canvas.itemconfig(
                self.friend_code_error_message, text='Please enter a valid friend code')
            self.canvas.itemconfig(
                self.friend_code_error_message, state='normal')
        elif self.client.check_if_user_is_already_friends(friend_code):
            self.canvas.itemconfig(
                self.friend_code_error_message, text='You are already friends with this person')
            self.canvas.itemconfig(
                self.friend_code_error_message, state='normal')
        elif not self.client.check_if_friend_code_exists(friend_code):
            self.canvas.itemconfig(self.friend_code_error_message,
                                   text='Friend code does not exist. Please enter a valid friend code')
            self.canvas.itemconfig(
                self.friend_code_error_message, state='normal')
        else:
            self.canvas.itemconfig(self.friend_code_error_message,
                                   text='Friend Request Sent')
            self.canvas.itemconfig(
                self.friend_code_error_message, fill='#FFFFFF')
            self.canvas.itemconfig(
                self.friend_code_error_message, state='normal')
            self.client.send_friend_request(friend_code)

    def add_text(self):
        self.canvas.itemconfig(self.personal_friend_code,
                               text=self.client.user_id)

    def copy_user_id_to_clipboard(self):
        t = tk.Tk()
        t.withdraw()
        t.clipboard_clear()
        t.clipboard_append(self.client.user_id)
        t.update()  # now it stays on the clipboard after the window is closed
        t.destroy()

    def add_radio_buttons(self):
        self.create_friend_list()
        self.create_friend_requests_list()
        self.create_pending_friends_list()

    def create_friend_list(self):
        for friend in self.client.friend_list:
            friend_screen_name = friend[2]
            friend_details = friend[0:2]
            status = friend[3]
            specifier_id = friend[4]
            self.add_friend_radiobutton_to_ui(
                friend_screen_name, friend_details, status, specifier_id)

    def add_friend_radiobutton_to_ui(self, txt, val, status, specifier_id):
        state = 'normal'
        colour = '#2A3441'
        active = '#12161C'
        if status == 'blk' and specifier_id == self.client.user_id:  # you have blocked them
            colour = '#FF4747'
            active = '#612a2a'
        elif (status == 'blk' and specifier_id != self.client.user_id) or ('deleted account' in txt):  # they have blocked you
            state = 'disabled'

        btn = tk.Radiobutton(self.friend_list_area,
                             text=txt,
                             variable=self.friend_list_value,
                             value=val,
                             indicatoron=0,
                             bg=colour,
                             height=2,
                             width=23,
                             relief='flat',
                             fg='#E3E7ED',
                             selectcolor=active,
                             command=lambda: self.set_active_button_value(btn),
                             borderwidth=0,
                             font=("MontserratRoman", 9, 'normal'),
                             state=state
                             )

        self.friend_list_area.window_create('end', window=btn)
        self.friend_list_area.insert('end', '\n')

    def create_friend_requests_list(self):
        for request in self.client.friend_request_list:
            print(request)
            friend_user_id = request[0]
            friend_details = request[0:1]
            self.add_friend_request_radiobutton_to_ui(
                friend_user_id, friend_details)

    def update_friend_request_list(self, friend_user_id, friend_public_key):
        friend_details = (friend_user_id, friend_public_key)
        self.add_friend_request_radiobutton_to_ui(
            friend_user_id, friend_details)

    def add_friend_request_radiobutton_to_ui(self, txt, val):

        btn = tk.Radiobutton(self.friend_request_area,
                             text=txt,
                             variable=self.incoming_request_value,
                             value=val,
                             indicatoron=0,
                             bg='#2A3441',
                             height=2,
                             width=23,
                             relief='flat',
                             fg='#E3E7ED',
                             selectcolor='#12161C',
                             command=lambda: self.set_active_friend_request_button_value(
                                 btn),
                             borderwidth=0,
                             font=("MontserratRoman", 9, 'normal')
                             )

        self.friend_request_area.window_create('end', window=btn)
        self.friend_request_area.insert('end', '\n')

    def set_active_friend_request_button_value(self, btn):
        self.active_request_button = btn

    def set_active_button_value(self, btn):
        self.active_friend_button = btn

    def block_friend(self):
        if self.active_friend_button.cget('bg') != '#FF4747':
            self.active_friend_button.config(bg='#FF4747')
            self.active_friend_button.config(selectcolor='#1c1212')
            self.client.block_friend(
                self.friend_list_value.get().split(' ')[0])
        else:
            print('User already blocked')

    def unblock_friend(self):
        if self.active_friend_button.cget('bg') != '#2A3441':
            self.active_friend_button.config(bg='#2A3441')
            self.active_friend_button.config(selectcolor='#12161C')
            self.client.unblock_friend(
                self.friend_list_value.get().split(' ')[0])
        else:
            print('User already unblocked')

    def accept_friend_request(self):
        """
        - update personal database to be accepted
        - send message to client to update their own database to fit
        - delete radiobutton
        """
        friend_id = self.incoming_request_value.get().split(' ')[0]
        self.client.accept_friend_request(friend_id, self.client.user_id)
        self.active_request_button.destroy()

    def reject_friend_request(self):
        """
        - delete friend from personal database
        - semd message to client to delete their own db to fit
        - delete radiobutton
        """
        friend_id = self.incoming_request_value.get().split(' ')[0]
        self.client.reject_friend_request(friend_id)
        self.active_request_button.destroy()

    def create_pending_friends_list(self):
        for pending_request in self.client.pending_friend_list:
            friend_user_id = pending_request
            self.add_pending_friends_radiobutton_to_ui(friend_user_id)

    def update_pending_friends_list(self, friend_user_id):
        self.add_pending_friends_radiobutton_to_ui(friend_user_id)

    def add_pending_friends_radiobutton_to_ui(self, friend_user_id):
        btn = tk.Radiobutton(self.pending_friends_area,
                             text=friend_user_id,
                             indicatoron=0,
                             bg='#2A3441',
                             height=2,
                             width=15,
                             relief='flat',
                             fg='#E3E7ED',
                             selectcolor='#12161C',
                             borderwidth=0,
                             font=("MontserratRoman", 9, 'normal'),
                             state='disabled'
                             )

        self.pending_friends_area.window_create('end', window=btn)
        self.pending_friends_area.insert('end', '\n')


class SettingsPage(tk.Frame):
    def __init__(self, parent, window, client: secure_client.Client):
        self.controller = parent
        self.client = client
        tk.Frame.__init__(self, window)

    def on_show(self):
        """Function called when frame is shown"""
        self.client.stop_listen()
        self.create_and_place()
        self.add_text()

    def create_and_place(self):

        self.canvas = tk.Canvas(
            self,
            bg="#0A0C10",
            height=504,
            width=745,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )

        self.canvas.place(x=0, y=0)
        self.header_rectangle = self.canvas.create_rectangle(
            0.0,
            0.0,
            745.0,
            43.0,
            fill="#12161C",
            outline="")

        settings_header_text = self.canvas.create_text(
            16.0,
            8.0,
            anchor="nw",
            text="Settings",
            fill="#E3E7ED",
            font=("MontserratRoman Bold", 24 * -1)
        )

        # CURRENT SCREEN NAME DISPLAY
        current_screen_name_header_text = self.canvas.create_text(
            16.0,
            61.0,
            anchor="nw",
            text="Current screen name",
            fill="#E3E7ED",
            font=("MontserratRoman Bold", 24 * -1)
        )

        self.option_addcurrent_screen_name_image = tk.PhotoImage(
            file=relative_to_assets("settings_current_screen_name.png"))
        current_screen_name_bg = self.canvas.create_image(
            176.5,
            112.0,
            image=self.option_addcurrent_screen_name_image
        )
        self.current_screen_name_text = self.canvas.create_text(
            37.0,
            99.0,
            anchor="nw",
            text="",
            fill="#E3E7ED",
            font=("MontserratRoman Bold", 24 * -1)
        )

        # CHANGE SCREEN NAME DISPLAY
        change_screen_name_text = self.canvas.create_text(
            16.0,
            160.0,
            anchor="nw",
            text="Change screen name",
            fill="#E3E7ED",
            font=("MontserratRoman Bold", 24 * -1)
        )

        self.new_screen_name_entry_image = tk.PhotoImage(
            file=relative_to_assets("settings_new_screen_name_entry.png"))
        new_screen_name_entry_bg = self.canvas.create_image(
            176.5,
            213.0,
            image=self.new_screen_name_entry_image
        )

        self.new_screen_name_entry = tk.Entry(
            self,
            bd=0,
            bg="#617998",
            fg="#E3E7ED",
            highlightthickness=0,
            font=("MontserratRoman")
        )

        self.new_screen_name_entry.place(
            x=37.0,
            y=192.0,
            width=279.0,
            height=40.0
        )

        self.new_screen_name_entry.bind(
            '<Return>', lambda e: self.change_screen_name())

        # CONFIRM SCREEN NAME BUTTON DISPLAY

        self.confirm_screen_name_button_image = tk.PhotoImage(
            file=relative_to_assets("settings_confirm_screen_name_button.png"))
        confirm_screen_name_button = tk.Button(
            self,
            image=self.confirm_screen_name_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.change_screen_name(),
            relief="flat",
            activebackground='#0A0C10'
        )
        confirm_screen_name_button.place(
            x=359.0,
            y=193.0,
            width=151.0,
            height=42.0
        )

        # DELETE ACCOUNT BUTTON DISPLAY

        self.delete_account_button_image = tk.PhotoImage(
            file=relative_to_assets("settings_delete_account_button.png"))
        delete_account_button = tk.Button(
            self,
            image=self.delete_account_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=self.popup_frame,
            relief="flat",
            activebackground='#0A0C10'
        )
        delete_account_button.place(
            x=16.0,
            y=436.0,
            width=229.0,
            height=42.0
        )

        # REQUEST DATA BUTTON DISPLAY

        self.request_data_button_image = tk.PhotoImage(
            file=relative_to_assets("settings_request_data_button.png"))
        request_data_button = tk.Button(
            self,
            image=self.request_data_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.request_all_user_data(),
            relief="flat",
            activebackground='#0A0C10'
        )
        request_data_button.place(
            x=443.0,
            y=436.0,
            width=302.0,
            height=42.0
        )

        # BACK TO CHATS BUTTON DISPLAY

        self.back_to_chats_button_image = tk.PhotoImage(
            file=relative_to_assets("settings_back_to_chats_button.png"))
        back_to_chats_button = tk.Button(
            self,
            image=self.back_to_chats_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.controller.show_frame(ChatPage),
            relief="flat",
            activebackground='#0A0C10'
        )
        back_to_chats_button.place(
            x=640.0,
            y=61.0,
            width=95.0,
            height=87.0
        )
        self.error_message = self.canvas.create_text(
            16.0,
            250.0,
            anchor="nw",
            text="",
            fill="#FF4747",
            font=("MontserratRoman Bold", 20 * -1),
            state='hidden'
        )

    def add_text(self):
        self.canvas.itemconfig(
            self.current_screen_name_text, text=self.client.screen_name)

    def change_screen_name(self):
        self.canvas.itemconfig(self.error_message, state='hidden')
        if self.new_screen_name_entry.get() == self.client.screen_name:
            # if screen name is same as old screen name display error message
            self.canvas.itemconfig(self.error_message, state='normal',
                                   text='Your new screen can not be the same as your current screen name')
        elif self.new_screen_name_entry.get() == '':
            self.canvas.itemconfig(self.error_message, state='normal',
                                   text='Your new screen name can not be empty')
        elif "deleted account" in self.new_screen_name_entry.get():
            self.canvas.itemconfig(self.error_message, state='normal',
                                   text="This can't be your screen name")
        else:
            self.canvas.itemconfig(
                self.current_screen_name_text, text=self.new_screen_name_entry.get())
            self.client.change_screen_name(self.new_screen_name_entry.get())

    def request_all_user_data(self):
        path = self.client.get_output_path()
        if not path:
            # tk.messagebox.showerror(
            #     title="Invalid Path!", message="Enter a valid output path.")
            return
        output_path = Path(f"{path}/user_data_dump.txt").expanduser().resolve()
        if output_path.exists():
            response = tk1.askyesno(
                "Continue?",
                f"Directory {path} already contains user_data_dump.txt\n"
                "Do you want to continue and overwrite?")
            if not response:  # they said no
                return
        print('[Requesting user data]')
        user_data = self.client.request_all_user_data()
        try:
            output_file = open(output_path, 'w')
            output_file.write(user_data)
            tk.messagebox.showinfo(
                "Success!", f"User data successfully saved at {output_path}")
        except:
            tk.messagebox.showerror(
                title="Error", message=f"Something went wrong when writing to {output_path}")

    # POPUP FRAME FUNCTIONS

    def popup_frame(self):
        top = tk.Toplevel(self.controller)
        top.protocol("WM_DELETE_WINDOW", self.popup_frame_error)
        self.controller.protocol("WM_DELETE_WINDOW", self.popup_frame_error)
        top.geometry("479x375")
        top.resizable(False, False)
        top.title("Confirm account deletion")
        self.disable_all_buttons()

        popup_canvas = tk.Canvas(
            top,
            bg="#0A0C10",
            height=375,
            width=479,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )

        popup_canvas.place(x=0, y=0)
        warning_header_text = popup_canvas.create_text(
            58.0,
            14.0,
            anchor="nw",
            text="Are you sure you want to \n   delete your account?",
            fill="#FF4747",
            font=("MontserratRoman Bold", 32 * -1)
        )

        self.yes_button_image = tk.PhotoImage(
            file=relative_to_assets("confirmation_popup_yes.png"))
        yes_button = tk.Button(
            top,
            image=self.yes_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.yes_button_clicked(top),
            relief="flat",
            activebackground='#2A3441'
        )
        yes_button.place(
            x=57.0,
            y=164.0,
            width=139.0,
            height=48.0
        )

        self.no_button_image = tk.PhotoImage(
            file=relative_to_assets("confirmation_popup_no.png"))
        no_button = tk.Button(
            top,
            image=self.no_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.no_button_clicked(top),
            relief="flat",
            activebackground='#2A3441'
        )
        no_button.place(
            x=279.0,
            y=163.0,
            width=139.0,
            height=50.0
        )

    def popup_frame_error(self):
        tk.messagebox.showerror('Error', 'Please select either yes or no')

    def no_button_clicked(self, top):
        top.destroy()
        self.controller.protocol("WM_DELETE_WINDOW", self.controller.on_close)
        self.enable_all_buttons()

    def yes_button_clicked(self, top):
        print('[DELETING ACCOUNT]')
        if self.client.delete_account():
            self.controller.on_close(True)
        else:
            tk.messagebox.showerror(
                title="Account Deletion Error", message="Something went wrong when deleting your account please try again later")
            self.controller.protocol(
                "WM_DELETE_WINDOW", self.controller.on_close)
            self.enable_all_buttons()

    def disable_all_buttons(self):
        for widget in self.winfo_children():
            if isinstance(widget, tk.Button):
                try:
                    widget.config(state='disabled')
                except Exception as e:
                    print(e)

    def enable_all_buttons(self):
        for widget in self.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state='normal')


# Driver Code
app = UIController()
app.resizable(False, False)
app.protocol("WM_DELETE_WINDOW", app.on_close)
app.mainloop()
