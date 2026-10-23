import fitz
import os
import graf
import re

# PDF se bira pri pokretanju
lokacija_pdf = None
dokument = None
grafPdf = graf.Graf()
# Razlika izmedju broja na stampanoj strani i broja PDF strane.
# U opstem slucaju 0; za originalni fakultetski primer bila 22.
pomeraj_stranica = 0


def postavi_dokument(putanja, pomeraj=0, lozinka=None):
    """Otvara izabrani PDF i resetuje prethodno logicko stanje indeksa."""
    global lokacija_pdf, dokument, grafPdf, pomeraj_stranica

    puna_putanja = os.path.realpath(os.path.expanduser(os.fspath(putanja)))
    if not os.path.isfile(puna_putanja):
        raise FileNotFoundError(f"PDF nije pronadjen: {puna_putanja}")
    if not puna_putanja.lower().endswith('.pdf'):
        raise ValueError("Izabrani fajl mora imati .pdf ekstenziju.")

    novi = fitz.open(puna_putanja)
    try:
        if not novi.is_pdf:
            raise ValueError("Izabrani fajl nije PDF.")
        if novi.needs_pass and not (lozinka and novi.authenticate(lozinka)):
            raise PermissionError("Za otvaranje PDF-a potrebna je ispravna lozinka.")
        if dokument is not None:
            dokument.close()
        dokument = novi
    except Exception:
        novi.close()
        raise

    lokacija_pdf = puna_putanja
    pomeraj_stranica = int(pomeraj)
    grafPdf = graf.Graf()

#metoda za citanje pdf dokumenta
def citanje_pdf():
    global grafPdf
    if dokument is None:
        raise RuntimeError("Najpre izaberite PDF preko postavi_dokument().")

    # svaki cvor je PDF strana (brojanje od 1), sa sopstvenim Trie indeksom.
    grafPdf = graf.Graf()
    tekstovi = []
    cvorovi = [None]
    for i in range(dokument.page_count):
        cvor = grafPdf.dodaj_cvor(i + 1)
        cvorovi.append(cvor)
        stranica = dokument[i]
        tekst = stranica.get_text()
        tekst = re.sub(r'ﬁ', 'fi', tekst)
        tekst = re.sub(r'ﬂ', 'fl', tekst)
        tekstovi.append(tekst)
        for rec in tekst.split():
            cvor.sadrzaj.dodajCvor(rec.lower())

    for i, tekst in enumerate(tekstovi):
        tezine = {}
        # Tekstualne reference: 'page 3', 'pages 4-5', itd.
        for broj_stampane, tezina in izdvoji_reference(tekst).items():
            broj_pdf = broj_stampane + pomeraj_stranica
            if 1 <= broj_pdf <= dokument.page_count:
                tezine[broj_pdf] = tezine.get(broj_pdf, 0) + tezina

        for link in dokument[i].get_links():
            if link.get('kind') == fitz.LINK_GOTO:
                cilj = link.get('page', -1) + 1
                if 1 <= cilj <= dokument.page_count:
                    tezine[cilj] = max(tezine.get(cilj, 0), 1)

        for broj_pdf, tezina in tezine.items():
            grafPdf.dodaj_granu(cvorovi[i + 1], cvorovi[broj_pdf], tezina)
    return sum(bool(tekst.strip()) for tekst in tekstovi)

# u tekstu prepoznaje npr. 'page 10', 'pages 10-12',
# 'pages 10 and 15', 'pages 10, 15, 20'.
def izdvoji_reference(tekst):
    tezine = {}
    obrazac = re.compile(
        r'(?<!\w)\(?pages?\b\s+'
        r'((?:\d+(?:\s*[-–—]\s*\d+)?)'
        r'(?:(?:\s*,\s*|\s+and\s+)\d+(?:\s*[-–—]\s*\d+)?)*)',
        re.IGNORECASE
    )
    for pogodak in obrazac.finditer(tekst):
        # Separator '-' oznacava OPSEG; ',' i 'and' nabrajaju stranice.
        for deo in re.split(r'\s*,\s*|\s+and\s+', pogodak.group(1), flags=re.IGNORECASE):
            granice = re.split(r'\s*[-–—]\s*', deo)
            if len(granice) == 2:
                pocetak, kraj = int(granice[0]), int(granice[1])
                if kraj < pocetak:
                    continue
                # Necemo generisati beskonacne/nepostojece opsege.
                # Ogranicenje opsega po velicini PDF-a, posle pomeraja.
                najvisi_broj = max(dokument.page_count, dokument.page_count - pomeraj_stranica) if dokument else kraj
                stranice = range(pocetak, min(kraj, najvisi_broj) + 1)
            else:
                stranice = (int(granice[0]),)
            for broj in stranice:
                if broj > 0:
                    tezine[broj] = tezine.get(broj, 0) + 1
    return tezine

# metoda za uklanjanje specijalnih znakova sa broja (zadrzana iz originala)
def clean_number(text):
    return re.sub(r'\D', '', text)

