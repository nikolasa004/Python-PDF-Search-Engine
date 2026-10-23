import pdf_modul
import colorama
import re
import pickle
import os
import obrada_logickih_izraza
import stek as stack

import argparse
import hashlib
from pathlib import Path
from getpass import getpass

#prihvata apsolutnu putanju ili relativnu u odnosu na cwd/projekat
def pronadji_pdf(unos):
    unos = unos.strip().strip('"').strip("'")
    putanja = Path(unos).expanduser()

    if putanja.is_file():
        return putanja.resolve()
    
    pored_skripte = Path(__file__).resolve().parent / putanja
    if pored_skripte.is_file():
        return pored_skripte.resolve()
    
    raise FileNotFoundError(f"PDF ne postoji: {unos}")

#svaki dokument, njegova verzija i pomeraj imaju poseban indeks
def fajl_kesa(pdf_putanja, pomeraj):
    podatak = pdf_putanja.stat()
    potpis = (f"v3|{pdf_putanja}|{podatak.st_size}|"f"{podatak.st_mtime_ns}|{pomeraj}")
    identifikator = hashlib.sha256(potpis.encode('utf-8')).hexdigest()[:20]
    return Path(__file__).resolve().parent / '.cache' / f'graf_{identifikator}.pkl'

#koristi samo lokalni kes koji je ova aplikacija generisala
def ucitaj_ili_indeksiraj(pdf_putanja, pomeraj=0, ponovo=False):
    pdf_putanja = Path(pdf_putanja).resolve()
    try:
        pdf_modul.postavi_dokument(pdf_putanja, pomeraj)
    except PermissionError:
        lozinka = getpass('Lozinka za PDF: ')
        pdf_modul.postavi_dokument(pdf_putanja, pomeraj, lozinka)

    putanja_kesa = fajl_kesa(pdf_putanja, pomeraj)
    if not ponovo and putanja_kesa.is_file():
        try:
            with putanja_kesa.open('rb') as f:
                ucitan = pickle.load(f)
            if isinstance(ucitan, pdf_modul.graf.Graf) and ucitan.broj_cvorova() == pdf_modul.dokument.page_count:
                pdf_modul.grafPdf = ucitan
                print(f"Indeks ucitan iz kesa ({pdf_modul.dokument.page_count} strana).")
                return
        except (OSError, EOFError, pickle.UnpicklingError, AttributeError, ValueError):
            print('Lokalni kes nije mogao da se ucita; pravim novi indeks.')

    print(f"Indeksiram: {pdf_putanja.name} ({pdf_modul.dokument.page_count} strana)...")
    broj_sa_tekstom = pdf_modul.citanje_pdf()
    if broj_sa_tekstom == 0:
        print('Upozorenje: nije pronadjen tekst. Skenirani PDF zahteva OCR.')
    print(f"Indeks spreman: {pdf_modul.grafPdf.broj_cvorova()} cvorova, "
          f"{pdf_modul.grafPdf.broj_grana()} veza.")
    putanja_kesa.parent.mkdir(parents=True, exist_ok=True)
    try:
        with putanja_kesa.open('wb') as f:
            pickle.dump(pdf_modul.grafPdf, f)
    except OSError as err:
        print(f"Nisam uspeo da sacuvam kes: {err}")


