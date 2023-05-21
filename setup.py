from setuptools import setup, find_packages

with open("devchat/requirements.txt", encoding='utf-8') as f:
    requirements = f.read().splitlines()


# Function to read the contents of the README.md file
def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


# Read the contents of the README.md file
long_description = read_file("README.md")

setup(
    name="devchat",
    version="0.1.7",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "devchat = devchat._cli:main",
        ],
    },
    url="https://github.com/covespace/devchat",
    license="Apache License 2.0",
    description="DevChat is an open-source tool that helps developers write prompts to "
                "generate code and documentation.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3'
    ]
)
