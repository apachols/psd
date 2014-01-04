#from __future__ import print_function

from django.db import models
#from django.contrib.auth.models import User
import sys
from django.contrib.sites.models import Site
from string import lower
from collections import defaultdict
from psd.register.psdcheckbox import MatchQuestion, MatchChoice, getPSDCheckboxOptions, genCodeForSeekAndPrefs, genSeekAndPrefs
from django.core.exceptions import ObjectDoesNotExist
from psd.register import describe
from psd.register.decorators import memoized_property

import logging
logger = logging.getLogger('psd.register.models')





class Person(models.Model):
    GENDERS = None
    
    first_name = models.CharField(max_length=30, verbose_name="First Name")
    last_name = models.CharField(max_length=30, verbose_name="Last Name")
    gender = models.CharField(max_length=40, verbose_name="Gender")
    age = models.PositiveIntegerField(verbose_name="Age")
    seeking_primary = models.NullBooleanField(verbose_name="Seeking Primary (Y/N)", blank=True)
    kinky = models.NullBooleanField(verbose_name="Kinky (Y/N)", blank=True)
    seek_gender = models.CharField(max_length=50, verbose_name="Genders Sought")
    
    seek_age_min = models.PositiveIntegerField(verbose_name="Minimum Age Wanted")
    seek_age_max = models.PositiveIntegerField(verbose_name="Maximum Age Wanted")
    seek_kinkiness = models.CharField(max_length=2, verbose_name="Kinkiness Wanted", blank=True, null=True)
    psdid = models.CharField(max_length=12, blank=True) # unique=TRUE

    def genderOptions(self):
        """
        This should be a class method. 
        Fetch list of locations from database and stash in local variable to avoid
        making too many database hits.
        """
        if Person.GENDERS == None:
            print( "Loading gender options and setting GENDER variable in Person" )
            logger.debug( "Loading gender options and setting GENDER variable in Person" )
            Person.GENDERS = getPSDCheckboxOptions( "Gender" )
            #logger.debug( "Got " + str( Person.GENDERS ) )
        return Person.GENDERS

    def __unicode__(self):
        return self.first_name + ' ' + self.last_name

    @memoized_property
    def gender_set(self):
        res = describe.csv_to_set(self.gender)
        return res

    @memoized_property
    def seek_gender_set(self):
        res = genSeekAndPrefs(self.seek_gender)[0]
        return set(res)

    @memoized_property
    def pref_gender_set(self):
        res = genSeekAndPrefs(self.seek_gender)[1]
        return set(res)
 
    def has_gender(self, g):
        return g in self.gender_set

    def wants_gender(self, g):
        return g in self.seek_gender_set
   
    def interest_score(self, other, event):
        if self.will_date(other, event):
            return 1 + self.bonus_for(other, event)
        else:
            return 0

    @memoized_property
    def will_date_kinky(self):
        return self.seek_kinkiness in ('K','EI')

    @memoized_property
    def will_date_nonkinky(self):
        return self.seek_kinkiness in ('NK','EI')

    def kink_works_out(self, other):
        if other.kinky:
            return self.will_date_kinky
        else:
            return self.will_date_nonkinky

    def mutual(self, other, event):
        return self.will_date(other, event) and other.will_date(self, event)

    def will_date(self, other, event):
        """
        Will self date other in the given event 'event'. 
        Param: other - a Person object
               event - an Event object.
        """
        return self.will_date_basic(other) and self.will_date_extra(other, event)

    def will_date_basic(self, other):
        return (
            other.gender_set.issubset(self.seek_gender_set) and
            other.age >= self.seek_age_min and
            other.age <= self.seek_age_max and
            self.kink_works_out(other) #and
         #   self.psdid != other.psdid
               )

    def will_date_extra(self, other, event):
        questions = [x for x in event.cached_extra_questions() if x.hard_match]
        for question in questions:
            if not self.will_date_re_single_question(other, question):
                return False
        return True

    def will_date_re_single_question(self, other, question):
        my_resp = Response.objects.get(question=question, owner=self)
        your_resp = Response.objects.get(question=question, owner=other)
        my_seek = set(my_resp.seek_answers.all())
        your_answers = set(your_resp.answers.all())
        your_good_answers = your_answers & my_seek
        your_bad_answers = your_answers - my_seek

        if question.strict_subset_match:
            ## Controversial! If it's a strict subset question, and
            ## you marked nothing at all for yourself, do you meet
            ## my criteria? This implementation says yes.
            return not bool(your_bad_answers)
        else:
            return bool(your_good_answers)

    def bonus_for(self, other, event):
        return self.basic_bonus_for(other) + self.extra_bonus_for(other, event)

    def basic_bonus_for(self, other):
        bonus = 0
        if other.age >= self.seek_age_min+5 and \
           other.age <= self.seek_age_max-5:
            bonus += 2
            
        if self.kinky == other.kinky:
            bonus += 2
            
        if self.seeking_primary and other.seeking_primary:
            bonus += 2

        if len( self.pref_gender_set.intersection(other.gender_set) ) > 0:
            bonus += 2
            
        return bonus 

    def extra_bonus_for(self, other, event):
        questions = [x for x in event.cached_extra_questions() if not x.hard_match]
        if questions:
            return sum(self.extra_bonus_for_single_question(other, question) for question in questions)
        else:
            return 0

    def extra_bonus_for_single_question(self, other, question):
        my_resp = Response.objects.get(question=question, owner=self)
        your_resp = Response.objects.get(question=question, owner=other)
        my_seek = set(my_resp.seek_answers.all())
        your_answers = set(your_resp.answers.all())
        return len(my_seek & your_answers)

    def mutual_with_any(self, group, event):
        return any(self.mutual(o, event) for o in group.members)

    @memoized_property
    def fullname(self):
        return self.first_name + " " + self.last_name

    def geekcode(self):
        return describe.geekcode(self)

    def minicode(self):
        return describe.minicode(self)

    def answers_for(self, question):
        try:
            my_resp = Response.objects.get(question=question, owner=self)
            return my_resp
        except Response.DoesNotExist:
            return None

    @memoized_property
    def one_cisgender(self):
        sg = self.gender_set
        return (len(sg) == 1) and (sg[0] in ('M','W'))


    @memoized_property
    def is_man_only(self):
        return (self.has_gender('M') or self.has_gender("TM")) and not ( self.has_gender('W') or self.has_gender('TW') )
 
    @memoized_property
    def is_woman_only(self):
        return (self.has_gender('W') or self.has_gender("TW")) and not ( self.has_gender('M') or self.has_gender('TM') )


    @memoized_property
    def only_alt_gendered(self):
        return (not self.has_gender('M')) and (not self.has_gender('W')) and (not self.has_gender('TM')) and (not self.has_gender('TW'))

    @memoized_property
    def wants_mf(self):
        return (self.wants_gender('M') or self.wants_gender('TM')) and (self.wants_gender('W') or self.wants_gender('TW'))

    @memoized_property
    def wants_m(self):
        return self.wants_gender('M') or self.wants_gender('TM')

    @memoized_property
    def wants_f(self):
        return self.wants_gender('W') or self.wants_gender('TW')



