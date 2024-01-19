import os

import numpy as np
from PIL import Image

from vtf import VTF

result_path = r"C:\Users\megaz\Desktop\pizda\gmod\result/"

for (dirpath, dirnames, filenames) in os.walk(r"C:\Users\megaz\Desktop\pizda\gmod_extract"):
    for file in filenames:
        if file.find(".vtf") != -1:
            with open(dirpath+"/"+file, "rb") as f:
                data = f.read()
                try:
                    vtf = VTF(data)
                    print(result_path+file+"_low.png")
                    low = Image.fromarray(np.asarray(vtf.get_low_res(), dtype=np.uint8))
                    # low.show()
                    # low.save(result_path+file+"_low.png")
                    for i in range(vtf.mipmapCount):
                        high = Image.fromarray(np.asarray(vtf.get_high_res(i), dtype=np.uint8))
                        high.save(result_path+file+f"_high_{i}.png")
                        # high.show()
                except Exception as e:
                    pass