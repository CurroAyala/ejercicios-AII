from math import sqrt


##########################
## FUNCIONES AUXILIARES ##
##########################

def sim_distance(prefs, person1, person2):
    '''
    Función que devuelve la similitud entre dos usuarios (personas) basada en la distancia euclídea.
    '''
    si = {}
    for item in prefs[person1]: 
        if item in prefs[person2]: si[item] = 1

        if len(si) == 0: return 0

        sum_of_squares = sum([pow(prefs[person1][item] - prefs[person2][item], 2) 
                    for item in prefs[person1] if item in prefs[person2]])
        
        return 1 / (1 + sum_of_squares)

def sim_pearson(prefs, p1, p2):
    '''
    Función que devuelve la similitud entre dos usuarios (personas) basada en la correlación de Pearson.
    '''
    si = {}
    for item in prefs[p1]: 
        if item in prefs[p2]: si[item] = 1

    if len(si) == 0: return 0

    n = len(si)

    sum1 = sum([prefs[p1][it] for it in si])
    sum2 = sum([prefs[p2][it] for it in si])

    sum1Sq = sum([pow(prefs[p1][it], 2) for it in si])
    sum2Sq = sum([pow(prefs[p2][it], 2) for it in si])	

    pSum = sum([prefs[p1][it] * prefs[p2][it] for it in si])

    num = pSum - (sum1 * sum2 / n)
    den = sqrt((sum1Sq - pow(sum1, 2) / n) * (sum2Sq - pow(sum2, 2) / n))
    if den == 0: return 0

    r = num / den

    return r

def calcular_mas_similares(prefs, person, n=5, similarity=sim_pearson):
        '''
        Función que calcula los n elementos más similares.
        n y similarity son parámetros opcionales.
        '''
        scores = [(similarity(prefs, person, other), other) 
                    for other in prefs if other != person]
        scores.sort()
        scores.reverse()
        return scores[0:n]


###########################
## FUNCIONES PRINCIPALES ##
###########################

def invertir_diccionario(dict):
    '''
    Función que invierte las claves de un diccionario anidado.
    '''
    res = {}
    for clave1 in dict:
        for clave2 in dict[clave1]:
            res.setdefault(clave2, {})
    
            res[clave2][clave1] = dict[clave1][clave2]
    return res

def calcular_similitudes(dict, n):
    '''
    Función que calcula los n elementos más similares de cada elemento de una matriz.
    '''
    res = {}
    dict_inv = invertir_diccionario(dict)

    c = 0 # Contador
    for clave1 in dict:
        c += 1
        if c%100 == 0: print("%d / %d" % (c, len(dict_inv))) # Aviso para comunicar que el programa no se ha congelado
        similares = calcular_mas_similares(dict_inv, clave1, n=n, similarity=sim_distance)
        res[clave1] = similares
    return res

def obtener_recomendaciones(prefs, person, similarity=sim_pearson):
    '''
    Función que calcula recomendaciones para una persona utilizando una media de los rankings de otros usuarios.
    '''
    totals = {}
    simSums = {}
    for other in prefs:
        # don't compare me to myself
        if other == person: continue
        sim = similarity(prefs, person, other)
        # ignore scores of zero or lower
        if sim <= 0: continue
        for item in prefs[other]:
            # only score movies I haven't seen yet
            if item not in prefs[person] or prefs[person][item] == 0:
                # Similarity * Score
                totals.setdefault(item, 0)
                totals[item] += prefs[other][item] * sim
                # Sum of similarities
                simSums.setdefault(item, 0)
                simSums[item] += sim

    # Create the normalized list
    rankings = [(total / simSums[item], item) for item, total in totals.items()]
    # Return the sorted list
    rankings.sort()
    rankings.reverse()
    return rankings

def obtener_recomendaciones_item(prefs, itemMatch, user):
    '''
    Función que calcula recomendaciones basadas en los items
    '''
    userRatings = prefs[user]
    scores = {}
    totalSim = {}
    # Loop over items rated by this user
    for (item, rating) in userRatings.items():
        # Loop over items similar to this one
        for (similarity, item2) in itemMatch[item]:
            print (item2)
            # Ignore if this user has already rated this item
            if item2 in userRatings: continue
            # Weighted sum of rating times similarity
            scores.setdefault(item2, 0)
            scores[item2] += similarity * rating
            # Sum of all the similarities
            totalSim.setdefault(item2, 0)
            totalSim[item2] += similarity

    # Divide each total score by total weighting to get an average
    try:
        rankings = [(score / totalSim[item], item) for item, score in scores.items()]
    except ZeroDivisionError:
        rankings = []

    # Return the rankings from highest to lowest
    rankings.sort()
    rankings.reverse()
    return rankings