set -e

pip install --no-binary :all: "pydantic<2"
pip install charset-normalizer --no-binary :all:
pip install git+https://github.com/yangbobo2021/tiktoken.git
pip install .
python -c "import site; print(site.getsitepackages())"