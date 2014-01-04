# views.py

import pdb, itertools
import sys
from functools import partial
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.template import RequestContext
from django.http import Http404, HttpResponseRedirect, HttpResponseNotFound, HttpResponse
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory

from psd.register.demographics import print_demographics_async
from psd.RcodeHooks import schedule_async, install_packages_async, test_R_async, make_nametags_async
import psd.register.demographics
import psd.register.views.contact
from psd.register.psdcheckbox import genCodeForSeekAndPrefs, genSeekAndPrefs
from psd.register.models import Person, RegRecord, RecessRecord, BreakRecord, DateRecord, CruiseRecord, Event, MatchRecord, TableListRecord, TableRecord, fetch_regrecord
from psd.register.matchmaker import updateMatchRecords_async
from psd.register.views.printouts import make_schedules
from psd.register.forms import PersonSearchForm, MakeRecessForm, MakeTableTableForm, PrintSchedulesForm, ScheduleForm, NextSheetForm, PSDIDorEmailForm, BreakForm, MultiBreakForm, CruiseForm

from psd import date_scheduler

from psd.register.views.util import HttpStreamTextResponse, async_print_text_response

import logging
logger = logging.getLogger('psd.register.dashboard')


class MyAction:
      action = "default"
      action_description = "default action"
      argument_description = "bleh"
      
      def __init__(self, arg1, arg2, arg3):
          self.action=arg1
          self.action_description=arg2
          self.argument_description=arg3
          
ACTIONS = ( MyAction('', 'Clean Display', ''),
        MyAction('allevents', 'View All Events', ''), 
        MyAction('editevent', 'Edit the Event Record', ''),
        MyAction('regrecords', 'Edit Reg Records', '' ),
        MyAction('listcomments', 'List Comments, Notes and Referrals', ''),
        MyAction('listchildcare', 'List Childcare Requests', ''),
        
        MyAction('listpeople', 'List People Registered', '[all]: list everyone, not just this event.'),
        MyAction('search', 'Search for Dating Entity',''),
        MyAction('email', 'Make email list of participants (seperates checked folks vs. not)', ''),
        MyAction('calcpay', 'Calc number of registered folks, total dollars collected, etc.', '' ),
        MyAction('emailpreevent', "Mass information email pre event", ""),
        MyAction('demographics', "Print out demographics of event", 'NotNo/In/All: Who to include from data.' ),
        MyAction('nametags', "Make csv list that can be turned into nametags", "" ),
        "",
        MyAction('maketabletable', "(1) Make an initial table of the dating tables.  Run once.  Will delete old tables.", "" ),
        MyAction('makerecess', "(1b) Make recess rounds for peoples breaks in the dating.", "" ),
        MyAction('checkin', "(2) Check-in participants", '' ),
        MyAction('walkinreg', "(3) Go to walk-in registration page", '' ),
        
        MyAction('matrix', '(4) Make the dating matrix files', '' ),
        MyAction('plandates', "(5) Figure out who is dating whom when and where", ''),
        MyAction('schedules', "(6) Make pdf of everyone's schedules", '' ),
        "",
        MyAction('datematrix', "Print out entire date matrix for event to screen.", '' ),
        MyAction('datesheet', "Enter marked up date sheets into database.", '' ),
        MyAction('countdates', "Count the number of dates everyone has", ''),
        MyAction('listmissingsheets', "List match records for event that are not fully filled in", "" ),
        MyAction('listbadcruises', "List cruise records with psdids that do not exist", "" ),
        MyAction('emailpostevent', "Mass email for matches post event", ""),
        MyAction('subgroupemail', "Email subgroup of an event (possibly with matches)", "" ),
        "",
        
        MyAction('clean', 'Admin: Clean Database (remove Person Records and User accounts without RegRecords)', '' ),
        MyAction('fix', 'Admin: Fix Group Flags - set the "group" flag based on number of people listed on regrecord', ''),
        MyAction('dropmissingsheets', "Remove match records for event that are not fully filled in", "" ),
        MyAction('installRpackages', 'Admin: Install SQL package into R program from CRAN repository.', '' ),
        MyAction('testR', 'Admin: Test R Calling.', '' )
        )





@staff_member_required
def check_in_driver(request, event_name, show_all=False):
    
    try:
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to do check-in for an event that does not exist or is closed.  Please try again." }, 
                                   context_instance=RequestContext(request)  )

    to_update = []
    to_warn = []
    if request.method == 'POST':
        here_list = request.POST.getlist('here')
        RegRecord.objects.filter(event=event_name, id__in=here_list).update(here=True)

        cancel_list = request.POST.getlist('cancelled')
        RegRecord.objects.filter(id__in=cancel_list).update(cancelled=True)

        id_list = request.POST.getlist('paid')
        for x in id_list:
            if x in here_list or x in cancel_list:
                to_update.append(x)
            else:
                to_warn.append(x)
        RegRecord.objects.filter(id__in=to_update).update(paid=True)

    regs = RegRecord.objects.filter( event=event_name ).order_by('nickname')
    viewable = regs.filter(here__exact=False, cancelled__exact=False)
    warnable = regs.filter(id__in=to_warn)
    return render_to_response('checkin.html', {'regs': viewable, 'warnings': warnable})





