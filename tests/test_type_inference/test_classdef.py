import astroid
import nose
from hypothesis import settings
from unittest import SkipTest
import tests.custom_hypothesis_support as cs
settings.load_profile("pyta")


def test_classdef_attribute_assign():
    """Test whether type of attributes are properly being set."""
    program = f'class Network:\n' \
              f'    def __init__(self, name, id):\n' \
              f'        self.name = name\n' \
              f'        self.id = id' \
              f'\n' \
              f'rogers = Network("Rogers", 5)\n' \
              f'rogers.name = "BoB"\n' \
              f'self = Network("asdf", 5)\n' \
              f'self.name = "asdfaBoB"\n' \
              f'\n'
    module, inferer = cs._parse_text(program)
    classdef_node = next(module.nodes_of_class(astroid.ClassDef))
    for attribute_lst in classdef_node.instance_attrs.values():
        for instance in attribute_lst:
            attribute_type = inferer.type_constraints\
                .lookup_concrete(classdef_node.type_environment.lookup_in_env(instance.attrname))
            value_type = inferer.type_constraints.lookup_concrete(instance.parent.value.type_constraints.type)
            assert attribute_type == value_type


def test_classdef_method_call():
    """Test whether type of the method call are properly being set"""
    program = f'class Network:\n' \
              f'    def __init__(self, name):\n' \
              f'        self.name = name\n' \
              f'    def get_name(self):\n' \
              f'        return self.name\n ' \
              f'\n' \
              f'rogers = Network("Rogers")\n' \
              f'rogers.get_name()' \
              f'\n'
    module, inferer = cs._parse_text(program)
    attribute_node = list(module.nodes_of_class(astroid.Attribute))[1]
    expected_rtype = attribute_node.parent.type_constraints.type
    actual_rtype = inferer.type_constraints.lookup_concrete(attribute_node.type_constraints.type.__args__[-1])
    assert actual_rtype == expected_rtype


def test_classdef_method_call_annotated_concrete():
    """Test whether types of the method calls are properly being set given the annotations."""
    program = f'class Network:\n' \
              f'    def __init__(self, name: str) -> None:\n' \
              f'        self.name = name\n' \
              f'        status = 0\n' \
              f'    def set_status(self, status: int) -> int:\n' \
              f'        self.status = status\n' \
              f'        return self.status\n' \
              f'\n'
    module, inferer = cs._parse_text(program)
    for functiondef_node in module.nodes_of_class(astroid.FunctionDef):
        self_name = functiondef_node.args.args[0].name
        actual_type = inferer.type_constraints.lookup_concrete(functiondef_node.type_environment.lookup_in_env(self_name))
        assert actual_type.__forward_arg__ == functiondef_node.parent.name
        for i in range(1, len(functiondef_node.args.annotations)):
            arg_name = functiondef_node.args.args[i].name
            actual_type = inferer.type_constraints.lookup_concrete(functiondef_node.type_environment.lookup_in_env(arg_name))
            assert actual_type.__name__ == functiondef_node.args.annotations[i].name
        expected_rtype = inferer.type_constraints\
            .lookup_concrete(functiondef_node.parent.type_environment.lookup_in_env(functiondef_node.name))
        assert functiondef_node.returns.name == expected_rtype.__args__[-1].__name__


def test_bad_attribute_access():
    """ User tries to access a non-existing attribute; or misspells the attribute name.
    """
    program = f'x = 1\n' \
              f'x.wrong_name\n'
    try:
        module, inferer = cs._parse_text(program)
    except:
        raise SkipTest()
    call_node = next(module.nodes_of_class(astroid.Call))
    expected_msg = f'Attribute access error!\n' \
                   f'In the Attribute node in line 2:\n' \
                   f'the object "x" does not have the attribute "wrong_name".'
    assert call_node.type_constraints.type.msg == expected_msg


def test_builtin_method_call_bad_self():
    """ User tries to call a method on an object of the wrong type (self).
    """
    program = f'x = 1\n' \
              f'x.append(1.0)\n'
    try:
        module, inferer = cs._parse_text(program)
    except:
        raise SkipTest()
    call_node = next(module.nodes_of_class(astroid.Call))
    expected_msg = f'In the Call node in line 2, when calling the method "append":\n' \
                   f'this function expects to be called on an object of the class List, but was called on an object of ' \
                   f'inferred type int.'
    assert call_node.type_constraints.type.msg == expected_msg


def test_builtin_method_call_bad_argument():
    """ User tries to call a method on an argument of the wrong type.
    """
    program = f'x = 1\n' \
              f'x.extend(1)\n'
    try:
        module, inferer = cs._parse_text(program)
    except:
        raise SkipTest()
    call_node = next(module.nodes_of_class(astroid.Call))
    expected_msg = f'In the Call node in line 2, when calling the method "extend":\n' \
                   f'in parameter (1), the function was expecting an object of type iterable ' \
                   f'but was given an object of type int.'
    assert call_node.type_constraints.type.msg == expected_msg


if __name__ == '__main__':
    nose.main()
