def add_number(a:int , b:int) -> int:
    return a+b

def test_add_numbers():
    assert add_number(2,3) == 5
    assert add_number(4,3) == 7
    assert add_number(3,3) == 6
    assert add_number(1,3) == 4


