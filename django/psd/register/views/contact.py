import pdb

from django.contrib.auth.models import User
from django.template import Context, RequestContext
from django.template.loader import get_template
from django.shortcuts import render_to_response

from psd.register.models import RegRecord, Event, DateRecord, CruiseRecord
from psd.register.forms import PostEmailForm, FeedbackForm, SubgroupEmailForm
from psd.register.views.util import HttpStreamTextResponse
from django.template.loader import find_template_source
from django.template import Template

import itertools
import logging
logger = logging.getLogger('psd.register.contact')




#def pre_email_body(reg, evt):
#    t = get_template('email/pre_event_email.txt')
#    c = Context({'rr': reg, 'event': evt})
#    return t.render(c)

#def pre_email(event_name):
#    regs = RegRecord.objects.filter(event=event_name).exclude(cancelled=True)
#    evt = Event.objects.get(event=event_name)
#    for r in regs:
#        u = User.objects.get(username=r.psdid)
#        if u:
#            u.email_user("important Poly Speed Dating info!", pre_email_body(r, evt), evt.info_email )
#        else:
#            print("Something went wrong with reg %s" % r)

def their_info(date):
    them = RegRecord.objects.get(event=date.event, psdid=date.other_psdid)
    d = {'their_email': them.email, 'their_nick': them.nickname, 'their_psdid': them.psdid}
    if hasattr(date, 'round'):
        d['round'] = date.round
    return d

def cruiser_info(event_name, psdid):
    me = RegRecord.objects.get(event=event_name, psdid=psdid)
    d = {'their_email': me.email, 'their_nick': me.nickname, 'their_psdid': me.psdid}
    return d

def public_info(event, psdid):
    try:
        me = RegRecord.objects.get(event=event, psdid=psdid)
        d = {'nick': me.nickname, 'psdid': me.psdid}
    except Exception as inst:
        logger.error( "Error in public_info(%s, %s): %s\n" % (event, psdid, inst ) )
        d = {'nick': "Not Found", 'psdid':psdid } 
    return d
    

def get_match_text(evt, reg, email_body, send_matches):
    evtname = evt.event
    t = get_template('email/your_matches.txt')
    
    if send_matches:
        if len( DateRecord.objects.filter(psdid=reg.psdid, event=evt.event, said_yes=None) ) > 0:
            message = "Please note: Unfortunately, your date sheet was missing, so we marked all your dates as 'No.'  If this is not what you wish, please contact us."
        else:
            message = None
            
        matches = DateRecord.objects.filter(psdid=reg.psdid, said_yes=True, they_said_yes=True, event=evtname, friend_date=False)
        matches = [their_info(m) for m in matches]

        fmatches = DateRecord.objects.filter(psdid=reg.psdid, said_yes=True, they_said_yes=True, event=evtname, friend_date=True)
        fmatches = [their_info(m) for m in fmatches]
    
        you_cruised = set(x.other_psdid for x in CruiseRecord.objects.filter(event=evtname, psdid=reg.psdid))
        they_cruised = set(x.psdid for x in CruiseRecord.objects.filter(event=evtname, other_psdid=reg.psdid))
    
        cruises = [cruiser_info(evtname, x) for x in they_cruised if x not in you_cruised]
    
        cmatches = [cruiser_info(evtname, x) for x in they_cruised if x in you_cruised]
    
        you_cruised = [ public_info(evtname,x) for x in you_cruised ]
        c = Context({'body':email_body, 'message':message, 'send_matches':True, 'matches': matches, 'fmatches': fmatches, 'cmatches': cmatches, 'cruises': cruises, 
            'tried_friends': reg.friend_dates, 'event': evt, 'rr': reg, 'you_cruised':you_cruised, 'cruised_any':(len(you_cruised)>0)})
    else:
        c = Context({'body':email_body, 'send_matches':False, 'event':evt, 'rr':reg } )
    text = t.render(c)
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')
    return text


    
