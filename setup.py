from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="degree_preserving_rewiring",
    version="0.1.0",
    description="Functions to tune the assortativity of a networkx Graph while maintaining degree sequence",
    package_dir={"": "degree_preserving_rewiring"},
    packages=find_packages(where="app"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    author="Shane Mannion",
    author_email="shane.mannion@ul.ie",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
