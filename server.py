
from netrworkingProtocols import BaseClass
from netrworkingProtocols import ClientDisconnectException
import socket
import threading
import rsa
import serverDatabase
import bcrypt
import hmac
import hashlib
import keyring
import secrets

"""
NOTES

MAX password length is 72 bytes
"""

HEADER = 2048  # make bigger if new message is needed
PORT = 65432  # TCP/UDP packets

SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'

active_clients = []
logged_in_clients = []
server_public_key, server_private_key = rsa.newkeys(512)

database = r"C:\Users\orank\OneDrive\Desktop\Computer Science\A-level NEA\OrganisedServerCode\serverDB.db"
sql = serverDatabase.Database(database)
sql.server_tables()


class UserHandler(BaseClass):
    def __init__(self, type: str, client, addr):
        super().__init__(type, client, addr)

        active_clients.append(self)
        self.client_public_key = None
        self.client_user_id = None
        self.can_recieve_msg = False

        print(f"\n[NEW CONNECTION] {self.addr[0], self.addr[1]} connected.")
        print(f"[TOTAL CONNECTIONS] {len(active_clients)}\n")

    def get_name(self):
        """Returns ip, port and client userID"""
        return f"{self.addr[0], self.addr[1], {self.client_user_id}}"

    def handel_disconnect(self):
        """Removes self from list of active clients and closes connection"""
        active_clients.remove(self)
        self.client.close()
        print(
            f'[CLIENT DISCONNECTED] {self.addr[0], self.addr[1]}')
        print(f"[TOTAL CONNECTIONS] {len(active_clients)}\n")

    # ------SENDING AND RECIEVING DATA------

    def send_data_to_client(self, data: dict):
        """Sends data to client autofilling public and private key arguments"""
        self.send_data(data,
                       server_private_key, server_public_key)

    def send_encrypted_data_to_client(self, data: dict):
        """Sends encrypted data to client autofilling nessesary arguments"""
        Epk = secrets.token_bytes(16)  # Epk is unique to each new message

        self.send_encrypted_data(
            data, Epk, server_private_key, server_public_key, self.client_public_key, 'client')

    def recieve_encrypted_data_from_client(self):
        """Returns the recieved encrypted data from client autofilling Private Key argument"""
        return self.recieve_encrypted_data(server_private_key)[1]

    # ------HANDELING FUNCTIONS------

    def handel(self):
        """Runs the inital functions to handel the first contact between a client and a server"""
        self.handel_inital_contact()
        self.handle_logged_out_client()

    def handel_inital_contact(self):  # maybe redundant check
        print(f"[handel_inital_contact STARTED]{'-' * 40}")
        self.swap_public_keys()
        print(f"[handel_inital_contact FINISHED]{'-' * 40}")

    def swap_public_keys(self):
        """Swaps public keys with the client setting self.client_public_key in the process"""
        print(
            f"[PUBLIC KEY SWAP] Swapping public keys with {self.get_name()}")
        self.client_public_key = self.receive_data()['public_key']

        self.send_data_to_client(
            {'recipient': 'client', 'public_key': server_public_key})

        print(f"[PUBLIC KEY SWAP FINISHED] with {self.get_name()}\n")

    def handle_logged_in_client(self):
        # send screen_name
        self.swap_public_keys()
        screen_name = sql.get_screen_name(self.client_user_id)
        self.send_data_to_client(
            {'recipient': 'CLIENT', 'screen_name': screen_name})

        # thread = threading.Thread(target=self.recieve_data_from_logged_in_user)
        # thread.start()
        self.recieve_data_from_logged_in_user()

    def recieve_data_from_logged_in_user(self):
        """
        - server needs to know who data is mean to be going to before trying to do anything with it
        """

        # recieved_data = (for_server: bool, seralized_lump_data: dict, seralized_signature: dict)
        connected = True
        while connected:
            recieved_data = self.recieve_encrypted_data(server_private_key)
            if recieved_data[0]:  # data is for the server
                data = recieved_data[1]
                if data['type'] == 'check_if_friend_code_exists':
                    self.send_encrypted_data_to_client(
                        {'exist': sql.check_user_id_exists(data['friend_code'])})
                if data['type'] == 'get_recipient_public_key':
                    print("\n\n GETTING RECIPIENT PUB KEY \n\n")
                    seralized_public_key = sql.get_public_key(
                        data['recipient_user_id'])
                    self.send_encrypted_data_to_client(
                        {'recipient_public_key': seralized_public_key})
                if data['type'] == 'get_friend_detials':
                    self.send_encrypted_data_to_client(
                        {
                            'screen_name': sql.get_screen_name(data['friend_user_id']),
                            'public_key': sql.get_public_key(data['friend_user_id'])
                        })
                if data['type'] == 'can_recieve_msg_value':
                    self.can_recieve_msg = data['can_recieve_msg']
                    if self.can_recieve_msg:
                        self.recieved_message_queue()
            else:  # lump data is for the client!
                self.forward_data_to_client(recieved_data)

    def forward_data_to_client(self, recieved_data):
        print('forwarding data to client')
        seralized_lump_data = recieved_data[1]
        seralized_signature = recieved_data[2]
        recipient_user_id = self.deserialize_dict(seralized_lump_data)[
            'recipient_user_id']
        for client in active_clients:
            if client.client_user_id == recipient_user_id and client.can_recieve_msg == True:
                client.forward_data(seralized_lump_data, seralized_signature)
                message_queue.deQeueu(recipient_user_id, recieved_data)
            else:
                message_queue.enQueue(recipient_user_id, recieved_data)

    def recieved_message_queue(self):
        print("RECIEVING MSG QUEUE HOPEFULLY")
        for message in message_queue.get():
            if message[0] == self.client_user_id:
                message_queue.deQeueu(message[0], message[1])
                self.forward_data(message[1][1], message[1][2])

    def handle_logged_out_client(self):
        login = False
        while login != True:
            determiner = self.receive_data()
            if determiner['type'] == 'login request':
                if self.handel_login():
                    login = True
            elif determiner['type'] == 'create account request':
                if self.handel_create_account():
                    login = True
        self.handle_logged_in_client()

        # self.recieve_encrypted_data(server_private_key)
        # self.handel_create_account()
        # self.handel_login()

    def handel_login(self):

        details = self.recieve_encrypted_data_from_client()
        user_exists = sql.check_user_id_exists(details['user_id'])
        if not user_exists:  # if user does not exist
            valid_password = False
        else:
            valid_password = self.validate_login_info(
                details['user_id'], details['password'])
        if valid_password:
            self.client_user_id = details['user_id']
        self.send_encrypted_data_to_client(
            {'recipient': 'CLIENT', 'valid_password': valid_password})
        return valid_password

    def handel_create_account(self):
        print(
            f'[handel_create_account STARTED] for {self.get_name()} {"-" * 40}')

        account_created = False
        # Checking if user_id is unique
        details = self.recieve_encrypted_data_from_client()

        # check if details are unique
        user_id_already_used = sql.check_user_id_exists(details['user_id'])

        self.send_encrypted_data_to_client(
            {'recipient': 'CLIENT', 'user_id_already_used': user_id_already_used})

        if not user_id_already_used:
            # Creating account
            try:
                print("[USER DETAILS UNIQUE]")
                user_account_details = self.recieve_encrypted_data_from_client()
                self.store_user_login_details(
                    user_account_details['user_id'], user_account_details['screen_name'], user_account_details['password'])
                account_created = True
            except Exception as e:
                print(e)
            finally:
                self.send_encrypted_data_to_client(
                    {'recipient': 'CLIENT', 'account created': account_created})
                self.client_user_id = user_account_details['user_id']
            print(
                f'[handel_create_account FINISHED] for {self.get_name()} {"-" * 40}')
        return account_created

        # print(f"User ID details {details['userID'], details['password']}")

        # self.store_user_login_details(details['userID'], details['password'])

    def store_user_login_details(self, user_id, screen_name, password):
        salt = bcrypt.gensalt()
        peppered_hash = self.hash_password(password, salt)
        seralized_public_key = self.serialize_object(self.client_public_key)

        sql.add_user(user_id, screen_name, peppered_hash,
                     salt, seralized_public_key)

    def hash_password(self, password: bytes, salt: bytes) -> str:
        password = password.encode()
        hash = bcrypt.hashpw(password, salt)
        temp = hmac.new(self.get_pepper(), hash, hashlib.sha256)
        peppered_hash = temp.hexdigest()
        return peppered_hash

    def validate_login_info(self, user_id: str, password: str):
        valid_password = False
        data = sql.get_password(user_id)
        print(data)
        stored_password = data[0][0]
        salt = data[0][1]
        if self.hash_password(password, salt) == stored_password:
            valid_password = True
        return valid_password

    def get_pepper(self):
        return keyring.get_password("a_level_nea", "oran").encode()


