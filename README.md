node-refactor-test
==================

An attempt to explore the consequences of what effect a refactoring of the Node class will have on storage of
the existing node data. 

Currently, all nodes are stored in a single class that manages the logic for the different kinds of nodes. My
suggestion is to make the Node an abstract container for the node data as well as any common methods, then have the
subclasses handle all of the different functionality. With the Modular ODM, this can be accomplished without
having the data storage for the Node information go away. This would allow us to convert items to other
types without a difficult conversion process, since all of the subclasses could share information. Of course,
there is always the potential for strange side effects, but only based on the difference in logic between classes,
not as a function of data conversion.

Each subclass can be responsible for knowing what the criteria for its uniqueness is, and that can be added to the
search functions for that subclass. This prevents sibling subclasses from trying to use their capabilities on other,
incompatible subclasses. Even so, you can maintain a hierarchy of classes in this structure.