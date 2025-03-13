from setuptools import setup, find_packages

setup(
    name="aquaexchange",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "geopandas",
        "pystac-client",
        "planetary-computer",
        "shapely",
        "pandas",
        "numpy",
        "rasterio",
        "lxml",
        "fastapi",
        "azure-storage-blob",
        "python-dotenv"
    ],
    author="Swaraj Saha",
    description="A package for processing farm pond data using Landsat imagery.",
    url="https://github.com/swaraj-saha/Blue_AquaExchange",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
