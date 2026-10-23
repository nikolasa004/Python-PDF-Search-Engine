#greska vezana za stek
class StackError(Exception):
    pass

#stek
class Stack(object):
    #konstruktor
    def __init__(self):
        self._data = []
    
    #vraca broj elemenata na steku
    def __len__(self):
        return len(self._data)

    #proverava da li je stek prazan
    def is_empty(self):
        if(len(self._data)==0):
            return True
        else:
            return False

    #dodaje element na stek
    def push(self, element):
        self._data.append(element)

    #vraca element sa vrha steka ako stek nije prazan, ako jeste baca gresku
    def top(self):
        if(self.is_empty()):
            raise StackError("Stek je prazan")
        return self._data[-1]

    #vraca i izbacuje element sa vrha steka ako stek nije prazan, ako jeste baca gresku
    def pop(self):
        if(self.is_empty()):
            raise StackError("Stek je prazan")
        return self._data.pop()