"""
Provides a base class with generic send/recieve functions but with in built data seralization
"""
# Cryptography imports
import rsa
import class_based_aes as aes

# Data serialization imports
import json
import pickle
import base64


HEADER = 2048  # used for send message protocol
FORMAT = 'utf-8'
# PORT = 65432  # TCP/UDP packets
# SERVER = "192.168.0.30"
# ADDR = (SERVER, PORT)


class ClientDisconnectException(Exception):
    pass


class BaseClass(aes.Encrypt, aes.Decrypt):
    def __init__(self, cs: str, client, addr):
        """
        Parameters:
        - type (str): Should be either 'SERVER' or 'CLIENT'.
        - client: (socket)
        - addr: (tuple)
        """
        self.type = cs
        self.client = client
        self.addr = addr

    def validate_signature(self, seralized_data, deseralized_signature) -> bool:
        """Validates a signature for argument passed into seralized_data """
        signature = deseralized_signature['signature']
        public_key = deseralized_signature['public_key']
        valid = False
        try:
            rsa.verify(seralized_data, signature, public_key)
            valid = True
        except:
            valid = False
        finally:
            return valid

    def generate_signature(self, seralized_data: bytes, private_key, public_key) -> dict[str, bytes]:
        """
        Creates a signature for parameter passed into seralized_data. 

        Returns signature along with public key to a dict with keys: signature, public_key
        """
        a = {'signature': rsa.sign(
            seralized_data, private_key, 'SHA-1'), 'public_key': public_key}
        return a

    def add_packet_header(self, data: bytes) -> bytes:
        """Returns bytes of exactly HEADER length with the first few bytes containing the number of bytes argument data is"""
        data_length = len(data)
        send_length = str(data_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        return send_length

    def send_with_header(self, data: bytes):
        """Sends a fixed sized packet containing the number of bytes in the next packet"""
        self.client.send(self.add_packet_header(data))
        self.client.send(data)

    def receive_data_with_header(self) -> bytes:
        """Receives the header and handels relevant logic for receiving relevant data returning the json data"""
        data_length = self.client.recv(HEADER).decode(FORMAT)
        if data_length != 0:
            data_length = int(data_length)
            json_data = self.client.recv(data_length)
            return json_data

    def send_encrypted_data(self, data: dict, Epk: bytes, private_key: rsa.PrivateKey, public_key: rsa.PublicKey, recipient_public_key: rsa.PublicKey, recipient, return_message=False, *recipient_user_id):
        """
        Sends data to self.client. Seralizes and encrypts it before sending

        Parameters:
        - data (dict): data you want to send
        - Epk (bytes): One time key used for symmetrical encryption
        - private_key: SENDERS private key
        - public_key: SENDERS public key
        - recipient_public_key
        - recipient: server or client
        - *recipient_user_id: only needed if data is a message from client to client
        """

        seralized_data = self.serialize_dict(data)
        encrypted_data = self.encrypt(seralized_data, Epk)

        encrypted_Epk = rsa.encrypt(Epk, recipient_public_key)

        lump_data = {'encrypted_data': encrypted_data,
                     'encrypted_Epk': encrypted_Epk,
                     'recipient': recipient}

        if data['type'] == 'message':
            lump_data['type'] = 'message'

        if len(recipient_user_id) != 0:
            lump_data['recipient_user_id'] = recipient_user_id[0]

        seralized_lump_data = self.serialize_dict(lump_data)

        signature = self.generate_signature(
            seralized_lump_data, private_key, public_key)

        seralized_signature = self.serialize_dict(signature)

        self.send_with_header(seralized_lump_data)
        self.send_with_header(seralized_signature)

        if return_message:
            return seralized_lump_data

    def recieve_encrypted_data(self, private_key: rsa.PrivateKey, return_public_key=False, return_Epk=False):
        """Recieves encrypted data from self.client returning data + others depending on arguments"""
        seralized_lump_data = self.receive_data_with_header()
        seralized_signature = self.receive_data_with_header()

        if seralized_lump_data != 0 and seralized_signature != 0:
            lump_data = self.deserialize_dict(seralized_lump_data)
            signature = self.deserialize_dict(seralized_signature)

            # If data should NOT be forwarded
            if (self.type == 'SERVER' and lump_data['recipient'] == 'server') or (self.type == 'CLIENT' and lump_data['recipient'] == 'client'):
                if self.validate_signature(seralized_lump_data, signature):
                    encrypted_Epk = lump_data['encrypted_Epk']
                    Epk = rsa.decrypt(encrypted_Epk, private_key)

                    seralized_decrypted_data = self.decrypt(
                        lump_data['encrypted_data'], Epk)
                    data = self.deserialize_dict(seralized_decrypted_data)

                    if self.type == 'SERVER' and data['type'] == 'DISCONNECT':
                        raise ClientDisconnectException('Client Disconnected')
                else:
                    print("[+] Signature fail / message was empty")

                if return_public_key:
                    # data is for either
                    return True, data, signature['public_key']
                elif return_Epk:
                    return True, data, Epk  # data is for either
                else:
                    return True, data  # data is for either
            else:
                # data is for server to forward to another client
                return False, seralized_lump_data, seralized_signature

    def forward_data(self, seralized_data, seralized_signature):
        """Sends data without signature or encryption"""
        self.send_with_header(seralized_data)
        self.send_with_header(seralized_signature)

    def send_data(self, data: dict, private_key: rsa.PrivateKey, public_key: rsa.PublicKey):
        """
        Sends data and signature to self.client serialising  it before sending

        Parameters:
        - data: data you want to send
        - private_key: SENDERS private key
        - public_key: SENDERS public_key
        """

        seralized_data = self.serialize_dict(data)

        signature = self.generate_signature(
            seralized_data, private_key, public_key)

        seralized_signature = self.serialize_dict(signature)

        self.send_with_header(seralized_data)
        self.send_with_header(seralized_signature)

    def receive_data(self) -> dict:
        """Receives data from self.client deserializing it before returning"""
        json_data = self.receive_data_with_header()
        json_signature = self.receive_data_with_header()

        signature = self.deserialize_dict(json_signature)

        if json_data != 0 and json_signature != 0 and self.validate_signature(json_data, signature):
            data = self.deserialize_dict(json_data)
            if self.type == 'SERVER' and data['type'] == 'DISCONNECT':
                raise ClientDisconnectException('Client Disconnected')
            else:
                return data
        else:
            print("[+] Signature Invalid/Recieved Empty Mesage")

    def serialize_dict(self, data: dict) -> bytes:
        """Seralizes a dictionary and encodes it in a JSON format then encodes it """
        obj_mapping = []  # contains the keys in the dict where the value was an object
        bytes_mapping = []  # contains the keys in the dict where the value was bytes
        for key, value in data.items():
            if self.is_user_defined_class(value):
                data[key] = self.serialize_object(value)
                obj_mapping.append(key)
            elif isinstance(value, bytes):
                data[key] = self.serialize_bytes(value)
                bytes_mapping.append(key)

        # all dicts need 'type' in for sending and recieving purposes in client and server code
        if 'type' not in data:
            data['type'] = 'None'

        data['obj_mapping'] = obj_mapping
        data['bytes_mapping'] = bytes_mapping
        data = json.dumps(data)
        data = data.encode(FORMAT)
        return data

    def deserialize_dict(self, data: bytes) -> dict:
        """Turns serialised bytes into a dictionary also deserializing any objects or bytes too"""
        data = data.decode(FORMAT)
        data = json.loads(data)
        for key, value in data.items():
            if key in data['obj_mapping']:
                data[key] = self.deserialize_object(value)
            elif key in data['bytes_mapping']:
                data[key] = self.deserialize_bytes(value)
        return data

    def serialize_bytes(self, data: bytes) -> str:
        """Returns bytes encoded to base64"""
        b64 = base64.b64encode(data)
        return b64.decode(FORMAT)

    def deserialize_bytes(self, data: str) -> bytes:
        """Returns a string encoded in base64 into bytes"""
        b64 = data.encode(FORMAT)
        return base64.b64decode(b64)

    def serialize_object(self, obj: object) -> str:
        """Returns a serialised string of the object using pickle"""
        pickled_object = pickle.dumps(obj)
        string_of_object = self.serialize_bytes(pickled_object)
        return string_of_object

    def deserialize_object(self, serialized_object: str) -> object:
        """Returns an python object of the serialised_object using pickle"""
        pickled_object = self.deserialize_bytes(serialized_object)
        unpickled_object = pickle.loads(pickled_object)
        return unpickled_object

    def is_user_defined_class(self, obj: object) -> bool:
        """
        Checks if object is an in-built python object or not
        """
        # 'hacky way' of checking taken from: https://stackoverflow.com/questions/14612865/how-to-check-if-object-is-instance-of-new-style-user-defined-class
        if hasattr(obj, '__class__'):
            return (hasattr(obj, '__dict__') or hasattr(obj, '__slots__'))