#pretraga reci u pdf dokumentu
def pretraga(tekst):
    global grafPdf

    rezultati={}
    #pretraga reci u grafu
    for cvor in grafPdf.cvorovi():
        postoji, brojPojavljivanja = cvor.sadrzaj.proveriRec(tekst)

        #ako ne postoji rec na stranici nema sta da se trazi
        if not postoji:
            continue

        #ukupan rang stranice je suma broja pojavljivanja reci i broja grana koje vode do te stranice a to je rang cvora
        rang = brojPojavljivanja + cvor.rang
        #na ukupan rang treba da se doda i broj pojavljivanja reci na stranici koja pokazuje na ovu stranicu
        for grana in grafPdf._ulazne_grane[cvor].values():
            postoji, brojPojavljivanja = grana.pocetak.sadrzaj.proveriRec(tekst)
            if postoji:
                rang+=brojPojavljivanja

        #ako postoji rec na stranici treba da se izvuce cela recenica u kojoj se rec nalazi
        stranica = dokument[cvor.broj_strane-1]
        tekstStranice = stranica.get_text()
        #namestanje ligaturnih karaktera
        tekstStranice = re.sub(r'ﬁ', 'fi', tekstStranice)
        tekstStranice = re.sub(r'ﬂ', 'fl', tekstStranice)
        recenice = tekstStranice.split("\n")

        #izdvajanje recenice u kojoj se rec nalazi
        for recenica in recenice:
            #obzirom da se rec moze javiti vise puta u recenici doslo bi do duplikata recenica
            #tako da se samo jednom dodaje recenica u rezultate
            prva=True
            for rec in recenica.split():
                #pri proveri reci nebitno je da li su velika ili mala slova i moze i da uz rec bude neki specijalni znak
                if re.search(r'(?<!\w)'+re.escape(tekst)+r'(?!\w)',rec,re.IGNORECASE) is not None:
                    if cvor.broj_strane not in rezultati:
                        #rezultat je tuple gde je prvi element recenica u kojoj se rec nalazi, drugi element je rang stranice a treci element je broj pojavljivanja razlicitih reci na stranici
                        if prva:
                            rezultati[cvor.broj_strane] = (recenica, rang,0)
                            prva=False
                    else:
                        if prva:
                            rezultati[cvor.broj_strane]=(rezultati[cvor.broj_strane][0]+"\n"+recenica, rang,0)
                            prva=False

    #obzirom da postoje razliciti nacini gde se rec moze pojaviti u recenici
    #preko trie se moze proveriti da li se rec pojavila u recenici i koliko se puta pojavila cista ili sa nekim specijalnim znakom ta rec
    #ne moze se proveriti da li se rec pojavila u recenici sa nekim drugim recima npr. neka_rec.[rec]...
    #ovde se moze proveriti koliko ima recenica pa sigurno ima bar toliko reci
    #tako da se ovde prolazi kroz rezultate i za rang uzima max od broja recenica ili trenutnog ranga
    for stranica in rezultati.keys():
        broj_recenica = len(rezultati[stranica][0].split("\n"))
        rezultati[stranica]=(rezultati[stranica][0],max(rezultati[stranica][1],broj_recenica),0)

    #sortiranje rezultata
    rezultati = dict(sorted(rezultati.items(), key=lambda item: item[1][1], reverse=True))

    return rezultati

#logicka operacija AND
def and_operacija(rezultat1,rezultat2):
    rezultat={}
    for stranica in rezultat1.keys():
        if stranica in rezultat2.keys():
            #dodavanje stranice u rezultat, sabiranje rangova i namestanje da se recenica ne ponavlja
            rezultat[stranica]=(rezultat1[stranica][0],rezultat1[stranica][1]+rezultat2[stranica][1],0)
            for recenica in rezultat2[stranica][0].split("\n"):
                if recenica not in rezultat[stranica][0]:
                    rezultat[stranica]=(rezultat[stranica][0]+"\n"+recenica,rezultat[stranica][1],0)

    return rezultat

#logicka operacija OR
def or_operacija(rezultat1,rezultat2):
    rezultat={}
    for stranica in rezultat1.keys():
        rezultat[stranica]=rezultat1[stranica]
    for stranica in rezultat2.keys():
        if stranica not in rezultat:
            rezultat[stranica]=rezultat2[stranica]
        else:
           #dodavanje stranice u rezultat, sabiranje rangova i namestanje da se recenica ne ponavlja
            rezultat[stranica]=(rezultat[stranica][0],rezultat[stranica][1]+rezultat2[stranica][1],0)
            for recenica in rezultat2[stranica][0].split("\n"):
                if recenica not in rezultat[stranica][0]:
                    rezultat[stranica]=(rezultat[stranica][0]+"\n"+recenica,rezultat[stranica][1],0) 

    return rezultat

