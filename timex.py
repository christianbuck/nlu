'''
Creates AMR fragments for time expressions
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput, json

import pipeline, config
from pipeline import choose_head, new_concept, new_amr_from_old, parent_edges
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
    nNewTrip = 0

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
        if 'dayperiod' in t.date_entity:
            dp = t.date_entity['dayperiod']
            dp_name = dayperiods[dp]    # e.g. 'afternoon'
            x = new_concept(pipeline.token2concept(dp_name), amr)
            new_triples.add((str(mc), 'dayperiod', str(x)))

        #print('####', t.date_entity)
        for k, v in t.date_entity.iteritems():
            if k in ['weekday','dayperiod']: continue   # handled above
            if isinstance(v,basestring):
                v = pipeline.token2concept(str(v))
                x = new_concept(v, amr)
                x = str(x)
            else:   # leave literal numeric values alone
                #print(amr.triples(instances=False))
                x = v
            new_triples.add((str(mc), k, x))

        for i in range(start, end+1): # for now mark everything as completed
            completed[0][i] = True
        for i,j in completed[1]:
            if i >= start and i <= end and j >= start and j <= end:
                completed[1][(i,j)] = True
                
        try:
            assert t.main_concept and (t.main_concept not in ['date-entity','temporal-quantity'] or len(new_triples)>nNewTrip)
        except AssertionError:
            if config.verbose or config.warn: print('Warning: Unhandled time expression', file=sys.stderr)
        nNewTrip = len(new_triples)

    #print(list(new_triples))
    
    amr = new_amr_from_old(amr, new_triples=list(new_triples))
    
    

    return depParse, amr, alignment, completed

#### Resources ####
# Todo: externalize

re_time = r'(T(?P<dayperiod>MO|AF|EV|NI)|T(?P<time>\d{2}:\d{2}))'

re_date = [
    re.compile(r'\w{4}-\w{2}-(?P<day>\d\d)'+re_time+'?'),   # XXXX-10-31
    re.compile(r'\w{4}-(?P<month>\d{2})\W'+re_time+'?'),    
    re.compile(r'\w{4}-(?P<month>\d{2})$'),     # XXXX-10
    re.compile(r'^(?P<year>\d{4})'+re_time+'?'),
    re.compile(r'\w{4}-W\w{2}-(?P<weekday>\d)'+re_time+'?'),
    re.compile(r'\w{4}-Q(?P<quarter>\d)'+re_time+'?'),
    re.compile(r'\w{4}-(?P<season>SP|SU|FA|WI)'+re_time+'?'),
    re.compile(re_time)
]

weekdays = [None,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

dayperiods = {'MO': 'morning', 'AF': 'afternoon', 'EV': 'evening', 'NI': 'night'}

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

    valid_types = [ 'DATE', 'DATE_RELATIVE', 'DURATION', 'SET', 'TIME' ]

    # TODO: handle "TIME"
    '''
    <TIMEX3 tid="t3" value="TNI" type="TIME">the Night</TIMEX3>
    <TIMEX3 tid="t3" value="TMO" type="TIME">morning</TIMEX3>
    <TIMEX3 tid="t3" value="TEV" type="TIME">evening</TIMEX3>
    <TIMEX3 tid="t3" value="TAF" type="TIME">the afternoon</TIMEX3>
    <TIMEX3 tid="t3" value="T18:00" type="TIME">6 p.m.</TIMEX3>
    <TIMEX3 tid="t2" value="XXXX-WXX-4TNI" type="TIME">Thursday night</TIMEX3>
    '''

    '''
    <TIMEX3 tid="t1" alt_value="OFFSET P-2Y" type="DATE" mod="MORE_THAN">more than two years ago</TIMEX3>
    <TIMEX3 tid="t1" alt_value="THIS P1Y OFFSET P-1Y" type="DATE" mod="EARLY">early last year</TIMEX3>
    '''
    
    '''
    <TIMEX3 tid="t3" value="XXXX-WXX-6TMO" type="SET">Saturday mornings</TIMEX3>
    <TIMEX3 tid="t3" value="XXXX-WXX-5T22:00" type="SET" periodicity="P1W">Fridays, 10 p.m.</TIMEX3>
    '''

    def __init__(self, timex, text = None):
        #print timex.attrib
        self.text = timex.text
        self.timex = dict(timex.attrib)
        self.type = self.timex['type']
        assert self.type in Timex3Entity.valid_types,self.type
        if self.type=='DURATION' and (self.text.endswith(' old') or self.text.endswith('-old')):
            self.type = 'AGE'
        
            
        self.date_entity = {}
        self.main_concept = 'temporal-quantity'
        self.wrapper = None
        
        if 'mod' in self.timex:
            assert self.timex['mod'] in ['EARLY','LATE','APPROX','MORE_THAN','LESS_THAN','EQUAL_OR_LESS','EQUAL_OR_MORE']
            self.date_entity['MOD'] = self.timex['mod'] # date_entity['mod'] is taken below, so 'MOD' here allows 2 modifiers to be present
            # TODO: APPROX->about, MORE_THAN=> more-than, etc. as heads rather than MOD

        if not 'value' in self.timex:
            self.timex['value'] = self.timex['alt_value']
            
        if self.is_absolute_time():
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
            matchexprs = {k:v for k,v in m.groupdict().items() if v is not None}
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


