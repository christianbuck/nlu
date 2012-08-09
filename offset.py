#!/usr/bin/python

class Offset(object):
    def __init__(self, s1, s2, ignore_traces=False):
        assert len(s2) >= len(s1)
        self.mapping = []
        self.__max_in = len(s1)-1
        self.__max_out = len(s2)
        self.__ignore_traces = ignore_traces

        offset = 0
        for i1, w1 in enumerate(s1):
            i2 = offset + i1
            while i2 < len(s2) and not self.__eqwords(s2[i2],w1):
                offset += 1
                i2 = offset + i1
                assert i2 < len(s2), "could not match: %s %s\n%s %s" %(len(s1),
                                                                s1, len(s2), s2)
            assert self.__eqwords(s1[i1], s2[i2])
            self.mapping.append(i2) # indices start from 1
        #print self.mapping
        assert len(self.mapping) == self.__max_in + 1

    def __eqwords(self, w1, w2):
        if w1 == w2:
            return True
        if self.__ignore_traces and '*' in w1 and '*' in w2:
            return True
        return False

    def __str__(self):
        return '; '.join("%s->%s" %(i,j) for i,j in enumerate(self.mapping))

    def map_to_longer(self, idx):
        assert idx >= 0, "idx should be in [0,%s]" %self.__max_in
        assert idx <= self.__max_in, "idx should be in [0,%s]" %self.__max_in
        return self.mapping[idx]

if __name__ == '__main__':
    s1 = '* mein kleines haus'.split()
    s2 = '*5* * mein kleines gruenes haus'.split()

    for ignore_traces in (True, False):
        o = Offset(s1, s2, ignore_traces)
        print o

        for i1, w in enumerate(s1):
            i2 = o.map_to_longer(i1)
            print i1, s1[i1], i2, s2[i2]
