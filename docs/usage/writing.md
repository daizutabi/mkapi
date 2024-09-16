# Writing Docstrings with MkAPI

Writing clear and informative docstrings is essential for effective documentation.
This guide explains how to write docstrings using MkAPI's features.

## What is a Docstring?

A docstring is a special type of comment in Python that describes what a
module, class, method, or function does. It is written as the first statement
in the code block and is enclosed in triple quotes (`"""` or `'''`).
Docstrings are accessible through the built-in `help()` function and are used
by documentation generators like MkAPI.

## Basic Structure of a Docstring

When writing a docstring, consider the following structure:

1. **Summary Line**: A brief description of the function or class.
2. **Parameters**: A section that describes the input parameters, their types,
   and what they represent.
3. **Returns**: A section that describes the return value and its type.
4. **Raises**: A section that lists any exceptions that the function may raise.
5. **Examples**: Optional, but providing examples of how to use the function
   can be very helpful.

Now that we understand the basic structure,
let's explore the unique features of MkAPI.

## Unique Features of MkAPI

One of the unique features of MkAPI is that it does not introduce its
own syntax within docstrings.
For example, to reference objects, you do not need to use Markdown link
syntax like `` [`object`][package.module.object] ``.
Simply writing the inline code is sufficient like `` `object` ``.

### Why Not Use Markdown Link Syntax?

Docstrings are often read directly in the source code by users and are also
displayed as popups in IDE (Integrated Development Environment)
like Visual Studio Code.
Unnecessary syntax can make the text difficult to read and distracting.
MkAPI takes this into consideration and generates readable
documentation without introducing special syntax within docstrings.
This keeps the docstrings clean and easy to understand.

### How Automatic Link Generation Works

MkAPI can automatically generate links from inline code.
It recognizes the context in which the docstring is written.

In a module's docstring, MkAPI resolves the names by referencing
the namespace within the module's scope.
In functions and classes, MkAPI resolves the names of children,
parent, and sibling objects.

This feature allows for more accurate and context-aware documentation generation.
When a docstring references an object, MkAPI will look up the hierarchy
to find the correct child, parent, or sibling, ensuring that the generated links
are accurate and relevant.

For example, if you have a class with several methods, and one method's
docstring references another method in the same class, MkAPI will correctly
resolve the reference to the sibling method.
Similarly, if a method references an attribute or another method in a parent class,
MkAPI will resolve the reference to the parent object.

This automatic resolution of parent and sibling names enhances the usability
and accuracy of the generated documentation, making it easier for users to
navigate and understand the relationships between different parts of your code.

### Automatic Link Generation for Types

MkAPI automatically generates links for type hints in class and
function definitions, and types written in the docstring sections.

Even when the types are outside the library and cannot be linked,
a tooltip with the full name is displayed.
This allows users to verify the actual type by hovering over it.

### Importance of the Summary Line

The summary line is used in the table of contents (TOC) for
modules and classes to display a list of members.
It is crucial for navigating users through the documentation.
MkAPI automatically generates the TOC, making it easier for users
to find and understand the structure of your code.

### Hot Reload

By using the `mkdocs serve` command, you can view your API documentation
in real-time while editing your source code and docstrings.
This feature allows you to see the changes immediately,
ensuring that your documentation is always up-to-date with your
latest code modifications.

Additionally, by using the `--dirty` mode, only the modified modules
are reloaded. This means that even if your library grows large,
you won't have to wait for the entire documentation to refresh.
This efficient reloading process saves time and enhances your productivity.

## Summary

This guide has provided an overview of how to write effective docstrings
using MkAPI's features. By following the structure and guidelines provided,
you can create clear and informative documentation.
