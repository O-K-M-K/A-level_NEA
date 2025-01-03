# Cryptography imports
import secrets
import rsa

# socket imports
from neat_networking_protocols import BaseClass
# from netrworkingProtocols import BaseClass
import socket

# file handling and database imports
from tkinter import filedialog
import serverDatabase
from PIL import Image
import os

# hashing imports
from hashlib import md5  # used in secret keeping NOT for password hashing

import threading


HEADER = 2048  # used for send message protocol
PORT = 65432  # TCP/UDP packets
FORMAT = 'utf-8'
SERVER = "192.168.56.1"
ADDR = (SERVER, PORT)
CLIENT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


class Client(BaseClass):
    def __init__(self, cs='CLIENT', client=CLIENT, addr=ADDR):
        super().__init__(cs, client, addr)
        self.client = client
        self.sql = None

        self.server_public_key = None
        self.public_key = None
        self.private_key = None
        self.master_key = None
        self.password_hash = None  # used for locally storing sensative data

        self.user_path = None
        self.image_path = None
        self.image_name_and_format = None
        self.user_id = ''
        self.screen_name = ''

        self.friend_list = None
        self.friend_request_list = None
        self.pending_friend_list = None
        self.current_message_history = []

        self.connected = False
        self.logged_in = False

        self.can_recieve_msg = False
        self.listen_thread = None
        self.stop_event = threading.Event()

        self.ChatPage = None
        self.AddFriendPage = None

        print('[CLIENT INSTANCE CREATED]')

    def connect(self) -> bool:
        """
        Attemps to connect to the server specified in the ADDR variable. 

        Returns:
            - True if connection sucsessful
            - False if not 
        """

        print("[ATTEMPTING TO CONNECT TO SERVER]")
        try:
            self.client.connect(ADDR)
            self.connected = True
        except Exception as e:
            print(f"[ERROR] Client was unable to connect to server: {ADDR}")
            self.connected = False
        print(f"[CONNECTED] {self.connected}")
        return self.connected

    def establish_inital_contact(self):
        """establishes initial contact with the server by generating public and private keys and swapping them"""
        print(f"[establish_inital_contact STARTED]")
        self.generate_init_keys()
        self.swap_public_keys()
        print(f"[establish_inital_contact FINISHED]")

    def send_disconnect_message(self):
        print("[SENDING DISCONNECT MESSAGE]")
        if self.logged_in:
            self.send_encrypted_data_to_server({'type': 'DISCONNECT'})
        else:
            self.send_data_to_server({'type': 'DISCONNECT'})
        print("[DISCONNECTED FROM SERVER]")

    def close_client(self):
        print('[CLOSING CLIENT]')
        self.client.close()

    def connect_to_database(self):
        """Creates and or connects to database in self.user_path"""
        db_path = os.path.join(self.user_path, 'user_data.db')
        self.sql = serverDatabase.Database(db_path)

    def close_db_connection(self):
        if self.logged_in:
            print('[CLOSING DATABASE]')
            self.sql.close_connection()

    def send_data_to_server(self, data):
        """Sends data to server autofilling public and private key parameter"""
        self.send_data(data,
                       self.private_key, self.public_key)

    def send_encrypted_data_to_server(self, data: dict):
        """Creates Epk and sends encrypted data to server"""
        print(f"[SENDING ENCRYPTED DATA TO SERVER] {data}")
        Epk = secrets.token_bytes(16)

        self.send_encrypted_data(
            data, Epk, self.private_key, self.public_key, self.server_public_key, 'server')

    def recieve_encrypted_data_from_server(self):
        """returns decrypted recieved data from server autofilling private key parameter"""
        return self.recieve_encrypted_data(self.private_key)[1]

    def send_encrypted_data_to_recipient(self, data, recipient_user_id, return_confg_data=False):
        """Creates Epk, gets recipients private key and sends data to server to forward to recipient"""
        print(f"[SENDING ENCRYTED DATA TO {recipient_user_id}] {data}")
        Epk = secrets.token_bytes(16)

        data['sender'] = self.user_id
        data['public_key'] = self.public_key

        # getting recipient public key from server
        self.send_encrypted_data_to_server(
            {'type': 'get_recipient_public_key',
             'recipient_user_id': recipient_user_id}
        )
        seralised_recipinet_public_key = self.recieve_encrypted_data_from_server()[
            'recipient_public_key']
        recipinet_public_key = self.deserialize_object(
            seralised_recipinet_public_key)

        encrypted_message = self.send_encrypted_data(
            data, Epk, self.private_key, self.public_key, recipinet_public_key, 'client', return_confg_data, recipient_user_id)

        if return_confg_data:
            return Epk

    # --------CREATE/LOGIN/DELETE ACCOUNT ----------

    def login(self, user_id: str, password: str):
        print("[ATTEMPING TO LOGIN]")
        login = False

        self.send_data_to_server({'type': 'login request'})
        self.send_encrypted_data_to_server(
            {'user_id': user_id, 'password': password})

        if self.recieve_encrypted_data_from_server()['valid_password']:
            login = True
            self.user_id = user_id
            self.password_hash = md5(password.encode()).digest()
            self.user_path = os.path.join('App./Users./', user_id)
            self.user_images_path = os.path.join(self.user_path, 'images')
            self.connect_to_database()
            self.get_keys_from_file()
            self.swap_public_keys()
        print(f"[LOGIN {login}]")
        return login

    def create_account(self, user_id: str, password: str, screen_name: str):
        print(f"[HANDELING create_account STARTED]")
        print(f"[VALIDATING ACCOUNT CREATION DETAILS]")

        valid_user_id = False
        account_created = False

        self.send_data_to_server({'type': 'create account request'})
        self.send_encrypted_data_to_server(
            {'user_id': user_id, 'recipient': 'SERVER'})

        if not self.recieve_encrypted_data_from_server()['user_id_already_used']:
            valid_user_id = True
            # user ID is unique therefore try to create account then send details to server
            self.password_hash = md5(password.encode()).digest()

            self.user_path = os.path.join('App./Users./', user_id)
            self.user_images_path = os.path.join(self.user_path, 'images')
            try:  # if new user
                os.makedirs(self.user_images_path)
                self.write_keys_to_file()
                self.connect_to_database()
                self.sql.client_tables()

                self.send_encrypted_data_to_server(
                    {'user_id': user_id, 'password': password, 'screen_name': screen_name})

                if self.recieve_encrypted_data_from_server()['account created']:
                    account_created = True
            except:  # if user already exists locally - should never occur
                print(f"[ERROR] User: {user_id} already exists")
                valid_user_id = False

        print(f"[HANDELING create_account FINISHED]")
        if valid_user_id and account_created:
            self.user_id = user_id
            self.swap_public_keys()
        return valid_user_id, account_created

    def delete_account(self):
        """
        Sends account deletion notification to server and all friends

        Returns if it was sucsessful or not
        """
        account_deleted = False
        self.send_encrypted_data_to_server({'type': 'deleting_account'})
        details = self.recieve_encrypted_data_from_server()
        if details['account_deleted']:

            account_deleted = True
            friend_user_ids = self.sql.get_all_acc_friends_user_ids()
            flat_friend_user_id = [
                id for tuple in friend_user_ids for id in tuple]
            for friend_id in flat_friend_user_id:
                self.send_encrypted_data_to_recipient(
                    {'type': 'sync_account_deletion', 'account_deletion_name': details['account_deletion_name']}, friend_id)
        return account_deleted

    def delete_directory(self):
        """Deletes everything in the users account directory and then the directory itself"""
        print("[DELETING ACCOUNT]")
        for filename in os.listdir(self.user_path):
            if os.path.isfile(os.path.join(self.user_path, filename)):
                os.remove(os.path.join(self.user_path, filename))
        for filename in os.listdir(self.user_images_path):
            if os.path.isfile(os.path.join(self.user_images_path, filename)):
                os.remove(os.path.join(self.user_images_path, filename))
        os.rmdir(self.user_images_path)
        os.rmdir(self.user_path)

    # -------PUBLIC AND PRIVATE KEYS-------

    def generate_init_keys(self):
        """Generates the clients public, private and master keys"""
        self.public_key, self.private_key = rsa.newkeys(512)
        self.master_key = secrets.token_bytes(16)

    def write_keys_to_file(self):
        """Writes clients public, private and master keys to local file in self.user_path"""

        # Encrypting and seralizing keys
        seralized_private_key = self.serialize_object(
            self.private_key).encode()
        key_data = {
            'public_key': self.public_key,
            'private_key': self.encrypt(seralized_private_key, self.password_hash),
            'master_key': self.encrypt(self.master_key, self.password_hash)
        }
        seralized_key_data = self.serialize_dict(key_data)

        with open(os.path.join(self.user_path, 'keys.txt'), 'wb') as keys:
            keys.write(seralized_key_data)

    def get_keys_from_file(self):
        """Retrieves clients public, private and master keys from local file in self.user_path"""

        # Reading data from file
        with open(os.path.join(self.user_path, 'keys.txt'), 'rb') as keys:
            seralized_key_data = keys.read()

        # Decrypting and deseralizing keys
        key_data = self.deserialize_dict(seralized_key_data)
        self.public_key = key_data['public_key']
        self.master_key = self.decrypt(
            key_data['master_key'], self.password_hash)
        seralized_private_key = self.decrypt(
            key_data['private_key'], self.password_hash).decode()
        self.private_key = self.deserialize_object(seralized_private_key)

    def swap_public_keys(self):
        """sends public key to server and recieves servers public key"""
        self.send_data_to_server(
            {'recipient': 'server', 'public_key': self.public_key})
        self.server_public_key = self.receive_data()['public_key']

    # -------GETTING FRIENDS LISTS-------

    def get_friend_list(self):
        """Sets self.friend_list to equal users friend list"""
        self.friend_list = self.sql.get_friend_list()

    def get_friend_request_list(self):
        """Sets self.friend_request_list = list of incoming friend requests"""
        self.friend_request_list = self.sql.get_friend_request_list(
            self.user_id)

    def get_pending_friends_list(self):
        """Sets self.pending_friend_list = list of outgoing friend requests"""
        self.pending_friend_list = self.sql.get_pending_friends_list(
            self.user_id)
        print(self.pending_friend_list)

    # -------LISTEN FOR MESSAGES-------

    def handel_logged_in_client(self):
        self.logged_in = True
        self.screen_name = self.receive_data()['screen_name']

    def listen(self):
        """Send message to server saying it can listen and starts the listening thread"""
        self.can_recieve_msg = True
        self.send_encrypted_data_to_server(
            {'type': 'can_recieve_msg_value', 'can_recieve_msg': self.can_recieve_msg})

        self.stop_event.clear()
        self.listen_thread = threading.Thread(
            target=self.recieving_data_from_client)
        self.listen_thread.start()

    def stop_listen(self):
        """Send message to server saying it can't listen and stops the listening thread"""
        try:
            self.can_recieve_msg = False
            self.send_encrypted_data_to_server(
                {'type': 'can_recieve_msg_value', 'can_recieve_msg': self.can_recieve_msg})

            self.stop_event.set()
            self.listen_thread.join()
            print('STOP Listen')
        except Exception as e:
            print(e)
            pass

    def recieving_data_from_client(self):
        while not self.stop_event.is_set():
            try:
                self.client.settimeout(2)
                # 2 will also be the delay time when stopping the thread
                total_data = self.recieve_encrypted_data(
                    self.private_key, False, True)
                recieved_data = total_data[1]
                Epk = total_data[2]
                if recieved_data['type'] == 'friend_request':
                    seralized_public_key = self.serialize_object(
                        recieved_data['public_key'])
                    self.sql.add_new_friend_request(
                        recieved_data['sender'], recieved_data['screen_name'], seralized_public_key, recieved_data['sender'])
                    self.get_friend_request_list()
                elif recieved_data['type'] == 'accepted_friend_request':
                    self.sql.accept_friend_request(
                        recieved_data['sender'], recieved_data['sender'])
                    self.get_friend_list()
                    self.ChatPage.update_friend_list()
                elif recieved_data['type'] == 'rejected_friend_request':
                    self.sql.reject_friend_request(recieved_data['sender'])
                    self.get_friend_list()
                elif recieved_data['type'] == 'blocked':
                    self.sql.new_blocked_friend(
                        recieved_data['sender'], recieved_data['sender'])
                    self.get_friend_list()
                    self.ChatPage.update_friend_list()
                elif recieved_data['type'] == 'unblocked':
                    self.sql.unblocked_friend(
                        recieved_data['sender'], recieved_data['sender'])
                    self.get_friend_list()
                    self.ChatPage.update_friend_list()
                elif recieved_data['type'] == 'sync_new_screen_name':
                    new_friends_screen_name = recieved_data['new_screen_name']
                    friend_id = recieved_data['sender']
                    self.sql.update_friend_screen_name(
                        friend_id, new_friends_screen_name)
                elif recieved_data['type'] == 'sync_account_deletion':
                    account_deletion_name = recieved_data['account_deletion_name']
                    friend_id = recieved_data['sender']
                    self.sql.friend_deleted_account(
                        friend_id, account_deletion_name)
                elif recieved_data['type'] == 'message':
                    self.handel_recieved_message(recieved_data, Epk)

            except socket.timeout:
                continue

    # -------SENDING/RECIEVING MESSAGES-------

    def handel_send_message(self, data: dict):
        """Sends message to server and then stores it"""
        print("[SENDING MESSAGE]")
        self.stop_listen()
        Epk = self.send_encrypted_data_to_recipient(
            data, data['recipient'], True)
        message = data['message']
        is_image = 0
        if data['is_image']:
            message = self.store_sent_image_to_files(self.image_path)
            is_image = 1

        self.store_sent_message(
            data, Epk, self.encrypt(message.encode(), Epk), is_image)
        self.listen()

    def handel_recieved_message(self, data: dict, Epk: bytes):
        """Handels recieved message accordingly if it is text or an image"""
        message = data['message']

        if data['is_image']:
            image_data = data['message']
            image_name_and_format = data['image_name_and_format']
            message = self.store_image_to_files(
                image_name_and_format, image_data)
            self.image_path = message

        message = message.encode()
        encrypted_message = self.encrypt(message, Epk)
        self.store_recieved_message(data, Epk, encrypted_message)

        # message_details = (x, x, x ,x from_me, is_image)
        message_details = (
            Epk, encrypted_message, data['date'], data['time'], 0, data['is_image'])
        message = self.decrypt_message(message_details, False)

        # if chat related recieved message is open display it
        if data['sender'] == self.ChatPage.active_chat_user_details.get().split(' ')[0]:
            formatted_message = self.ChatPage.format_stored_message_for_display(
                message)
            self.ChatPage.display_message(formatted_message)

    def decrypt_message(self, message_details, Epk_encrypted=True):
        """Returns tuple (decrypted_message, date, time, from_me, is_image)"""
        Epk = message_details[0]
        encrypted_message = message_details[1]
        date = message_details[2]
        time = message_details[3]
        from_me = message_details[4]
        is_image = message_details[5]

        if Epk_encrypted:
            Epk = self.decrypt(Epk, self.master_key)

        decrypted_message = self.decrypt(encrypted_message, Epk).decode()
        return (decrypted_message, date, time, from_me, is_image)

    def store_sent_message(self, data: dict, Epk: bytes, encrypted_message: bytes, is_image: int):
        """Stores sent message encrypting the Epk with self.master_key"""
        encrypted_Epk = self.encrypt(Epk, self.master_key)
        self.sql.store_message(
            data['recipient'], encrypted_Epk, encrypted_message, data['date'], data['time'], 1, is_image)

    def store_recieved_message(self, data: dict, Epk: bytes, encrypted_message: bytes):
        """Stores recieved message encrypting the Epk with self.master_key"""
        encrypted_Epk = self.encrypt(Epk, self.master_key)
        self.sql.store_message(
            data['sender'], encrypted_Epk, encrypted_message, data['date'], data['time'], 0, data['is_image'])

    def get_message_history(self, friend_id: str):
        return self.sql.get_message_list(friend_id)

    def decrypt_message_history(self, friend_id: str):
        self.current_message_history = []
        encrypted_message_history = self.get_message_history(friend_id)

        for message_details in encrypted_message_history:
            values = self.decrypt_message(message_details)
            self.current_message_history.append(values[:])

    # -------Add Friend Page fuctions-------

    def block_friend(self, friend_user_id):
        self.sql.new_blocked_friend(self.user_id, friend_user_id)
        self.send_encrypted_data_to_recipient(
            {'type': 'blocked'}, friend_user_id)

    def unblock_friend(self, friend_user_id):
        self.sql.unblocked_friend(self.user_id, friend_user_id)
        self.send_encrypted_data_to_recipient(
            {'type': 'unblocked'}, friend_user_id)

    def accept_friend_request(self, friend_id: str, specifier_id: str):
        self.sql.accept_friend_request(friend_id, specifier_id)
        self.send_encrypted_data_to_recipient(
            {'type': 'accepted_friend_request',
             'friend_id': self.user_id
             }, friend_id)

    def reject_friend_request(self, friend_id: str):
        self.sql.reject_friend_request(friend_id)
        self.send_encrypted_data_to_recipient(
            {'type': 'rejected_friend_request',
             'friend_id': self.user_id
             }, friend_id)

    def send_friend_request(self, friend_user_id: str):
        self.send_encrypted_data_to_recipient(
            {'type': 'friend_request',
             'screen_name': self.screen_name
             }, friend_user_id)
        self.store_friend_request(friend_user_id)
        self.AddFriendPage.update_pending_friends_list(friend_user_id)

    def store_friend_request(self, friend_user_id: str):
        """Gets friend details from server for an accepted friend request and stores them"""
        self.send_encrypted_data_to_server(
            {'type': 'get_friend_detials', 'friend_user_id': friend_user_id})
        details = self.recieve_encrypted_data_from_server()
        self.sql.add_new_friend_request(
            friend_user_id, details['screen_name'], details['public_key'], self.user_id)

    def check_if_user_is_already_friends(self, friend_user_id: str):
        already_friends = True
        friend_count = self.sql.check_if_user_is_already_friends(
            friend_user_id)
        if friend_count == 0:
            already_friends = False
        return already_friends

    def check_if_friend_code_exists(self, freind_user_id: str) -> bool:
        self.send_encrypted_data_to_server(
            {'type': 'check_if_friend_code_exists', 'friend_code': freind_user_id})
        return self.recieve_encrypted_data_from_server()['exist']

    # -------SENDING IMAGES-------

    def get_image_data(self, image_path: str):
        """Returns binary data of image at image_path"""
        image_file = open(image_path, 'rb')
        return image_file.read()

    def store_sent_image_to_files(self, image_path: str):
        """
        Gets sent image sent image path and then stores it

        Returns stored image path
        """
        image_name_and_format = image_path.split('/')[-1]

        image_file = open(image_path, 'rb')

        image_data = image_file.read()
        return self.store_image_to_files(image_name_and_format, image_data)

    def store_image_to_files(self, image_name_and_format, image_data):
        """Stores image to self.user_images_path"""
        new_image_path = self.find_sutable_image_path(image_name_and_format)
        new_image_file = open(new_image_path, 'wb')
        new_image_file.write(image_data)
        return new_image_path

    def find_sutable_image_path(self, image_name_and_format: str):
        """
        Finds sutable image name by adding (i) if there are duplicates

        Returns full image path 
        """
        counter = 0
        image_path = os.path.join(self.user_images_path, image_name_and_format)
        path_name, extention = os.path.splitext(image_path)

        base_path = f"{path_name}({counter}){extention}"
        while os.path.isfile(base_path):
            counter += 1
            base_path = f"{path_name}({counter}){extention}"
        return base_path

    def compress_image(self, image_path: str):
        """
        Compresses an image to:
            - max 100px,100px 
            - LANCZOS resampling
            - save quality: 65%

        Returns new image path
           """
        old_path, extension = os.path.splitext(image_path)
        file_name = old_path.split('/')[-1]
        split_path = image_path.split('/')[:-1]
        new_path = f"{'/'.join(split_path)}/{file_name}(downsized_for_encryption){extension}"

        image = Image.open(image_path)
        image.thumbnail((100, 100), Image.Resampling.LANCZOS)
        image.save(new_path, optimize=True, quality=65)
        return new_path

    def client_get_image_path(self):
        """
        Displays popup asking user to select an image file

        Returns selected image path
        """

        image_path = filedialog.askopenfilename(initialdir="/downloads",
                                                title="Select Image",
                                                filetypes=(("jpeg files", "*.jpeg"), ("png files", "*.png")))
        if not image_path:  # if user cancels on file explorer
            return False

        self.image_path = self.compress_image(image_path)
        self.image_name_and_format = self.image_path.split('/')[-1]

        return self.image_path

    # -------ACCOUNT MODIFICATION-------

    def change_screen_name(self, new_screen_name):
        """Notifys the server of screen name change"""
        self.screen_name = new_screen_name
        self.send_encrypted_data_to_server(
            {'type': 'change_screen_name', 'new_screen_name': self.screen_name})

        friend_user_ids = self.sql.get_all_acc_friends_user_ids()

        # flatten list
        flat_friend_user_id = [id for tuple in friend_user_ids for id in tuple]
        for friend_id in flat_friend_user_id:
            self.send_encrypted_data_to_recipient(
                {'type': 'sync_new_screen_name', 'new_screen_name': self.screen_name}, friend_id)

    def request_all_user_data(self):
        """Returns all data server has on user"""
        self.send_encrypted_data_to_server({'type': 'request_all_user_data'})
        user_details = self.recieve_encrypted_data_from_server()[
            'user_details']
        return f"user_id: {user_details[0]}\nscreen_name{user_details[1]}\nseralized_public_key: {user_details[2]}"

    def get_output_path(self):
        """Returns chosen path to save user data"""
        output_path = filedialog.askdirectory(
            title="Select place to save data")
        return output_path
