"""
Code to assess success of matching and who is there and so forth.
"""

from psd.register.models import *
from psd.register.psdcheckbox import MatchQuestion, MatchChoice, getPSDCheckboxOptions, genCodeForSeekAndPrefs, genSeekAndPrefs

import numpy as np
import pandas as pd
from pandas import DataFrame, Series


def person_gender( p ):
    if p.only_alt_gendered:
        return "Other"
    if p.is_man_only:
        return "Men"
    if p.is_woman_only:
        return "Women"
    return "Both"


def gay_str_bi( p ):
    if p.wants_mf:
        return "bi"
    elif not p.is_man_only and not p.is_woman_only:
        if p.wants_m:
            return "wM"
        elif p.wants_f:
            return "wW"
        else:
            return "wO"
    elif (p.wants_m and p.is_man_only) or (p.wants_f and p.is_woman_only):
        return "gay"
    else:
        return "str"


def want_string( p ):
    if p.wants_mf:
        return "wMW"
    elif p.wants_m:
        return "wM"
    elif p.wants_f:
        return "wW"
    else:
        return "wO"

def is_trans(self):
        return self.has_gender("TW") or self.has_gender("TM")

def wants_trans(self):
    return self.wants_gender('TW') or self.wants_gender('TM')
    


def wants_alt(self):
        sg = self.seek_gender_set - set( ['W','M','TW','TM' ] )
        return len(sg) > 0
        
def is_pansexual(self):
        return self.wants_mf and wants_trans(self) and wants_alt(self)

def complex_gender(p):
    sg = p.gender_set - set( ['W','M','TW','TM' ] )
    alts = len(sg) > 0
    stt = ""
    if p.only_alt_gendered:
        return "O"
    if p.has_gender('M'):
        stt += "M"
    if p.has_gender('W'):
        stt += "W"
    if is_trans(p):
        stt = "T" + stt
    if alts:
        stt += "A"
    return stt

def complex_seek_gender(p):
    sg = p.seek_gender_set - set( ['W','M','TW','TM' ] )
    alts = len(sg) > 0
    stt = ""
    if is_pansexual(p):
        return "Pan"
    
    if p.only_alt_gendered:
        return "O"
    if p.wants_gender('M'):
        stt += "M"
    if p.wants_gender('W'):
        stt += "W"
    if wants_trans(p):
        stt = "T" + stt
    if alts:
        stt += "A"
    return stt


def make_demographics_table( folks ):
    psdids = [r.psdid for r in folks for p in r.members ]
    df = DataFrame( index = psdids )
    df[ 'name' ] = [p.fullname for r in folks for p in r.members]
    df[ 'group' ] = [r.is_group for r in folks for p in r.members ]
    df[ 'age' ] = [p.age for r in folks for p in r.members ]
    df[ 'gstring' ] = [p.gender for r in folks for p in r.members ]
    df[ 'gender' ] = [person_gender(p) for r in folks for p in r.members ]
    df[ 'is_trans' ] = [is_trans(p) for r in folks for p in r.members ]
    df[ 'is_pan' ] = [is_pansexual(p) for r in folks for p in r.members ] 
    df[ 'seek' ] = [want_string(r) for r in folks for p in r.members ]
    df[ 'seek_trans'] = [wants_trans(p) for r in folks for p in r.members ] 
    df[ 'gen_comp'] = [complex_gender(p) for r in folks for p in r.members ]
    df[ 'seek_comp' ] = [complex_seek_gender(p) for r in folks for p in r.members ] 
    return df



    
    
def print_demog_table( df ):
    print df.to_string()
    
def gender_table( df ):
    return pd.pivot_table( df, "name", rows=["group","gender"], cols="seek", aggfunc=len, margins=True )
        

def gender_age_table( df ):
    df[ 'decade' ] = pd.cut( df[ 'age' ], bins=[0,20,25,30,35,40, 45,50,60,70,1000] )
    return pd.pivot_table( df, "name", rows=["group","gender"], cols="decade", aggfunc=len, margins=True )
    

def gender_string( rr ):
    if rr.is_group:
        return "group"
    elif rr.is_man_only:
        return "man"
    elif rr.is_woman_only:
        return "woman"
    else:
        return "other"


def date_distribution_iter( event_name ):
    
    folks = RegRecord.objects.filter( event=event_name )

    gends = [person_gender(p) for r in folks for p in r.members ]
    
    # header
    yield "PSDID,minicode,gender,desire,bi,num.M,num.W,num.G,num.O,num.Fr\n"
    for f in folks:
        countdict = { "M":0, "W":0, "G":0, "Friend":0, "O":0 }
        for dt in DateRecord.objects.filter(event=event_name,psdid=f.psdid ):
            dt_rr = fetch_regrecord( event_name, dt.other_psdid )
            if dt.friend_date:
                countdict["Friend"] += 1
            elif dt_rr.is_group:
                countdict["G"] += 1
            elif dt_rr.is_man_only:
                countdict["M"] += 1
            elif dt_rr.is_woman_only:
                countdict["W"] += 1
            else:
                countdict["O"] += 1
        outstr = ','.join( [f.psdid, f.minicode(), gender_string(f), '/'.join(f.seek_genders), gay_str_bi(f), str(countdict["M"]), str(countdict["W"]), str(countdict["G"]), str(countdict["O"]), str(countdict["Friend"]) ] )
        yield outstr + "\n"


    
    
