from nltk.tree import ParentedTree

class SpanTree(ParentedTree):
    """
    Tree with added get_span functionality.
    This requires you to call 'convert' on the
    root node.
    """

    def convert(self): # todo: better name
        """
        replace leaf label with numbers to we can
        easily read the spans from subtrees
        """
        for i, pos in enumerate(self.treepositions('leaves')):
            self[pos] = i
        self.enumerated = True

    def get_span(self):
        """
        returns the span of the (sub-)tree
        (0,0) is only the first word
        (0,1) are the first two words
        """
        return (min(self.leaves()), max(self.leaves()))

    def span_is_subtree(self, start, end):
        for st in self.subtrees():
            st_start, st_end = st.get_span()
            if st_start == start and st_end == end:
                return True
        return False

    def span_from_pos(self, pos):
        leaf_id, depth = map(int, pos.split(':'))

        #print leaf_id, depth, role
        sub_tree = self[self.leaf_treeposition(leaf_id)[:-(depth+1)]]
        #print sub_tree.leaves()
        span_words = sub_tree.leaves()
        span = (leaf_id, leaf_id+len(span_words)-1)
        return span
