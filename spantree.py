from nltk.tree import ParentedTree
import re

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

    def subtree_from_pos(self, leaf_id, depth):
        sub_tree = self[self.leaf_treeposition(leaf_id)[:-(depth+1)]]
        return sub_tree

    def parse_pos(self, pos):
        try:
            leaf_id, depth = map(int, pos.split(':'))
            return leaf_id, depth
        except:
            return None, None

    def find_trace(self, trace_id):
        '''
        looks for a subtree with a node value of *-trace_id
        return position in tree
        '''
        for pos in self.treepositions():
            if self[pos[:-1]].height() > 2:
                m = re.search('-(?P<traceid>\d+)$', self[pos].node)
                if m and int(m.groupdict()['traceid']) == trace_id:
                    return pos
        return None

    def span_from_pos(self, leaf_id, depth):
        # requires no conversion
        #print sub_tree.leaves()
        #leaf_id, depth
        subtree = self.subtree_from_pos(leaf_id, depth)
        #print 'node:', subtree.node
        #print 'children:', subtree.leaves()
        span_words = subtree.leaves()
        span = (leaf_id, leaf_id+len(span_words)-1)
        return span
