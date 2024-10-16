import numpy as np


def dixon_test(data):
    data_sorted = np.sort(data)
    n = len(data_sorted)
    print("Datos ordenados:", data_sorted)

    if n < 3:
        return []

    lower = (data_sorted[1] - data_sorted[0]) / (data_sorted[-1] - data_sorted[0])
    upper = (data_sorted[-1] - data_sorted[-2]) / (data_sorted[-1] - data_sorted[0])
    
    print(f"Lower: {lower}, Upper: {upper}")

    critical_value_lower = 0.2
    critical_value_upper = 0.2

    outliers = []
    if lower > critical_value_lower:
        outliers.append(data_sorted[0])
    if upper > critical_value_upper:
        outliers.append(data_sorted[-1])

    return outliers
