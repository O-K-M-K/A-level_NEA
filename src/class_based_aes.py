"""
An OOP approach to AES in python. 

If you are using OOP you can inherit from aes.Encrypt and aes.Decrypt 

Otherwise create instances of each class and use .encrypt() and .decrypt()
"""


# CONSTANTS
S_BOX = (
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
    0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
    0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
    0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
    0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
    0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
    0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
    0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
    0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
    0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
    0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
    0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
    0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
    0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
    0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16,
)

INVERSE_S_BOX = (
    82, 9, 106, 213, 48, 54, 165, 56, 191, 64, 163, 158, 129, 243, 215, 251, 124, 227, 57, 130, 155, 47, 255, 135, 52, 142, 67, 68, 196, 222, 233, 203, 84, 123, 148, 50, 166, 194, 35, 61, 238, 76, 149, 11, 66, 250, 195, 78, 8, 46, 161, 102, 40, 217, 36, 178, 118, 91, 162, 73, 109, 139, 209, 37, 114, 248, 246, 100, 134, 104, 152, 22, 212, 164, 92, 204, 93, 101, 182, 146, 108, 112, 72, 80, 253, 237, 185, 218, 94, 21, 70, 87, 167, 141, 157, 132, 144, 216, 171, 0, 140, 188, 211, 10, 247, 228, 88, 5, 184, 179, 69, 6, 208, 44, 30, 143, 202, 63, 15, 2, 193, 175, 189, 3, 1, 19, 138, 107, 58, 145, 17, 65, 79, 103, 220, 234, 151, 242, 207, 206, 240, 180, 230, 115, 150, 172, 116, 34, 231, 173, 53, 133, 226, 249, 55, 232, 28, 117, 223, 110, 71, 241, 26, 113, 29, 41, 197, 137, 111, 183, 98, 14, 170, 24, 190, 27, 252, 86, 62, 75, 198, 210, 121, 32, 154, 219, 192, 254, 120, 205, 90, 244, 31, 221, 168, 51, 136, 7, 199, 49, 177, 18, 16, 89, 39, 128, 236, 95, 96, 81, 127, 169, 25, 181, 74, 13, 45, 229, 122, 159, 147, 201, 156, 239, 160, 224, 59, 77, 174, 42, 245, 176, 200, 235, 187, 60, 131, 83, 153, 97, 23, 43, 4, 126, 186, 119, 214, 38, 225, 105, 20, 99, 85, 33, 12, 125
)

CONSTANT_COLUMN = (0x1, 0x2, 0x4, 0x8, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36)

MATRIX = [[0x2, 0x3, 0x1, 0x1], [0x1, 0x2, 0x3, 0x1],
          [0x1, 0x1, 0x2, 0x3], [0x3, 0x1, 0x1, 0x2]]

INV_MATRIX = [[0x0e, 0x0b, 0x0d, 0x09], [0x09, 0x0e, 0x0b, 0x0d],
              [0x0d, 0x09, 0x0e, 0x0b], [0x0b, 0x0d, 0x09, 0x0e]]

ENCODING = 'utf-8'


class keyExpansion():

    def key_expansion(self, key: bytes):
        key_schedule = []
        # key = key.encode(encoding)
        key = self.bytes_to_matrix(key)
        # Adding first round key
        key_schedule.append(key)
        # key expansion 10 rounds for 128 bit key
        for current_round in range(10):
            round_key = []
            # taking last column and applying set of opperations to it
            final_column = key_schedule[current_round][3]
            transformed_column = self.round_constant(
                self.sub_word(self.rot_word(final_column), True), current_round)
            # using transformed_column to create next round key by xoring with previous round keys
            for i in range(4):
                transformed_column = self.xor(
                    transformed_column, key_schedule[current_round][i])
                # copies value in list rather than list itself
                xor_column = transformed_column[:]
                round_key.append(xor_column)
            key_schedule.append(round_key)
        return key_schedule

    def bytes_to_matrix(self, key: bytes) -> list:
        """converts 16 bytes into a 4x4 matrix"""
        return [list(key[j:j+4]) for j in range(0, 16, 4)]

    def rot_word(self, column):
        """Shifts all items in list forward one with the front most item moving to the back"""
        return column[1:] + [column[0]]

    def sub_word(self, column, encrypt):
        # uses both nibbles of 1 bit as coordinates for s box subsitution
        if encrypt == True:
            for i in range(4):
                column[i] = S_BOX[column[i]]
        else:
            for i in range(4):
                column[i] = INVERSE_S_BOX[column[i]]
        return column

    def round_constant(self, column, round):
        # xor column with column from constant column dependant on current round
        column[0] ^= CONSTANT_COLUMN[round]
        return column

    def xor(self, a, b):
        # xors 2 same length lists together
        for i in range(len(a)):
            a[i] ^= b[i]
        return a


