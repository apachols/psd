
import sys

from string import lower

from psd.register.psdcheckbox import get_preference_for
#from psd.register.models import Response
# TODO: How to import this?

import logging
logger = logging.getLogger('psd.register.models')

def csv_to_set(s):
    """
    >>> csv_to_set('a,b')
    set(['a', 'b'])
    >>> csv_to_set('')
    set([])
    """
    return set(s.split(',') if s else [])

def getReadableStringFromMatchQuestion(obj, match_question, tagFunction, conjunction="and"):
    """
    tagFunction is a function that takes a matchchoice code and returns boolean value of whether
    self has checked that box or not.  E.g., atLoc.
    
    It can also take a function that returns a 0,1,2 weight, in which case the 2 weights
    are marked with a "*" to denote extra interest.  E.g., prefG
    """
    hits = []
    for tup in match_question:
        val = tagFunction( obj, tup[0] )
        if val==2:
            hits.append( tup[1] + "*" )
        elif val:
            hits.append( tup[1] )

    
    if len(hits) == 0:
        return ""
    elif len(hits) == 1:
        return hits[0]
    elif len(hits) == 2:
        return hits[0] + " " + conjunction + " " + hits[1]
    else:
        ss = hits[0]
        for lo in hits[1:-1]:
            ss = ss + ", " + lo
        
        ss = ss + ", " + conjunction + " " + hits[-1]
           
        return ss

def isG(p, gen):
    if gen in csv_to_set(p.gender):
        return True
    else:
        return False

def lookG(p, gen):
    gs = p.seek_gender_set
    if gen in gs:
        return True
    else:
        return False

def prefG(p, gen):
    return get_preference_for(p.seek_gender, gen) > 1

def genderDesc(p):
    ss = getReadableStringFromMatchQuestion(p, p.genderOptions(), isG)
    if ss == "":
        return "No preference given (so anyone could match)"
    else:
        return ss

    return ss.strip()

def genderLookDesc(p):
    try:
        ss = getReadableStringFromMatchQuestion( p, p.genderOptions(), lookG, conjunction="and/or" )
        if ss == "":
            return "nothing (which will prevent all matches)"
        else:
            return ss
        return ss.strip()
    except Exception as inst:
        logger.error( "Caught error in genderLookDesc" )
        logger.error( str(inst) )
        logger.error( "ouch" )
    
    return "FAILED in genderLookDesc()"
    
def genderPrefDesc(p):
    try:
        ss = getReadableStringFromMatchQuestion(p, p.genderOptions(), prefG, conjunction="and")
        if ss == "":
            return ""
        else:
            return ss
        return ss.strip()
    except Exception as inst:
        logger.error( "Caught error" )
        logger.error( str(inst) )
        logger.error( "ouch" )
        
    return "FAILED in genderPrefDesc()"


def minicode(p):
    """Short string to describe person's dating characteristics"""
    s = str(p.age) + ' ' + p.gender.replace(",","/") + ' '
    if p.kinky:
       s = s + "k"
    if p.seeking_primary:
       s = s + "p"
    s = s + " -> " + str(p.seek_age_min) + "-" + str(p.seek_age_max)\
                     + ' ' + p.seek_gender.replace(",","/") + ' ' + lower(p.seek_kinkiness[0])
    return s  #.tolower()


def conjunction_fragment( my_resp, conj="and" ):
    if len(my_resp) == 0:
        return None
    elif len(my_resp) == 1:
        return str( my_resp[0] )
    elif len(my_resp) == 2:
        return str( my_resp[0] ) + " " + conj + " " + str( my_resp[1] )        
    else:
        frg = ', '.join( [str(x) for x in my_resp[:-1] ] )
        return frg + ", " + conj + " " + str(my_resp[-1])

    
