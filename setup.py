from setuptools import setup, find_packages

with open("devchat/requirements.txt", encoding='utf-8') as f:
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
