"""Helpers for performing tests."""
import itertools
from typing import Type, Tuple, Callable, Iterable, Iterator, TypeVar

from srctools.math import (
    Py_Vec, Cy_Vec,
    Py_FrozenVec, Cy_FrozenVec,
    Py_Angle, Cy_Angle,
    Py_Matrix, Cy_Matrix,
    Py_parse_vec_str, Cy_parse_vec_str,
)
from srctools import math as vec_mod
import pytest
import math
import builtins

VALID_NUMS = [
    # 10e38 is the max single value, make sure we use double-precision.
    30, 1.5, 0.2827, 2.3464545636e47,
]
VALID_NUMS += [-x for x in VALID_NUMS]

VALID_ZERONUMS = VALID_NUMS + [0, -0]

# In SMD files the maximum precision is this, so it should be a good reference.
EPSILON = 1e-6

PyCVec = Tuple[Type[Py_Vec], Type[Py_Angle], Type[Py_Matrix], Callable[..., Tuple[float, float, float]]]
T = TypeVar('T')
VecClass = Type[vec_mod.VecBase]
AngleClass = Type[vec_mod.AngleBase]


def iter_vec(nums: Iterable[T]) -> Iterator[Tuple[T, T, T]]:
    for x in nums:
        for y in nums:
            for z in nums:
                yield x, y, z


def assert_ang(ang, pitch=0, yaw=0, roll=0, msg='', tol=EPSILON):
    """Asserts that an Angle is equal to the provided angles."""
    # Don't show in pytest tracebacks.
    __tracebackhide__ = True

    pitch %= 360
    yaw %= 360
    roll %= 360

    # Ignore slight variations, and handle one being ~359.99
    if not (
        math.isclose(ang.pitch, pitch, abs_tol=tol) or
        math.isclose(ang.pitch - pitch, 360.0, abs_tol=tol)
    ):
        failed = 'pitch'
    elif not (
        math.isclose(ang.yaw, yaw, abs_tol=tol) or
        math.isclose(ang.yaw - yaw, 360.0, abs_tol=tol)
    ):
        failed = 'yaw'
    elif not (
        math.isclose(ang.roll, roll, abs_tol=tol) or
        math.isclose(ang.roll - roll, 360.0, abs_tol=tol)
    ):
        failed = 'roll'
    else:
        # Success!
        return

    new_msg = "Angle({:.10g}, {:.10g}, {:.10g}).{} != ({:.10g}, {:.10g}, {:.10g})".format(ang.pitch, ang.yaw, ang.roll, failed, pitch, yaw, roll)
    if msg:
        new_msg += ': ' + str(msg)
    pytest.fail(new_msg)


def assert_vec(vec, x, y, z, msg='', tol=EPSILON, type=None):
    """Asserts that Vec is equal to (x,y,z)."""
    # Don't show in pytest tracebacks.
    __tracebackhide__ = True

    assert builtins.type(vec).__name__ in ('Vec', 'FrozenVec')
    if type is not None:
        assert builtins.type(vec) is type, f'{builtins.type(vec)} != {type}: {msg}'

    if not math.isclose(vec.x, x, abs_tol=tol):
        failed = 'x'
    elif not math.isclose(vec.y, y, abs_tol=tol):
        failed = 'y'
    elif not math.isclose(vec.z, z, abs_tol=tol):
        failed = 'z'
    else:
        # Success!
        return

    new_msg = "{!r}.{} != ({}, {}, {})".format(vec, failed, x, y, z)
    if msg:
        new_msg += ': ' + str(msg)
    pytest.fail(new_msg)


def assert_rot(rot, exp_rot, msg=''):
    """Asserts that the two rotations are the same."""
    # Don't show in pytest tracebacks.
    __tracebackhide__ = True

    for x, y in itertools.product(range(3), range(3)):
        if not math.isclose(rot[x, y], exp_rot[x, y], abs_tol=EPSILON):
            break
    else:
        # Success!
        return

    new_msg = f'{rot} != {exp_rot}\nAxis: {x},{y}'
    if msg:
        new_msg += ': ' + str(msg)
    pytest.fail(new_msg)


if Py_Vec is Cy_Vec:
    parms = [(Py_Vec, Py_FrozenVec, Py_Angle, Py_Matrix, Py_parse_vec_str)]
    names = ['Python']
    print('No _vec! ')
else:
    parms = [(Py_Vec, Py_FrozenVec, Py_Angle, Py_Matrix, Py_parse_vec_str),
             (Cy_Vec, Cy_FrozenVec, Cy_Angle, Cy_Matrix, Cy_parse_vec_str)]
    names = ['Python', 'Cython']


@pytest.fixture(params=parms, ids=names)
def py_c_vec(request):
    """Run the test twice, for the Python and C versions."""
    orig_vec = vec_mod.Vec
    orig_fvec = vec_mod.FrozenVec
    orig_Angle = vec_mod.Angle
    orig_Matrix = vec_mod.Matrix
    orig_parse = vec_mod.parse_vec_str

    try:
        (
            vec_mod.Vec,
            vec_mod.FrozenVec,
            vec_mod.Angle,
            vec_mod.Matrix,
            vec_mod.parse_vec_str,
        ) = request.param
        yield request.param
    finally:
        vec_mod.Vec = orig_vec
        vec_mod.FrozenVec = orig_fvec
        vec_mod.Angle = orig_Angle
        vec_mod.Matrix = orig_Matrix
        vec_mod.parse_vec_str = orig_parse


def parameterize_cython(param: str, py_vers, cy_vers):
    """If the Cython version is available, parameterize the test function."""
    if py_vers is cy_vers:
        return pytest.mark.parametrize(param, [py_vers], ids=['Python'])
    else:
        return pytest.mark.parametrize(param, [py_vers, cy_vers], ids=['Python', 'Cython'])


@pytest.fixture(params=['Vec', 'FrozenVec'])
def frozen_thawed_vec(py_c_vec, request) -> VecClass:
    """Support testing both mutable and immutable vectors."""
    yield getattr(vec_mod, request.param)


@pytest.fixture(params=['Angle', 'FrozenAngle'])
def frozen_thawed_angle(py_c_vec, request) -> AngleClass:
    """Support testing both mutable and immutable angles."""
    yield getattr(vec_mod, request.param)