@staff_member_required
def check_in_old(request, event_name ):
    
    try:
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to do check-in for an event that does not exist or is closed.  Please try again." }, 
                                   context_instance=RequestContext(request)  )

    to_update = []
    to_warn = []
    if request.method == 'POST':
        here_list = request.POST.getlist('here')
        print "here list: %s" % (here_list, )
        
        RegRecord.objects.filter(event=event_name, id__in=here_list).update(here=True)

        cancel_list = request.POST.getlist('cancelled')
        RegRecord.objects.filter(id__in=cancel_list).update(cancelled=True)

        id_list = request.POST.getlist('paid')
        for x in id_list:
            if x in here_list or x in cancel_list:
                to_update.append(x)
            else:
                to_warn.append(x)
        RegRecord.objects.filter(id__in=to_update).update(paid=True)

    regs = RegRecord.objects.filter( event=event_name ).order_by('nickname')
    viewable = regs.filter(here__exact=False, cancelled__exact=False)
    warnable = regs.filter(id__in=to_warn)
    viewable = sorted(viewable, key=lambda reg: reg.nickname.lower() )
    return render_to_response('checkin.html', {'regs': viewable, 'warnings': warnable})


@staff_member_required
def check_in(request, event_name ):
    
    try:
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to do check-in for an event that does not exist or is closed.  Please try again." }, 
                                   context_instance=RequestContext(request)  )

    checked_in = []
    to_update = []

    warnings = []
    
    # Grab everyone from the event.
    regs = RegRecord.objects.filter( event=event_name )
    
    if request.method == 'POST':

        # handle any undo actions
        undo_list = request.POST.getlist('undo')
        #print "here list: %s" % (here_list, )
        #print "undo list: %s" % (here_list, )
        if len( undo_list ) > 0:
            print "Undoing check-in for %s" % ( undo_list, )
            undos = regs.filter( event=event_name, id__in=undo_list )
            undos.update(here=False)
            for reg in undos:
                reg.message = "Undid check-in for %s (%s).  %s now marked as NOT HERE!" % (reg.nickname, reg.psdid, reg.nickname)
                warnings.append( reg )
        else:
            undos = None
            
        # handle any check-in actions
        here_list = request.POST.getlist('here')
        if len( here_list ) > 0:
            checked_in = regs.filter( event=event_name, id__in=here_list )
            checked_in.update(here=True)
        else:
            checked_in = None
            
        id_list = request.POST.getlist('paid')
        for x in id_list:
            if x in here_list:
                to_update.append(x)
            else:
                x.psdid = x
                x.message = "Warning: %s just mrked as paid, but not marked as here."
                x.nickname = x.psdid
                warnings.append( x )
        RegRecord.objects.filter(id__in=to_update).update(paid=True)

    # decide who to show on form    
    viewable = regs.filter(cancelled__exact=False)
    viewable = viewable.filter(here__exact=False)    # optional.... good idea?
    
    viewable = sorted(viewable, key=lambda reg: reg.psdid.lower() )
    return render_to_response('checkin.html', {'regs': viewable, 'warnings': warnings, 'checked_in':checked_in, 'event_name':event_name })


@staff_member_required
def multi_break( request ):
    """
    Handle form with multiple breaks listed.  Enter them into database
    """
    BreakFormset = formset_factory(BreakForm, extra=10, max_num=10)
  
    if request.method == 'POST':
        print "At post"
        pformset = BreakFormset(request.POST)
        rform = MultiBreakForm(request.POST)
        if pformset.is_valid() and rform.is_valid():
            
            rzn = rform.cleaned_data['reason']
            print "General reason: " + str(rzn)
            
            for form in pformset.forms:
                    if not form.cleaned_data:
                        continue
                    pcd = form.cleaned_data
                    p = BreakRecord(**pcd)
                    if p.notes == None or p.notes=="":
                        p.notes = rzn
                    p.psdid = p.psdid.upper()
                    p.other_psdid = p.other_psdid.upper()
                    print "Saving ", p
                    p.save()
        #else:
        #    return render_to_response( 'error.html', {'message' : "Sorry.  Forms invalid. Please try again." }, 
        #                           context_instance=RequestContext(request)  )
    else:
        pformset = BreakFormset()
        rform = MultiBreakForm()
        
    return render_to_response('multi_break.html', {'pformset': pformset, 'rform': rform}, context_instance=RequestContext(request))







@staff_member_required
def list_comments(request, event_name, acts):
    """List all comments, notes and referrals made by people registering for specified event.
     Useful for generating who knows whom."""

    regs = RegRecord.objects.filter(event=event_name, cancelled=False).order_by( '-id' )

    return render_to_response('list_comments.html', {'regs': regs, 'event_name':event_name, 'actions':acts})



@staff_member_required
def list_childcare(request, event_name, acts):
    """List all childcare requests made by people registering for specified event.
     Useful for generating who knows whom."""

    regs = RegRecord.objects.filter(event=event_name, cancelled=False).order_by( '-id' )

    return render_to_response('list_childcare.html', {'regs': regs, 'event_name':event_name, 'actions':acts})