def extra_question_code_nameless( question, p ):
    """
    Generate extra question string _without_ using the name of the question.
    """
    respobj = p.answers_for(question=question)
    if not respobj is None:
        my_resp = [x for x in respobj.answers.all()]
        my_seek = [x for x in respobj.seek_answers.all()]
    else:
        my_resp = []
        my_seek = []
    ident = conjunction_fragment(my_resp, "and" )

    if not question.ask_about_seek:
        if ident is None:
            return ''
        else:
            return 'You said %s.' % ( ident, )
            
    if not ident is None:
        if question.hard_match:
            frag2 = "that your dates be open to dating %s" % (ident, )
        else:
            frag2 = "your dates to be looking for %s" % (ident, )
            
    look = conjunction_fragment(my_seek, "and" )
    
    if ident is None and look is None:
        return ''
    
    if look is None:
        if question.hard_match:
            frag3 = "were not open to any of these things."
        else:
            frag3 = "expressed no preferences in what you were looking for."
    else:
        if question.hard_match:
            frag3 = "said you were open to dating %s." % (look, )
        else:
            frag3 = "want to be matched with %s." % (look, )
        
    if ident is None:
        if question.hard_match:
            return 'You made no constraints on what people be open to.  You %s' % ( question.question, frag3 )
        else:
            return 'You %s' % ( frag3 )        
    else:
        if question.hard_match:
            return 'You require %s.  You %s' % ( frag2, frag3 )
        else:
            return 'You want %s.  You %s' % ( frag2, frag3 )




def extra_question_code( question, p ):

    if not question.include_name:
        return extra_question_code_nameless( question, p )

    respobj = p.answers_for(question=question)
    if not respobj is None:
        my_resp = [x for x in respobj.answers.all()]
        my_seek = [x for x in respobj.seek_answers.all()]
    else:
        my_resp = []
        my_seek = []
    ident = conjunction_fragment(my_resp, "and" )
    
    if not question.ask_about_seek:
        if ident is None:
            return 'Regarding %s, you said nothing.' % ( question.question, )
        else:
            return 'Regarding %s, you said %s.' % ( question.question, ident )
            
    if not ident is None:
        if question.hard_match:
            frag2 = "that your dates be open to dating %s" % (ident, )
        else:
            frag2 = "your dates to want %s" % (ident, )
            
    look = conjunction_fragment(my_seek, "and" )
    
    if ident is None and look is None:
        return 'Regarding %s, you did not check off any options.' % (question.question, )
    
    if look is None:
        if question.hard_match:
            frag3 = "were not open to any of these things."
        else:
            frag3 = "expressed no preferences in what you were looking for."
    else:
        if question.hard_match:
            frag3 = "said you were open to dating %s." % (look, )
        else:
            frag3 = "want to be matched with %s." % (look, )
        
    if ident is None:
        if question.hard_match:
            return 'Regarding %s, you made no constraints on what people be open to.  You %s' % ( question.question, frag3 )
        else:
            return 'Regarding %s, you %s' % ( question.question, frag3 )        
    else:
        if question.hard_match:
            return 'Regarding %s, you require %s.  You %s' % ( question.question, frag2, frag3 )
        else:
            return 'Regarding %s, you want %s.  You %s' % ( question.question, frag2, frag3 )

        
def extra_question_paragraph( p, event, sep ):
    questions = [x for x in event.cached_extra_questions()]
    if questions:
        return sep.join( extra_question_code( q, p ) for q in questions)
    else:
        return None



def geekcode(p, asGroupMember=True, html=False, event=None):
    """
    p is Person object
    """
    if asGroupMember:
        sep = '  '
    else:
        sep = '<p><p>' if html else '\n\n'
        
    try:
        s = ""
        if p.kinky:
            s = "a kinky " + str(p.age) + " year old"
        else:
            s = "a not-kinky " + str(p.age) + " year old"
            
        if not asGroupMember and p.seeking_primary:
                s += ", potentially interested in a primary,"
        
        s += " looking for " + str(p.seek_age_min) + "-" + str(p.seek_age_max) + " yr old"

        if p.seek_kinkiness == 'K':
            s += " kinky " + genderLookDesc(p)
        elif p.seek_kinkiness == 'NK':
            s += " non-kinky " + genderLookDesc(p)
        elif p.seek_kinkiness == 'EI':
            s += " " + genderLookDesc(p)
        else:
            logger.error( "Seek_kinkiness is invalid (%s) in geekcode(person)" % (p.seek_kinkiness, ) )
            s += " " + genderLookDesc(p)
            
        s += "."
        gp = genderPrefDesc(p)
        if ( len(gp) > 0 ):
            gp = gp[0].capitalize() + gp[1:]
            s += "  " + gp + " are preferred."
            
        s += sep + "Your dates must be willing to date all of the following: " + genderDesc(p) + "."
        
        if event != None:
            ext = extra_question_paragraph( p, event, sep )
            if ext != None:
                s += sep + ext 
        
        return s
    except Exception as inst:
            import traceback
            traceback.print_exc()
            logger.error( "Unexpected error:", sys.exc_info()[0] )     
            logger.error( "%s\n%s\n%s" % ( type(inst), inst.args, inst ) )           
            logger.error( "geekcode() for person failed" )
            return "some person or other (ERROR)"