def make_demographics_frame( event_name, who_print ):
    """
    Old, Depreciated
    
    Make a csv file of a bunch of info on daters
    """
    
    folks = RegRecord.objects.filter( event=event_name )

    if who_print == "Here":
        folks = folks.filter( here=True )
    elif who_print=="NotNo":
        folks.filter( cancelled=False )
    
    # header
    yield "PSDID,minicode,gender,desire,bi,num.M,num.W,num.G,num.O,num.Fr\n"
    for f in folks:
        countdict = { "M":0, "W":0, "G":0, "Friend":0, "O":0 }
        for dt in DateRecord.objects.filter(event=event_name,psdid=f.psdid ):
            dt_rr = fetch_regrecord( event_name, dt.other_psdid )
            if dt.friend_date:
                countdict["Friend"] += 1
            elif dt_rr.is_group:
                countdict["G"] += 1
            elif dt_rr.is_man_only:
                countdict["M"] += 1
            elif dt_rr.is_woman_only:
                countdict["W"] += 1
            else:
                countdict["O"] += 1
        outstr = ','.join( [f.psdid, f.minicode(), gender_string(f), '/'.join(f.seek_genders), gay_str_bi(f), str(countdict["M"]), str(countdict["W"]), str(countdict["G"]), str(countdict["O"]), str(countdict["Friend"]) ] )
        yield outstr + "\n"
   


def name_tag_iter( event_name ):
    """
    Iterate through all regrecords and make a nametag for each
    person for each regrecord.
    Sort by regrecord nickname, alphabetically case-insensitive.
    """ 
    # header
    yield "pubname,PSDID,first_name,last_name,email\n"
    
    # all folks
    folks = RegRecord.objects.filter( event=event_name )
    folks = sorted( folks, key=lambda flk: flk.nickname.lower() )
    
    #print "Generating nametags for %s folks for event '%s'" % ( len(folks), event_name, )
    for f in folks:
        peeps = f.members
        for p in peeps:
            yield "%s,%s,%s,%s,%s\n" % (f.nickname,f.psdid,p.first_name,p.last_name,f.email )

def make_demog_from_event( event_name, who_print="All" ):
    folks = RegRecord.objects.filter( event=event_name )
    if who_print == "Here":
        folks = folks.filter( here=True )
    elif who_print=="NotNo":
        folks.filter( cancelled=False )

    if len( folks ) == 0:
        return None
    else:
        df = make_demographics_table( folks )
        return df

def print_demographics_async( event_name, who_print="All" ):

    folks = RegRecord.objects.filter( event=event_name )
    if who_print == "Here" or who_print =="In":
        folks = folks.filter( here=True )
    elif who_print=="NotNo":
        folks = folks.filter( cancelled=False )

    yield "Demographic Summary for Event '%s', selection flag %s\n" % (event_name, who_print )
    
    if len( folks ) == 0:
        yield "No reg records for %s with %s\n" % (event_name, who_print)
    else:
        date_units = len(folks)
        num_groups = len( folks.filter( is_group=True ) )
        
        df = make_demographics_table( folks )
        num_people = len(df)
        
        yield """
        Some totals:
        # Units: %s
        # Groups: %s
        # People: %s""" % ( date_units, num_groups, len(df), )
    
        pt = pd.pivot_table( df, "name", rows=["group"], cols="gender", aggfunc=len, margins=True )
        yield "\n\nGroup by Gender Breakdown\n%s" % (pt.to_string(na_rep='.'), )
        
        yield "\n\nGender by Desire Breakdown (by Group Status)\n%s" % (gender_table( df ).to_string( na_rep='.'), )
        
        yield "\n\nGender by Age Breakdown (by Group Status)\n%s" % (gender_age_table(df).to_string( na_rep="." ) )
        
        pt = pd.pivot_table( df, "name", rows=["group",'is_trans'], cols="seek_trans", aggfunc=len, margins=True )
        yield "\n\nCount of Transgender (by Group Status)\n%s" % (pt.to_string(na_rep='.'), )

        pt = pd.pivot_table( df, "name", rows=["group",'gen_comp'], cols="seek_comp", aggfunc=len, margins=True )
        yield "\n\nCounts for Expanded Gender (by Group Status)\n%s" % (pt.to_string(na_rep='.'), )


#def date_count_iter( event_name ):
#    """
#    Print out the number of matches each dater got
#    """
#    
#    folks = RegRecord.objects.filter( event=event_name )
#
#    # header
#    yield "PSDID,minicode,gender,desire,bi,date.PSDID,date.type,round,match,their.match\n"
#
#    for f in folks:
#        for dt in DateRecord.objects.filter(event=event_name,psdid=f.psdid ):
#            outstr = ','.join( [f.psdid, f.minicode(), gender_string(f), '/'.join(f.seek_genders), gay_str_bi(f) )
#            
#            outstr += dt.friend_date + "," + dt.round + "," + dt. 
#            #dt_rr = fetch_regrecord( event_name, dt.other_psdid )
#            yield outstr + "\n"



                            
