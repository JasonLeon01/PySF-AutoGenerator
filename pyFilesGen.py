import os
import shutil

import build.Release.pysf.sf as sf

if __name__ == "__main__":
    attrs = [
        attr for attr in dir(sf) if not (attr.startswith("__") and attr.endswith("__"))
    ]
    if not os.path.exists("result"):
        os.makedirs("result")
    if os.path.exists("result/pysf"):
        shutil.rmtree("result/pysf")
    os.makedirs("result/pysf")

    with open("result/pysf/__init__.py", "w") as file:
        file.write("from . import pysf\n")
        file.write("sf =  pysf.sf\n\n")

        for attr in attrs:
            file.write(f"{attr} = sf.{attr}\n")

    print("Successfully generated __init__.py")