def atLoc(rr, loc):
    gs = csv_to_set(rr.location)
    if loc in gs:
        return True
    else:
        return False

    
def rr_minicode(rr):
    """Short string to describe record's dating characteristics"""

    if not rr.is_group:
        s = minicode(rr.indiv)
    else:
        peeps = rr.members
        s = minicode(peeps[0])
        for p in peeps[1:]:
                s += "; " + minicode(p)

        if rr.groups_match_all:
            s += "-all"

    if not rr.seek_groups:
        s += ""
    elif rr.groups_match_all:
        s += "-all"
    else:
        s += "-any"

    if rr.friend_dates:
        s += "-F"

    if rr.stationary:
        s += "(S)"

    s += ' ' + rr.location.replace(",","/")
    
    return s
        
def rr_geekcode(rr, html=False, event=None ):
    try:
        numPeeps = rr.size
        
        if not rr.is_group:
            s = "You are " + geekcode(rr.indiv, False, html, event)
        else:
            peeps = rr.members
            s = "You all are a group of the following " + str(numPeeps) + " people:\n1) " + geekcode(peeps[0], True, html, event )
            for (k,p) in enumerate( peeps[1:] ):
                    s += "\n%s) %s" % (k+2, geekcode(p, True, html, event))

            if not rr.groups_match_all:
                s += "\n\nHaving dates that match only one of you is fine."
            else:
                s += "\n\nDates must be compatible with all of you."

        s += "\n\n"

        if not rr.seek_groups:
            s += "You are not interested in dating groups."
        elif rr.groups_match_all:
            if numPeeps > 1:
                s += "You are interested in dating groups if everyone in each group is compatible with someone in the other group."
            else:
                s += "You are interested in dating groups if you match everyone in the group."
        else:
            s += "You are interested in dating groups if you match at least one person in the group."
             
        if rr.friend_dates:
            s += "  Friendship dates are okay."
        else:
            s += "  You do not want friendship dates."

        if rr.stationary:
            s += "  You need to stay in the same spot."

        try:
            ss = getReadableStringFromMatchQuestion( rr, rr.locationOptions(), atLoc, conjunction="or" )
            if ss == "":
                s += "  No residence given."
            else:
                s += "  We will try to match you with people from " + ss + "."
        except Exception as inst:
            logger.error( "Unexpected error: %s\n%s\n%s\n%s" % ( sys.exc_info()[0], type(inst), inst.args, inst ) )           
            s += "  From (location lookup fail)"
        except:
            logger.error( "Really weird error --- help!" )
            
        if html:
            return s.replace( "\n", "<p>" )
        else:
            return s
    except:
        logger.error( "rr_geekcode() regrecord failed" )
        return "error-some dating group or other"
    
    
    
    #    def pronoun(g):
#        if not isinstance(g, list):
#            g = g.split(',')
#        if 'Q' in g or ('M' in g and 'W' in g) or ('TM' in g and 'TW' in g): return "Zie"
#        elif 'TM' in g: return "He"
#        elif 'TW' in g: return "She"
#        elif 'M' in g: return "He"
#        elif 'W' in g: return "She"
#        else: return "Zie"
#        ## This last case should be impossible, but...


