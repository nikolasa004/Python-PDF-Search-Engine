from fuzzywuzzy import fuzz
from fuzzywuzzy import process

#klasa za cvor od trie
class TrieCvor:
    def __init__(self,slovo) -> None:
        self._deca = {}
        self._slovo = slovo
        #ako je cvor kraj reci treba da se zna
        #takodje tu se cuva i koliko puta se rec pojavila
        self._krajReci = False
        self._brojPojavljivanja = 0

    @property
    def deca(self):
        return self._deca
    
    @property
    def slovo(self):
        return self._slovo
    
    @property
    def krajReci(self):
        return self._krajReci
    
    @property
    def brojPojavljivanja(self):
        return self._brojPojavljivanja
    
    @krajReci.setter
    def krajReci(self, krajReci):
        self._krajReci = krajReci

    @brojPojavljivanja.setter
    def brojPojavljivanja(self, brojPojavljivanja):
        self._brojPojavljivanja = brojPojavljivanja

#klasa za trie
class Trie:
    def __init__(self) -> None:
        self.koren = TrieCvor("")

    #dodavanje reci u trie
    def dodajCvor(self, rec):
        trenutni = self.koren
        for slovo in rec:
            if slovo not in trenutni.deca:
                trenutni.deca[slovo] = TrieCvor(slovo)
            trenutni = trenutni.deca[slovo]
        trenutni.krajReci = True
        trenutni.brojPojavljivanja += 1

    #provera da li rec postoji u trie(na stranici)
    def proveriRec(self, rec):
        trenutni = self.koren
        for slovo in rec:
            #gleda se da li postoji slovo u deci trenutnog cvora i to veliko ili malo slovo
            if slovo not in trenutni.deca:
                return False,0
            
            trenutni = trenutni.deca[slovo]

        #ako je kraj reci gleda se da li je to cela rec ili samo deo neke reci
        #ako je kraj reci vraca se True i broj pojavljivanja
        #ako nije mora da se proveri da nije posle toga specijalni znak, ako jeste vraca se True i broj pojavljivanja
        #ako nije vraca se False i 0
        broj_pojavljivanja = self._proveriRec(trenutni)
        if broj_pojavljivanja > 0:
            return True,broj_pojavljivanja
                    
        return False,0
        
    #pomocna metoda za proveriRec
    def _proveriRec(self,trenutni,broj_pojavljivanja=0):
        if trenutni.krajReci:
            broj_pojavljivanja += trenutni.brojPojavljivanja
        for slovo in trenutni.deca.keys():
            if not slovo.isalnum():
                broj_pojavljivanja = self._proveriRec(trenutni.deca[slovo],broj_pojavljivanja)
        return broj_pojavljivanja
        
    #metoda za autocomplete, vraca listu reci koje pocinju sa zadatim prefiksom i brojem pojavljivanja te reci
    def autocomplete(self,rec):
        #pronalazak cvora koji odgovara prefiksu
        trenutni = self.koren
        for slovo in rec:
            if slovo not in trenutni.deca:
                return {}
            
            trenutni = trenutni.deca[slovo]
        
        #lista reci koje pocinju sa zadatim prefiksom
        reci = {}
        #pronalazak ostatka reci koji pocinju sa zadatim prefiksom
        self._autocomplete(trenutni,rec,reci)
        return reci
    
    #pomocna metoda za autocomplete
    def _autocomplete(self,trenutni,rec,reci):
        if trenutni.krajReci:
            reci[rec] = trenutni.brojPojavljivanja
        for slovo in trenutni.deca.keys():
            if slovo.isalnum():
                self._autocomplete(trenutni.deca[slovo],rec+slovo,reci)

    #metoda za autocorrect, vraca listu reci koje su slicne zadatoj reci i brojem pojavljivanja te reci
    def autocorrect(self,rec):
        #pravljenje liste svih reci iz trie
        reci = {}
        self._autocomplete(self.koren,"",reci)

        #pronalazak reci koje su slicne zadatoj reci
        slicne_reci = process.extract(rec,reci.keys(),scorer=fuzz.ratio)
        
        #vracanje recnika sa najslicnijim recima i brojem pojavljivanja
        izlaz = {}
        for rec in slicne_reci:
            if rec[1] > 75:
                izlaz[rec[0]] = reci[rec[0]]

        return izlaz


#testiranje
if __name__ == "__main__":
    trie = Trie()
    trie.dodajCvor("series")
    trie.dodajCvor("series")
    trie.dodajCvor("series")
    trie.dodajCvor("data")
    trie.dodajCvor("data")
    trie.dodajCvor("structures")
    trie.dodajCvor("structures")
    trie.dodajCvor("structures")
    print(trie.proveriRec("series"))
    print(trie.proveriRec("data"))
    print(trie.proveriRec("structures"))
    print(trie.proveriRec("trie"))