class RegRecord(models.Model):
    LOCATION = None
    
    nickname = models.CharField(max_length=30, verbose_name="Nickname")
    email = models.EmailField(verbose_name="Email")
    add_to_mailings = models.BooleanField(default=True, verbose_name="Join Our Mailing List (Y/N)")
    seek_groups = models.BooleanField(verbose_name="Date Groups (Y/N)")
    groups_match_all = models.BooleanField(verbose_name="All Group Members Must Match (Y/N)")
    #only_groups = models.BooleanField( verbose_name="Only Date Groups if Dating Groups (Y/N)" )
    friend_dates = models.BooleanField(verbose_name="Friend Dates (Y/N)")
    referred_by = models.CharField(max_length=30, blank=True, verbose_name="Referred By")
    pals = models.TextField(blank=True, verbose_name="Friends")
    location = models.CharField(max_length=30, blank=True, verbose_name="Location")
    wants_childcare = models.BooleanField(verbose_name="Need Childcare (Y/N)")
    children = models.TextField(blank=True, verbose_name="Children")
    comments = models.TextField(blank=True, verbose_name="Comments")
    event = models.CharField(max_length=15, blank=True)
    people = models.ManyToManyField(Person, blank=True)
    #user = models.OneToOneField(User, null=True, blank=True)
    psdid = models.CharField(max_length=12, blank=True) # 8 for triads
    paid = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    pending = models.BooleanField(default=False)
    here = models.BooleanField(default=False)
    stationary = models.BooleanField(default=False)
    is_group = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    matches = models.IntegerField(blank=True, null=True, default=0)
    oneway = models.IntegerField(blank=True, null=True, default=0)

    @memoized_property
    def is_indiv(self):
        return not self.is_group
  
    @memoized_property
    def members(self):
        return self.people.all()

    @memoized_property
    def size(self):
        return self.people.count()

    @memoized_property
    def ev(self):
        return Event.objects.get(event=self.event)

    
    def locationOptions(self):
        """
        This should be a class method. 
        Fetch list of locations from database and stash in local variable to avoid
        making too many database hits.
        """
        
        if RegRecord.LOCATION == None:
            logger.debug( "Loading location options and setting LOCATION variable in regrecord" )
            RegRecord.LOCATION = getPSDCheckboxOptions( "Location" )
            #logger.debug( "Got " + str( RegRecord.LOCATION ) )
        return RegRecord.LOCATION


    def hasNotes( self ):
        if self.notes == "":
           return False
        else:
           return True

    def addNote(self, note ):
        """ append note to field """
        if self.hasNotes():
            self.notes = self.notes + "; " + note
        else:
            self.notes = note
        self.save()
        
        
    def __unicode__(self):
        try:
            return "RR(%s) %s-%s-%s" % (self.id, self.event, self.psdid, '+'.join(unicode(s) for s in self.members))
        except:
            logger.error( sys.exc_info()[0] )
            return "[ERROR - Contact Sys Admin]"

    def full_names(self):
        try:
            return "%s" % ( '+'.join(unicode(s) for s in self.members ), )
        except:
            logger.error( sys.exc_info()[0] )
            return "[ERROR - Contact Sys Admin]"
        
    def integrity_ok(self):
        if self.is_group:
            if self.size > 1:
                return False
        else:
            if self.size != 1:
                return False

        return True

    @memoized_property
    def indiv(self):
        assert not self.is_group
        assert self.size == 1, self
        return self.members[0]

