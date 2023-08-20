import os
from devchat.namespace import Namespace


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
