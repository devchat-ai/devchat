import sys

from tinydb import TinyDB


def remove_topic_table(file_path: str):
    try:
        db = TinyDB(file_path)
        if "topics" in db.tables():
            db.drop_table("topics")
            print("The 'topics' table has been removed.")
        else:
            print("The file does not contain a 'topics' table.")
    except Exception as exc:
        print(f"Error: {exc}. The file is not a valid TinyDB file or could not be processed.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python remove_topic_table.py <file_path>")
        sys.exit(1)

    remove_topic_table(sys.argv[1])