#    def all_like(self, whom):
#        ''' Do everyone in this group like a person? '''
#        return all(p.will_date(whom) for p in self.people)
#
#    def all_liked_by(self, whom):
#        ''' Is everyone in this group liked by a person? '''
#        return all(whom.will_date(p) for p in self.people)
#
#    def any_like_all(self, other):
#        ''' Does anyone in this group like everyone in another group? '''
#        return any(other.all_liked_by(p)  for p in self.people)

    def any_match_someone(self, other):
        ''' Does anyone in this group mutually match someone in another group? '''
        return any(p.mutual_with_any(other, self.ev) for p in self.members)

    def all_match_someone(self, other):
        ''' Does everyone in this group mutually match someone in another group? '''
        return all(p.mutual_with_any(other, self.ev) for p in self.members)

    @memoized_property
    def location_set(self):
        return describe.csv_to_set(self.location)

    @memoized_property
    def genders(self):
        return set(g for p in self.members for g in p.gender_set)

    @memoized_property
    def seek_genders(self):
        return set(g for p in self.members for g in p.seek_gender_set)

    def has_gender(self, g):
        return g in self.genders

    def wants_gender(self, g):
        return g in self.seek_genders

    @memoized_property
    def one_cisgender(self):
        if self.is_group:
            return False
        sg = self.genders
        return (len(sg) == 1) and (sg[0] in ('M','W'))

    @memoized_property
    def is_man_only(self):
        return (self.has_gender('M') or self.has_gender("TM")) and not ( self.has_gender('W') or self.has_gender('TW') )
 
    @memoized_property
    def is_woman_only(self):
        return (self.has_gender('W') or self.has_gender("TW")) and not ( self.has_gender('M') or self.has_gender('TM') )

    @memoized_property
    def only_alt_gendered(self):
        return (not self.has_gender('M')) and (not self.has_gender('W')) and (not self.has_gender('TM')) and (not self.has_gender('TW'))

    @memoized_property
    def wants_mf(self):
        return (self.wants_gender('M') or self.wants_gender('TM')) and (self.wants_gender('W') or self.wants_gender('TW'))

    @memoized_property
    def wants_m(self):
        return self.wants_gender('M') or self.wants_gender('TM')

    @memoized_property
    def wants_f(self):
        return self.wants_gender('W') or self.wants_gender('TW')

    def mf_gender_match(self, other):
        return (self.has_gender('M') and other.has_gender('M'))  or \
               (self.has_gender('W') and other.has_gender('W'))

    def mf_gender_cross(self, other):
        return (self.has_gender('M') and other.has_gender('W'))  or \
               (self.has_gender('W') and other.has_gender('M'))

    def location_overlap(self, other):
        return bool(self.location_set & other.location_set)

    def will_date(self, other, event):
        if other.is_group and (not self.seek_groups):
            return False
        if self.is_group:
            if self.groups_match_all:
                return self.all_match_someone(other)
            else:
                return self.any_match_someone(other)
        elif other.is_group:
            if self.groups_match_all:
                return all(self.indiv.will_date(o, event) for o in other.members)
            else:
                return any(self.indiv.will_date(o, event) for o in other.members)
        else:
            return self.indiv.will_date(other.indiv, event)

    def bonus_for(self, other, event):
        score = 0

        if self.location_overlap(other):
            score += 2

        if self.is_group and self.groups_match_all and not other.is_group:
            score += 1

        ## If I'm a group, no further bonuses, I guess?
        if self.is_indiv:
            if other.is_indiv:
                score += self.indiv.bonus_for(other.indiv, event)
            else:
                ## So they're a group...
                ## If you want to match everyone, assume your interest is limited by
                ## whoever you match LEAST with. If you only want to match one, 
                ## obviously, you care about the best match.
                if self.groups_match_all:
                    score += min(self.indiv.bonus_for(o, event) for o in other.members)
                else:
                    score += max(self.indiv.bonus_for(o, event) for o in other.members)

        return score
    

    def interest_score(self, other):
        #print "\nInterest_score: %s\nTo %s" % (self.geekcode(), other.geekcode() )
        if self.will_date(other, self.ev):
            return 1 + self.bonus_for(other, self.ev)
        else:
            return 0

    @memoized_property
    def treat_as_man(self):
        return self.has_gender("M") or self.has_gender("TM") #(self.is_group) or self.is_man_only

    @memoized_property
    def treat_as_woman(self):
        return not self.treat_as_man


    @memoized_property
    def straightish_male(self):
        return self.is_man_only and not (self.wants_gender("M") or self.wants_gender("TM"))
        
        
    def ok_gay_match(self, other):
        """ Return true if person is not bi or the match would be a "gay" match"""
        if not self.wants_mf:
            return True
        return (self.treat_as_woman and other.treat_as_woman) or \
               (self.treat_as_man and other.treat_as_man)

  
    def ok_str_match(self, other):
       if not self.wants_mf:
            return True
       return (self.treat_as_woman and other.treat_as_man) or \
               (self.treat_as_man and other.treat_as_woman)
  

    def matrix_score(self, other, matrix_type):
        if ( matrix_type == 'gay' and not self.ok_gay_match( other ) ) \
           or ( matrix_type == 'str' and not self.ok_str_match( other ) ):
            return 0
        
        return self.interest_score(other)
    
    def ok_match(self, other, matrix_type ):
        return self.matrix_score(other,matrix_type) > 0
    
    def all_past_dates(self, exclude_event=None):
        """ Return all past dates person has had (possibly excluding some specified event) """
        if exclude_event == None:
            drs = DateRecord.objects.filter(psdid=self.psdid)
        else:
            drs = DateRecord.objects.filter(psdid=self.psdid).exclude( event=exclude_event )
        drids = set(c.other_psdid for c in drs)
        
        return drids
    
