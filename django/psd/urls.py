from django.conf.urls.defaults import *
from django.contrib.auth.views import login
from django.contrib.auth.views import logout
from django.contrib.auth.views import password_reset
from django.contrib.auth.views import password_reset_done
from django.contrib.auth.views import password_reset_confirm
from django.contrib.auth.views import password_reset_complete
from django.contrib.auth.views import password_change
from django.contrib.auth.views import password_change_done

from psd.register.views import do_sign_up, sign_up_user, registration_note
from psd.register.views.dashboard import check_in, event_manager, potential_matches, next_date_sheet, date_sheet, break_matches

import sys, os
import psd.settings

import psd.register.views.users
import psd.register.views.contact

#from psd.register.views.users import current_datetime
#from psd.playpen.views import current_datetime

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # ('^.*','django.views.generic.simple.direct_to_template', {'template': 'maintenance.html'})

    # Participant user screens    
    ('^accounts/login/$', login),
    ('^accounts/login$', login),
    ('^accounts/logout/$', logout),
    url('^accounts/view/$', psd.register.views.users.show_me_all, name="account-view"),  # their reg record screen

    # various info screens
    url('^about/(?P<what>[0-9A-Za-z]+)$', "psd.register.views.users.about_page", name="about-page"),

    # handling password changes and resets
    url('^reset/$', password_reset, {'email_template_name':'registration/password_reset_email.html'}, name="password-reset"),
    ('^reset/done/$', password_reset_done),
    ('^reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', password_reset_confirm), 
    (r'^reset/complete/$', password_reset_complete),
    ('^accounts/changepw/$', password_change),
    ('^accounts/changepw/done$', password_change_done),

    # Registration for the event
    ('^regnote/(?P<event_name>[0-9A-Za-z]+)$', registration_note ),
    url('^individual/(?P<event_name>[0-9A-Za-z]+)$', do_sign_up, name="individual-registration"),
    url('^group/(?P<event_name>[0-9A-Za-z]+)$', do_sign_up, {'group_form':True}, name="group-registration"),
    url('^extra/(?P<event_name>[0-9A-Za-z]+)$', do_sign_up, {'group_form':False, 'reg_override':True}, name="additional-registration"),
    url('^user/(?P<event_name>[0-9A-Za-z]+)', sign_up_user, name="user-registration"),
    ('^individual$', 'django.views.generic.simple.direct_to_template', {'template': 'no_event_specified.html'}),
    ('^group$', 'django.views.generic.simple.direct_to_template', {'template': 'no_event_specified.html'}),
    # simple feedback form for the event
    url('^feedback/(?P<event_name>[0-9A-Za-z]+)', "psd.register.views.contact.contact_us", name="feedback"),
  
    # Link for PayPal to talk to us
    url(r'^endpoint/$', psd.register.views.PaypalPaymentEndpoint(), name="paypal-endpoint"),

    # ADMIN LINKS
    url('^manage/(?P<event_name>[0-9A-Za-z]+)/datematrix', "psd.register.views.dashboard.get_dating_matrix", name="date-matrix" ),
    url('^manage/(?P<event_name>[0-9A-Za-z]+)/edit/(?P<psdid>[0-9A-Za-z]+)', do_sign_up, name="update-reg"),
    url('^manage/(?P<event_name>[0-9A-Za-z]+)/walkin/rereg/(?P<psdid>[0-9A-Za-z]+)', do_sign_up, {'mark_as_here':True}, name="walk-in-update" ),
    url('^manage/(?P<event_name>[0-9A-Za-z]+)/walkin/individual', do_sign_up, {'mark_as_here':True}, name="walk-in-reg-individual"),
    url('^manage/(?P<event_name>[0-9A-Za-z]+)/walkin/group', do_sign_up, {'mark_as_here':True, 'group_form':True}, name="walk-in-reg-group"),
    ('^manage/(?P<event_name>[0-9A-Za-z]+)/(?P<action>[a-zA-Z]*)/(?P<extraArg>[0-9a-zA-Z]*)$', event_manager),
    ('^manage/(?P<event_name>[0-9A-Za-z]+)/(?P<action>[a-zA-Z]*)$', event_manager),
    url('^manage/(?P<event_name>[0-9A-Za-z]+)$', event_manager, {'action':""}, name="event-manager" ),
    url('^manage/?$', event_manager, {'event_name':'', 'action':"allevents"}, name="event-lister" ),
    url('^admin/checkin/(?P<event_name>[0-9A-Za-z]+)$', check_in, name="check-in"),
    ('^admin/multibreak$', "psd.register.views.dashboard.multi_break" ),
    
    # Scheduling and making the pdf of schedules
    url('^admin/schedules/(?P<event_name>[0-9A-Za-z]+)', "psd.register.views.dashboard.schedule_form", name="make-schedules"), 
    url('^admin/printschedules/(?P<event_name>[0-9A-Za-z]+)/(?P<include_code>[A-Za-z]+)', psd.register.views.printouts.make_schedules, name="print-schedules"),
    ('^admin/printschedules/(?P<event_name>[0-9A-Za-z]+)', psd.register.views.printouts.make_schedules),
    url('^admin/post_event/(?P<event_name>[0-9A-Za-z]+)', psd.register.views.contact.post_email, name="email-post-event"),
    url('^admin/email/(?P<event_name>[0-9A-Za-z]+)', psd.register.views.contact.subgroup_email, name="subgroup-email"),
    url('^admin/pre_event/(?P<event_name>[0-9A-Za-z]+)', psd.register.views.contact.pre_email, name="email-pre-event"),
    
    # user management
    url('^view/(?P<event_name>[0-9A-Za-z]+)/(?P<psdid>[0-9A-Za-z]+)', "psd.register.views.dashboard.view_user", name="view-user" ),
    url('^edit/(?P<event_name>[0-9A-Za-z]+)/(?P<psdid>[0-9A-Za-z]+)', "psd.register.views.dashboard.edit_user", name="edit-user" ),
    url('^edit/(?P<event_name>[0-9A-Za-z]+)', "psd.register.views.dashboard.edit_event", name="edit-event" ),
    
    url('^profile/(?P<psdid>[0-9A-Za-z]+)$', psd.register.views.users.show_me_all, name="admin-account-view"),  # their reg record screen
    ('^matches/(?P<event_name>[0-9A-Za-z]+)/(?P<psdid>[0-9A-Za-z]+)$', potential_matches),
    url('^break/(?P<event_name>[0-9A-Za-z]+)/(?P<psdid>[0-9A-Za-z]+)$', break_matches, name="admin-break-matches"),
    url('^datesheet/(?P<event_name>[0-9A-Za-z]+)/(?P<psdid>[0-9A-Za-z]+)$', date_sheet, name="date-sheet"),
    url('^prettydatesheet/(?P<event_name>[0-9A-Za-z]+)/(?P<psdid>[0-9A-Za-z]+)$', date_sheet, name="pretty-date-sheet", kwargs={'pretty':True} ),
    url('^nextdatesheet/(?P<event_name>[0-9A-Za-z]+)/$', next_date_sheet, name="next-date-sheet"),

    # Django documentation stuff
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    url('^$', psd.register.views.users.list_events, name="list_events")
    # some testing 
    #('^test', test_function),
    #    (r'^now/$', current_datetime )
)


# This is dirty dirty dirty!
if 'runserver' in sys.argv or 'runserver_plus':
    urlpatterns += patterns('', url(r'^media/(.*)$', 'django.views.static.serve', kwargs={'document_root': os.path.join(psd.settings.PROJECT_PATH, 'media')}), )
    urlpatterns += patterns('', url(r'^(.*)$', 'django.views.static.serve', kwargs={'document_root': psd.settings.WEBSITE_PATH}), )
    print "urlpatterns supplemented!"
    
print "project path='%s'" % (psd.settings.PROJECT_PATH, )



