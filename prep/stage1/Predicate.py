''' Created on Jun 15, 2012

@author: yaqin276
'''
import sys
import re
import json


from corefStanford import corefStan
from corefOntoNotes import corefOnto
from bbnNamedEntity import bbnNE
from itertools import imap
import nltk

import on
from on.corpora import tree


class predicate(object):
    '''

    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.grammar_rules = ["S(NP VP-h)->(VP-h :arg0 NP)","VP(MD VP-h)->(VP null null)"]
    def getAOntonotes(self):
        '''
        See on/__init__.py for usages of ontonotes object
        '''
        '''
        Create a config object
        '''
        cfg = on.common.util.load_options(positional_args=False)
        '''
        Create an ontonotes object by passing in a config object
        '''
        a_ontonotes = on.ontonotes(cfg)
        return a_ontonotes

    def prepro_sentence(self, s):
        s = s.replace('(', '-LRB-')
        s = s.replace(')', '-RRB-')
        s = s.replace('[', '-LSB-')
        s = s.replace(']', '-RSB-')
        s = s.replace('{', '-LCB-')
        s = s.replace('}', '-RCB-')
        return s

    def true_brackets(self, s):
        s = s.replace('-LRB-','(')
        s = s.replace('-RRB-',')')
        s = s.replace('-LSB-','[')
        s = s.replace('-RSB-',']')
        s = s.replace('-LCB-','{')
        s = s.replace('-RCB-','}')
        return s


    def remove_space(self, s):
        return re.sub(r'\s+',' ', s)

    def read_parse_trees(self, filename):
        parses = [pt.replace('\n',' ') for pt in open(filename).read().split('\n\n') if pt.strip()]
        trees = imap(nltk.tree.Tree.parse, parses)
        trees = [t.replace('\n',' ') for t in imap(str, trees)]
        return map(self.remove_space, trees)

    def extractInfo(self,a_ontonotes,json_directory,files_with_coref,XML_name_entity):
        docID = ''
        sentNo = 0


        '''
        given an ontonotes object and iterate over the subcorpora it contains (usually only one subcorpus)
        '''
        '''
        a_subcorpus is a dictionary, containing a treebank for all fileids, a document and generally contains other banks.
        '''

        cOntoNotes = corefOnto()
        cStanford = corefStan()
        neBBN = bbnNE()

        # Get a list of the files for which coreference is annotated in OntoNotes
        coref_list = []
        coref_list_file = open(files_with_coref,'r')
        for line in coref_list_file:
                coref_list.append(line.rstrip('\n'))
        coref_chains = {}


        for a_subcorpus in a_ontonotes:
            #a_prop_bank = a_subcorpus['prop']
            #for a_prop_doc in a_prop_bank:
            #    for a_prop_snt in a_prop_doc:
            #        print a_prop_snt
            #        print a_prop_snt.lemma
            #        print a_prop_snt.pb_sense_num
            #        print dir(a_prop_snt.predicate)
            #        print a_prop_snt.predicate.token_index
            #        print a_prop_snt.predicate.primary_predicate
            #        print a_prop_snt.predicate.parent
            #        print a_prop_snt.predicate.index_in_parent
            #        print a_prop_snt.predicate.proposition
            #        print a_prop_snt.predicate.sep
            #        print a_prop_snt.predicate.type
            #        print a_prop_snt.predicate.sentence_index
            #
            #    #print a_prop_doc
            #        sys.exit()
            a_tree_bank = a_subcorpus['parse']
            '''
            The treebank class represents a collection of :class:`tree_document` classes
            '''

            # If coreference is annotated in OntoNotes for the document, construct the coref_chains dictionary using this information
            coref_chains = {}
            for doc in a_subcorpus['coref']:
                coref_chains = cOntoNotes.getCorefChains(doc, coref_chains, a_tree_bank)


            for a_tree_document in a_tree_bank:
                '''
                The tree_document class contains a collection of trees
                '''
                print "current file id is ",a_tree_document.document_id, " including ", len(a_tree_document.tree_ids)," trees"

                docID = (a_tree_document.document_id.split('/')[-1]).split('@')[0]

                # If OntoNotes does not have coreference for the document: load pre-generated JSON object for the document and extract coreference information
                if not docID in coref_list: ### Get coref from the output of the Stanford coreNLP tool

                        # Extract sentences from the tree - these will be used later to adjust the start and end word spans calculated on clean strings (adjustments required to take into consideration trace information in the "tree" sentence)
                        dictSents = {}
                        for tree in a_tree_document:
                            subfolder = tree.document_id.split('/')[-2]
                            json_file_name = json_directory + '/' + subfolder + '/' + docID + '.json'
                            print "Reading json from", json_file_name
                            json_object = json.load(open(json_file_name))
                            docID = (tree.document_id.split('/')[-1]).split('@')[0]
                            sentNo = int(tree.id.split('@')[0]) + 1
                            string = tree.get_word_string()
                            string = self.prepro_sentence(string)
                            if not dictSents.has_key(docID):
                                    dictSents[docID] = {}
                            dictSents[docID][sentNo] = (string,'')

                        # Extract coref information from the .json files
                        #print dictSents
                        #print len(json_object['sentences'])
                        #for i, s in enumerate(json_object['sentences']):
                        #    print i, s['text']
                        coref_json = [s['coref'] if 'coref' in s else [] for s in json_object['sentences']]
                        for sentNo in range(len(json_object['sentences'])):
                                string = json_object['sentences'][sentNo]['text']
                                string = self.prepro_sentence(string)
                                dictSents[docID][sentNo+1] = (dictSents[docID][sentNo+1][0],string)
                        #coref_chains_temp = cStanford.getCorefChains(json_object['coref'],docID,dictSents)
                        coref_chains_temp = cStanford.getCorefChains(coref_json, docID, dictSents)
                        coref_chains = dict(coref_chains.items() + coref_chains_temp.items())
                else:
                    print "found %s in coreflist" %(docID)
                # Extract named entities from the BBN corpus
                dep_location = ''
                for element in a_tree_document.absolute_file_path.split('/'):
                        if not '.parse' in element and element != '':
                                dep_location += ('/' + element)
                dep_location += '/'
                print "DepLocation:", dep_location
                named_ents = neBBN.getNamedEnts(docID,XML_name_entity,dep_location,a_tree_bank)
                print "bbn:", named_ents
                #sys.exit()

                print "CorefChains:", coref_chains
                for a_tree in a_tree_document:
                    #self.extract_propbank_spans(a_tree)
                    #sys.exit()

                    sentNo = int(a_tree.id.split('@')[0])

                    subfolder = a_tree.document_id.split('/')[-2]
                    json_file_name = json_directory + '/' + subfolder + '/' + docID + '.json'
                    print "Reading json from", json_file_name
                    json_object = json.load(open(json_file_name))
                    for s in json_object['sentences']:
                        for w in s['words']:
                            #print w
                            w[1].pop("CharacterOffsetBegin")
                            w[1].pop("CharacterOffsetEnd")

                    parse_file_name = json_directory + '/' + subfolder + '/' + docID + '.parse'
                    print "Reading gold parse from", parse_file_name
                    parse_trees = self.read_parse_trees(parse_file_name)
                    assert len(parse_trees) == len(a_tree_document.tree_ids)
                    pt = parse_trees[sentNo]
                    #print parse_trees
                    #sys.exit()



                    data = {}
                    docID = (a_tree.document_id.split('/')[-1]).split('@')[0]
                    print "current file id is ", a_tree.document_id," current tree id is ", a_tree.id
                    #print a_tree.pretty_print()
                    print a_tree.get_word_string()

                    data['document_id'] = a_tree.document_id
                    data['sentence_nr'] = sentNo
                    data['treebank_sentence'] = self.true_brackets(a_tree.get_word_string())
                    data['coref_chains'] = coref_chains[docID].get(sentNo+1,[])
                    data['bbn_ne'] = named_ents[docID].get(sentNo+1,[])

                    data['goldparse'] = pt

                    for k in json_object['sentences'][sentNo]:
                        data[k] = json_object['sentences'][sentNo][k]


                    #self.printPropbank(a_tree, 0)
                    #sys.exit()

                    #print data

                    json_file_name = json_directory + '/' + subfolder + '/' + docID + '.' + str(sentNo) + '.json'
                    print "writing to ", json_file_name

                    json.dump(data, open(json_file_name,'w'), indent=2)

                    #print json.dumps(data, indent=2)
                    #converted_tree = self.convert(head_rules, a_tree, a_tree, coref_chains, named_ents, listEntType)
                    #print "converted amr"
                    #print converted_tree.pretty_print()
                    #
                    #rec_num = 0
                    #var_dict = {}
                    #coref_dict = {}
                    #converted_str = at.toString(converted_tree,rec_num, var_dict, coref_dict)
                    #
                    #amr_filename = "/home/buck/corpora/ontonotes-release-4.0/data/files/data/english/annotations/" + a_tree.document_id.split('@',1)[0] + ".protoamr"
                    #print "writing to:", amr_filename
                    ##sys.exit()
                    #of = open(amr_filename, 'wa')
                    #of.write(converted_str + "\n")
                    #of.close()
                    #
                    #print converted_str
                    ##sys.exit()
                    ##raw_input("Press ENTER to continue")


    def generateLeafwithProptag(self,a_tag,a_word,arg_type):
        temp_tree = None
        if arg_type != []:
            temp_tree = tree.tree(a_word +"|"+"|".join(arg_type))
            temp_tree.word = a_word +"|"+"|".join(arg_type)
        else:
            print "a_word:", a_word
            temp_tree = tree.tree(a_word)
            temp_tree.word = a_word
        return temp_tree

    def generateNodewithProptag(self,a_tag,arg_type):
        temp_tree = None
        if arg_type != []:
            temp_tree = tree.tree(a_tag+"|"+"|".join(arg_type))
        else:
            temp_tree = tree.tree(a_tag)
        return temp_tree

    def printPropbank(self, a_tree, depth=0):
        print " "*depth, '( [',
        if len(a_tree.argument_node_list) > 0: # current tree is an argument in propbank'
            print str(a_tree.argument_node_list[0].argument.type),
        if a_tree.compound_function_tag != []:
            print a_tree.compound_function_tag,
        print a_tree.tag,
        print a_tree.word,
        print ']',
        if not a_tree.is_leaf():
            for c_tree in a_tree.children:
                self.printPropbank(c_tree, depth+1)
        #print "\n"," "*depth, ')'
        print ')'


def main():
    '''
    json_directory = "/nfs/nlg/semmt/data/on_fixed/ontonotes-release-4.0/data/files/data/english/annotations/nw/wsj" # .JSON files that Christian will generate / has generated
    files_with_coref = "/nfs/nlg/semmt/tools/eng2amr/prepro_pipeline/ontonotes-db-tool-v0.999b/src/WSJFilesWithCoref.txt" # List of files for which coreference is annotated in OntoNotes
    XML_name_entity = "/nfs/nlg/semmt/data/bbn_fixed/bbn-pcet/data/WSJtypes-subtypes"
    '''
    json_directory = sys.argv.pop(1)
    files_with_coref = sys.argv.pop(1)
    XML_name_entity = sys.argv.pop(1)
    # the call to on.common.util.load_options() handles the rest of the command-line arguments

    pred = predicate()
    a_ontonotes = pred.getAOntonotes()

    #json_directory = "/home/buck/corpora/ontonotes-release-4.0/data/files/data/english/annotations/nw/wsj/" # .JSON files that Christian will generate / has generated
    #files_with_coref = "/home/buck/Dropbox/isi/OntonotesUtil/ontonotes-db-tool-v0.999b/src/WSJFilesWithCoref.txt" # List of files for which coreference is annotated in OntoNotes
    #XML_name_entity = "/home/buck/Dropbox/isi/bbn-pcet/data/WSJtypes-subtypes/"
    #he = head()
    #head_rules = he.loadHeadrules("/home/buck/Dropbox/isi/OntonotesUtil/ontonotes-db-tool-v0.999b/data/headrules.txt")
    #head_rules = he.loadHeadrules("/nfs/nlg/semmt/tools/eng2amr/prepro_pipeline/ontonotes-db-tool-v0.999b/data/headrules.txt")
    #listEntType = ['PERSON','PERSON_DESC','GPE','ORGANIZATION','PRODUCT','LOCATION','FAC','NORP','PLANT','ANIMAL','DISEASE','GAME','LANGUAGE','LAW'] # List of Named Entity types accommodated - ignore SUBSTANCE, WORK_OF_ART AND CONTACT_INFO which aren't categorised in the AMR spec list of "hallucinated" types
    
    pred.extractInfo(a_ontonotes,json_directory,files_with_coref,XML_name_entity) # Dependency files that Christian will generate / has generated
	
	#pred.traverseTrees(a_ontonotes,head_rules,json_directory,files_with_coref,XML_name_entity,listEntType) # Dependency files that Christian will generate / has generated

if __name__=="__main__":
    main()