@staff_member_required
def list_people(request, event_name, acts, all_people=False):
    """List all people and comments made by people registering for specified event"""

    if all_people:
        regs = RegRecord.objects.all().order_by( '-id' )
    else:
        regs = RegRecord.objects.filter(event=event_name, cancelled=False).order_by( '-id' )
        
    return render_to_response('list_people.html', {'regs': regs, 'event_name':event_name, 'actions':acts})


@staff_member_required
def list_users(request, acts ):
    """
    List all users, their email, and how many regrecords they have.
    
    TODO: Finish this method, make template, and wire it up into the command thing
    """
    
    users = User.objects.all().order_by( '-id' )
    for u in users:
        ln = RegRecord.objects.filter( psdid=u.username ).count()
        u.num_records = ln
        print u'%s,%s,%s,%s,%s' % (u.id,u.username,u.email,u.first_name.encode('ascii','replace'),ln)
        
    return render_to_response('list_users.html', {'users': u, 'actions':acts})





@staff_member_required
def generate_email_list(request, event_name, acts):
    """Generate mailing list for the event"""

    regs = RegRecord.objects.filter(event=event_name)

    return render_to_response('email_list.html', {'regs': regs, 'event_name':event_name, 'actions':acts})





def clean_database():
    """
    Delete person records with no regrecords.  
    Delete users with no regrecords that are not staff level
    List regrecords that have no user account.
    """
    
    results = unicode("")
    users = User.objects.all()
    rrs = RegRecord.objects.all()
    
    all_rr_ids= set()
    allfolk = set()
    results += "\nID List: "
    for rr in rrs:
        folk = [p.psdid for p in rr.people.all() ]
        allfolk.update(folk)
        #results += "\n" + rr.psdid + "/" + str(rr)
        all_rr_ids.add( rr.psdid )
        try:
            usr = User.objects.get( username=rr.psdid )
        except User.DoesNotExist:
            results += "\nNo user for %s\n" % (rr,)
        except User.MultipleObjectsReturned:
            results += "\nMultiple users for %s\n" % (rr, )
        
    people_deleted = 0
    for p in Person.objects.all():
        if not p.psdid in allfolk:
            res = "Deleting %s" % p 
            logger.debug( res )
            results += "\n" + res
            p.delete()
            people_deleted += 1
            
    users_deleted = 0
    for usr in users:
        if not usr.is_staff:
            if not usr.username in all_rr_ids:
                res = "Deleting User %s" % usr
                logger.debug( res )
                results += "\n" + res
                usr.delete()
                users_deleted += 1 
        else:
            results += "\nSkipping staff " + str(usr)
    
    return """<pre>database cleaned
    # People deleted = %s
    # users deleted = %s
    Details: %s
    </pre><br>
    All rrs: %s""" % (people_deleted, users_deleted, results, all_rr_ids )


def fix_group_codes():
    res = ""
    for rr in RegRecord.objects.all():
        if (rr.is_group and len( rr.people.all() ) == 1) or (not rr.is_group and len(rr.people.all()) != 1):
            st = "%s  %s  %s  %s" % ( rr.psdid, rr.event, rr.is_group, len(rr.people.all()))
            logger.debug( "Fix Group Code: " + st )
            res += "\n<br>" + st
            if rr.is_group:
                 rr.is_group = False
            else:
                 rr.is_group = True
            rr.save()
    if res == "":
        res = "no broken group flags found"
        
    res2 = ""
    for pp in Person.objects.all():
        seeks = pp.seek_gender_set
        prefs = pp.pref_gender_set
        if seeks == prefs:
            pp.seek_gender = genCodeForSeekAndPrefs( seeks, set() )
            pp.save()
            res2 += "\n<br>Updated seek-pref set for %s to %s" % (pp, pp.seek_gender)
    if res2 == "":
        res2 = "no bad seek-pref sets found"
        
    return res + "\n<br>" + res2



def list_bad_cruises_iter( event_name ):
    
    dr = CruiseRecord.objects.filter( event=event_name ).order_by( 'psdid' )
    
    yield( """List of bad cruise records (and all other records by the same person).  Bad cruise records have been removed from the database.<table>""")
    for d in dr:
        rr = fetch_regrecord( event_name, d.other_psdid )
        if rr == None:
            d.delete()
            yield "<tr><td>%s<td><td>" % (d,)
            for xx in CruiseRecord.objects.filter( event=event_name, psdid=d.psdid ):
                yield str(xx.other_psdid) + " " 
            yield "</tr>"
            
    yield( "</table>" )




def drop_missing_datesheets_iter( event_name, drop_records = False ):
    
    dr = DateRecord.objects.filter( event=event_name ).order_by( 'psdid' )
    
    if not drop_records:
        yield """Match Records with missing data"""
    else:
        yield """Dropping the following Match Records with missing data."""
    yield( """<table>""")
    for d in dr:
        if d.said_yes == None or d.they_said_yes == None:
            strg = "<tr><td>%s<td></tr>\n" % (d,)
            d.delete()
            yield strg
            
    yield "<tr><td>Next block<hr></td></tr>"
    
#    dr = dr.order_by( 'other_psdid' )
#    for d in dr:
#        if d.they_said_yes == None:
#            strg = "<tr><td>%s<td></tr>\n" % (d,)
#            d.delete()
#            yield strg
#            yield "<tr><td>%s<td></tr>\n" % (d,)

    yield( "</table>" )


    