def send_email( evt, rr, subject, body, really_email=False ):
    """
    Send email to given person as indicated by RegRecord 'rr'.
    'body' is the entire text of the email.
    Return: the text of email sent, or the problem with sending it, if there was one.
    """
    try:
        #logger.info( "Emailing user associated with %s" % (rr, ) )
        u = User.objects.get(username=rr.psdid)
        # make sure user has right email
        if u.email != rr.email:
            logger.info( "Permanently Changing email of %s to %s from %s" % (rr.psdid, rr.email, u.email) )
            u.email = rr.email
            u.save()
        if really_email:
            u.email_user(subject, body, evt.info_email)
        return body
    except Exception as inst:
        prob ="Something went wrong with reg %s / %s" % (rr, inst)
        logger.info(prob)
        return prob


def send_formatted_email( evt, rr, subject, body, send_matches, really_email=False ):
    """
    Send email to given person as indicated by RegRecord 'rr'.
    Uses the "your_matches.txt" template.  'body' holds the email body.  Will
    be prefaced by Dear BLAH and ended with "love PSD Robot #4."
    """
    logger.info( "Going to generate text" )
    logger.info( "evt: %s\nrr: %s" % ( evt, rr ) )
    match_text = get_match_text( evt, rr, body, send_matches )
    logger.info( "Generated match text" )
    return send_email( evt, rr, subject, match_text, really_email )

   

def post_email_handler_iter(  form, event, regs ):
    """
    Send form letter to everyone in the list of regrecords 'regs'
    """
    logger.info( "Post Email Handling for %s" % (event, ) )
    event_name = event.event
    subject = form.cleaned_data['subject']
    body = form.cleaned_data['body']
    send_matches = form.cleaned_data['send_matches']
    really_send = form.cleaned_data['really_send']
    
    evt = Event.objects.get(event=event_name)

    yield """send_matches = %s    really_send = %s
    Sending %s records right now...
    """ % (send_matches,really_send,len(regs))
    
    smptxt = ""
    cntr = 0
    for r in regs:
        logger.info( "Next reg... %s/%s" % (cntr, len(regs)) )
        cntr += 1
        smptxt = ""
        try:
            logger.info( "Sending... #%s: %s"  % (cntr, r.psdid) )
            smptxt = send_formatted_email( evt, r, subject, body, send_matches, really_send )
            logger.info( "Sent #%s: %s" % (cntr, r.psdid) )
            yield "\n<hr>#%s: %s<hr>\n" % (cntr, r.psdid) + smptxt
        except Exception as inst:
            prob ="Something went wrong with post_email_handler_iter for %s / %s" % (r, inst)
            logger.info( prob )
            yield "\n<hr>#%s: ERROR on %s\nError is: %s\nGenerated Text (not sent):\n%s\n" % (cntr, r.psdid, inst, smptxt)
        logger.info( "Done loop." )

    yield "Finished!"
    logger.log( "Finished post_email_handler_iter" )

#def email_staff_thingy():
#                staff = User.objects.filter(is_staff=True)
#            preamble = """Hello, PSD staff person! PSD daters were just sent a mass email. Below
#the line is an example of an email that one dater received.
#
#Beep boop,
#PSD Robot #5
#
#
#"""
#            for s in staff:
#                s.email_user(subject, preamble + body, evt.info_email)
#                if send_matches:
#                    ## Just use the last reg from the previous loop!
#                    s.email_user("Poly Speed Dating results", preamble + post_email_body(r, evt), evt.info_email)


    
    
    
def pre_email(request, event_name ):
    try:
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to email for an event that does not exist.  Please try again." }, 
                                   context_instance=RequestContext(request)  )

    if request.method == 'POST':
        form = PostEmailForm(request.POST)
        if form.is_valid():
            email_gremlin = email_reminders_iter( form, event )
            return HttpStreamTextResponse( email_gremlin, event.event )

    else:
        try:
            t = find_template_source('email/email_reminder.txt')[0]
        except:
            t="error: default template not found"
        initial = { 'event_name': event_name, 'subject':"Reminder of upcoming PSD event---you are registered!", 'body':t }
        form = PostEmailForm( initial=initial )

    return render_to_response('pre_event_email.html', {'form': form, 'event':event, 'event_name':event_name})
 
   
