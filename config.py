'''
Created on Aug 14, 2012

@author: Nathan Schneider (nschneid)
'''

verbose = False

warn = False
'''Show warnings, even if verbose is False'''

fullNombank = False
'''Include concepts & arguments for NomBank predicates that cannot be verbalized'''

alignments = False
'''Include AMR triple-to-token alignments in the output'''

errorTolerant = False
'''If True, any exception encountered for an input sentence will be displayed 
and execution will proceed the next sentence. Otherwise, all exceptions are fatal.'''

showSentence = True
