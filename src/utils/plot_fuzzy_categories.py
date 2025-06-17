import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 1, 1000)

categories = {
    "nada": lambda x: np.where(x <= 0.1, 1.0, 0.0),
    "poco": lambda x: np.maximum(np.minimum((x - 0.1)/0.15, (0.4 - x)/0.15), 0.0),
    "medio": lambda x: np.maximum(np.minimum((x - 0.3)/0.2, (0.7 - x)/0.2), 0.0),
    "muy": lambda x: np.where(x >= 0.8, 1.0, np.maximum(0.0, (x - 0.6)/0.2))
}

plt.figure(figsize=(10, 6))
for name, func in categories.items():
    plt.plot(x, func(x), label=name, linewidth=2)

plt.title("Funciones de Pertenencia")
plt.xlabel("Valor de sabor (x)")
plt.ylabel("Grado de pertenencia (μ)")
plt.legend()
plt.grid(True)
plt.xticks(np.arange(0, 1.1, 0.1))
plt.show()