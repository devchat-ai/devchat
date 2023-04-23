from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="devchat",
    version="0.1.2",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "devchat = devchat._cli:main",
        ],
    },
)
