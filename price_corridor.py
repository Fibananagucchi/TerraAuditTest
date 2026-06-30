import numpy as np

def calculate_corridor(area_hectares):
    # Демо-дані для MVP (історичні ціни оренди за 1 га з системи Прозорро)
    base_prices_per_ha = [45000, 48000, 52000, 41000, 95000, 47000, 50000, 49000, 120000]
    
    min_p = np.percentile(base_prices_per_ha, 25)
    median_p = np.median(base_prices_per_ha)
    max_p = np.percentile(base_prices_per_ha, 85)
    
    return (
        int(min_p * area_hectares),
        int(max_p * area_hectares),
        int(median_p * area_hectares)
    )