@staff_member_required   
def schedule_form(request, event_name):
    evt = Event.objects.get(event=event_name)
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid(): 
            trials = form.cleaned_data["trials"]
            rounds = form.cleaned_data["rounds"]
            who_incl = form.cleaned_data["include"]
        
            #date_scheduler.schedule( event_name, rounds, trials, who_include=who_incl )
            sch_func = partial( date_scheduler.schedule, event_name, rounds, trials, who_include=who_incl )

            #sch_func()
                        
            yield_gen = async_print_text_response( sch_func )
            #for r in yield_gen:
            #    print r
                #yield_gen()
            return HttpStreamTextResponse( yield_gen, event_name, ACTIONS=ACTIONS )
            #return HttpStreamTextResponse( "done", event_name, ACTIONS=ACTIONS )
        
    form = ScheduleForm()
    return render_to_response('command_arg_form.html', {'form': form, 'event': evt, 'command_title':'Generate Dating Schedule', 'button_name':'Start Scheduling'}, context_instance=RequestContext(request) )



@staff_member_required   
def print_schedules_form(request, event_name):
    evt = Event.objects.get(event=event_name)
    if request.method == 'POST':
        form = PrintSchedulesForm(request.POST)
        if form.is_valid(): 
            who_incl = form.cleaned_data["include"]
            #results = 'Make with psdmanage.py command.  Then go to [root url to django]/schedules/%s to have schedules rendered.' % (event_name, ) 
            return HttpResponseRedirect( reverse( "print-schedules", kwargs={'event_name':event_name,'include_code':who_incl} ) )
        
    form = PrintSchedulesForm()
    return render_to_response('command_arg_form.html', {'form': form, 'event': evt, 'command_title':'Print PDF of Schedules',
                                                        'button_name':'Render Schedules'},
                               context_instance=RequestContext(request) )



def fetch_matchrecord( psdid1, psdid2, event_name ):
    try:
        mr = MatchRecord.objects.get( psdid1 = psdid1, psdid2 = psdid2, event=event_name )
        return mr
    except:
        return None


@staff_member_required
def potential_matches( request, event_name, psdid ):
    try:
        peep = RegRecord.objects.get( event=event_name, psdid=psdid )
    except:
         return HttpResponseNotFound('<h1>event %s or psdid  %s not real?</h1>' % (event_name, psdid, ) )

    recs = MatchRecord.objects.filter( psdid1=psdid, event=event_name )
    recs2 = MatchRecord.objects.filter( psdid2=psdid, event=event_name )
 
    likes = dict( [(r.psdid2, r) for r in recs ] )
    likeds = dict( [(r.psdid1, r) for r in recs2 ] )
    
    alls = set(likes.keys()).union( likeds.keys() )
    matchlist = []
    
    mutuals = set(likes.keys()).intersection( likeds.keys() )
    crushes = set(likes.keys()).difference( likeds.keys()  )
    stalkers = set(likeds.keys()).difference( likes.keys() )
    
    for psdid2 in itertools.chain( mutuals, crushes, stalkers ):
        if likes.has_key(psdid2):
            lh = likes[psdid2]
        else:
            lh = None
        if likeds.has_key(psdid2):
            rh = likeds[psdid2]
        else:
            rh = None

        yay = not( lh == None or rh == None )

        try:
            person2 = RegRecord.objects.get( event=event_name, psdid=psdid2 )
            try:
                date_record = DateRecord.objects.get( event=event_name, psdid=psdid, other_psdid=psdid2 )
            except:
                date_record = None
        except:
            person2 = 'psdid %s for %s not found in reg records?' % (psdid2, event_name)

        matchlist.append( {'psdid2':psdid2, 'like':lh, 'liked':rh, 'person2':person2, 'yay':yay, 'date':date_record } )
    
    return render_to_response( 'potential_matches.html', locals(),
                                 context_instance=RequestContext(request)  )
    
 
 
@staff_member_required
def break_matches(request, event_name, psdid ):
    """
    Break matches.  Remove from the current potential matches matrix and
    also add a BreakRecord so that there is never a match in the future,
    either.
    """
    try:
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to do break list for an event '%s' that does not exist.  Please try again." % (event_name,)}, 
                                   context_instance=RequestContext(request)  )

    try:
        rr = RegRecord.objects.get(psdid=psdid, event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to do break list for a PSDID '%s' that does not exist.  Please try again." % (psdid,) }, 
                                   context_instance=RequestContext(request)  )

    break_list = []
    if request.method == 'POST':
        break_list = request.POST.getlist('break')
        brecs = MatchRecord.objects.filter(event=event_name, psdid1=psdid, psdid2__in=break_list)
        for br in brecs:
            mt = BreakRecord(psdid=psdid, other_psdid=br.psdid2, notes="hand break via break_matches function")
            mt.save()
            br.delete()

    liked = set( [r.psdid1 for r in MatchRecord.objects.filter( event=event_name, psdid2=psdid ) ])
    matches = MatchRecord.objects.filter( event=event_name, psdid1=psdid ).order_by('psdid2')
    
    for m in matches:
        try:
            p2 = RegRecord.objects.get( psdid=m.psdid2, event=event_name )
            m.namestring = p2.namestring
            m.mutual = m.psdid2 in liked
        except:
            logger.error( "Failed to find the RegRecord for '%s-%s'" % ( event_name, m.psdid2 ) )
            m.namestring = "[Error: Failed to Find]"
            
    return render_to_response('matchlist.html', {'matches': matches, 'rr': rr, 'breaklist':break_list})


