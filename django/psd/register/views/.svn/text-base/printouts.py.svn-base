from psd.register.models import RegRecord, DateRecord

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch 
    from reportlab.lib.enums import TA_CENTER
except ImportError:
    pass

import logging
logger = logging.getLogger('psd.register.views.printout')

def make_table_line(date):
    circle = '____'
    suffix = '(F)' if date.friend_date else ''

    ## This should be something like:
    #return [date.round, date.other_psdid + suffix, 'Table %s' % date.table,
    #        circle, circle, '']
    ## but there's no such thing as a table yet.

    return [date.round, date.other_psdid + suffix, '%s' % date.table,
            circle, circle, '']

def make_table(reg, num_rounds, break_line=7):
    header = ['Rnd', 'Date', 'Table', 'YES\nI am\ninterested', 'NO\nI am not\ninterested',
              'Comments to Organizers\n(mismatch, no-show,\nbad behavior, etc.)']
    dates = list(DateRecord.objects.filter(psdid=reg.psdid, event=reg.event))
    dates = dict((x.round, x) for x in dates)
    lines = [header]
    for i in range(1, num_rounds+1):
        if i in dates:
            lines.append(make_table_line(dates[i]))
        else:
            lines.append([i, '', '', '', '', ''])
    t = Table(lines, rowHeights=[0.4 * inch] * len(lines), colWidths=[None, None, None, None, None, 4 * inch])
    t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1, -1), 0.5, colors.black)]))
    t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1, 0), 1, colors.black)]))
    if break_line < num_rounds:
         t.setStyle(TableStyle([('LINEBELOW', (0,break_line), (-1, break_line), 0.5, colors.black)]))
         t.setStyle(TableStyle([('BOTTOMPADDING', (0,break_line), (-1, break_line), 10)]))
    #t.setStyle(TableStyle([('TOPPADDING', (0,num_rounds), (-1, num_rounds), 10)]))
    return t

def make_schedule(reg, num_rounds):
    """
    Make schedule for single dating group
    """
    #Story = [Spacer(1,1*inch)]
    Story = []
    psc = ParagraphStyle("centered", alignment=TA_CENTER)
    psc_large = ParagraphStyle("title", fontSize=14, alignment=TA_CENTER)

    def add_para(text, style=None):
        style = style or psc
        Story.append(Paragraph(text, style))
        Story.append(Spacer(10,10))

    add_para(u'<b>\xa7 PSD Dating Schedule for %s (%s) \xa7</b>' % (reg.nickname, reg.psdid), psc_large)
    Story.append(Spacer(1, 0.25*inch))
    add_para('REMEMBER:')
    add_para("It is inappropriate to ask for any contact information during your date, to ask what\
              your date thinks of you, or to otherwise escalate the date.")
    add_para("(F) after a Date denotes a <i>friendship date</i> - neither of you should match the \
                other one's dating preferences. Let us know if there's a mistake!")
    Story.append(Spacer(1, 0.5*inch))
    add_para("<u><b>THE TABLE OF DATES</b></u>")
    t = make_table(reg, num_rounds)
    Story.append(t)
    Story.append(Spacer(1, 0.5*inch))
    add_para("Cruises: 1 _____________    2 _____________    3 _____________")
    add_para("""<i>Instructions: After each date, please check off YES if you
            want your information given to your date(s) or NO if you do not. If both
            parties indicate interest by selecting YES, we will swap your email addresses
            for you. Comments are for if the match violated the parameters you had
            entered, your date did something inappropriate or didn't show, or if there is
            anything else we should know.</i>""")
    add_para("<i>Please return this form to us at the end of the evening.</i>")
    Story.append(PageBreak())
    return Story



def make_schedule_pdf( event_name, include_code="In"):
    """ 
    Make a PDF document with one page per person holding all of the pre-computed
    dating schedules.  This method _does not_ compute those schedules.  They must
    be in the database.
    """
    
    logger.debug( "Making schedules for %s with %s included" % (event_name, include_code) )
    story = []
    regs = RegRecord.objects.filter(event=event_name).order_by( 'psdid' )
    
    # determine number of rounds
    alldates = list(DateRecord.objects.filter(event=event_name))
    rndIDs = (x.round for x in alldates)
    num_rnd = max(rndIDs)
    logger.debug( "Number of rounds for this event=%s" % (str(num_rnd),) )
    
    scheds = 0
    
    for reg in regs:
        if ((include_code=="In") and reg.here) or ((include_code=="NotNo") and not reg.cancelled):
             story.extend(make_schedule(reg, num_rounds=num_rnd))
             scheds = scheds + 1
             
    logger.debug( "Made %s schedules" % (scheds, ) )
    if scheds == 0:
        return None
    else:
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=schedules.pdf'
        doc = SimpleDocTemplate(response, topMargin=(0.5 * inch), bottomMargin=(0.5 * inch))
        doc.build(story)
        return response
    
    
def make_schedules(request, event_name, include_code="In"): 
    response = make_schedule_pdf( event_name, include_code )
    
    if response == None: 
        return render_to_response( 'error.html', {'message' : "Sorry.  You are making schedules for a group with no regrecords.  Please try again."}, 
                                   context_instance=RequestContext(request)  )
    else:
        return response
