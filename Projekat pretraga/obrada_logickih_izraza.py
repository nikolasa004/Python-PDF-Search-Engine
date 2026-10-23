import stek as stack

#funkcija koja deli izraz na tokene
def tokenizacija(izraz):
    tokeni = []
    #ide se slovo po slovo i ako se naidje na razmak ili zagradu onda se pravi token
    indeks_zadnjeg_tokena = 0
    for i in range(len(izraz)):
        if izraz[i] == " " or izraz[i] == "(" or izraz[i] == ")":
            tokeni.append(izraz[indeks_zadnjeg_tokena:i])
            if izraz[i] != " ":
                tokeni.append(izraz[i])
            indeks_zadnjeg_tokena = i+1

    #dodavanje poslednjeg tokena
    tokeni.append(izraz[indeks_zadnjeg_tokena:])
    return tokeni

# AND i binarni NOT (razlika skupova) imaju prednost u odnosu na OR.
# Operatori istog prioriteta evaluiraju se sleva nadesno.
PRIORITET = {"OR": 1, "AND": 2, "NOT": 2}

#funkcija koja pretvara izraz u postfiks notaciju
def u_postfix(izraz):
    tokeni = [token for token in tokenizacija(izraz) if token != ""]
    if not tokeni:
        return "Niste uneli validan izraz!!!"

    postfix = []
    stek = stack.Stack()
    ocekuje_se_rec = True

    for token in tokeni:
        if token == "(":
            if not ocekuje_se_rec:
                return "Nedostaje operator pre zagrade!!!"
            stek.push(token)
        elif token == ")":
            if ocekuje_se_rec:
                return "Prazne zagrade ili operator pre zatvaranja zagrade!!!"
            while not stek.is_empty() and stek.top() != "(":
                postfix.append(stek.pop())
            if stek.is_empty():
                return "Niste uneli validan izraz, proverite zagrade!!!"
            stek.pop()
            ocekuje_se_rec = False
        elif token in PRIORITET:
            if ocekuje_se_rec:
                return "Operator ne moze biti na pocetku izraza ili posle drugog operatora!!!"
            while (not stek.is_empty() and stek.top() in PRIORITET
                   and PRIORITET[stek.top()] >= PRIORITET[token]):
                postfix.append(stek.pop())
            stek.push(token)
            ocekuje_se_rec = True
        else:
            if not ocekuje_se_rec:
                return "Ne mogu dve reci biti jedna pored druge bez operatora!!!"
            postfix.append(token)
            ocekuje_se_rec = False

    if ocekuje_se_rec:
        return "Izraz ne moze da se zavrsi operatorom ili otvorenom zagradom!!!"

    while not stek.is_empty():
        token = stek.pop()
        if token == "(":
            return "Niste uneli validan izraz, proverite zagrade!!!"
        postfix.append(token)
    return postfix
