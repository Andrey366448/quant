# @title
import numpy as np


def simple_npy_to_txt_3d(npy_file, txt_file=None):
    """
    Простая конвертация 3D .npy в .txt
    """
    data = np.load(npy_file)

    if txt_file is None:
        txt_file = npy_file.replace('.npy', '.txt')

    with open(txt_file, 'w') as f:
        f.write(f"# Shape: {data.shape}\n")
        for i in range(data.shape[0]):
            f.write(f"# Slice {i}\n")
            np.savetxt(f, data[i], fmt='%.6f')
            f.write("\n")

    print(f"Готово! Файл сохранен как: {txt_file}")


# Использование
simple_npy_to_txt_3d("new_G_set.npy")
simple_npy_to_txt_3d("new_routes.npy")