#    def all_additionals_old(self):
#        """ Return list of all additional folks to not date"""
#        from django.db import connection, transaction
#        cursor = connection.cursor()
#
#        cursor.execute("SELECT MatchA,MatchB from additionals WHERE MatchA=%s OR MatchB=%s", [self.psdid, self.psdid] )
#        psdids = cursor.fetchall()
#        psdids = set(c[c[0]==self.psdid] for c in psdids)
#        return psdids

    def all_additionals(self):
        """
        Return list of all additional folks to not date
        """
        drs = BreakRecord.objects.filter( psdid=self.psdid )
        drids = set(c.other_psdid for c in drs)

        odrs = BreakRecord.objects.filter(other_psdid=self.psdid)
        drids ^= set(c.psdid for c in odrs)

        return drids
        
    @memoized_property
    def namestring(self):
        pnames = ', '.join( c.fullname for c in self.members )
        return self.nickname + ": " + pnames
    
    
    def geekcode(self):
        return describe.rr_geekcode(self, False, self.ev )

    def minicode(self):
        return describe.rr_minicode(self)
    
    def htmlcode(self):
        return describe.rr_geekcode(self, True, self.ev )
    
    def registration_flag(self):
        """
        Flag to put up in the check-in list, if any
        """
        flg = []
        if self.matches <= 4:
            flg.append( "FLAG" )
        
        nts = self.notes.upper()
        if "DRINK" in nts:
            flg.append( "DRINK" )
        if "SEE ME" in nts or "FLAG" in nts:
            flg.append( "CHECK" )
        if "!NEED COMPANION!" in nts:
            flg.append( "SSM" )
        if "!" in nts:
            flg.append( "READ" )
            
        return ",".join( flg )

    