class SharedFunctions(keyExpansion):
    def sub_bytes(self, block, encrypt: bool):
        """
        Substitues all bytes in block for relevant bytes in S_BOX
        Parameters:
        - encrypt (bool): If encrypting set True // If decrypting set False
        """
        for i in range(len(block)):
            block[i] = self.sub_word(block[i], encrypt)
        return block

    def rotate(self, block):
        """swaps rows and columns"""
        block = list(zip(*block))
        return [list(block[i]) for i in range(len(block))]

    def gf_mult(self, a: int, b: int) -> int:
        """multiplication in gaussian feild 2^8"""
        if b == 1:
            result = a
        else:
            result = 0
            for i in range(8):
                if (b & 1):  # if lsb = 1 xor with a
                    result ^= a
                sgt255 = a & 0x80
                a <<= 1  # shift a left
                if sgt255:  # modulo
                    a ^= 0x11b
                b >>= 1  # shift b down
        return result

    def mix_columns(self, block, encrypt: bool):
        """
        Uses matrix multiplicatin to mix
        Parameters:
        - encrypt (bool): If encrypting set True // If decrypting set False
        """
        mixed_columns = [[0, 0, 0, 0], [
            0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        if encrypt == True:
            for i in range(4):
                for j in range(4):
                    for k in range(4):
                        mixed_columns[i][j] ^= self.gf_mult(
                            block[i][k], MATRIX[j][k])
        else:
            for i in range(4):
                for j in range(4):
                    for k in range(4):
                        mixed_columns[i][j] ^= self.gf_mult(
                            block[i][k], INV_MATRIX[j][k])
        return mixed_columns

    def xor_key(self, block, round: int, key_schedule: list):
        # xors column with specific round key
        return [self.xor(block[i], key_schedule[round][i]) for i in range(4)]


class Encrypt(SharedFunctions):

    def encrypt(self, plain_text: bytes, key: bytes) -> bytes:
        cipher_text = []
        key_schedule = self.key_expansion(key)
        # formatting data
        # plain_text = plain_text.encode(ENCODING)
        padded_plain_text = self.padding(plain_text)
        # Encrpytion Algorithm - encrypts in blocks of 16 bytes
        for i in range(0, len(padded_plain_text), 16):
            block = padded_plain_text[i:i+16]
            block = self.bytes_to_matrix(block)
            # Start of actual encryption
            # XOR with IV before this step.

            block = self.xor_key(block, 0, key_schedule)
            for round in range(1, 10):
                block = self.sub_bytes(block, True)
                block = self.rotate(
                    self.encrypt_shift_rows(self.rotate(block)))
                block = self.mix_columns(block, True)
                block = self.xor_key(block, round, key_schedule)
            block = self.sub_bytes(block, True)
            block = self.rotate(self.encrypt_shift_rows(self.rotate(block)))
            block = self.xor_key(block, 10, key_schedule)
            # IV = block
            cipher_text.append(block)

        # Convert the flattened list to a continuous byte stream
            # flattened_cipher_text = [
            #     byte for sublist in cipher_text for byte in sublist]

            # Decode the bytes to UTF-8
            # utf8_result = bytes(flattened_cipher_text)
            ct = sum(sum(cipher_text, []), [])
        return bytes(ct)

    def padding(self, data: bytes) -> bytes:
        """padds data to become a multiple of 128 bits"""
        bytes_remaining = (16-len(data) % 16)
        characters = (chr(bytes_remaining).encode(ENCODING)) * bytes_remaining
        data += characters
        return data

    def encrypt_shift_rows(self, block):
        for i in range(4):
            block[i] = block[i][i:] + block[i][:i]
        return block


class Decrypt(SharedFunctions):

    def decrypt(self, cipher_text: bytes, key: bytes) -> bytes:
        plain_text = []
        key_schedule = self.key_expansion(key)
        # Decryption Algorithm - decrypts in blocks of 16 bytes

        for i in range(0, len(cipher_text), 16):
            block = cipher_text[i:i+16]
            block = self.bytes_to_matrix(block)

            # STARTING THE ACTUAL DECRYPTION NOW BABY
            block = self.xor_key(block, 10, key_schedule)
            block = self.rotate(self.decrypt_shift_rows(self.rotate(block)))
            block = self.sub_bytes(block, False)
            for round in range(1, 10):
                block = self.xor_key(block, 10-round, key_schedule)
                block = self.mix_columns(block, False)
                block = self.rotate(
                    self.decrypt_shift_rows(self.rotate(block)))
                block = self.sub_bytes(block, False)
            block = self.xor_key(block, 0, key_schedule)
            plain_text.append(block)

        # flattened_plain_text = [
        #    byte for sublist in plain_text for byte in sublist]
        pt = self.remove_padding(plain_text)

        # ptt = sum(sum(pt, []), [])

        return bytes(pt)
        # plain_text = self.remove_padding(plain_text)
        # return (''.join(map(chr, plain_text))).encode()

    def remove_padding(self, data):
        # x = final character in string
        # remove x ammount of characters from end of string
        data = sum(sum(data, []), [])  # moving from 3D list to 1D list
        return data[:-data[-1]]

    def decrypt_shift_rows(slef, block):
        for i in range(4):
            block[i] = block[i][-i:] + block[i][:-i]
        return block
