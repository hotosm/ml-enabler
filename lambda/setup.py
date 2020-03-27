"""Setup."""

from setuptools import setup, find_packages

inst_reqs = [
    "mercantile",
    "requests",
    "pillow",
    "numpy"
]
extra_reqs = {"test": ["pytest", "pytest-cov"]}

setup(
    name="app",
    version="0.0.1",
    description=u"Lambda Download and Predict",
    python_requires=">=3",
    keywords="AWS-Lambda Python",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
