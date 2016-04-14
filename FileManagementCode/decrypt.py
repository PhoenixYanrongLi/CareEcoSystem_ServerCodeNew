"""

DEPRECATED CLASS

Decrpyt.py decrypts all encryted .txt files in a path and outputs another .txt file
with decrypt added to the end.

decryptDataFiles takes in a directory where it looks for .txt files, decrypts them, then deletes the encrypted file.
decrypt takes in an encrypted file, a file to write the decrypted data to, the encryption key, and the iv.

"""
__author__ = "Bradley Zylstra"
__version__ = "1.0"
__maintainer__ = "Bradley Zylstra"
__email__ = "bradleybaldwin@gmx.com"
__status__ = "Development"

from binascii import unhexlify
from os import listdir
from os import remove
from os.path import isfile, join
from Crypto.Cipher import AES


def decryptDataFiles(directory):
    header = False
    for f in listdir(directory):
        # searches for files that have a .txt ending and do not contain the string decrypt
        if isfile(join(directory, f)) and f.find('.txt') >= 0 and f.find('decrypt') < 0:
            # append decrypt to the decrypted data file
            newFile = f[:-4]
            newFile += 'decrypt.txt'

            decrypt(open(join(directory, f), 'r'), open(join(directory, newFile), 'w+'), 'jimkwonisthebest',
                    'mobilemonitoring', header)

            # delete the encrypted file
            remove(join(directory, f))


def decrypt(in_file, out_file, key, iv, header):
    if header:
        header = in_file.readline()
        out_file.write(header)

    for line in in_file:
        # Create a new cipher for each line, strip new line character from read string
        cipher = AES.new(key, AES.MODE_CBC, iv)
        line = line.rstrip()

        # Handles a line that does not have the correct number of bytes by padding with zeroes
        if len(line) % 16 != 0:
            offset = 16 - len(line) % 16
            for i in range(0, offset):
                line += '0'
        out_file.write(cipher.decrypt(unhexlify(line)).strip() + '\n')
