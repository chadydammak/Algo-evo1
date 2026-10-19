
import math
import random

INF = math.inf
N = 8

# Indices Python 0..7 representent les villes 1..8.
COUTS = [
    [0,   14,  15,  INF, INF, INF, INF, 17],
    [14,  0,   13,  14,  20,  INF, INF, 21],
    [15,  13,  0,   11,  21,  17,  9,  9],
    [INF, 14,  11,  0,   11,  10,  8,  20],
    [INF, 20,  21,  11,  0,   15,  18, INF],
    [INF, INF, 17,  10,  15,  0,   9,  INF],
    [INF, INF, 9,   8,   18,  9,   0,  13],
    [17,  21,  9,   20,  INF, INF, 13,  0],
]

# Circuit initial impose par l'enonce : 1-2-3-4-5-6-7-8-1
INITIAL = list(range(N))


def cout_tour(tour):
    """Retourne le cout du circuit, ou inf si une liaison est interdite."""
    total = 0
    for i in range(N):
        a = tour[i]
        b = tour[(i + 1) % N]
        cout = COUTS[a][b]
        if cout == INF:
            return INF
        total += cout
    return total


def afficher_tour(tour):
    """Affiche un circuit avec les villes numerotees de 1 a 8."""
    return " -> ".join(str(v + 1) for v in tour + [tour[0]])


def voisins_par_echange(tour):
    """Genere les circuits en echangeant deux villes, en gardant la ville 1 fixe."""
    for i in range(1, N - 1):
        for j in range(i + 1, N):
            voisin = tour.copy()
            voisin[i], voisin[j] = voisin[j], voisin[i]
            if cout_tour(voisin) < INF:
                yield voisin, (tour[i], tour[j])


def recherche_taboue(iterations=100, duree_taboue=5):
    courant = INITIAL.copy()
    meilleur = courant.copy()
    # Dictionnaire mouvement -> iteration jusqu'a laquelle il est tabou
    tabou = {}

    print("\n=== 1. RECHERCHE TABOUE ===")
    print("Solution initiale :", afficher_tour(courant))
    print("Cout initial :", cout_tour(courant))

    for iteration in range(1, iterations + 1):
        candidats = []

        for voisin, mouvement in voisins_par_echange(courant):
            # Interdire temporairement le mouvement inverse.
            inverse = (mouvement[1], mouvement[0])
            est_tabou = tabou.get(inverse, 0) > iteration
            valeur = cout_tour(voisin)

            # Critere d'aspiration : autoriser si meilleur que le record.
            if not est_tabou or valeur < cout_tour(meilleur):
                candidats.append((valeur, voisin, mouvement))

        if not candidats:
            print("Arret : aucun voisin autorise.")
            break

        valeur, suivant, mouvement = min(candidats, key=lambda x: x[0])
        courant = suivant
        tabou[mouvement] = iteration + duree_taboue

        if valeur < cout_tour(meilleur):
            meilleur = courant.copy()

        # Nettoyer les entrees expirees.
        tabou = {m: fin for m, fin in tabou.items() if fin > iteration}

        print(
            f"Iteration {iteration:3d} | "
            f"cout courant = {cout_tour(courant):5} | "
            f"meilleur = {cout_tour(meilleur):5}"
        )

    print("Meilleur circuit :", afficher_tour(meilleur))
    print("Meilleur cout :", cout_tour(meilleur))
    return meilleur


def recuit_simule(temperature_initiale=10.0, alpha=0.8, iterations=5, seed=42):
    rng = random.Random(seed)
    courant = INITIAL.copy()
    meilleur = courant.copy()
    temperature = temperature_initiale

    print("\n=== 2. RECUIT SIMULE (5 ITERATIONS) ===")
    print("Solution initiale :", afficher_tour(courant))
    print("Cout initial :", cout_tour(courant))

    for iteration in range(1, iterations + 1):
        # Choisir aleatoirement un voisin valide. Si aucun voisin n'existe,
        # on termine proprement.
        voisins = [v for v, _ in voisins_par_echange(courant)]
        if not voisins:
            print("Aucun voisin valide : arret.")
            break

        voisin = rng.choice(voisins)
        cout_courant = cout_tour(courant)
        cout_voisin = cout_tour(voisin)
        delta = cout_voisin - cout_courant

        if delta <= 0:
            accepte = True
            probabilite = 1.0
        else:
            probabilite = math.exp(-delta / temperature)
            accepte = rng.random() < probabilite

        if accepte:
            courant = voisin

        if cout_tour(courant) < cout_tour(meilleur):
            meilleur = courant.copy()

        print(f"\nIteration {iteration}")
        print(f"Temperature : {temperature:.3f}")
        print("Voisin :", afficher_tour(voisin))
        print("Cout du voisin :", cout_voisin)
        print("Delta :", delta)
        print(f"Probabilite d'acceptation : {probabilite:.4f}")
        print("Voisin accepte :", "oui" if accepte else "non")
        print("Cout courant :", cout_tour(courant))
        print("Meilleur cout :", cout_tour(meilleur))

        temperature *= alpha

    print("\nMeilleur circuit :", afficher_tour(meilleur))
    print("Meilleur cout :", cout_tour(meilleur))
    return meilleur


