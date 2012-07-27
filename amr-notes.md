Notes on Daniel's AMR class
---------------------------

The `dev` directory is a submodule linking to the repository on NFS.
The latest version of the `Amr` class is on the `new_amr` branch.

```python
>>> from dev.amr.amr import Amr
>>> y = Amr.from_triples([('p', 'ARG0-of', 'w'), ('w', 'ARG1', 'b')], {'p': 'person', 'w': 'write-01', 'b': 'book'})
# stores the second arg as y.node2concepts
# infers one or more roots and stores them in the set y.roots
>>> y
DAG{ (p / person :ARG0-of (w / write-01 :ARG1 (b / book) )) }
>>> y.triples(instances=False)
[('p', 'ARG0-of', ('w',)), ('w', 'ARG1', ('b',))]
# in this notation the RHS is a tuple (so as to permit hyperedges)
>>> q = Amr.from_string('(c / cookie)')
```
