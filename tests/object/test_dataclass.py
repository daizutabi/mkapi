# def test_dataclass_attributes():
#     from mkapi.object import get_object

#     obj = get_object("mkapi.node.Import")
#     assert obj
#     assert isinstance(obj, Class)()
#     assert obj.name == "Person"
#     assert obj.doc.text == "This is a test class."
#     assert obj.doc.sections == [
#         Section(name="Attributes", items=[
#             Item(name="name", type="str", description="The name of the person."),
#             Item(name="age", type="int", description="The age of the person."),
#         ])
