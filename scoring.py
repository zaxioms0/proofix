from lit_count import occurences, OccEntry


def scoring(entry: OccEntry, mode : str):
    return entry.pos_occs + entry.neg_occs


def get_best_literal(exclude):
    best_lits = sorted(
        occurences.keys(), key=lambda k: scoring(occurences[k], ""), reverse=True
    )
    for lit in best_lits:
        if lit not in exclude:
            return lit