def selection_tournoi(population, rng, taille=3):
    candidats = rng.sample(population, min(taille, len(population)))
    return min(candidats, key=cout_tour)


def croisement_ox(parent1, parent2, rng):
    """Croisement OX sur les villes 2..8 ; la ville 1 reste au debut."""
    a = parent1[1:]
    b = parent2[1:]
    taille = len(a)
    debut, fin = sorted(rng.sample(range(taille), 2))

    enfant = [None] * taille
    enfant[debut:fin + 1] = a[debut:fin + 1]
    genes_restants = [ville for ville in b if ville not in enfant]
    positions_libres = [i for i, ville in enumerate(enfant) if ville is None]

    for position, ville in zip(positions_libres, genes_restants):
        enfant[position] = ville

    return [0] + enfant


def algorithme_genetique(taille_population=40, generations=100,
                         taux_mutation=0.15, seed=42):
    rng = random.Random(seed)
    population = []

    # Ne garder que les circuits dont toutes les liaisons existent.
    tentatives = 0
    while len(population) < taille_population:
        candidat = [0] + rng.sample(list(range(1, N)), N - 1)
        if cout_tour(candidat) < INF:
            population.append(candidat)
        tentatives += 1
        if tentatives > 200000:
            raise RuntimeError(
                "Impossible de generer assez de circuits valides. "
                "Verifiez la matrice des couts."
            )

    meilleur = min(population, key=cout_tour).copy()

    print("\n=== 3. ALGORITHME GENETIQUE ===")
    print("Taille population :", taille_population)
    print("Nombre de generations :", generations)

    for generation in range(1, generations + 1):
        nouvelle_population = [meilleur.copy()]  # elitisme

        while len(nouvelle_population) < taille_population:
            parent1 = selection_tournoi(population, rng)
            parent2 = selection_tournoi(population, rng)
            enfant = croisement_ox(parent1, parent2, rng)

            if rng.random() < taux_mutation:
                i, j = rng.sample(range(1, N), 2)
                enfant[i], enfant[j] = enfant[j], enfant[i]

            # Le croisement/mutation peut creer une liaison interdite.
            # Dans ce cas, on ignore l'enfant et on reessaie.
            if cout_tour(enfant) < INF:
                nouvelle_population.append(enfant)

        population = nouvelle_population
        candidat = min(population, key=cout_tour)
        if cout_tour(candidat) < cout_tour(meilleur):
            meilleur = candidat.copy()

        if generation % 10 == 0 or generation == 1:
            print(
                f"Generation {generation:3d} | "
                f"meilleur cout = {cout_tour(meilleur)}"
            )

    print("Meilleur circuit :", afficher_tour(meilleur))
    print("Meilleur cout :", cout_tour(meilleur))
    return meilleur


def verifier_circuit_reference():
    """Verifie le circuit de cout 98 identifie dans l'analyse."""
    circuit = [0, 1, 3, 4, 5, 6, 2, 7]
    print("\n=== VERIFICATION DU CIRCUIT DE REFERENCE ===")
    print("Circuit :", afficher_tour(circuit))
    print("Cout :", cout_tour(circuit))


def main():
    # Les methodes utilisent des parametres fixes pour faciliter la reproduction.
    print("RENDU - PROBLEME DU VOYAGEUR DE COMMERCE")
    print("Hypothese : matrice symetrique ; liaison '-' interdite.")

    print("\nCout de la solution initiale :", cout_tour(INITIAL))
    recherche_taboue(iterations=100, duree_taboue=5)
    recuit_simule(
        temperature_initiale=10.0,
        alpha=0.8,
        iterations=5,
        seed=42
    )
    algorithme_genetique(
        taille_population=40,
        generations=100,
        taux_mutation=0.15,
        seed=42
    )
    verifier_circuit_reference()


if __name__ == "__main__":
    main()
