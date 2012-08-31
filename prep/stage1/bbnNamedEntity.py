# LKG

import os
from xml.dom.minidom import parseString
from on.corpora import tree
from commonUtil import cUtil
from collections import defaultdict
from itertools import chain
#from xml.etree import ElementTree
class bbnNE(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''

    # Identify the concept for a named entity and use it the the generation of a named entity AMR fragment / subtree
    def covNEtoAMR(self,a_tree,arg_type,entType,entSubType,descriptor):
        descriptor = descriptor.lower().replace(' ','-')
        if entType == 'PERSON':
                if descriptor == '':
                        concept = entType
                else:
                        concept = descriptor
        elif entType == 'PERSON_DESC':
                concept = ''
        elif entType =='ORGANIZATION':
                if entSubType == 'CORPORATION':
                        concept = 'company'
                elif entSubType == 'GOVERNMENT':
                        concept = 'government-organization'
                else:
                        concept = entSubType
        elif entType in ['GPE', 'LOCATION', 'EVENT', 'NORP']:
                if entSubType == 'OTHER':
                        concept = entType
                else:
                        concept = entSubType
        elif entType == 'FAC':
                if entSubType == 'OTHER':
                        concept = 'facility'
                else:
                        concept = entSubType + '-facility'
        else: # Covers: PLANT, ANIMAL, DISEASE, GAME, LANGUAGE, LAW, PRODUCT
                if not entType in ['SUBSTANCE', 'WORK_OF_ART','CONTACT_INFO']:
                        concept = entType

        conv_tree = self.convName(a_tree,arg_type,concept)
        print conv_tree
        return conv_tree


    # Convert a named entity into an AMR fragment. Returns a fragment of the temporary tree (interim - NOT AMR format)
    def convName(self,a_tree,arg_type,concept):
        temp_tree = None
        temp_tree = self.generateNodewithProptag(a_tree.name_type,arg_type,concept)
        name_child = self.generateNodewithProptag("name",["name"],'')
        for index, a_child in enumerate(a_tree.get_word_string().split()):
            temp_child = self.generateLeafwithProptag(a_child +"|"+"op"+str(index+1),'"'+a_child +'"'+"|"+"op"+str(index+1),[])
            name_child.children.append(temp_child)
        temp_tree.children.append(name_child)
        return temp_tree


    # Generation of an AMR fragment - for leaves. Returns a fragment of the temporary tree (interim - NOT AMR format)
    def generateLeafwithProptag(self,a_tag,a_word,arg_type):
        temp_tree = None
        if arg_type != []:
            temp_tree = tree.tree(a_word +"|"+"|".join(arg_type))
            temp_tree.word = a_word +"|"+"|".join(arg_type)
        else:
            temp_tree = tree.tree(a_word)
            temp_tree.word = a_word
        return temp_tree


    # Generation of an AMR fragment - for nodes. Returns a fragment of the temporary tree (interim - NOT AMR format)
    def generateNodewithProptag(self,a_tag,arg_type,concept):
        concept = concept.lower()
        temp_tree = None
        if arg_type != [] and arg_type != ["name"]:
            temp_tree = tree.tree(concept+"|"+"|".join(arg_type))
        elif arg_type == ["name"]:
            temp_tree = tree.tree(a_tag+"|"+"|".join(arg_type))
        else:
            temp_tree = tree.tree(concept)
        return temp_tree


    # Return a list of words for a sentence, given an input string with XML markup
    def getWordList(self,string):
        listWords = []
        listWordsTemp = []
        listTag = []

        string = string.replace('ENAMEX TYPE','ENAMEXTYPE').replace('TIMEX TYPE','TIMEXTYPE').replace('NUMEX TYPE','NUMEXTYPE').replace('  ',' ')
        listWordsTemp = string.split(' ')
        for word in listWordsTemp:
            if not '<' in word:
                listWords.append(word)
            else:
                if word[0] == '<':
                    cleanWordList = (word.split('>')[1]).split(' ')

                else:
                    cleanWordList = (word.split('<')[0]).split(' ')
                for cleanWord in cleanWordList:
                    if '<' in cleanWord: # More cleaning to do as there is no space between the word and end tag
                        cleanWord = cleanWord.split('<')[0]
                    listWords.append(cleanWord)
        return listWords


    # Return start and end word indices (as a tuple) given an input string (fragment of sentence) and a list of words. The previous list of start indices prevents the same indices being returned if the same input string is supplied multiple times - e.g. "Taiwan" may appear more than once in the same sentence
    def getWordIndices(self,string,listWords,prevStartIndices):
        start = 0
        end = 0
        bStartSet = False
        counter = 0

        stringWords = string.rstrip(' ').lstrip(' ').split(' ')

        for i in range(0,len(listWords)):
            if bStartSet == True:
                if listWords[i] != stringWords[counter-1]:
                    bStartSet = False
                    counter = 0
                    return (start,(start + len(stringWords)))
                else:
                    counter += 1
            if listWords[i] == stringWords[0] and i not in prevStartIndices: # Potential match
                bStartSet = True
                start = i
                counter += 1

        end = start + len(stringWords)
        return (start,end)


    def add_spaces(self, onto, bbn):
        #onto: Analysts were disappointed that the enthusiasm
        #bbn: <ENAMEX TYPE="PER_DESC">Analysts</ENAMEX> were disappointed that the enthusiasm <ENAMEX TYPE="PER_DESC">investors</ENAMEX> showed for stocks in the wake of <ENAMEX TYPE="ORGANIZATION:CORPORATION">Georgia-Pacific</ENAMEX> 's <NUMEX TYPE="MONEY">$ 3.18 billion</NUMEX> bid for <ENAMEX TYPE="ORGANIZATION:CORPORATION">Great Northern Nekoosa</ENAMEX> evaporated so quickly .
        # convert bbn to onto by adding spaces, ignoring markup
        bbn = bbn.strip()
        onto = onto.strip()
        onto = onto.replace('&','&amp;')  # hack!
        bbn = bbn.replace('\\/','/')
        onto = onto.replace('\\/','/')

        out = []
        lo = len(onto)
        j = 0
        i = 0
        #print 'onto', onto
        #print 'bbn', bbn
        while i < lo:
            #print i, j, out
            if bbn[j] == '<': # copy tag
                while bbn[j] != '>':
                    out.append(bbn[j])
                    j += 1
                out.append(bbn[j])
                j += 1
                continue
            if bbn[j] == onto[i]:
                out.append(bbn[j])
                j += 1
                i += 1
                continue
            if onto[i] == ' ':
                out.append(' ')
                i += 1
                continue
            else:
                assert False, "weird: \n\t %s \n\t %s\n \n\t %s" %(onto, bbn, ''.join(out))

        # maybe close tag
        if j < len(bbn) and bbn[j] == '<': # copy tag
            while j < len(bbn) and bbn[j] != '>':
                out.append(bbn[j])
                j += 1
            out.append(bbn[j])
            j += 1
        out = ''.join(out)
        return out

    # Perform a string split using multiple separators. Returns a list of tokens
    # Code snippet from: http://stackoverflow.com/questions/1059559/python-strings-split-with-multiple-separators
    def multi_split(self,s, seps):
        res = [s]
        for sep in seps:
            s, res = res, []
            for seq in s:
                res += seq.split(sep)
        return res


    # Compute the intersction of two lists. Returns a list representing the intersection
    # Code snippet from: http://stackoverflow.com/questions/642763/python-intersection-of-two-lists
    def intersect(self,a, b):
        return list(set(a) & set(b))


    # Return the index from an entry in a dependecy parse tree relation
    def getCleanIndex(self,string):
        index = int(filter(lambda x: x.isdigit(), string))
        return index


    # Build a dictionary representing the dependecy parses for each sentence in document - data read from flat file
    def buildDepDict(self, docID, folderLocation):
        dictDep = {} # {docID: {sentNo: {governor: [dependent(s)]}}}
        sentNo = 0
        for fileName in os.listdir(folderLocation):
            if fileName == docID + '.dep':
                fileName = os.path.join(folderLocation, fileName)
                print "Reading dependencies from %s" %fileName
                depParseFile = open(fileName, 'r')
                sentNo = 1
                dictDep[docID] = {}
                for line in depParseFile:
                    if not dictDep[docID].has_key(sentNo):
                        dictDep[docID][sentNo] = defaultdict(list)
                    line = line.rstrip('\n')
                    if line == '': # Sentences separated by blank lines
                        sentNo += 1
                    else:
                        listElement = self.multi_split(line, ['(', ', ', ')'])
                        relation = listElement[0]
                        governor = self.getCleanIndex(listElement[1].split('-')[-1])-1 # Ensure that the word index starts at zero
                        dependent = self.getCleanIndex(listElement[2].split('-')[-1])-1
                        if not relation == 'root': # Ignore the root as it provides no useful information
                            dictDep[docID][sentNo][governor].append(dependent)
                            #if not dictDep[docID].has_key(sentNo):
                            #    dictDep[docID][sentNo] = {governor: [dependent]}
                            #else:
                            #    if not dictDep[docID][sentNo].has_key(governor):
                            #        dictDep[docID][sentNo][governor] = [dependent]
                            #    else:
                            #        dictDep[docID][sentNo][governor].append(dependent)
                depParseFile.close()
        return dictDep


    # Merge the description information in X_DESC named entity types with the X type.
    #Returns a modified named entity dictionary after the "merge".
    #Merging is applied for the following types and their X_DESC types:
    #                        PERSON, ORGANIZATION, GPE, PRODUCT and FAC
    def mergeEntDesc(self,dictNameEnt):
        resultDict = {}
        print '#####', dictNameEnt
        for docID in dictNameEnt:
            resultDict[docID] = {}
            for sentNo in dictNameEnt[docID]:
                resultDict[docID][sentNo] = []
                listElements = dictNameEnt[docID][sentNo]
                listDescr = []
                listTemp = []
                for element in listElements:
                    if element[3] in ['PERSON', 'ORGANIZATION', 'GPE', 'PRODUCT', 'FAC']:
                            listTemp.append(element)
                    elif element[3] in ['PER_DESC', 'ORG_DESC', 'GPE_DESC', 'PRODUCT_DESC', 'FAC_DESC']:
                            listDescr.append(element)
                            if element[3] == 'PER_DESC':
                                listTemp.append(element)
                    else:
                        listTemp.append(element)
                if listDescr != []:
                    for m in range(0, len(listTemp)):
                        for d in listDescr:
                            # Is the descriptor a match for the 'main' type and is 'main' the head of the descriptor according to the dependency tree?
                            if listTemp[m][3][:3] == d[3][:3] and self.intersect(listTemp[m][5], d[2].split(' ')) != []:
                                # Merge the information from the descriptor into the entry for main
                                descriptor = d[2]
                                # Overwrite entry in tempList
                                #listTemp[m] =
                                (listTemp[m][0],listTemp[m][1],listTemp[m][2],listTemp[m][3],listTemp[m][4],descriptor,listTemp[m][6])
                listTemp.sort()
                for e in range(0,len(listTemp)):
                    # If the 6th element in the named entity tuple is a list of dependents (has not been replaced by a descriptor string), replace it with the empty string as no descriptor is available for this named entity
                    if not isinstance(listTemp[e][5],basestring):
                        listTemp[e] = (listTemp[e][0],listTemp[e][1],listTemp[e][2],listTemp[e][3],listTemp[e][4],'',listTemp[e][6])
                resultDict[docID][sentNo] = listTemp
        print '#####', resultDict
        return resultDict


    # Returns a
    # File format: one block per sentence (separated by a blank line). Each line contains a triple of the form: relation_name(governor,dependent)
    def getNamedEnts(self,docID,folderLocationNE,folderLocationDep,treebank):
        dictNameEnt = {} # {docID: {sentNo: [(start_word_index, end_word_index, named_entity_string, type, sub_type, descriptor, consumed?),...]}}

        # Pre-load the Stanford dependency parse files as dependency information will be used in the construction of AMR fragments
        dictDepParse = self.buildDepDict(docID,folderLocationDep)
        #print 'dictDepParse:', dictDepParse

        common = cUtil()

        # Get "clean" and "tree" sentences - both are used in computing the word indices
        dictSents = common.getSentences(treebank)

        # Extract Named Entities from the BBN corpus files:
        sentNo = 1 # was 0
        bRead = False
        prevStartIndices = []

        # Pick the named entity file according to the doc ID - there are 4 files per OntoNotes "folder"
        quadrant = ''
        docExt = int(docID[-2:])
        if docExt < 25:
                quadrant = 'a'
        elif 25 <= docExt < 50:
                quadrant = 'b'
        elif 50 <= docExt < 75:
                quadrant = 'c'
        else:
                quadrant = 'd'

        # Open and read in named entity XML file
        fileName = 'wsj' + docID[4:6] + quadrant + '.qa'
        nameEntFile = open(folderLocationNE + '/' + fileName, 'r')

        for line in nameEntFile:
            #print line
            if '<DOCNO>' in line: # Obtain docID and reset list of previous start indices
                prevStartIndices = []
                docIDInFile = ((line.split('> ')[1].split(' <')[0])[:3] + '_' + (line.split('> ')[1].split(' <')[0])[3:]).lower()
                if docIDInFile == docID:
                    bRead = True
                else:
                    bRead = False
                continue
            if 'DOC>' in line or 'ROOT>' in line:
                continue
            if bRead == True: # If this is the document that you are looking for...
                print 'looking at line', line
                if line.startswith("'    "):
                    line = line[1:]
                line = line.rstrip('\n').rstrip('\r').rstrip(' ').replace('     ','')
                # Extract clean string and return as a list of words (from which start and end indices can be extracted)
                #wordList = self.getWordList(line)
                #print dictSents
                #print docID
                #print dictSents[docID]
                #print dictSents[docID][sentNo]
                treeString = dictSents[docID][sentNo][0]
                cleanString = dictSents[docID][sentNo][1]
                line = self.add_spaces(cleanString, line)
                line = '<SENTENCE>' + line + '</SENTENCE>' # Wrappers so that each sentence can be read as a separate XML string
                print line
                parsedLine = parseString(line)
                #parseTree = ElementTree.parse(line)
                # Retrieve the first xml tag (<tag>data</tag>) that the parser finds with the matching name:
                for element in chain( parsedLine.getElementsByTagName('ENAMEX'),
                                      parsedLine.getElementsByTagName('NUMEX'),
                                      parsedLine.getElementsByTagName('TIMEX')):
                    dependents = []
                    xmlTag = element.toxml()
                    xmlTagName = xmlTag.split()[0][1:]
                    xmlTagContent = xmlTag.split('>')[1]
                    xmlTagContent = xmlTagContent.split('<')[0]
                    xmlTagAttr = xmlTag.split('=\"')[1].split('\">')[0]
                    listTagAttr = xmlTagAttr.split(':')
                    entType = listTagAttr[0]
                    if len(listTagAttr) > 1:
                        entSubType = listTagAttr[1]
                    else:
                        entSubType = ''
                    # Find start and end word index from the 'clean' string verion of the line
                    indices = self.getWordIndices(xmlTagContent,cleanString.split(' '),prevStartIndices)
                    #print sentNo
                    #print xmlTagContent
                    #print indices
                    # Get dependents of the words in the xmlTagContent - for PERSON, ORGANIZATION, GPE, PRODUCT and FAC types (which can take a descriptor)
                    if '<ENAMEX' in xmlTag:
                        if entType in ['PERSON', 'ORGANIZATION', 'GPE', 'PRODUCT', 'FAC']:
                            taggedWordList = xmlTagContent.split(' ')
                            cleanWordList = cleanString.split(' ')
                            for taggedIndex in range(indices[0],indices[1]):
                                if dictDepParse[docID][sentNo].has_key(taggedIndex):
                                    for depIndex in dictDepParse[docID][sentNo][taggedIndex]:
                                        dependent = cleanWordList[depIndex]
                                        if dependent not in taggedWordList:
                                            dependents.append(dependent)
                    prevStartIndices.append(indices[0])
                    # Adjust indices to use 'tree' string indices, not clean string indices
                    indices = common.adjustIndices(cleanString, treeString, indices[0], indices[1])
                    #print indices
                    #print '---------'
                    if not dictNameEnt.has_key(docID):
                        dictNameEnt[docID]  = {}
                    if not dictNameEnt[docID].has_key(sentNo):
                        dictNameEnt[docID][sentNo] = []
                    dictNameEnt[docID][sentNo].append((indices[0],indices[1],xmlTagContent,entType,entSubType,dependents,xmlTag))
                prevStartIndices = []
                sentNo += 1
        nameEntFile.close()

        # Modify dictNameEnt entries to merge PERSON, ORGANIZATION, GPE, PRODUCT and FAC entities with their entity description NEs (X_DESC)
        dictNameEnt = self.mergeEntDesc(dictNameEnt)
        print dictNameEnt
        return dictNameEnt
