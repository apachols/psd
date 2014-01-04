"""
Code to build database of who is willing to date whom
"""

from django.db import transaction

from psd.register.models import MatchRecord, LinkRecord, RegRecord, Person, BreakRecord, DateRecord
from collections import defaultdict

   
    
def print_matrix(m, no_group=False):
    for a in m.keys():
        if not no_group or (not a[1].is_group and not a[0].is_group):
           print("%d\t %s(%s) X %s(%s)\n" % ( m[a], a[0].nickname, a[0].minicode(), a[1].nickname, a[1].minicode(),))

def make_matrix(matrix_type):
    assert matrix_type in ('gay','str','all')
    lefts = RegRecord.objects.all()
    rights = RegRecord.objects.all()
    return dict(((l,r), l.matrix_score(r, matrix_type)) \
                for l in lefts for r in rights)


def mutualize_matrix(scores):
    for (l,r) in scores:
        scores[l,r] = min(scores[l,r], scores[r,l])

def make_sym_matrix(matrix_type):
    m = make_matrix(matrix_type)
    mutualize_matrix(m)
    return m


def write_csv(event,fh):
    fh.write("event,PSDID1,PSDID2,match,gay_ok,str_ok\n") # header
    regs = RegRecord.objects.filter(event=event)
    for l in regs:
        for r in regs:
            match = min(l.interest_score(r), r.interest_score(l))
            gay_ok = l.ok_gay_match(r) and r.ok_gay_match(l)
            str_ok = l.ok_str_match(r) and r.ok_str_match(l)
            cells = (l.event,l.psdid,r.psdid,match,int(gay_ok),int(str_ok))
            row = ','.join(str(c) for c in cells)
            fh.write(row)
            fh.write('\n')



def sum_mean_median(nums):
    if len(nums) == 0:
        return (0,0,0)
    
    total = sum(nums)
    mean = float(total) / len(nums)
    ## Now, the median.
    snums = sorted(nums)
    index = len(nums) / 2
    if len(nums) % 2 == 1:
        ## Even length array: average the two middle entries.
        median = (snums[index] + snums[index - 1]) / 2.
    else:
        ## Odd length array: len/2 will be the middle.
        median = snums[index]
    return (total, mean, median)


def all_alias_history( rr ):
    """
    Get all psdids that dated anyone listed as an alias for the
    given rr 
    """
    aliases = LinkRecord.objects.filter( psdid=rr.psdid )
    drids = set(c.psdid_alias for c in aliases)
    
    to_ban = set()
    for alias in drids:
        drs = BreakRecord.objects.filter( psdid=alias )
        to_ban ^= set(c.other_psdid for c in drs)

        odrs = BreakRecord.objects.filter(other_psdid=alias)
        to_ban ^= set(c.psdid for c in odrs)

        drs = DateRecord.objects.filter(psdid=alias).exclude( event=rr.event )
        to_ban ^= set(c.other_psdid for c in drs)
    
    return to_ban

def expand_psdid_set( psdid_set ):
    """
    Return all aliases of all psdids in this set
    """
    aliases = LinkRecord.objects.filter( psdid__in=psdid_set )
    return set( a.psdid_alias for a in aliases )


@transaction.commit_on_success 
def updateSingleMatch(l, r, event, update_database=True, matches=None, likes=None, likeds=None):
        """
        Update match preference for 'l' to 'r' for event 'event'
        Used for tweaking an individual dater and seeing the results.
        """
        if l.psdid == r.psdid:
            return
        
        alladd = l.all_additionals()
        allpast = l.all_past_dates(exclude_event=event)
        numadd = len(alladd)

        alladd ^= allpast
        ltot = len(alladd)
        alladd ^= all_alias_history(l)
        nalias = len(alladd) - ltot
        alladd ^= expand_psdid_set(alladd)  # expand folks we won't date to their aliases.
        nexp = len(alladd) - nalias - ltot
        outputStr = "%7s [brks: %2d past: %2d alias: %2d expnd: %2d]: " % (l.psdid, numadd, len(allpast), nalias, nexp)
       
        lint = l.interest_score(r)
        rint = r.interest_score(l)
        if r.psdid in alladd and lint > 0 and rint > 0:
                outputStr += "."
                
        if not r.psdid in alladd and lint > 0:
                if matches != None:
                    likes[l.psdid] += 1
                    likeds[r.psdid] += 1
                match = min(lint, rint)
                if match > 0:
                    outputStr += "+"
                    if matches != None:
                        matches[l.psdid] += 1
                else:
                    outputStr += "o"
                if update_database:
                        gay_ok = l.ok_gay_match(r) 
                        str_ok = l.ok_str_match(r)
                        mt = MatchRecord(event=event, psdid1=l.psdid, psdid2=r.psdid, match=lint,
                                         gay_ok=gay_ok, str_ok=str_ok)
                        mt.save()
                       
        if update_database and matches != None:
            l.matches = matches[l.psdid]
            l.oneway = likes[l.psdid]
            l.save()    
            
        return outputStr
    
    

