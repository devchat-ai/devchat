from setuptools import setup, find_packages

setup(
    name="devchat",
    version="0.1.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "devchat = devchat._cli:main",
        ],
    },
)