def fetch_regrecord( event_name, psdid ):
    """ Get a regrecord, if there is one """
    try:
         per = RegRecord.objects.get( event=event_name, psdid=psdid )
         return per
    except ObjectDoesNotExist:
        logger.error( "Failed to find RR '%s-%s'." % ( event_name, psdid, ) )
        return None

 
    
class MatchRecord( models.Model ):
    psdid1 = models.CharField(max_length=30, verbose_name="subject's PSDID")
    psdid2 = models.CharField(max_length=30, verbose_name="object's PSDID")
    event = models.CharField(max_length=15, blank=True)
    match = models.PositiveIntegerField(verbose_name="Likability")
    gay_ok = models.BooleanField(verbose_name="Gay Round Okay")
    str_ok = models.BooleanField(verbose_name="Straight Round Okay")
    
#    def __init__(self,event,psdid1,psdid2,match,gay_ok,str_ok):
#        self.psdid1=psdid1
#        self.psdid2=psdid2
#        self.event=event
#        self.match=match
#        self.gay_ok=gay_ok
#        self.str_ok=str_ok
        
    def __unicode__(self):
        return self.psdid1 + "-" + self.psdid2 + ": " + self.score_string()

    def score_string(self):
        strg = str(self.match) + "/"
        if self.gay_ok:
            strg += "G"
        if self.str_ok:
            strg += "S"
        return strg


class Organization(models.Model):
    site = models.ForeignKey(Site)
    info_email = models.EmailField(verbose_name="Email for asking registration questions" )
    mailing_list_url = models.CharField( max_length=100, verbose_name="Link to the mailing list for the organization" )
    homepage_url = models.CharField( max_length=100, verbose_name="Link to the home page for the organization" )
    
    def __unicode__(self):
        return "[Organization Object for %s]" % (self.site, )

