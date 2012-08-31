# LKG
# LKG

import on, sys
import nltk
from commonUtil import cUtil
from collections import defaultdict

class corefOnto(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''

    # Extract a list of sentence-internal coreference chains from the OntoNotes annotations
    def getCorefChains(self, doc, dictSentCoref, a_tree_bank):
        common = cUtil()
        sentsDict = common.getSentences(a_tree_bank)

        #dictSentCoref format: {docID: {sentNo: [(start_word_index,end_word_index,type,identifier,string,used_up),...]}}

        for corefC in doc:
            docID = str(corefC.document_id)
            docID = docID.split('/')[3].split('@')[0]
            if not dictSentCoref.has_key(docID):
                    dictSentCoref[docID] = {}
            corefChainID = int(corefC.identifier)

            for corefL in corefC:
                sentNo = corefL.sentence_index + 1

                corefStringWords = corefL.string.split(' ')
                start_word_index = corefL.start_word_index
                if corefStringWords[0].lower() in ['the','mrs','ms','miss','mr','mrs.','ms.','mr.']:
                    corefStringWords.pop(0)
                    start_word_index += 1
                string = ' '.join(corefStringWords)

                # nschneid: modified, was
                '''
                deduct = 0
                for word in corefStringWords:
                    if word.lower() not in ['the','mrs.','mr.']:
                            string += word + ' '
                    else:
                            deduct += 1
                string = string.rstrip(' ')
                start_word_index = corefL.start_word_index + deduct
                '''


                end_word_index = corefL.end_word_index + 1
                #print "COREFL", corefL.start_word_index, corefL.end_word_index, corefL.start_token_index, corefL.end_token_index
                adjusted = common.adjustIndices(sentsDict[docID][sentNo][1], sentsDict[docID][sentNo][0], start_word_index, end_word_index)
                start_word_index = adjusted[0]
                end_word_index = adjusted[1]
                if not corefL.type in ['ATTRIB','HEAD','APPOS']:
                    if not dictSentCoref[docID].has_key(sentNo): # First time sentence seen
                        dictSentCoref[docID][sentNo] = [(start_word_index, end_word_index, corefChainID, string, False)]
                    else: # Entries for sentence already in dictionary
                        dictSentCoref[docID][sentNo].append((start_word_index, end_word_index, corefChainID, string, False))


        # Sort the list of tuples for each sentence in the dictionary so that they are ordered by start_word_index
        for docID in dictSentCoref:
            for sentNo in dictSentCoref[docID]:
                tempList = dictSentCoref[docID][sentNo]
                tempList.sort()
                fDist = {}
                listCorefMult = []
                listCorefChains = []
                listFinal = []
                # Now swap any items so that if there are two elements with the same start_word_index, the one with the larger span appears first
                if len(tempList) > 1:
                    for i in range(0,len(tempList)-1):
                        if tempList[i][0] == tempList[i+1][0] and tempList[i][1] < tempList[i+1][1]:
                            tempList[i+1], tempList[i] = tempList[i], tempList[i+1]
                        # As we are only interested in sentence internal coreference, compile a list of corefChainIDs in the sentence
                        listCorefChains.append(int(tempList[i][2]))
                    # Add corefChainID for the last entry in the list
                    listCorefChains.append(int(tempList[i+1][2]))
                    fDist = nltk.FreqDist(listCorefChains) # Find how many times each corefChainID appears in the sentence
                    for e in fDist:
                        if fDist[e] > 1:
                            listCorefMult.append(e)
                # Construct list of sentence internal coreference instances and write back to dictionary
                for element in tempList:
                    if int(element[2]) in listCorefMult:
                        listFinal.append(element)
                dictSentCoref[docID][sentNo] = listFinal
        return dictSentCoref
