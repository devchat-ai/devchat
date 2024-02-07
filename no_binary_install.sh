set -e
source $CONDA_PREFIX/etc/profile.d/conda.sh

# input target dir with shell script argument
if [ -n "$1" ]; then
    TARGET_DIR=$1
else
    # Error
    echo "Please input a target dir with shell script argument"
    exit 1
fi
mkdir -p $TARGET_DIR

conda remove -n devchat-no-binary --all --yes
conda create -n devchat-no-binary python=3.8 -y

conda activate devchat-no-binary

SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
OLD_FOLDERS=$(mktemp)
ls $SITE_PACKAGES > "$OLD_FOLDERS"


pip install --no-binary :all: "pydantic<2"
pip install charset-normalizer --no-binary :all:
pip install git+https://github.com/yangbobo2021/tiktoken.git
pip install .


NEW_FOLDERS=$(mktemp)
ls $SITE_PACKAGES > "$NEW_FOLDERS"
ADDED_FOLDERS=$(comm -13 "$OLD_FOLDERS" "$NEW_FOLDERS")

for folder in $ADDED_FOLDERS; do
    cp -r "$SITE_PACKAGES/$folder" "$TARGET_DIR"
done

rm "$OLD_FOLDERS" "$NEW_FOLDERS"

NETWORKX_ATLAS="$TARGET_DIR/networkx/generators/atlas.py"
sed -i '' 's|importlib\.resources|importlib_resources|' "$NETWORKX_ATLAS"	

echo "DevChat packages have installed to $TARGET_DIR"
