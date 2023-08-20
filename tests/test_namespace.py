import os
from devchat.namespace import Namespace


def test_is_valid_name():
    # Test valid names
    assert Namespace.is_valid_name('') is True
    assert Namespace.is_valid_name('a') is True
    assert Namespace.is_valid_name('A.b') is True
    assert Namespace.is_valid_name('a.2.c') is True
    assert Namespace.is_valid_name('a_b') is True
    assert Namespace.is_valid_name('a-b') is True
    assert Namespace.is_valid_name('a_3.4-d') is True

    # Test invalid names
    assert Namespace.is_valid_name('.') is False
    assert Namespace.is_valid_name('..') is False
    assert Namespace.is_valid_name('a..b') is False
    assert Namespace.is_valid_name('.a') is False
    assert Namespace.is_valid_name('3.') is False
    assert Namespace.is_valid_name('a/.b') is False
    assert Namespace.is_valid_name('a\\b') is False
    assert Namespace.is_valid_name('a*b') is False
    assert Namespace.is_valid_name('a?1') is False
    assert Namespace.is_valid_name('a:b') is False
    assert Namespace.is_valid_name('a|b') is False
    assert Namespace.is_valid_name('a"b') is False
    assert Namespace.is_valid_name('2<b') is False
    assert Namespace.is_valid_name('a>b') is False


def test_get_path(tmp_path):
    # Create a Namespace instance with the temporary directory as the root path
    namespace = Namespace(str(tmp_path))

    # Test case 1: a path that exists
    # Create a file in the 'usr' branch
    os.makedirs(os.path.join(tmp_path, 'usr', 'a', 'b', 'c'), exist_ok=True)
    assert namespace.get_path('a.b.c') == os.path.join('usr', 'a', 'b', 'c')

    # Test case 2: a path that doesn't exist
    assert namespace.get_path('d.e.f') is None

    # Test case 3: a path that exists in a later branch
    # Create a file in the 'sys' branch
    os.makedirs(os.path.join(tmp_path, 'sys', 'g', 'h', 'i'), exist_ok=True)
    assert namespace.get_path('g.h.i') == os.path.join('sys', 'g', 'h', 'i')

    # Test case 4: a path in 'usr' overwrites the same in 'sys'
    # Create the same file in the 'usr' and 'sys' branches
    os.makedirs(os.path.join(tmp_path, 'usr', 'j', 'k', 'l'), exist_ok=True)
    os.makedirs(os.path.join(tmp_path, 'sys', 'j', 'k', 'l'), exist_ok=True)
    assert namespace.get_path('j.k.l') == os.path.join('usr', 'j', 'k', 'l')


def test_list_names(tmp_path):
    os.makedirs(os.path.join(tmp_path, 'usr', 'a', 'b', 'c'))
    os.makedirs(os.path.join(tmp_path, 'org', 'a', 'b', 'd'))
    os.makedirs(os.path.join(tmp_path, 'sys', 'a', 'e'))

    namespace = Namespace(str(tmp_path))

    # Test listing child commands
    commands = namespace.list_names('a')
    assert commands == ['a.b', 'a.e']

    # Test listing all descendant commands
    commands = namespace.list_names('a', recursive=True)
    assert commands == ['a.b', 'a.b.c', 'a.b.d', 'a.e']

    # Test listing commands of an invalid name
    commands = namespace.list_names('b')
    assert commands is None

    # Test listing commands when there are no commands
    commands = namespace.list_names('a.e')
    assert not commands

    # Test listing commands of the root
    commands = namespace.list_names()
    assert commands == ['a']
