import sys

if sys.platform == "win32":
    import result.pysf.pysf.sf as sf
elif sys.platform == "darwin":
    import result.pysf.pysf.sf as sf
else:
    print("Unsupported operating system")
    sys.exit(1)

if __name__ == "__main__":
    attrs = [attr for attr in dir(sf) if not (attr.startswith("__") and attr.endswith("__"))]
    with open("result/pysf/__init__.py", "w") as file:
        file.write(f"from .pysf.sf import (\n")
        for attr in attrs:
            file.write(f"   {attr},\n")
        file.write(f")\n")
    print("Successfully generated __init__.py")
