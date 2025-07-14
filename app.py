# Slab fitting function based on required (in meters) and available slabs (in cm)
from typing import List, Tuple

def fit_slab(required_m: Tuple[float, float], available_slabs_cm: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], float]:
    # Convert required dimensions from meters to cm
    required_w = required_m[0] * 100
    required_h = required_m[1] * 100

    best_fit = None
    least_waste = float('inf')

    for slab in available_slabs_cm:
        slab_w, slab_h = slab

        # Try normal orientation
        if slab_w >= required_w and slab_h >= required_h:
            waste = (slab_w * slab_h) - (required_w * required_h)
            if waste < least_waste:
                best_fit = slab
                least_waste = waste

        # Try rotated orientation
        elif slab_w >= required_h and slab_h >= required_w:
            waste = (slab_w * slab_h) - (required_w * required_h)
            if waste < least_waste:
                best_fit = slab
                least_waste = waste

    return best_fit, least_waste































