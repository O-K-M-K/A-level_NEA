# socket imports
from neat_networking_protocols import BaseClass
from neat_networking_protocols import ClientDisconnectException
# from netrworkingProtocols import BaseClass
# from netrworkingProtocols import ClientDisconnectException
import socket

# cryptography imports
import rsa
import secrets

# password hashing imports
import bcrypt
import hmac
import hashlib
import keyring

import threading
import serverDatabase

HEADER = 2048  # make bigger if needed
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
        return f"{self.addr[0], self.addr[1], self.client_user_id}"

    def handel_disconnect(self):
        """Removes self from list of active clients and closes connection"""
        active_clients.remove(self)
        self.client.close()
        print(
            f'[CLIENT DISCONNECTED] {self.addr[0], self.addr[1], self.client_user_id}')
        print(f"[TOTAL CONNECTIONS] {len(active_clients)}\n")

    # ------SENDING AND RECEIVING DATA------

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
        """Returns the recieved decrypted data from client autofilling Private Key argument"""
        return self.recieve_encrypted_data(server_private_key)[1]

    # ------HANDLE INITIAL CONTACT FUNCTIONS------

    def handel(self):
        """Runs the inital functions to handel the first contact between a client and a server"""
        print(f"[HANDELING LOGGED OUT CLIENT {self.get_name()}]")
        self.handel_inital_contact()
        self.handle_logged_out_client()

    def handel_inital_contact(self):
        self.swap_public_keys()

    def swap_public_keys(self):
        """Swaps public keys with the client setting self.client_public_key in the process"""
        print(
            f"[PUBLIC KEY SWAP] Swapping public keys with {self.get_name()}")
        self.client_public_key = self.receive_data()['public_key']

        self.send_data_to_client(
            {'recipient': 'client', 'public_key': server_public_key})

        print(f"[PUBLIC KEY SWAP FINISHED] with {self.get_name()}\n")

    # ------HANDEL LOGGED OUT CLIENT FUNCTIONS------

    def handle_logged_out_client(self):
        """Handels logged out client by waiting to recieve a determiner specifying what the user is trying to do and calling functions appropriately"""
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

    def handel_login(self) -> bool:
        """Handels clients login attempt"""
        login_details = self.recieve_encrypted_data_from_client()
        user_exists = sql.check_user_id_exists(
            login_details['user_id'])

        if not user_exists:  # if user does not exist
            valid_password = False
        elif self.is_user_already_online(login_details['user_id']):
            valid_password = False
        else:
            valid_password = self.validate_login_info(
                login_details['user_id'], login_details['password'])

        if valid_password:
            self.client_user_id = login_details['user_id']

        self.send_encrypted_data_to_client(
            {'recipient': 'CLIENT', 'valid_password': valid_password})
        return valid_password

    def handel_create_account(self):
        """Handels clients create account attempt"""
        account_created = False

        details = self.recieve_encrypted_data_from_client()

        user_id_already_used = sql.check_user_id_exists(details['user_id'])

        self.send_encrypted_data_to_client(
            {'recipient': 'CLIENT', 'user_id_already_used': user_id_already_used})

        if not user_id_already_used:  # if user id not taken
            # Creating account
            try:
                user_account_details = self.recieve_encrypted_data_from_client()
                account_created = self.store_user_login_details(
                    user_account_details['user_id'], user_account_details['screen_name'], user_account_details['password'])
            except Exception as e:
                print(e)
            finally:
                self.send_encrypted_data_to_client(
                    {'recipient': 'CLIENT', 'account created': account_created})
                self.client_user_id = user_account_details['user_id']
            print(
                f'[ACCOUNT CREATED FOR] for {self.get_name()}')
        return account_created

    def is_user_already_online(self, user_id):
        for user in active_clients:
            if user.client_user_id == user_id:
                return True
        return False

    def store_user_login_details(self, user_id, screen_name, password):
        """Adds users id, screen name, hashed password, password salt and public key to the servers database"""
        salt = bcrypt.gensalt()  # salt generated outside function as it needs to be stored
        peppered_hash = self.hash_password(password, salt)
        seralized_public_key = self.serialize_object(
            self.client_public_key)  # sql cant store python objects

        return sql.add_user(user_id, screen_name, peppered_hash,
                            salt, seralized_public_key)

    def hash_password(self, password: bytes, salt: bytes) -> str:
        """Hashes and salts peppers password as per OWASP guidelines 2024"""
        password = password.encode()
        hash = bcrypt.hashpw(password, salt)
        temp = hmac.new(self.get_pepper(), hash, hashlib.sha256)
        peppered_hash = temp.hexdigest()
        return peppered_hash

    def validate_login_info(self, user_id: str, password: str):
        """Checks recieved password against stored hash and returns relevant bool"""
        print(f"[VALIDATING LOGIN FOR {self.get_name()}]")
        valid_password = False
        data = sql.get_password(user_id)
        stored_password = data[0][0]
        salt = data[0][1]
        if self.hash_password(password, salt) == stored_password:
            valid_password = True
        return valid_password

    def get_pepper(self):
        """Gets stored pepper from Windows Key Store"""
        return keyring.get_password("a_level_nea", "oran").encode()

    # ------HANDEL LOGGED IN CLIENT FUNCTIONS----------

    def handle_logged_in_client(self):
        print(f"[HANDELING LOGGED IN USER {self.get_name()}]")
        # second swap required to get the 'real' keys rather than the temp keys
        self.swap_public_keys()

        screen_name = sql.get_screen_name(self.client_user_id)
        self.send_data_to_client(
            {'recipient': 'CLIENT', 'screen_name': screen_name})

        self.recieve_data_from_logged_in_user()

    def recieve_data_from_logged_in_user(self):
        """Recieved encrypted data from logged in user and handels it accordingly"""

        # recieved_data = (for_server: bool, seralized_lump_data: dict, seralized_signature: dict)
        connected = True
        while connected:
            recieved_data = self.recieve_encrypted_data(server_private_key)
            if recieved_data[0]:  # data is for the server
                print(f"[RECIEVED DATA FROM {self.get_name()} FOR SERVER]")
                data = recieved_data[1]
                print(f"{data = }\n\n")

                if data['type'] == 'check_if_friend_code_exists':
                    self.send_encrypted_data_to_client(
                        {'exist': sql.check_user_id_exists(data['friend_code'])})

                if data['type'] == 'get_recipient_public_key':
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
                if data['type'] == 'request_all_user_data':
                    user_details = sql.get_user_details(self.client_user_id)
                    self.send_encrypted_data_to_client(
                        {
                            'user_details': user_details
                        }
                    )
                if data['type'] == 'deleting_account':
                    account_deleted, account_deletion_name = sql.delete_account_server(
                        self.client_user_id)
                    self.send_encrypted_data_to_client(
                        {
                            'account_deleted': account_deleted,
                            'account_deletion_name': account_deletion_name
                        }
                    )

                if data['type'] == 'change_screen_name':
                    new_screen_name = data['new_screen_name']
                    print('UPDATING SCREEN NAME')
                    sql.update_screen_name_server(
                        self.client_user_id, new_screen_name)

                if data['type'] == 'can_recieve_msg_value':
                    self.can_recieve_msg = data['can_recieve_msg']
                    if self.can_recieve_msg:
                        self.recieved_message_queue()

            else:  # lump data is for the client!
                print(f"[RECIEVED DATA FROM {self.get_name()} TO FORWARD]")
                self.forward_data_to_client(recieved_data)

    def forward_data_to_client(self, recieved_data):
        """Attempts to forward data to intended recipient. If it can't adds to the message queue instead"""
        recipient_found = False
        seralized_lump_data = recieved_data[1]
        seralized_signature = recieved_data[2]
        recipient_user_id = self.deserialize_dict(seralized_lump_data)[
            'recipient_user_id']

        for client in active_clients:
            if client.client_user_id == recipient_user_id and client.can_recieve_msg == True:
                from_message_queue = self.get_name() == client.get_name()
                print(
                    f"[FORWARDING DATA FROM {self.get_name()} TO {client.get_name()}] FROM MESSAGE QUEUE {from_message_queue}")
                client.forward_data(seralized_lump_data, seralized_signature)
                recipient_found = True
                break

        if not recipient_found:
            # adding recipient_user_id as it means deserialization is not needed for each item when searching queue
            message_queue.enQueue(recipient_user_id, recieved_data)

    def recieved_message_queue(self):
        """Sends messages waiting in message_queue to relevant client"""
        for message in message_queue.get().copy():
            if message[0] == self.client_user_id:
                message_queue.deQeueu(self.client_user_id, message[1])
                self.forward_data_to_client(message[1])


class MessageQueue():
    def __init__(self):
        self.__items = []

    def isEmpty(self):
        return len(self.__items) == 0

    def enQueue(self, client_recieving_user_id: str, message: list):
        values = (client_recieving_user_id, message)
        self.__items.append(values)

    def deQeueu(self, client_recieving_user_id: str, message: list):
        if not self.isEmpty():
            values = (client_recieving_user_id, message)
            try:
                self.__items.remove(values)
            except Exception as e:
                print(f"[deQueue ERROR] {e}")

    def get(self):
        return self.__items


def worker(client, addr):
    # allows disconnect excpetion to be handeled within each new users thread rather than having to leave the thread
    new_user = UserHandler('SERVER', client, addr)
    try:
        new_user.handel()
    except ClientDisconnectException:
        new_user.handel_disconnect()


# ------DRIVER CODE------

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
