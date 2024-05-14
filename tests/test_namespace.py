import os

import pytest

from devchat.engine import Namespace


def test_is_valid_name():
    # Test valid names
    assert Namespace.is_valid_name("") is True
    assert Namespace.is_valid_name("a") is True
    assert Namespace.is_valid_name("A.b") is True
    assert Namespace.is_valid_name("a.2.c") is True
    assert Namespace.is_valid_name("a_b") is True
    assert Namespace.is_valid_name("a-b") is True
    assert Namespace.is_valid_name("a_3.4-d") is True

    # Test invalid names
    assert Namespace.is_valid_name(".") is False
    assert Namespace.is_valid_name("..") is False
    assert Namespace.is_valid_name("a..b") is False
    assert Namespace.is_valid_name(".a") is False
    assert Namespace.is_valid_name("3.") is False
    assert Namespace.is_valid_name("a/.b") is False
    assert Namespace.is_valid_name("a\\b") is False
    assert Namespace.is_valid_name("a*b") is False
    assert Namespace.is_valid_name("a?1") is False
    assert Namespace.is_valid_name("a:b") is False
    assert Namespace.is_valid_name("a|b") is False
    assert Namespace.is_valid_name('a"b') is False
    assert Namespace.is_valid_name("2<b") is False
    assert Namespace.is_valid_name("a>b") is False


def test_get_file(tmp_path):
    # Create a Namespace instance with the temporary directory as the root path
    namespace = Namespace(tmp_path)

    # Test case 1: a file that exists
    # Create a file in the 'usr' branch
    os.makedirs(os.path.join(tmp_path, "usr", "a", "b", "c"), exist_ok=True)
    file_path = os.path.join(tmp_path, "usr", "a", "b", "c", "file1.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write("test")
    assert namespace.get_file("a.b.c", "file1.txt") == file_path

    # Test case 2: a file that doesn't exist
    assert namespace.get_file("d.e.f", "file2.txt") is None

    # Test case 3: a file that exists in a later branch
    # Create a file in the 'sys' branch
    os.makedirs(os.path.join(tmp_path, "usr", "g", "h", "i"), exist_ok=True)
    os.makedirs(os.path.join(tmp_path, "sys", "g", "h", "i"), exist_ok=True)
    file_path = os.path.join(tmp_path, "sys", "g", "h", "i", "file3.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write("test")
    assert namespace.get_file("g.h.i", "file3.txt") == file_path

    # Test case 4: a file in 'usr' overwrites the same in 'sys'
    # Create the same file in the 'usr' and 'sys' branches
    os.makedirs(os.path.join(tmp_path, "usr", "j", "k", "l"), exist_ok=True)
    usr_file_path = os.path.join(tmp_path, "usr", "j", "k", "l", "file4.txt")
    os.makedirs(os.path.join(tmp_path, "sys", "j", "k", "l"), exist_ok=True)
    sys_file_path = os.path.join(tmp_path, "sys", "j", "k", "l", "file4.txt")
    with open(usr_file_path, "w", encoding="utf-8") as file:
        file.write("test")
    with open(sys_file_path, "w", encoding="utf-8") as file:
        file.write("test")
    assert namespace.get_file("j.k.l", "file4.txt") == usr_file_path


def test_list_files(tmp_path):
    # Create a Namespace instance with the temporary directory as the root path
    namespace = Namespace(tmp_path)

    # Test case 1: a path that exists
    # Create a file in the 'usr' branch
    os.makedirs(os.path.join(tmp_path, "usr", "a", "b", "c"), exist_ok=True)
    file_path = os.path.join(tmp_path, "usr", "a", "b", "c", "file1.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write("test")
    assert namespace.list_files("a.b.c") == [file_path]

    # Test case 2: a path that doesn't exist
    with pytest.raises(ValueError):
        namespace.list_files("d.e.f")

    # Test case 3: a path exists but has no files
    os.makedirs(os.path.join(tmp_path, "org", "d", "e", "f"), exist_ok=True)
    assert not namespace.list_files("d.e.f")

    # Test case 4: a path that exists in a later branch
    # Create a file in the 'sys' branch
    os.makedirs(os.path.join(tmp_path, "usr", "g", "h", "i"), exist_ok=True)
    os.makedirs(os.path.join(tmp_path, "sys", "g", "h", "i"), exist_ok=True)
    file_path = os.path.join(tmp_path, "sys", "g", "h", "i", "file2.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write("test")
    assert namespace.list_files("g.h.i") == [file_path]

    # Test case 5: a path in 'usr' overwrites the same in 'sys'
    # Create the same file in the 'usr' and 'sys' branches
    os.makedirs(os.path.join(tmp_path, "usr", "j", "k", "l"), exist_ok=True)
    usr_file_path = os.path.join(tmp_path, "usr", "j", "k", "l", "file3.txt")
    os.makedirs(os.path.join(tmp_path, "sys", "j", "k", "l"), exist_ok=True)
    sys_file_path = os.path.join(tmp_path, "sys", "j", "k", "l", "file3.txt")
    with open(usr_file_path, "w", encoding="utf-8") as file:
        file.write("test")
    with open(sys_file_path, "w", encoding="utf-8") as file:
        file.write("test")
    assert namespace.list_files("j.k.l") == [usr_file_path]


def test_list_names(tmp_path):
    os.makedirs(os.path.join(tmp_path, "usr", "a", "b", "c"))
    os.makedirs(os.path.join(tmp_path, "org", "a", "b", "d"))
    os.makedirs(os.path.join(tmp_path, "sys", "a", "e"))

    namespace = Namespace(tmp_path)

    # Test listing child commands
    commands = namespace.list_names("a")
    assert commands == ["a.b", "a.e"]

    # Test listing all descendant commands
    commands = namespace.list_names("a", recursive=True)
    assert commands == ["a.b", "a.b.c", "a.b.d", "a.e"]

    # Test listing commands of an invalid name
    with pytest.raises(ValueError):
        namespace.list_names("b")

    # Test listing commands when there are no commands
    commands = namespace.list_names("a.e")
    assert len(commands) == 0

    # Test listing commands of the root
    commands = namespace.list_names()
    assert commands == ["a"]
