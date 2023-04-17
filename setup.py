from setuptools import setup, find_packages

setup(
    name="devchat",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "devchat = devchat._cli:main",
        ],
    },
)
