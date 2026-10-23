import trie

#klasa za cvor grafa
class Cvor:
    def __init__(self,broj_strane) -> None:
        #rang cvora se odnosi na to koliko ima referenci na njega
        self._rang = 0
        self._broj_strane = broj_strane
        #cvor sadrzi i trie za tu stranicu
        self._sadrzaj = trie.Trie()
    
    @property
    def rang(self):
        return self._rang
    
    @rang.setter
    def rang(self, value):
        self._rang = value

    @property
    def broj_strane(self):
        return self._broj_strane
    
    @property
    def sadrzaj(self):
        return self._sadrzaj

    #metoda koja omogucava da cvor bude kljuc mape
    def __hash__(self):
        return hash(self._broj_strane)
    
    def __str__(self):
        return str(self._rang)
    
#klasa za granu grafa
class Grana:
    def __init__(self,pocetak,kraj,tezina) -> None:
        self._pocetak = pocetak
        self._kraj = kraj
        self._tezina = tezina

    @property
    def pocetak(self):
        return self._pocetak
    
    @property
    def kraj(self):
        return self._kraj
    
    @property
    def tezina(self):
        return self._tezina
    
    #metoda koja vraca krajeve
    def krajevi(self):
        return self._pocetak,self._kraj
    
    #metoda koja vraca suprotni cvor
    def suprotan(self, v):
        if not isinstance(v, Cvor):
            raise TypeError('v mora biti instanca klase Cvor')
        if self._kraj == v:
            return self._pocetak
        elif self._pocetak == v:
            return self._kraj
        raise ValueError('v nije cvor grane')

    #metoda koja omogucava da grana bude kljuc mape
    def __hash__(self):
        return hash((self._pocetak,self._kraj))
    
    def __str__(self):
        return f"{self._pocetak.broj_strane} -> {self._kraj.broj_strane} (tezina: {self._tezina})"
    
#klasa za graf
class Graf:
    def __init__(self):
        self._ulazne_grane = {}
        self._izlazne_grane = {}

    #metoda koja proverava da li je cvor u grafu
    def validacija(self,x):
        if not isinstance(x,Cvor):
            raise ValueError('Objekat nije cvor')
        if x not in self._ulazne_grane:
            raise ValueError('Cvor ne pripada grafu')
        
    #metoda koja vraca broj cvorova u grafu
    def broj_cvorova(self):
        return len(self._ulazne_grane)
    
    #metoda koja vraca broj grana u grafu
    def broj_grana(self):
        broj=0
        for cvor in self._ulazne_grane:
            broj+=len(self._ulazne_grane[cvor])
        return broj
    
    #metoda koja vraca sve cvorove u grafu
    def cvorovi(self):
        return self._ulazne_grane.keys()
    
    #metoda koja vraca sve grane u grafu
    def grane(self):
        skup=set()
        for cvor in self._ulazne_grane:
            for grana in self._ulazne_grane[cvor].values():
                skup.add(grana)
        return skup
    
    #metoda koja vraca granu izmedju dva cvora
    def grana(self,u,v):
        self.validacija(u)
        self.validacija(v)
        return self._ulazne_grane[v].get(u)

    #metoda koja dodaje cvor u graf
    def dodaj_cvor(self,x):
        cvor=Cvor(x)
        self._ulazne_grane[cvor]={}
        self._izlazne_grane[cvor]={}
        return cvor
    
    #metoda koja dodaje granu u graf i poveca rang cvora
    def dodaj_granu(self,u,v,tezina):
        #provera da li cvorovi postoje
        self.validacija(u)
        self.validacija(v)
        
        # rang predstavlja tezinu ulaznih referenci
        # ako grana vec postoji, ukloni njenu prethodnu tezinu.
        stara_grana = self._izlazne_grane[u].get(v)
        if stara_grana is not None:
            v.rang -= stara_grana.tezina
        grana=Grana(u,v,tezina)
        self._ulazne_grane[v][u]=grana
        self._izlazne_grane[u][v]=grana
        v.rang+=tezina

    #metoda koja vraca cvor na osnovu broja strane
    def cvor(self,x):
        for cvor in self._ulazne_grane:
            if cvor.broj_strane==x:
                return cvor
        raise ValueError('Cvor ne postoji')

#testiranje
if __name__ == "__main__":
    graf = Graf()
    cvor1 = graf.dodaj_cvor(1)
    cvor2 = graf.dodaj_cvor(2)
    cvor3 = graf.dodaj_cvor(3)
    cvor4 = graf.dodaj_cvor(4)
    cvor5 = graf.dodaj_cvor(5)
    graf.dodaj_granu(cvor1, cvor2, 1)
    graf.dodaj_granu(cvor2, cvor3, 2)
    graf.dodaj_granu(cvor3, cvor4, 3)
    graf.dodaj_granu(cvor4, cvor5, 4)
    graf.dodaj_granu(cvor4, cvor5, 4)
    print(graf.broj_cvorova())
    print(graf.broj_grana())
    print(cvor5.broj_strane)
    i=0
    for cvor in graf.cvorovi():
        print(i, cvor)
        i+=1
    i=0
    for grana in graf.grane():
        print(i, grana)
        i+=1
    print(graf.grana(cvor1, cvor2))
    print(graf.grana(cvor2, cvor3))
    print(graf.grana(cvor3, cvor4))
    print(graf.grana(cvor4, cvor5))