def post_email(request, event_name ):   
    try:
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to email for an event that does not exist.  Please try again." }, 
                                   context_instance=RequestContext(request)  )
    
    if request.method == 'POST':
        form = PostEmailForm(request.POST)
        if form.is_valid():
            regs = RegRecord.objects.filter(event=event_name, here=True)
            email_gremlin = post_email_handler_iter( form, event, regs )
            return HttpStreamTextResponse( email_gremlin, event.event )
            
    else:
        #try:
        #    t = find_template_source('email/your_matches.txt')[0]
        #except:
        #    t="error: default template not found"
        default_text = "Enter text here"
        initial = { 'event_name': event_name, 'subject':"Your PSD Matches", 'body':default_text }
        #initial = { 'event_name': event_name, 'subject':"PSD Matches.", 'body':t }
        form = PostEmailForm( initial=initial )

    return render_to_response('post_event_email.html', {'form': form, 'event':event, 'event_name':event_name})


def subgroup_email( request, event_name ):
    """
    Send form letter, possibly with matches, to list of psdids
    psdid list comes from form as char string, 'psdids'
    
    """
    try:
        event = Event.objects.get(event=event_name)
    except Event.DoesNotExist:
        return render_to_response( 'error.html', {'message' : "Sorry.  You are trying to email for an event that does not exist.  Please try again." }, 
                                   context_instance=RequestContext(request)  )
    
    if request.method == 'POST':
        form = SubgroupEmailForm(request.POST)
        if form.is_valid():
            psdids = form.cleaned_data['psdids']
            psdids = psdids.split(",")
            regs = RegRecord.objects.filter( event=event_name, psdid__in=psdids )
            got_psdids = set([r.psdid for r in regs])
            missed = set(psdids) - got_psdids
            email_gremlin = post_email_handler_iter( form, event, regs )
            who_send = "Sending to %s\nFailed to send to %s\n" % (", ".join(got_psdids), ", ".join( missed) )
            return HttpStreamTextResponse( itertools.chain( (who_send,), email_gremlin), event.event )
    else:
        #try:
        #    t = find_template_source('email/your_matches.txt')[0]
        #except:
        #    t="error: default template not found"
        default_text = "Enter text here"
        initial = { 'event_name': event_name, 'subject':"Your PSD Matches", 'body':default_text }
        #initial = { 'event_name': event_name, 'subject':"PSD Matches.", 'body':t }
        form = SubgroupEmailForm( initial=initial )

    return render_to_response('subgroup_contact_email.html', {'form': form, 'event':event, 'event_name':event_name})



def email_reminders_iter( form, event ):
    subject = form.cleaned_data['subject']
    body_template = form.cleaned_data['body']
    #    do_flagging = form.cleaned_data['do_flagging']
    really_send = form.cleaned_data['really_send']
    
    regs = RegRecord.objects.filter(event=event.event, cancelled=False)

    yield """really_send = %s   # regrecords = %s""" % (really_send, len(regs))
    smptxt = ""
    cntr = 0
    for r in regs:
        cntr += 1
        if r.matches < 5:
            r.flagged = True
        else:
            r.flagged = False
        try:
            email_template = Template( body_template )
            body = email_template.render( Context( {'rr':r, 'event':event} ) )
            smptxt = send_email( event, r, subject, body, really_email=really_send )
            yield "\n<hr>#%s: %s<hr>\n" % (cntr, r.psdid) + smptxt
        except Exception as inst:
            yield "<p>Problem rendering email for %s / %s" % (r,inst,) 
    yield "<hr><h2>Finished!</h2>"
#    regs = RegRecord.objects.filter( event=event.event )
#    event = Event.objects.get( event=event.event )
#    for r in regs:
#        subject = "PSD Tomorrow! Reminder for %s" % (rr.psdid,)
#        #if not r.cancelled and not "!DEMOG!" in r.notes and not "!NO PAY!" in r.notes:
#        if not r.cancelled:
#            emailReminder( r, event, email_tem, do_flagging=do_flagging )
            


   
            
def contact_us(request, event_name):
    evt = Event.objects.get(event=event_name)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            subject = "PSD website feedback"
            if form.cleaned_data['psdid']:
                subject += ' from %s' % form.cleaned_data['psdid']
            t = get_template('email/feedback.txt')
            c = Context({'cd': form.cleaned_data, 'event': evt})
            body = t.render(c)

            staff = User.objects.filter(is_staff=True)
            for s in staff:
                s.email_user(subject, body, evt.info_email )
        return render_to_response('feedback_received.html', {'event': evt}, context_instance=RequestContext(request))

    else:
        form = FeedbackForm()
    return render_to_response('feedback.html', {'form': form, 'event': evt}, context_instance=RequestContext(request) )