class Event(models.Model):
    event = models.CharField( max_length=20 )
    longname = models.CharField( max_length=40 )
    location = models.CharField( max_length= 100 )
    address = models.CharField( max_length=100 )
    locationURL = models.CharField( max_length=100 )
    accessdetails = models.TextField( max_length=200 )
    cost = models.PositiveIntegerField(verbose_name="Cost per person")
    doorcost = models.PositiveIntegerField(verbose_name="Cost per person at door")
    payment_systems = models.CharField( max_length=40, verbose_name="List of payment systems that are turned on" )    
    paypal_email = models.EmailField(verbose_name="Email for paypal account")
    wepay_email = models.EmailField(verbose_name="Email for wepay account" )
    info_email = models.EmailField(verbose_name="Email for asking registration questions" )
    mailing_list_url = models.CharField( max_length=100, verbose_name="Link to the mailing list for this event" )
    homepage_url = models.CharField( max_length=100, verbose_name="Link to the home page for this event or event organizers" )
    has_childcare = models.BooleanField( default=False, verbose_name="Childcare will be provided at the event" )
    regclosed = models.BooleanField( default=False, verbose_name="Registration is closed---no additions allowed" )
    regfrozen = models.BooleanField( default=False, verbose_name="Registration is frozen--no updating of registration forms allowed" )
    no_ssm = models.BooleanField( default=False, verbose_name="Single straight men will be asked to bring a gender-balance companion" )
    no_emailing = models.BooleanField( default=False, verbose_name="Do not email update emails or admin log emails (check if there is no internet service)." )
    extra_questions = models.ManyToManyField(MatchQuestion, blank=True)
    date = models.DateField()
    starttime = models.TimeField()
    deadlinetime = models.TimeField()
    stoptime = models.TimeField()
    
    def __unicode__(self):
        return self.event + " on " + str(self.date)

    
    def cached_extra_questions(self):
        return self.extra_questions.all()
    

class DateRecord(models.Model):
    """ 
    This stores dating history.   
    
    There _should be_ pairs of entries where if psdid, other_psdid is in the 
    database, then the reverse should be as well.
    """
    friend_date = models.BooleanField(default=True, verbose_name="Date was a Friendship Date (Y/N)")
    psdid = models.CharField(max_length=12, blank=True)
    other_psdid = models.CharField(max_length=12, blank=True)
    table = models.CharField(max_length=12,blank=True)
    round = models.PositiveIntegerField(verbose_name="Dating Round")
    #    event = models.ForeignKey(Event, null=True)
    event = models.CharField( max_length=20 )
    said_yes = models.NullBooleanField(default=True, verbose_name="psdid said YES to other_psdid (Y/N)", null=True )
    they_said_yes = models.NullBooleanField(default=True, verbose_name="other_psdid said YES to psdid (Y/N)", null=True )
    notes = models.TextField(blank=True,null=True)

    def is_mutual(self):
        if self.said_yes==None or self.they_said_yes==None:
             return None
        elif self.said_yes and self.they_said_yes:
             return True
        else:
             return False

    @property
    def we_filled(self):
        return self.said_yes != None

    @property
    def they_filled(self):
        return self.they_said_yes != None
    
   
    @property
    def filled(self):
        return self.said_yes != None and self.they_said_yes != None
    
    
    def __unicode__(self):
        if self.said_yes==None:
             if self.they_said_yes==None:
                ss = " ?/?"
             elif self.they_said_yes:
                ss = " ?/yes"
             else:
                ss = " ?/no"

             if self.friend_date:
                 ss = ss + " (F)"
             return "%s dating %s - %s" % (self.psdid, self.other_psdid, ss, )
        else:
             ss = ""
             if self.said_yes:
                 if self.they_said_yes==None:
                     ss = "yes/?"
                 elif self.they_said_yes:
                     ss = "mutual"
                 else:
                     ss = "yes/no"
             else:
                 if self.they_said_yes==None:
                     ss = "no/?"
                 elif self.they_said_yes:
                     ss = "no/yes"
                 else:
                     ss = "no/no"

             if self.friend_date:
                 ss = ss + " (F)"
             return "%s dating %s - %s" % (self.psdid, self.other_psdid, ss)
         