class MessageQueue():
    def __init__(self):
        self.__items = []

    def isEmpty(self):
        return self.__items == []

    def enQueue(self, client_recieving_user_id: str, message: list):
        values = (client_recieving_user_id, message)
        self.__items.append(values)
        print(f'\n[MESSAGE ADDED TO QUEUE] {values = }\n')

    def deQeueu(self, client_recieving_user_id: str, message: list):
        if not self.isEmpty:
            values = (client_recieving_user_id, message)
            print(f'\n[MESSAGE REMOVED FROM QUEUE] {values = }\n')
            return self.__items.remove(values)

    def get(self):
        return self.__items


def worker(client, addr):
    # allows disconnect excpetion to be handeled within each new users thread rather than having to leave the thread
    new_user = UserHandler('SERVER', client, addr)
    try:
        new_user.handel()
    except ClientDisconnectException:
        new_user.handel_disconnect()


# DRIVER CODE ---------------------------------------------------------

def main():
    # create new socket object
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # bind socket to port and IP
        server.bind(ADDR)
    except:
        print(f"Unable to bind to server {SERVER} and port {PORT}")
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER} {PORT}")
    while True:
        client, addr = server.accept()  # waits till new connection
        thread = threading.Thread(target=worker, args=(client, addr))
        thread.start()


message_queue = MessageQueue()
main()
