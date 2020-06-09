class Abstract:
    """Abstract class."""

    def call(self):
        """Abstract method."""
        raise NotImplementedError

    def func(self):
        """Function."""


class Concrete(Abstract):
    """Concrete class."""

    def call(self):
        """Concrete method."""

    # Should be added.
    def func(self):
        pass

    # Should not be added.
    def __call__(self):
        return self.call()

    # Should not be added.
    def __repr__(self):
        return self.call()

    # Should not be added.
    def __str__(self):
        return self.call()

    # and so on.
