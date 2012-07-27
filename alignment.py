#!/usr/bin/env python2.7
'''
Bidirectional mapping/set of alignments between two sequences. 
The mapping holds token offsets within the sequences.

@author: Nathan Schneider (nschneid)
@since: 2012-07-26
'''
from __future__ import print_function
import os, sys, re
from collections import defaultdict

class Alignment(object):
	'''
	Bidirectional mapping/set of alignments between two sequences. 
	The mapping holds token offsets within the sequences.
	
	>>> source = [0, 1, 2, 3, 4]
	>>> target = [0, 1, 2, 3]
	
	# one-to-one
	
	+ + + + source
	|  /  |
	- - - - target
	
	>>> a = Alignment()
	>>> a.link(0, 2)
	>>> a.link(1, 1)
	>>> a.aligned(3, 0)
	False
	>>> a.link(3, 0)
	>>> a.aligned(3, 0)
	True
	>>> a[0:]
	2
	>>> a[:0]
	3
	>>> print(a[4:])
	None
	>>> a[0:2]
	[(0, 2)]
	>>> a[0:0]
	[]
	>>> a[(0,1):(1,2)]
	[(0, 2), (1, 1)]
	>>> a[(1,2):0]
	[]
	>>> print(a[slice(Ellipsis,0)])
	[(3, 0)]
	>>> a.coversSource(source)
	False
	>>> a.coversTarget(target)
	False
	
	# one-to-many
	
	+ + + +
	|  /| |
	- - - -
	
	>>> b = Alignment('one2many', a[:])
	>>> b
	Alignment('one2many', [(0, 2), (1, 1), (3, 0)])
	>>> b.link(1, 3)
	>>> b[1:]
	set([1, 3])
	>>> b[:3]
	1
	>>> b[:]
	[(0, 2), (1, 1), (1, 3), (3, 0)]
	>>> b.coversSource(source)
	False
	>>> b.coversTarget(target)
	True
	
	# many-to-many
	
	+ + + +
	|\ /| |
	- - - -
	
	>>> c = Alignment('many2many', b[:])
	>>> c.link(4, 2)
	>>> c.link(2, 2)
	>>> c[(0,2,4):(0,1,2)]
	[(0, 2), (2, 2), (4, 2)]
	>>> c.coversSource(source)
	True
	>>> c.coversTarget(target)
	True
	>>> c.adjacencies(source, target)	# doctest:+NORMALIZE_WHITESPACE
	[[0, 0, 1, 0], 
	 [0, 1, 0, 1], 
	 [0, 0, 1, 0], 
	 [1, 0, 0, 0], 
	 [0, 0, 1, 0]]
	
	>>> d = Alignment('many2many', c[:])
	>>> d==b
	False
	>>> d.unlink(4, 2)
	>>> d.unlink(2, 2)
	>>> Alignment('one2many', d[:])==b
	True
	
	# try to add invalid links
	
	>>> a.link(4, 2)	# doctest:+ELLIPSIS
	Traceback (most recent call last):
	...
	ValueError: Illegal alignment: linking 4 to 2 would violate one2one structure
	>>> b.link(4, 2)
	Traceback (most recent call last):
	...
	ValueError: Illegal alignment: linking 4 to 2 would violate one2many structure
	>>> c.link(1, 1)
	Traceback (most recent call last):
	...
	ValueError: Alignment from 1 to 1 already exists
	>>> c.unlink(0, 0)
	Traceback (most recent call last):
	...
	ValueError: No alignment from 0 to 0 exists, so cannot remove it
	'''
	def __init__(self, form='one2one' or 'one2many' or 'many2one' or 'many2many', pairs=None):
		sform, tform = form.split('2')
		assert sform in ['one', 'many']
		assert tform in ['one', 'many']
		self._form = form
		
		# forward mapping (source -> target)
		if tform=='many':
			self._fwd = defaultdict(set)
		else:
			self._fwd = {}
			
		# backward mapping (target -> source)
		if sform=='many':
			self._bwd = defaultdict(set)
		else:
			self._bwd = {}
			
		if pairs is not None:
			for s,t in pairs:
				self.link(s,t)
			
	def link(self, s, t):
		'''
		Add an alignment link from source index s to target index t 
		(will not modify any existing alignments)
		'''
		if self.aligned(s, t):
			raise ValueError('Alignment from {} to {} already exists'.format(s, t))
		
		sform, tform = self._form.split('2')
		if sform=='many':
			self._bwd[t].add(s)
		else:
			if t in self._bwd:
				raise ValueError('Illegal alignment: linking {} to {} would violate {} structure'.format(s, t, self._form))
			self._bwd[t] = s
		
		if tform=='many':
			self._fwd[s].add(t)
		else:
			if s in self._fwd:
				raise ValueError('Illegal alignment: linking {} to {} would violate {} structure'.format(s, t, self._form))
			self._fwd[s] = t
		
		
	def unlink(self, s, t):
		'''
		Removes an existing alignment link from source index s to target index t
		'''
		if not self.aligned(s, t):
			raise ValueError('No alignment from {} to {} exists, so cannot remove it'.format(s, t))
		
		sform, tform = self._form.split('2')
		if sform=='many':
			self._bwd[t].remove(s)
		else:
			del self._bwd[t]
		
		if tform=='many':
			self._fwd[s].remove(t)
		else:
			del self._fwd[s]
	
	def fwd(self, s):
		'''Forward lookup: retrieve target index(es) corresponding to the given source index.
		If one-to-one or many-to-one and the source index is unaligned, returns None.'''
		return self._fwd.get(s, set() if self._form.split('2')[1]=='many' else None)
		
	def bwd(self, t):
		'''Backward lookup: retrieve source index(es) corresponding to the given target index.
		If one-to-one or one-to-many and the target index is unaligned, returns None.'''
		return self._bwd.get(t, set() if self._form.split('2')[0]=='many' else None)
	
	def coversSource(self, sourceIndices):
		return all(self.fwd(s) not in [None,set()] for s in sourceIndices)
		
	def coversTarget(self, targetIndices):
		return all(self.bwd(t) not in [None,set()] for t in targetIndices)
		
	def aligned(self, s, t):
		'''Given a source index and a target index, determines whether an 
		alignment link connects them.'''
		if self._form.split('2')[1]=='many':
			return t in self.fwd(s)
		return self.fwd(s)==t
		
	def adjacencies(self, sourceIndices, targetIndices):
		'''Adjacency matrix.'''
		return [[int(self.aligned(s,t)) for t in targetIndices] for s in sourceIndices]
		
	def __getitem__(self, key):
		assert isinstance(key, slice)
		assert key.step is None
		src, tgt = key.start, key.stop
		if src is not None and tgt is not None:
			# list all existing alignments between the given source index(es) 
			# and the given target index(es)
			if src is Ellipsis:
				src = self._fwd.keys()
			elif not hasattr(src, '__iter__'):
				src = {src}
			
			if tgt is Ellipsis:
				tgt = self._bwd.keys()
			elif not hasattr(tgt, '__iter__'):
				tgt = {tgt}

			return [(s,t) for s in src for t in tgt if self.aligned(s,t)]
		elif (src is None or src is Ellipsis) and (tgt is None or tgt is Ellipsis):
			# list all alignment pairs
			if self._form.split('2')[1]=='many':
				return [(s,t) for s in self._fwd for t in self._fwd.get(s,[])]
			return self._fwd.items()
		elif tgt is None:	# forward lookup
			if hasattr(src, '__iter__'):
				return [self.fwd(s) for s in src]
			else:
				return self.fwd(src)
		else:	# backward lookup
			if hasattr(tgt, '__iter__'):
				return [self.bwd(t) for t in tgt]
			else:
				return self.bwd(tgt)
	
	def __eq__(self, that):
		return self.__dict__==that.__dict__
	
	def __repr__(self):
		return 'Alignment(%s, %s)' % (repr(self._form), repr(self[:]))

if __name__=='__main__':
	import doctest
	doctest.testmod()