def check_id( psdid, event ):
    drs = DateRecord.objects.filter( psdid=psdid, event=event, said_yes=None )
    return len(drs) > 0


@staff_member_required   
def gen_next_date_sheet_form( request, event_name, just_submitted=False, submitted_psdid=None, dates=None, err_message=None ):
    form = NextSheetForm()
    nextids = list(r.psdid for r in RegRecord.objects.filter( event=event_name, here=True ) )
    if len(nextids) > 0:
        nextids.sort()
        needs = [ psdid for psdid in nextids if check_id( psdid, event_name)  ]
        per = 100 * len(needs) / len(nextids)
        print( "%s - %s = %s" % ( len(needs), len(nextids), per, ) )
        progressbar = ""
        for x in range(0,100):
            if x <= per:
                progressbar += "X"
            else:
                progressbar += "_"
    else:
        needs = []
        progressbar = "No date sheets found"
        
    return render_to_response( "next_sheet_form.html", {'form':form, 'event':event_name, 'just_submitted':True, 'dates':dates,
                                                 'submitted_psdid':submitted_psdid, 'err_message':err_message, 'nextids':nextids,
                                                 'progressbar':progressbar, 'needs': needs, 'event_name':event_name }, 
                                                 context_instance=RequestContext(request) )
    
    
@staff_member_required   
def next_date_sheet(request, event_name):
    evt = Event.objects.get(event=event_name)
    if request.method == 'POST':
        form = NextSheetForm(request.POST)
        if form.is_valid(): 
            psdid = form.cleaned_data["psdid"].upper()
            rev = reverse("date-sheet", kwargs={'event_name':event_name,'psdid':psdid} )
            return HttpResponseRedirect( rev )

    else:
        return gen_next_date_sheet_form( request, event_name )
    


def get_date_schedule( psdid, event_name ):
    """
    Get sequence of dates for 'psdid' at 'event_name'
    Used for printing to django templates
    """
    print "Getting date schedule for %s at %s" % (psdid, event_name )
    dates = DateRecord.objects.filter( event=event_name, psdid=psdid ).order_by('round')
    
    gots = [x.round for x in dates]
    if len(gots) > 0:
        mx = max( gots )
        miss = set( range(1,mx+1)).difference(gots)
    
        datedict = {}
              
        for d in dates:
            d.other_person = fetch_regrecord( event_name, d.other_psdid )
            if not d.other_person == None:
                d.other_code = d.other_person.minicode()
            else:
                d.other_code = "missing person"
                
            d.match = fetch_matchrecord( d.psdid, d.other_psdid, event_name )
            datedict[ d.round ] = d
    
        for rnd in miss:
            datedict[ rnd ] = { 'round':rnd, 'other_person':"no date", 'other_code':"" }
        
        dates = [ datedict[x] for x in range(1,mx+1) ]
    else:
        print "No found dates"
        dates = []
        
    return dates



            
@staff_member_required
def date_sheet(request, event_name, psdid, pretty=False ):
    
    try:
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to do date list for an event '%s' that does not exist.  Please try again." % (event_name,)}, 
                                   context_instance=RequestContext(request)  )

    try:
        rr = RegRecord.objects.get(psdid=psdid, event=event_name)
    except RegRecord.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to do date list for a PSDID '%s' that does not exist.  Please try again." % (psdid,) }, 
                                   context_instance=RequestContext(request)  )

    #CruiseFormset = modelformset_factory(CruiseRecord, exclude=('psdid','event_name',), extra=3, max_num=5)
    CruiseFormset = formset_factory(CruiseForm, extra=3, max_num=5)

    if request.method == 'POST':
        cformset = CruiseFormset(request.POST)
      
        if cformset.is_valid():
            err_message = ""
            for form in cformset.forms:
                if not form.cleaned_data:
                    continue
                #pcd = form.cleaned_data
                #p = CruiseRecord(**pcd)
                #p.psdid = psdid
                #p.event = event_name
                opsdid = form.cleaned_data['other_psdid'].upper()
                if RegRecord.objects.filter(psdid=opsdid, event=event_name).count() == 0:
                    err_message = err_message + "<br>Bad Cruise - '%s'" % (opsdid,)
                    
                # make CruiseRecord if it does not exist.
                if CruiseRecord.objects.filter(psdid=psdid,event=event_name,other_psdid=opsdid).count() == 0:
                        p = CruiseRecord( psdid=psdid, event=event_name, other_psdid=opsdid) 
                        p.save()
            
            yeses = request.POST.getlist('yes')                    
            dates = DateRecord.objects.filter( event=event_name, psdid=psdid ).order_by('round')
            for d in dates:
                d2 = DateRecord.objects.get(psdid=d.other_psdid, event=event_name, other_psdid=psdid)
                if not (d.other_psdid in yeses):
                    d.said_yes = False
                    d2.they_said_yes = False
                else:
                    d.said_yes = True
                    d2.they_said_yes = True
                d.save()
                d2.save()
                    
            return gen_next_date_sheet_form( request, event_name, just_submitted=True, submitted_psdid=psdid, 
                                             dates=dates, err_message=err_message )
        # else bad form:
        #     fall through.  just repost the original and try again.
    
    queryset=CruiseRecord.objects.filter(psdid=psdid,event=event_name)
    cformset = CruiseFormset(initial=queryset.values())
          
    dates = get_date_schedule( psdid, event_name )
    if pretty:
        return render_to_response('prettydatesheet.html', {'dates': dates, 'rr': rr, 'event':event, 'event_name':event.event, 'cformset':cformset } )
    else:
        return render_to_response('datesheet.html', {'dates': dates, 'rr': rr, 'event':event, 'event_name':event.event, 'cformset':cformset } )

    

   
   
