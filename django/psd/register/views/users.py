
import pdb

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from psd.register.models import Organization, RegRecord, Event
from datetime import date
import django.http
from django.contrib.sites.models import Site

import logging
logger = logging.getLogger('psd.register.users')

    
def list_events( request ):
    """
    List all events and links to their registration pages
    """
    
    today = date.today()
    open_events = Event.objects.filter( date__gte=today )
    
    old_events = Event.objects.filter( date__lt=today )
    return render_to_response( 'list_events.html', locals(), context_instance=RequestContext(request) )

    
    
@login_required
def show_me_all(request, psdid=None):
    """
    This renders the profile page for a user so they can see what they registered
    for and what is upcoming.
    Also provides links to future events that they have not registered for.
    """
    if psdid == None:
        user = request.user
        reg_list = RegRecord.objects.filter(psdid=user.username)
        staff_call = False
    elif request.user.is_staff:
        staff_call = True
        reg_list = RegRecord.objects.filter(psdid=psdid)
    else:
        return django.http.HttpResponseForbidden()
    
    # so ugly!
    today = date.today()
    reg_list_cur = []
    reg_list_past = []
    regged_evts = set()
    for r in reg_list:
        r.eventrec = Event.objects.get(event=r.event)
        if r.eventrec.date < today:
            reg_list_past.append( r)
        else:
            r.info_email = r.ev.info_email  # stash variable for template
            reg_list_cur.append(r)
        regged_evts.add( r.event )
        
    # get all open events
    evts = Event.objects.all()
    open_events = []
    for evt in evts:
        if evt.date >= today and not evt.event in regged_evts:
            open_events.append( evt )
            
    if reg_list:
        if reg_list[0].is_group:
            group_or_individual = "group"
        else:
            group_or_individual = "individual"
    else:
        group_or_individual = "individual"
        
    return render_to_response('show_me_all.html', locals(),  
                                  context_instance=RequestContext(request))
#    else:
#        return render_to_response('registration/user_not_found.html', {}, context_instance=RequestContext(request))


@login_required
def show_me(request, event_name):
    user = request.user
    reg_list = RegRecord.objects.filter(psdid=user.username).filter(event=event_name)
    event = Event.objects.get( event=event_name )
    if reg_list:
        return render_to_response('show_me.html', {'reg': reg_list[0], 'event':event},  context_instance=RequestContext(request))
    else:
        return render_to_response('registration/user_not_found.html', {}, context_instance=RequestContext(request))


@login_required
def show_me_all2(request, psdid):
    reg_list = RegRecord.objects.filter(psdid=psdid)

    if reg_list:
        return render_to_response('show_me.html', {'reg': reg_list[0]},  context_instance=RequestContext(request))
    else:
        return render_to_response('registration/user_not_found.html', {}, context_instance=RequestContext(request))





def about_page(request, what=None):
    """ 
    Return about pages (such as info pages regarding gender) rendered with log-in
    links and whatnot.
    """
    
    # about pages are (not yet) event specific. 
    try:
        event = Organization.objects.get( site=Site.objects.get_current() )
    except:
        logger.warning( "No event or organization object found for about page lookup" )
        event = None
                
    return render_to_response( ['about/%s.html' % what, 'about/notfound.html'], locals(), context_instance=RequestContext(request))

 