@transaction.commit_on_success 
def updateMatches(l, regs, event, update_database=True, matches=None, likes=None, likeds=None):
        """
        Update match preference for 'l' to all regrecords in regs for event 'event'
        """
        alladd = l.all_additionals()
        allpast = l.all_past_dates(exclude_event=event)
        numadd = len(alladd)

        alladd ^= allpast
        ltot = len(alladd)
        alladd ^= all_alias_history(l)
        nalias = len(alladd) - ltot
        alladd ^= expand_psdid_set(alladd)
        nexp = len(alladd) - nalias - ltot
        outputStr = "%7s [brks: %2d past: %2d alias: %2d expnd: %2d]: " % (l.psdid, numadd, len(allpast), nalias, nexp)
       
        tick = 0
        for r in regs:  
            tick = tick + 1
            if l.psdid == r.psdid:
                continue
            lint = l.interest_score(r)
            rint = r.interest_score(l)
            if r.psdid in alladd and lint > 0 and rint > 0:
                outputStr += "."
                
            if not r.psdid in alladd and lint > 0:
                if matches != None:
                    likes[l.psdid] += 1
                    likeds[r.psdid] += 1
                match = min(lint, rint)
                if match > 0:
                    outputStr += "+"
                    if matches != None:
                        matches[l.psdid] += 1
                else:
                    outputStr += "o"
                if update_database:
                        gay_ok = l.ok_gay_match(r) 
                        str_ok = l.ok_str_match(r)
                        mt = MatchRecord(event=event, psdid1=l.psdid, psdid2=r.psdid, match=lint,
                                         gay_ok=gay_ok, str_ok=str_ok)
                        mt.save()
                       
        if update_database and matches != None:
            l.matches = matches[l.psdid]
            l.oneway = likes[l.psdid]
            l.save()    
            
        return outputStr
    
    
def updateMatchPairsFor( rr ):
    """
    Update single person
    Also regenerate all matches _to_ single person.
    """

    regs = RegRecord.objects.filter(event=rr.event, cancelled=False)

    outputStr = updateMatches( rr, regs, rr.event, True )
   
    for r in regs:
        outputStr += updateSingleMatch( r, rr, rr.event, True )

    return outputStr

    
    
def updateMatchRecords_async(event, update_database=True, last_triple=False):
    """ 
    Figure out pairs of potential dates.   Also store number of matches
    for each regrecord.
    
    Will not match folks who have previous dating history or who are 'banned' by
    a special entry in the 'additionals' table.
    
    Regarding the gay_ok and str_ok flags: this code makes an _asymmetric matrix_ where entries are nonzero
        if psdid1 is okay with it being a gay dating round or straight dating round.
        
    Returns: triple of (number matches, number regrecords, number of possible pairings)
    """
        
    MatchRecord.objects.filter( event=event ).delete()
    
    yield "breaks - number of hand-coded breaks in database\npast - number of past recorded dates in database, excluding this event\n"
    regs = RegRecord.objects.filter(event=event, cancelled=False)
   
    ticker=0
    matches = defaultdict(int)
    likes = defaultdict(int)
    likeds = defaultdict(int)
    
    # force the entire regs list to load.
    yield "Number of regrecords fetched: %s\n" % (len(regs), )
    for l in regs:
        ticker = ticker + 1
        outputStr = updateMatches( l, regs, event, update_database, matches, likes, likeds )
        yield "%02d] %s\n" % (ticker, outputStr, )

    yield("%s total matches: mean %s - median %s" % sum_mean_median(matches.values())  )
    yield("%s total interest: mean %s - median likes %s," % sum_mean_median(likes.values()) )
    yield("Is liked by %s" % ( sum_mean_median(likeds.values())[2], ) )

    if last_triple:
        recticker=(len(regs)-1)*len(regs)
        yield (sum(matches.values()), len(regs), recticker )





def updateMatchRecords(event, verbose=False, update_database=True):
    """ 
    Returns: triple of (number matches, number regrecords, number of possible pairings)
    """
    
    recIter = updateMatchRecords_async( event, update_database, last_triple=True )
    for ln in recIter:
        if verbose:
            print ln
    
    return ln