@staff_member_required
def get_dating_matrix(request, event_name ):
    print "Here we go!" 
        
    try:
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to generate the date matrix for an event '%s' that does not exist.  Please try again." % (event_name,)}, 
                                   context_instance=RequestContext(request)  )

    rr = RegRecord.objects.filter(event=event_name, cancelled=False)
    rr = sorted(rr, key=lambda reg: reg.psdid )

    mxrnd = 0
    for r in rr:
                  
        dates = get_date_schedule( r.psdid, event_name )
        r.dates = dates
        mxrnd = max( dates[-1].round, mxrnd )
        
    return render_to_response('datematrix.html', {'rr': rr, 'event':event, 'event_name':event.event, 'rounds':range(1,mxrnd+1) } )




@staff_member_required
def view_user( request, event_name, psdid ):
    try:
        rr = RegRecord.objects.get(event=event_name, psdid=psdid)
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to edit a regrecord (or event) that does not exist  Please try again." }, 
                                   context_instance=RequestContext(request)  )
    
    recs = MatchRecord.objects.filter( psdid1=psdid, event=event_name )
 
    for r in recs:
        try:
            r.person2 = RegRecord.objects.get( event=event_name, psdid=r.psdid2 )
        except:
          r.person2 = '<h1>psdid %s for %s not found in reg records?</h1>' % (r.psdid2, event_name)
           
    match_text = psd.register.views.contact.get_match_text( event, rr, "", True )
    return render_to_response('user_blurb.html', locals(), context_instance=RequestContext(request) )



@staff_member_required
def edit_user( request, event_name, psdid ):
    try:
        regrec = RegRecord.objects.get(event=event_name, psdid=psdid)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to edit a regrecord that does not exist  Please try again." }, 
                                   context_instance=RequestContext(request)  )
    
    rev = reverse("admin:register_regrecord_change", args=(regrec.id,))
    return HttpResponseRedirect( rev )



@staff_member_required
def edit_event( request, event_name ):
    try:
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to edit an event that does not exist.  Please try again." }, 
                                   context_instance=RequestContext(request)  )
    
    rev = reverse("admin:register_event_change", args=(event.id,))
    return HttpResponseRedirect( rev )
    
    
def gen_set_from_string( string ):
    """
    Given a string of numbers and number ranges, generate set of all those numbers
    """
    if string:
        statOK = set()
        for x in string.split(","):
            x = x.split("-")
            if len(x) > 1:
                statOK.update( range( int(x[0]), int(x[1])+1 ) )
            else:
                statOK.add( int(x[0]) )
    else:
        statOK = set()
            
    return statOK
        
        
        
@staff_member_required   
def make_table_table_view(request, event_name):
    evt = Event.objects.get(event=event_name)
    if request.method == 'POST':
        form = MakeTableTableForm(request.POST)
        if form.is_valid(): 
            N = form.cleaned_data["N"]
            statOK = form.cleaned_data["statOK"]
            groupOK = form.cleaned_data["groupOK"]
            
            try:
                statOK = gen_set_from_string( statOK )
                groupOK = gen_set_from_string(groupOK )
                res = make_table_table(event_name, N, statOK, groupOK)
                results = "<br>".join( ( str(x) for x in res ) )
            except Exception as inst:
                results = "Error with input---probably string formatting in statOK or groupOK<br>%s" % (inst,) 
            
    else:
        form = MakeTableTableForm()
        results = ""
        
    return render_to_response('command_arg_form.html', {'form': form, 'event': evt, 'command_title':'Make Table of Physical Tables',
                                                        'button_name':'Delete Old Tables and Make New Ones',
                                                        'results':results},
                               context_instance=RequestContext(request) )



@staff_member_required   
def make_recess_view(request, event_name):
    evt = Event.objects.get(event=event_name)
    if request.method == 'POST':
        form = MakeRecessForm(request.POST)
        if form.is_valid(): 
            kind = form.cleaned_data["kind"]
            RecessRecord.objects.filter(kind=kind, psdid="template", event=event_name ).delete()
            txt = form.cleaned_data["breaktext"]
            txt = txt.split("\n")
            for t in txt:
                if t != "":
                    r = RecessRecord()
                    r.kind = kind
                    r.psdid="template"
                    r.rounds = t
                    r.event=event_name
                    r.save()            
    else:
        form = MakeRecessForm()

    brlist = RecessRecord.objects.filter( psdid="template", event=event_name )
    breaks = {}
    for b in brlist:
        if b.kind in breaks:
            breaks[b.kind].append( b )
        else:
            breaks[b.kind] = [b]
    num_breaks = len(breaks)
    print "Got %s breaks " % (num_breaks,) 
    return render_to_response('recess_creator.html', locals(),
                               context_instance=RequestContext(request) )


