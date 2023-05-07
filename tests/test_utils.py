import pytest
from devchat.utils import parse_files


def test_parse_files_empty_input():
    assert not parse_files([])


def test_parse_files_nonexistent_file():
    with pytest.raises(ValueError, match="File .* does not exist."):
        parse_files(["nonexistent_file.txt"])


def test_parse_files_empty_file(tmpdir):
    empty_file = tmpdir.join("empty_file.txt")
    empty_file.write("")

    with pytest.raises(ValueError, match="File .* is empty."):
        parse_files([str(empty_file)])


def test_parse_files_single_file(tmpdir):
    file1 = tmpdir.join("file1.txt")
    file1.write("Hello, World!")

    assert parse_files([str(file1)]) == ["Hello, World!"]


def test_parse_files_multiple_files(tmpdir):
    file1 = tmpdir.join("file1.txt")
    file1.write("Hello, World!")
    file2 = tmpdir.join("file2.txt")
    file2.write("This is a test.")

    assert parse_files([str(file1), str(file2)]) == ["Hello, World!", "This is a test."]


def test_parse_files_invalid_path(tmpdir):
    file1 = tmpdir.join("file1.txt")
    file1.write("Hello, World!")
    invalid_path = "invalid/path/file2.txt"

    with pytest.raises(ValueError, match="File .* does not exist."):
        parse_files(f"{file1},{invalid_path}")
