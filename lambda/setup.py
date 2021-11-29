"""Setup."""

from setuptools import setup, find_packages

inst_reqs = [
    "mercantile == 1.1.5",
    "requests",
    "geojson",
    "pillow",
    "gdal == 2.4.2",
    "shapely == 1.6.4",
    "affine == 2.3.0",
    "numpy == 1.19.0", 
    "rasterio == 1.1.5"
]
extra_reqs = {"test": ["pytest", "pytest-cov"]}

setup(
    name="app",
    version="0.5.0",
    description=u"Lambda Download and Predict",
    python_requires=">=3",
    keywords="AWS-Lambda Python",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