#logicka operacija NOT (binarna operacija)
def not_operacija(rezultat1,rezultat2):
    rezultat={}
    for stranica in rezultat1.keys():
        if stranica not in rezultat2.keys():
            rezultat[stranica]=rezultat1[stranica]
    return rezultat

#autocomplete i autocorrect
def autocomplete(tekst,tip="autocomplete"):
    global grafPdf

    #prolazi se kroz sve stranice i traze se reci koje pocinju sa unetim tekstom
    #te reci se dodaju u rezultate kao kljuc a vrednost je broj pojavljivanja te reci u pdf dokumentu
    rezultati={}
    for cvor in grafPdf.cvorovi():
        if tip=="autocomplete":
            reci = cvor.sadrzaj.autocomplete(tekst)
        else:
            reci = cvor.sadrzaj.autocorrect(tekst)
        for rec in reci.keys():
            if rec not in rezultati:
                rezultati[rec]=reci[rec]
            else:
                rezultati[rec]+=reci[rec]
    
    #sortiranje rezultata
    rezultati = dict(sorted(rezultati.items(), key=lambda item: item[1], reverse=True))

    #vracanje prvih 5 rezultat ako ih ima toliko
    brojac=0
    rezultati_final={}
    for rec in rezultati.keys():
        if brojac==5:
            break

        if rec!=tekst and rec.lower()!=tekst.lower() and rec.upper()!=tekst.upper() and rec.capitalize()!=tekst.capitalize():
            if rec.lower() not in rezultati_final.keys():
                rezultati_final[rec.lower()]=rezultati[rec]
                brojac+=1

    return rezultati_final

    
    
#metoda za kreiranje pdf dokumenta sa rezultatima pretrage
#uz takodje i bojenje reci koje se traze
def sacuvaj(rezultati,unos, izlazni_folder=None):
    # upit moze imati karaktere nedozvoljene u Windows imenima datoteka.
    bezbedan_naziv = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', unos).strip(' .')[:90] or 'pretraga'
    ime_pdf="rezultati_"+bezbedan_naziv+".pdf"
    naslov="Rezultati pretrage za rec: "+unos

    #lokacija pdf dokumenta
    folder = os.fspath(izlazni_folder) if izlazni_folder is not None else os.path.join(os.path.dirname(__file__), "Rezultati")
    os.makedirs(folder, exist_ok=True)
    lokacija_pdf=os.path.join(folder,ime_pdf)

    #kreiranje pdf dokumenta
    pdf = fitz.open()

    #dodavanje naslova
    stranica_naslov=pdf.new_page()
    font="Times-Bold"
    velicina_fonta=25
    rect_naslova = fitz.Rect(20, stranica_naslov.rect.height / 2 - 140, stranica_naslov.rect.width - 20, stranica_naslov.rect.height / 2 + 140)
    # smanjuje font ako naslov ne moze da stane u zadati okvir.
    while velicina_fonta >= 10:
        result = stranica_naslov.insert_textbox(rect_naslova, naslov, fontname=font, fontsize=velicina_fonta)

        if result >= 0:
            break
        velicina_fonta -= 1

    #uzimanje teksta sa prvih 10 stranica
    i=0
    for stranica in rezultati.keys():
        if i == 10:
            break

        #dodavanje stranice u pdf dokument
        # sacuvaj dimenzije izvorne strane (A4 nije pravilo za sve PDF-ove).
        originalna_stranica = dokument[stranica - 1]
        nova_stranica=pdf.new_page(width=originalna_stranica.rect.width, height=originalna_stranica.rect.height)
        rect = nova_stranica.rect

        #dodavanje teksta sa stranice
        nova_stranica.show_pdf_page(rect,dokument,stranica-1)

        i+=1

    # i kada se trazi jedna rec, ona mora biti u listi za proveru granica.
    reci = [rec for rec in re.findall(r'[^\s()\"]+', unos)
            if rec not in ("AND", "OR", "NOT")]
    for i in range(1, pdf.page_count):
        stranica = pdf[i]
        for trazena_rec in reci:
            if not trazena_rec:
                continue
            for pojava in stranica.search_for(trazena_rec):
                prosireni_klip = (pojava[0] - 5, pojava[1], pojava[2] + 5, pojava[3])
                tekst_oko_reci = stranica.get_text("text", clip=prosireni_klip)
                if not deo_reci(trazena_rec, tekst_oko_reci):
                    oznaka = stranica.add_highlight_annot(pojava)
                    oznaka.set_colors(stroke=[0, 1, 0])
                    oznaka.update()

    #sacuvavanje pdf dokumenta
    pdf.save(lokacija_pdf)
    pdf.close()

#metoda koja proverava da li je rec deo druge reci
def deo_reci(unos,rec):
    #regeks
    patern = r'(?<!\w)' + re.escape(unos) + r'(?!\w)'
    match = re.search(patern, rec, re.IGNORECASE)
    return match is None
    
#testiranje
if __name__ == "__main__":
    print("Pokrenite pretraga.py da biste izabrali PDF.")