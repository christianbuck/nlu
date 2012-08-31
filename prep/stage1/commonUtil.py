# LKG


class cUtil(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''


    # Given a start and end index taken from a 'clean' string (one with no trace information), adjust the indices to match the word indices in the 'tree' string
    # @staticmethod
    def adjustIndices(self, cleanString, treeString, startIndex, endIndex):
        


        start = 0
        end = 0
        adj = 0

        endIndex -= 1

        cleanStringList = cleanString.split(' ')
        treeStringList = treeString.split(' ')

        #print 'start: ', startIndex, ' end: ', endIndex
        #print " ".join( "%s (%s) " %(w,i) for i,w in enumerate(cleanStringList))
        #print "NE:", " ".join(cleanStringList[startIndex:endIndex+1])
        #print cleanStringList[startIndex], treeStringList[startIndex]
        print 'clean: ', cleanString
        print 'treestring: ', treeString

        if endIndex >= len(cleanString):
            print 'start: ', startIndex, ' end: ', endIndex
            print 'clean: ', cleanString
            #print cleanStringList[startIndex], treeStringList[startIndex]
            print 'treestring: ', treeString
            assert False
            #print cleanStringList[endIndex], treeStringList[endIndex]

        if cleanStringList[startIndex] == treeStringList[startIndex] and cleanStringList[endIndex-1] == treeStringList[endIndex-1]: # No change
                return (startIndex, endIndex)
        else: # Adjustments needed
                # Start Index
                if cleanStringList[startIndex] == treeStringList[startIndex]:
                        start = startIndex
                else:
                        adj = startIndex
                        while cleanStringList[startIndex] != treeStringList[adj]:
                                adj += 1
                        start = adj

                # End Index
                if cleanStringList[endIndex] == treeStringList[endIndex + (adj - startIndex)]:
                        end = endIndex + (adj - startIndex)
                else:
                        adj = endIndex + (adj - startIndex)
                        while cleanStringList[endIndex] != treeStringList[adj]:
                                adj += 1
                        end = adj
        print 'NEW: start: ', start, ' end: ', end
        return (start, end )
        #return (start, end + 1)


    # Return a dictionary of clean and tree (with trace information) sentences
    def getSentences(self, a_tree_bank):
        dictSents = {}
        for a_tree_document in a_tree_bank:
                for tree in a_tree_document:
                        clean_string = ''
                        docID = (tree.document_id.split('/')[-1]).split('@')[0]
                        sentNo = int(tree.id.split('@')[0]) + 1
                        string = tree.get_word_string()
                        cleanList = string.split(' ')
                        for element in cleanList:
                                if element != '0' and '*' not in element:
                                        clean_string += element + ' '
                        clean_string = clean_string.rstrip(' ')
                        if not dictSents.has_key(docID):
                                dictSents[docID] = {}
                        dictSents[docID][sentNo] = (string,clean_string)
        return dictSents
