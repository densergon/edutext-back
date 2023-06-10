import numpy as np
import pandas as pd

# Parámetros
dx = 0.2
dy = 0.2
dt = 1 / 500
nx = int(1 / dx) + 1
ny = int(1 / dy) + 1

# Creo la malla vacía
U = np.zeros((nx, ny))
U_n = np.zeros((nx, ny))

for i in range(nx):
    for j in range(ny):
        x = i * dx  # valor correspondiente en la coordenada x
        y = j * dy  # igual, es como el incremento
        U[i, j] = 100 * np.sin(np.pi * x) * np.cos(np.pi * y)  # Asignar función en t=0

for k in range(4):  # ajusta los tiempos
    if k == 0:
        # Imprimir la tabla en t=0 (columnas como columnas)
        filas = np.arange(0, 1 + dx, dx)  # índices
        columnas = np.arange(0, 1 + dy, dy)
        f = np.round(U, decimals=3)
        sol = pd.DataFrame(f, index=filas, columns=columnas)
        print("Matriz U en t =", k)
        print(sol)
        print()
    else:
        for i in range(1, nx - 1):
            for j in range(1, ny - 1):
                U_n[i, j] = (
                    U[i, j]
                    + (dt / (dx * dx)) * (U[i + 1, j] - 2 * U[i, j] + U[i - 1, j])
                    + (dt / (dy * dy)) * (U[j, i + 1] - 2 * U[i, j] + U[j, i - 1])
                )
        U = U_n.copy()

        # Imprimir la tabla en t=1 (columnas como columnas)
        filas = np.arange(0, 1 + dx, dx)  # índices
        columnas = np.arange(0, 1 + dy, dy)  # índices
        f = np.round(U, decimals=3)
        sol = pd.DataFrame(f, index=filas, columns=columnas)
        print("Matriz U en t =", k)
        print(sol)
        print()
