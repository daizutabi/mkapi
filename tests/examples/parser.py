from dataclasses import dataclass


@dataclass
class DocstringAttribute:
    """class docstring

    Attributes:
        x (integer): attribute X
        y: attribute Y
    """

    x: int
    """attribute x"""

    y: int
    """attribute y"""

    z: int
    """attribute z

    second paragraph
    """


@dataclass
class PrivateAttribute:
    x: int
    """attribute x"""

    _y: int
    """private attribute y"""
