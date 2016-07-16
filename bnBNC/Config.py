import base64, hashlib

from os import path

class UserDB():
    def __init__(self, filePath):
        self.filePath = filePath

        # Read database file
        if path.isfile(filePath):
            with open(filePath, 'rt') as file:
                self.data = [line.split() for line in file]
        else:
            self.data = []

        for d in self.data:
            print(d)

    def count(self):
        return len(self.data)

    def getUser(self, username):
        for item in self.data:
            if str(item[0]).lower() == str(username).lower():
                return item
        return None

    def userExists(self, username):
        return self.getUser(username) is not None

    def validatePassword(self, username, password):
        user = self.getUser(username)
        if user is None or len(user) < 2: return False

        pw = base64.b64decode(password)
        return hashlib.md5(pw).hexdigest() == user[1]