def person_search( request ):

    search_made = False
    if request.method == 'POST':
        form = PersonSearchForm(request.POST)
        if form.is_valid(): 
            psdid = form.cleaned_data.get("psdid")
            email = form.cleaned_data.get("email")
            name = form.cleaned_data.get("name")

            users = set()
            rrs = set()
            precs = set()

            # look for psdid
            if psdid != "":
                users.update( User.objects.filter( username__icontains=psdid ) )
                rrs.update( RegRecord.objects.filter( psdid__icontains=psdid ) )
                precs.update( Person.objects.filter( psdid__icontains=psdid ) )
            
            if email != "":
                users.update( User.objects.filter( email__icontains=email ) )
                rrs.update( RegRecord.objects.filter( email__icontains=email ) )
            
            if name != "":
                users.update( User.objects.filter( first_name__icontains=name ) )
                rrs.update( RegRecord.objects.filter( nickname__icontains=name ) )
                precs.update( Person.objects.filter( first_name__icontains=name ) )
                precs.update( Person.objects.filter( last_name__icontains=name ) )

            search_made = True
            return render_to_response('dashboard/person_search.html', locals(), context_instance=RequestContext(request) )
    else:
        form = PersonSearchForm()
    
    return render_to_response('dashboard/person_search.html', locals(), context_instance=RequestContext(request) )



def walk_in_reg( request, event_name ):
    try:
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to do walk-in reg for an event that does not exist.  Please try again." }, 
                               context_instance=RequestContext(request)  )

    if request.method == 'POST':
        form = PSDIDorEmailForm(request.POST)
        if form.is_valid(): 
            usr = form.cleaned_data.get("user")
            rev = reverse( "walk-in-update", kwargs={"event_name":event.event, "psdid":usr.username } )
            return HttpResponseRedirect( rev )
    else:
        form = PSDIDorEmailForm()
    
    return render_to_response('walkin_menu.html', locals(), context_instance=RequestContext(request) )


def make_table_table( event_name, N, statOKs, groupOKs ):
    try:
        oldrec = TableListRecord.objects.get( event=event_name )
        TableRecord.objects.filter( group=oldrec ).delete()
        oldrec.delete()
    except TableListRecord.DoesNotExist:
        pass
    grp = TableListRecord( event=event_name )
    grp.save()
    cyc = itertools.cycle( (0,1,2,1) )
    res = []

    for k in range(1,N+1):
        tb = TableRecord(group=grp, name="Table " + str(k), quality=5+int(N-k)/12+cyc.next(), groupOK=False, statOK=False )
        if k in groupOKs:
            tb.groupOK = True
        if k in statOKs:
            tb.statOK = True

        tb.save()
        res.append(tb)
    return res
 



def calc_pay_numbers( event_name ):
    totalfolks = 0
    pendings = 0
    paidcount = 0
    cancelled = 0
    comped = 0
    paypal = 0
    refunded = 0
    here = 0
    paidNoShow = 0
    door = 0
    doorString = ""
    regs = RegRecord.objects.filter( event=event_name ).order_by( 'psdid' )
    lists = {'cancelled':[], 'comped':[], 'nopaypal':[], 'refunded':[], 'pending':[], 'paidnoshow':[], 'herenopay':[], 'weirdpaypal':[] }
    for r in regs:
        totalfolks = totalfolks + r.size
        notefield = r.notes.lower()
        if r.paid:
            if "paypal transation id" in notefield:
                paypal = paypal + r.size
                paidcount = paidcount + r.size 
            elif "comp" in notefield and not "Need companion" in notefield:
                comped = comped + r.size
                lists['comped'].append( r )
            else:
                paidcount = paidcount + r.size
                lists['nopaypal'].append(r)
        else:
            if "paypal transation id" in notefield and not "refunded" in notefield.lower():
                lists['weirdpaypal'].append(r)
                 
        if r.pending and not r.cancelled:
            lists['pending'].append(r)
            pendings = pendings + r.size
            
        if r.cancelled:
            cancelled = cancelled + r.size
            lists['cancelled'].append(r)
            
        if "refunded" in notefield.lower() and not r.paid:
            refunded = refunded + r.size
            lists['refunded'].append(r)
            
        if r.here:
            here = here + r.size
            if not r.paid:
                lists['herenopay'].append( r )
                
        if r.paid and not r.here:
            paidNoShow = paidNoShow + r.size
            lists['paidnoshow'].append(r)
            
        if "door" in notefield:
            door = door + r.size
            if doorString == "":
                doorString = r.notes
            else:
                doorString += "; " + r.notes
            
    headstr = """
    total = %s  
    paid = %s
    comped = %s       (based on finding "comp" in notes field)
    pending = %s
    cancelled = %s
    paypal = %s    (based on finding "paypal transaction id" in notes field.
    refunded = %s   (based on "paypal transaction id" and no paid flag, or "refunded" in notes field)
    here = %s
    paid no show = %s  (paid, not here)
    door = %s  (door mentioned)
         Remarks are: %s
    """ % ( totalfolks, paidcount, comped, pendings, cancelled, paypal, refunded, here, paidNoShow, door, doorString)
    
    for (ltype,lst) in lists.iteritems():
        headstr += "\n** %s **" % (ltype, )
        for rec in lst:
            headstr += "\n\t%s (%s) - %s" % (rec.nickname, rec.psdid, rec.notes.replace("\n", "\t\t; ") )
    
    return headstr + "\n"