class TableListRecord(models.Model):
    event = models.CharField(max_length=15, blank=True)

    def __unicode__(self):
        #numtabs = len( self.group_set.all() )
        #s = "List for %s (%s tables)" % (self.event, numtabs)
        s = "List for %s" % (self.event,)
        return s
        
class TableRecord(models.Model):
    name = models.CharField(max_length=12, blank=True)
    statOK = models.BooleanField(default=False, verbose_name="Okay for stationary folks (Y/N)")
    groupOK =  models.BooleanField(default=False, verbose_name="Okay for groups (Y/N)")
    quality = models.PositiveIntegerField(verbose_name="Quality")
    group = models.ForeignKey(TableListRecord)
    
    def __unicode__(self):
        s = "%s/%s - %s" % ( self.group.event, self.name, self.quality )
        if self.statOK:
            s += "/stat"
        if self.groupOK:
            s += "/grp"
        return s
        
    
    
class BreakRecord(models.Model):
    """ 
    This stores a hand-break (i.e., two people who should not be seated
    next to each other)   
    
    There does not need to be symmetry in these (i.e. pairs of entries where 
    if psdid, other_psdid is in the 
    database, then the reverse should be as well.)
    """
    friend_ok = models.BooleanField(default=False, verbose_name="Friendship Date Still Okay (Y/N)")
    psdid = models.CharField(max_length=12, blank=True)
    other_psdid = models.CharField(max_length=12, blank=True)
    notes = models.TextField(blank=True)

    def __unicode__(self):
        return "%s X %s - %s" % ( self.psdid, self.other_psdid, self.notes )
    

class CruiseRecord(models.Model):
    """
    This stores a cruise (i.e. one person wants their info sent
    unilaterally to another person).
    """
    psdid = models.CharField(max_length=7, blank=True)
    other_psdid = models.CharField(max_length=7, blank=True)
    event = models.CharField( max_length=20 )

    def __unicode__(self):
        return "%s cruised %s at %s" % (self.psdid, self.other_psdid, self.event)


class LinkRecord(models.Model):
    """
    This registers that psdid should not date anyone that psdid_alias has dated
    """
    psdid = models.CharField(max_length=7, blank=True)
    psdid_alias = models.CharField(max_length=7, blank=True)
 
    def __unicode__(self):
        return "%s takes history from %s" % (self.psdid, self.psdid_alias,)

class RecessRecord(models.Model):
    """
    This means the given psdid has mandatory free time during the given
    rounds of the given event. Can also have the special psdid "template".
    The 'volatile' field should be set to False for hand-added recesses
    (e.g. a person has said they need to leave early).
    """
    psdid = models.CharField(max_length=12, blank=True)
    event = models.CharField(max_length=15)
    rounds = models.CharField(max_length=30)
    kind = models.CharField(max_length=20)
    volatile = models.BooleanField(default=False)

    def __unicode__(self):
        return "Recess for %s at %s: rounds %s '%s'" % (self.psdid, self.event, self.rounds, self.kind)



class Response(models.Model):
    owner = models.ForeignKey(Person)
    question = models.ForeignKey(MatchQuestion)
    answers = models.ManyToManyField(MatchChoice)
    seek_answers = models.ManyToManyField(MatchChoice, related_name='seek_response_set')

    def __unicode__(self):
        shortanswer = '/'.join(x.choice_code for x in self.answers.all())
        shortseek = '/'.join(x.choice_code for x in self.seek_answers.all())
        return "%s - %s - %s seeks %s" % (self.owner, self.question.question_code, shortanswer, shortseek)