def main():
    parser = argparse.ArgumentParser(description='Pretraga teksta u proizvoljnom PDF-u.')
    parser.add_argument('--pdf', help='Putanja do PDF fajla (ako izostane, pita se korisnik).')
    parser.add_argument('--page-offset', type=int, default=0, help='Pomeraj stampanog broja stranice u odnosu na PDF broj (podrazumevano 0).')
    parser.add_argument('--reindex', action='store_true', help='Ponovo izgradi indeks.')
    args = parser.parse_args()

    izbor = args.pdf if args.pdf is not None else input('Unesite putanju do PDF fajla: ')
    try:
        pdf_putanja = pronadji_pdf(izbor)
        ucitaj_ili_indeksiraj(pdf_putanja, args.page_offset, args.reindex)
    except (FileNotFoundError, PermissionError, ValueError, RuntimeError) as exc:
        print(colorama.Fore.RED + f"Greska pri otvaranju PDF-a: {exc}" + colorama.Style.RESET_ALL)
        return
    except Exception as exc:
        # bilo koji drugi neuspeh pri otvaranju/indexiranju: korisna poruka.
        print(colorama.Fore.RED + f"Ne mogu da obradim PDF: {exc}" + colorama.Style.RESET_ALL)
        return

    print(f"Izabrani PDF: {pdf_putanja.name}")

    #konzola
    while True:
        unos = input("Unesite pretragu ili 'kraj' za izlazak: ")
    
        reci_split=unos.split()
        unos=""
        for rec in reci_split:
            if rec=="AND" or rec=="OR" or rec=="NOT":
                unos+=rec
            else:
                unos+=rec.lower()
            unos+=" "
        unos=unos[:-1]
        reci_split=[]

        rezultati={}

        if unos=="":
            print(colorama.Fore.RED+"Niste uneli nista!!!"+colorama.Style.RESET_ALL)
            continue

        #ako ima * u unosu onda je to znak za autocomplete
        if "*" in unos:
            rezultati=pdf_modul.autocomplete(unos[:-1])

            #ispis rezultata
            if len(rezultati)==0:
                print(colorama.Fore.RED+"Nema slicnih reci"+colorama.Style.RESET_ALL)
            else:
                print(colorama.Fore.BLUE+"Najbolja podudaranja:"+colorama.Style.RESET_ALL)
                i=1
                for rec in rezultati.keys():
                    print(colorama.Fore.BLUE+str(i)+colorama.Style.RESET_ALL+"-"+colorama.Fore.GREEN+rec+colorama.Style.RESET_ALL)
                    i+=1

            continue

        #ideja kod fraza, to jest unosa vise reci gde te reci moraju da budu jedna pored druge
        #je da se radi kao rec1 AND rec2 AND rec3... i onda se za svaku recenicu proveri
        #sa fraza in recenica i ako se nadje onda se ispise ta recenica, ako se ne nadje onda se ne ispise
        da_li_fraza=False
        fraza=""
        if '"' in unos:
            if unos.count('"')!=2:
                print(colorama.Fore.RED+"Niste uneli ispravno frazu!!!"+colorama.Style.RESET_ALL)
                continue
            if '"' in unos[1:-1]:
                print(colorama.Fore.RED+"Niste uneli ispravno frazu!!!"+colorama.Style.RESET_ALL)
                continue

            da_li_fraza=True
            unos=unos[1:-1]
            fraza=unos
            unos=unos.replace(" "," AND ")

        #interakcija sa korisnikom
        if unos == "kraj":
            break
        else:
            #ako je uneto vise reci pretraga se vrsi za svaku rec posebno
            if " " in unos and "AND" not in unos and "OR" not in unos and "NOT" not in unos:
                reci_split = unos.split(" ")
                reci = []
                for i in range(len(reci_split)):
                    if reci_split[i]=="":
                        continue
                    reci.append(reci_split[i])

                for rec in reci:
                    #za svaku rec se dobijaju rezultati i oni se dodaju u rezultate tako sto ako kljuc vec postoji samo se sabiraju vrednosti i tekst i rang
                    #ako kljuc ne postoji dodaje se novi kljuc i njegov tekst i rang

                    rezultati_reci=pdf_modul.pretraga(rec)
                
                    for rezultat in rezultati_reci.keys():
                        prvo_dodavanje=True
                        if rezultat in rezultati:
                            #posto ima vise reci u pretrazi moze se desiti sa se razlicite pojavljuju u istoj recenici
                            #tada dolazi do dupliranja recenica pa se to izbegava
                            for recenica in rezultati_reci[rezultat][0].split("\n"):
                                if recenica not in rezultati[rezultat][0]:
                                    if prvo_dodavanje:
                                        rezultati[rezultat]=(rezultati[rezultat][0]+"\n"+recenica,rezultati[rezultat][1]+rezultati_reci[rezultat][1],rezultati[rezultat][2]+1)
                                        prvo_dodavanje=False
                                    else:
                                        rezultati[rezultat]=(rezultati[rezultat][0]+"\n"+recenica,rezultati[rezultat][1],rezultati[rezultat][2])
                                else:
                                    if prvo_dodavanje:
                                        rezultati[rezultat]=(rezultati[rezultat][0],rezultati[rezultat][1]+rezultati_reci[rezultat][1],rezultati[rezultat][2]+1)
                                        prvo_dodavanje=False
                        else:
                            rezultati[rezultat]=(rezultati_reci[rezultat][0],rezultati_reci[rezultat][1],1)
             
                #glavna stvar za rang je da se pojavi sto vise reci iz pretrage na stranici, nebitno koliko puta se rec pojavila
                for rezultat in rezultati.keys():
                    rezultati[rezultat]=(rezultati[rezultat][0],rezultati[rezultat][1]*rezultati[rezultat][2],rezultati[rezultat][2])

                #sortiranje rezultata    
                rezultati = dict(sorted(rezultati.items(), key=lambda item: item[1][1], reverse=True))
            elif "AND" in unos or "OR" in unos or "NOT" in unos:
                #ako je u pitanju logicki izraz prvo se pretvara u postfiks notaciju
                postfix=obrada_logickih_izraza.u_postfix(unos)

                #ako je unet nevalidan izraz bice string a ne lista
                if type(postfix)==str:
                    print(colorama.Fore.RED+postfix+colorama.Style.RESET_ALL)
                    continue

                #ide se kroz postfiks notaciju i izvrsavaju se operacije
                #za svake dve reci se izvrsi pretraga i onda se izvrsi operacija AND, OR ili NOT
                #rezultati se cuvaju u steku
                stek_rezultata=stack.Stack()

                for token in postfix:
                    if token=="AND":
                        rezultat1=stek_rezultata.pop()
                        rezultat2=stek_rezultata.pop()
                        rezultat=pdf_modul.and_operacija(rezultat1,rezultat2)
                        stek_rezultata.push(rezultat)
                    elif token=="OR":
                        rezultat1=stek_rezultata.pop()
                        rezultat2=stek_rezultata.pop()
                        rezultat=pdf_modul.or_operacija(rezultat1,rezultat2)
                        stek_rezultata.push(rezultat)
                    elif token=="NOT":
                        rezultat2=stek_rezultata.pop()
                        rezultat1=stek_rezultata.pop()
                        rezultat=pdf_modul.not_operacija(rezultat1,rezultat2)
                        stek_rezultata.push(rezultat)
                    else:
                        rezultati=pdf_modul.pretraga(token)
                        stek_rezultata.push(rezultati)

                #rezultat je na vrhu steka
                rezultati=stek_rezultata.pop()

                #sortiranje rezultata
                rezultati = dict(sorted(rezultati.items(), key=lambda item: item[1][1], reverse=True))
            else:
                rezultati=pdf_modul.pretraga(unos)

            #u slucaju fraze se proverava da li se fraza nalazi u recenici i cuvaju se samo recenice koje sadrze tu frazu
            if da_li_fraza:
                rezultati_fraze={}
                for rezultat in rezultati.keys():
                    for recenica in rezultati[rezultat][0].split("\n"):
                        if fraza in recenica.lower():
                            if rezultat not in rezultati_fraze:
                                rezultati_fraze[rezultat]=(recenica,rezultati[rezultat][1],0)
                            else:
                                rezultati_fraze[rezultat]=(rezultati_fraze[rezultat][0]+"\n"+recenica,rezultati_fraze[rezultat][1],0)
                rezultati=rezultati_fraze

                #sortiranje rezultata na osnovu broja recenica jer ovde rang ne vazi
                # Sortiranje rezultata na osnovu dužine rečenica
                rezultati =dict(sorted(rezultati.items(), key=lambda x: len(x[1][0]), reverse=True))

            #ispis rezultata
            i=1
            if len(rezultati)==0:
                print(colorama.Fore.RED+"Nema rezultata pretrage"+colorama.Style.RESET_ALL)
            else:
                brojac=0
                for rezultat in rezultati.keys():
                    if brojac%10==0 and brojac!=0:
                        nastavak=input("Pritisnite enter za nastavak, 'nazad' za prekid ili 'sacuvaj' da sacuvate prvih 10 rezultata: ")
                        if nastavak=="nazad":
                            break

                        if nastavak=="sacuvaj":
                            pdf_modul.sacuvaj(rezultati,unos)
                            print(colorama.Fore.BLUE+"Rezultati su uspesno sacuvani!!!"+colorama.Style.RESET_ALL)
                            break

                    broj_strane=rezultat

                    tekst="..."+rezultati[rezultat][0]+"..."

                    #bojenje teksta u crveno i ispis
                    #treba da se boji rec nebitno da li su velika ili mala slova
                    #treba da se boji samo rec koja je odvojena ili uz neki specijalni znak a ne rec koja je deo neke reci
                    if " " in unos and "AND" not in unos and "OR" not in unos and "NOT" not in unos:
                        reci_split=unos.split(" ")
                        reci=[]
                        for j in range(len(reci_split)):
                            if reci_split[j]=="":
                                continue
                            reci.append(reci_split[j])

                        for rec in reci:
                            tekst=re.sub(r'(?<!\w)'+re.escape(rec)+r'(?!\w)',colorama.Fore.GREEN+rec+colorama.Style.RESET_ALL,tekst,flags=re.IGNORECASE)
                    elif "AND" in unos or "OR" in unos or "NOT" in unos:
                        reci=unos.split(" ")
                        reci_bez_operatora=[]
                        for rec in reci:
                            if rec=="AND" or rec=="OR" or rec=="NOT":
                                continue

                            nova_rec=rec.replace("(","").replace(")","")
                            reci_bez_operatora.append(nova_rec)
                    
                        if not da_li_fraza:
                            for rec in reci_bez_operatora:
                                tekst=re.sub(r'(?<!\w)'+re.escape(rec)+r'(?!\w)',colorama.Fore.GREEN+rec+colorama.Style.RESET_ALL,tekst,flags=re.IGNORECASE)
                        else:
                            tekst=re.sub(r'(?<!\w)'+re.escape(fraza)+r'(?!\w)',colorama.Fore.GREEN+fraza+colorama.Style.RESET_ALL,tekst,flags=re.IGNORECASE)
                    else:
                        tekst=re.sub(r'(?<!\w)'+re.escape(unos)+r'(?!\w)',colorama.Fore.GREEN+unos+colorama.Style.RESET_ALL,tekst,flags=re.IGNORECASE)

                    tekst=tekst.replace("\n","...\n...")
                    print(f"{colorama.Fore.BLUE+str(i)+colorama.Style.RESET_ALL}-stranica {broj_strane}:\n{tekst}\n") 

                    i+=1
                    brojac+=1

            #ako je bilo manje od 10 rezultata za unos jedne reci onda je moguce da to nije zeljena rec
            #zato se pronadju slicne reci i ponude kao moguci izbor
            if i<10 and " " not in unos:
                rezultati=pdf_modul.autocomplete(unos,"autocorrect")

                #ispis rezultata
                if len(rezultati)!=0:
                    print(colorama.Fore.BLUE+"Da li ste mozda mislili:"+colorama.Style.RESET_ALL)
                    i=1
                    for rec in rezultati.keys():
                        print(colorama.Fore.BLUE+str(i)+colorama.Style.RESET_ALL+"-"+colorama.Fore.GREEN+rec+colorama.Style.RESET_ALL)
                        i+=1

    pdf_modul.dokument.close()


if __name__ == '__main__':
    main()
