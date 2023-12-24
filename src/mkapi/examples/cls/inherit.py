class Base:
    """Base class."""

    def func(self):
        """Function."""


class Sub(Base):
    """Subclass."""

    # Should be added.
    def func(self):
        pass

    # Should not be added.
    def __call__(self):
        pass

    # Should not be added.
    def __repr__(self):
        pass

    # Should not be added.
    def __str__(self):
        pass

    # and so on.
