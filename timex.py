'''
Creates AMR fragments for time expressions
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput, json

from dev.amr.amr import Amr

import pipeline
from pipeline import choose_head, new_concept, parent_edges
from xml.etree import ElementTree

'''
Example input, from wsj_0002.0:

  "timex": [
    [
      "t1",
      3,
      5,
      "<TIMEX3 tid=\"t1\" value=\"P55Y\" type=\"DURATION\">55 years old</TIMEX3>"
    ], ...
  ]
'''


def main(sentenceId, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    new_triples = set()

    time_expressions = pipeline.loadTimex(sentenceId)
    for tid, start, end, raw_timex in time_expressions:
        t = Timex3Entity(ElementTree.fromstring(raw_timex))
        h = choose_head(range(start,end+1), depParse)

        mc = new_concept(pipeline.token2concept(t.main_concept), amr, alignment, h)

        if t.wrapper != None:
            alignment.unlink(mc, h)
            wc = new_concept(pipeline.token2concept(t.wrapper)+'-'+t.type, amr, alignment, h)
            new_triples.add((str(wc), 'op1', str(mc)))
        else:
            amr.node_to_concepts[str(mc)] += '-'+t.type

        if 'weekday' in t.date_entity:
            wd = int(t.date_entity['weekday'])
            wd_name = weekdays[wd] # e.g. 'friday'
            x = new_concept(pipeline.token2concept(wd_name), amr)
            new_triples.add((str(mc), 'weekday', str(x)))

        print ('####', t.date_entity)
        for k, v in t.date_entity.iteritems():
            if k=='weekday': continue   # handled above
            if isinstance(v,basestring):
                v = pipeline.token2concept(str(v))
                x = new_concept(v, amr)
                x = str(x)
            else:   # leave literal numeric values alone
                print(amr.triples(instances=False))
                x = v
            new_triples.add((str(mc), k, x))

        for i in range(start, end+1): # for now mark everything as completed
            completed[0][i] = True
        for i,j in completed[1]:
            if i >= start and i <= end and j >= start and j <= end:
                completed[1][(i,j)] = True



    #for i,j,name,coarse,fine in entities:    # TODO: what is the last one?
    #    h = choose_head(range(i,j+1), depParse)
    #    #print((i,j),name,h,depParse[h+1]['dep'], file=sys.stderr)
    #
    #    x = alignment[:h] # index of variable associated with i's head, if any
    #
    #    if coarse.endswith('_DESC'):
    #        # make the phrase head word the AMR head concept
    #        # (could be a multiword term, like Trade Representative)
    #        if not (x or x==0): # need a new variable
    #            x = new_concept(pipeline.token2concept(depParse[h][0]['dep']), amr, alignment, h)
    #            triples.add((str(x), '-DUMMY', ''))
    #    else:
    #        if not (x or x==0): # need a new variable
    #            ne_class = fine.lower().replace('other','') or coarse.lower()
    #            concept, amr_name = amrify(ne_class, name)
    #            x = new_concept(pipeline.token2concept(concept)+'-FALLBACK',    # -FALLBACK indicates extra information not in the sentence (NE class)
    #                            amr, alignment, h)
    #            n = new_concept('name', amr)
    #            triples.add((str(x), 'name', str(n)))
    #            for iw,w in enumerate(amr_name.split()):
    #                triples.add((str(n), 'op'+str(iw+1), '"'+w+'"'))
    #
    #
    #    for k in range(i,j+1):
    #        assert not completed[0][k]
    #        completed[0][k] = True
    #        #print('completed token',k)
    #        if k!=h:
    #            for link in parent_edges(depParse[k]):
    #                completed[1][link] = True  # we don't need to attach non-head parts of names anywhere else
    print(list(new_triples))
    amr = Amr.from_triples(amr.triples(instances=False)+list(new_triples), amr.node_to_concepts)

    return depParse, amr, alignment, completed

#### Resources ####
# Todo: externalize


re_date = [
    re.compile(r'\w{4}-\w{2}-(?P<day>\d\d)'),   # XXXX-10-31
    re.compile(r'\w{4}-(?P<month>\w{2})\W'),    
    re.compile(r'\w{4}-(?P<month>\w{2})$'),     # XXXX-10
    re.compile(r'^(?P<year>\d{4})'),
    re.compile(r'\w{4}-W\w{2}-(?P<weekday>\d)'),
    re.compile(r'\w{4}-Q(?P<quarter>\d)'),
    re.compile(r'\w{4}-(?P<season>SP|SU|FA|WI)')
]

weekdays = [None,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

timex3_type_to_role = {
    "DATE" : "date-entity"
}

# P-1Y, P1Y, P100Y
re_pexpr = re.compile(r'^(THIS )?P(?P<quant>-?\d+)(?P<unit>[HDWMY]+)$')

timex3_units = {
    'time': {
        'S' : 'second',
        'M' : 'minute',
        'H' : 'hour'
    },
    'day': {
        'D' : 'day',
        'W' : 'week',
        'M' : 'month',
        'Y' : 'year'
    }
}

timex3_ref_to_roles = {
    'PRESENT_REF' : 'now',
    'PAST_REF' : 'previously',
    'FUTURE_REF' : 'subsequently'
}


class Timex3Entity(object):

    valid_types = [ 'DATE', 'DATE_RELATIVE', 'DURATION', 'SET' ]

    def __init__(self, timex, text = None):
        #print timex.attrib
        self.text = timex.text
        self.timex = dict(timex.attrib)
        self.type = self.timex['type']
        assert self.type in Timex3Entity.valid_types
        if self.type=='DURATION' and (self.text.endswith(' old') or self.text.endwith('-old')):
            self.type = 'AGE'
        
        self.date_entity = {}
        self.main_concept = 'temporal-quantity'
        self.wrapper = None

        if self.is_absolute_time(): # side effect: merges alt_value with value in self.timex
            self.main_concept = 'date-entity'
            self.parse_absolute_time()
            return
        
        if self.timex['value'].startswith('THIS '):
            self.main_concept = 'date-entity'
        elif self.is_ref():
            self.main_concept = self.parse_ref()

        # extract info from value and store in self.date_entity
        if 'value' in self.timex:
            v = self.timex['value']
            if v == "PRESENT_REF":
                self.main_concept = 'now'
                return
            for regexp in ([re_pexpr] if self.type in ['DURATION','AGE'] or v.startswith('THIS ') else re_date):
                m = regexp.search(v)
                if m == None:
                    continue
                matchexprs = m.groupdict()
                if 'unit' in matchexprs:
                    matchexprs['unit'] = timex3_units['time' if 'T' in v and self.type in ['DURATION','AGE'] else 'day'][v[-1]]
                if 'quant' in matchexprs:
                    try:
                        matchexprs['quant'] = int(matchexprs['quant'])
                    except ValueError:
                        try:
                            matchexprs['quant'] = float(matchexprs['quant'])
                        except ValueError:
                            pass
                self.date_entity.update(matchexprs)
            

        if 'alt_value' in self.timex:
            v = self.timex['alt_value'].split()
            
            hasThis = False
            if v[0]=='THIS':
                if v[1]=='NI':
                    pass    # TODO: tonight
                
                hasThis = True
                
            
            if 'OFFSET' in v:
                self.type += "_RELATIVE"
                offset = v[v.index('OFFSET')+1]
                self.date_entity['unit'] = timex3_units['time' if 'T' in offset else 'day'][offset[-1]]
                quantity = offset[1:-1]
                try:
                    self.date_entity['quant'] = int(quantity)
                    if self.date_entity['quant'] < 0:
                        self.wrapper = 'ago'
                        self.date_entity['quant'] = -self.date_entity['quant']
                    else:
                        assert self.date_entity['quant'] > 0
                        self.wrapper = 'hence'
                        
                    if hasThis: # use 'last' or 'next' instead of 'ago'/'hence'
                        self.date_entity['mod'] = {'ago': 'last', 'hence': 'next'}[self.wrapper]
                        self.wrapper = None
                except ValueError:
                    pass
                    #assert quantity == 'X', "value should be int or X but is %s" %quantity
            else:
                self.date_entity['mod'] = 'this'

    def is_absolute_time(self):
        '''
        indicates if timex can be expressed by date entity
        try to match any of the regexps in re_data and return True if one fits
        '''
        if not 'value' in self.timex:
            self.timex['value'] = self.timex['alt_value']
        v = self.timex['value']
        for regexp in re_date:
            m = regexp.search(v)
            if m != None:
                return True
        return False

    def parse_absolute_time(self):
        v = self.timex['value']
        for regexp in re_date:
            m = regexp.search(v)
            if m == None:
                continue
            matchexprs = m.groupdict()
            if 'time' in matchexprs:
                matchexprs['time'] = '"'+matchexprs['time']+'"'
            for u in ['day','month','year','quarter']:
                if u in matchexprs:
                    matchexprs[u] = int(matchexprs[u])
            self.date_entity.update(matchexprs)

    def is_ref(self):
        '''
        indicates whether timex refers to present, future or past
        '''
        return self.timex['value'].endswith('REF')

    def parse_ref(self):
        v = self.timex['value']
        if not v in timex3_ref_to_roles:
            return None
        return timex3_ref_to_roles[v]