@staff_member_required
def event_manager( request, event_name, action=None, extraArg=None ):
    """ 
    This method redirects a bunch of calls to a bunch of different functions.
    It also prints out a list of commands you can do with these calls.
    """
    if action=="" or action=="main":
        results="""Click on action desired."""
    elif action=="editevent":
        return edit_event( request, event_name )
    elif action=="allevents":
        rev = reverse("admin:register_event_changelist")
        return HttpResponseRedirect( rev )
    elif action=="regrecords":
        rev = reverse("admin:register_regrecord_changelist")
        return HttpResponseRedirect( rev )
    elif action=="listcomments":
        return list_comments(request, event_name, ACTIONS)
    elif action== "listchildcare":
        return list_childcare(request, event_name, ACTIONS)
    elif action=="listpeople":
        list_all = extraArg=="all"
        return list_people(request, event_name, ACTIONS, list_all)
    elif action=="clean":
        results=clean_database()
    elif action=="fix":
        results=fix_group_codes()
    elif action=="search":
        return person_search( request )
    elif action=="matrix":
        updateProc = updateMatchRecords_async(event_name)
        return HttpStreamTextResponse( updateProc, event_name, ACTIONS=ACTIONS )
    elif action=="walkinreg":
        return walk_in_reg( request, event_name )
    elif action=="email":
        results = generate_email_list(request,event_name,ACTIONS)
        return results
    elif action=="countdates":
        resp = HttpResponse(psd.register.demographics.date_distribution_iter(event_name), mimetype='text/plain')
        resp['Content-Disposition'] = 'attachment; filename=datecounts.csv'
        return resp
    elif action=="schedules":
        return print_schedules_form( request, event_name )
    elif action=="demographics":
        if extraArg==None:
            extraArg="NotNo"        
        return HttpStreamTextResponse( print_demographics_async( event_name, who_print=extraArg ), event_name, head_string="<p>Demographics for %s with '%s' included</p>" % (event_name, extraArg) )
    elif action=="nametags":
        resp = HttpResponse(psd.register.demographics.name_tag_iter(event_name), mimetype='text/plain')
        resp['Content-Disposition'] = 'attachment; filename=nametags.csv'
        return resp
        #        return HttpStreamTextResponse( make_nametags_async( event_name ), event_name, head_string="<p>Demographics for %s with '%s' included</p>" % (event_name, extraArg) )
    elif action=="plandates":
        return schedule_form( request, event_name )
    elif action=="maketabletable":
        return make_table_table_view( request, event_name )
    elif action=="makerecess":
        return make_recess_view( request, event_name )
    elif action=="listmissingsheets":
        return HttpStreamTextResponse( drop_missing_datesheets_iter( event_name, False), event_name, ACTIONS=ACTIONS)
    elif action=="dropmissingsheets":
        return HttpStreamTextResponse( drop_missing_datesheets_iter( event_name, True), event_name, ACTIONS=ACTIONS)
    elif action=="listbadcruises":
        return HttpStreamTextResponse( list_bad_cruises_iter( event_name ), event_name, ACTIONS=ACTIONS )
    elif action=="emailpostevent":
        return HttpResponseRedirect( reverse( "email-post-event", kwargs={'event_name':event_name} ) )
    elif action=="subgroupemail":
        return HttpResponseRedirect( reverse( "subgroup-email", kwargs={'event_name':event_name} ) )
    elif action=="emailpreevent":
        return HttpResponseRedirect( reverse( "email-pre-event", kwargs={'event_name':event_name} ) )
    elif action=="checkin":
        return HttpResponseRedirect( reverse( "check-in", kwargs={'event_name':event_name} ) )
    elif action=="installRpackages":
        return HttpStreamTextResponse( install_packages_async(), event_name, head_string="<p>Attempting to download and install R packages</p>" )
    elif action=="testR":
        return HttpStreamTextResponse( test_R_async(), event_name, head_string="<p>Testing R Code</p>" )
    elif action=="calcpay":
        return HttpStreamTextResponse( calc_pay_numbers(event_name), event_name, head_string="<p>Computing Pay Statistics</p>" )
    elif action=="datesheet":
        return HttpResponseRedirect( reverse( "next-date-sheet", kwargs={'event_name':event_name} ) )
    elif action=="datematrix":
        return HttpResponseRedirect( reverse( "date-matrix", kwargs={'event_name':event_name} ) )
    else:
       results="Action '%s' not understood." % (action,)
    
    if not results == """Click on action desired.""":
        results = "<b>RESULT:</b><p>" + results
        
    return render_to_response( 'event_manager.html', {'event_name':event_name,
                                   'actions':ACTIONS,
                                   'results':results } )
    


