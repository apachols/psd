import traceback
from psd import loader, polymatch
import logging, time
logger = logging.getLogger('psd.date_scheduler')
from psd.register.models import *
from psd.register import table_matcher 

def find_sad_people( schedules, target, event_name ):
    sad = []
    tps = { 'alt':0, 'main':0, 'friend':0 }
    total = 0
    logger.info( "Finding Sad People---Those with few dates" )
    print "PSDID\tgot\t%\t#m\t#one\tminicode"
    for psdid,sch in schedules.items():
        dts = sch.count_dates()
        
        for t in tps.iterkeys():
            tps[t] += dts.get(t,0)
        
        tdat = dts.get('alt',0) + dts.get('main',0)
        rr = RegRecord.objects.get(psdid=psdid,event=event_name)
        if rr.matches > 0:
            pergot = 100 * tdat / min(rr.matches,target)
        else:
            pergot = 0
        if tdat < 5 or pergot <= 50 or (tdat < target/2 and pergot <= 75):
            print "%s\t%s\t%s\t%s\t%s\t%s" % (psdid, tdat, pergot, rr.matches, rr.oneway, rr.minicode() )
        total += tdat
        
    print "Counts of dates scheduled"
    print tps
    
    print "Mean real dates = %s" % (1.0*total/len(schedules) )
    print "Total Dates = %s" % ( sum( [x for x in tps.itervalues()] ), )
    

def print_and_log( str ):
    logger.info( str )
    print( str )
    
def schedule(event_name, rounds, trials, who_include="In"):
    print_and_log("""
        Scheduling for event %s 
        folks included: %s
        rounds: %s
        trials: %s
        target dates: %s""" % (event_name, who_include, rounds, trials, rounds-3))
    try:
        for i in range(20):
            print( "tick...." )
            time.sleep(0.01)
        time.sleep(0.2)
            
        daters = loader.get_all_daters(event_name, who_include)
        print_and_log( "Number of daters to schedule: %s" % (len(daters['all']), ) )
        
        print_and_log( "making schedules now" )
        schedules = polymatch.make_schedules_random(event_name, daters, rounds, trials, scramble_rounds=True)
        
        if len(schedules) == 0:
            print_and_log( "No one scheduled.  Bailing" )
            return
        else:
            print_and_log( "Daters have been scheduled" )
            
        print_and_log( "finding sad people" )
        find_sad_people( schedules, rounds - 3, event_name )
        
        ## That returned a dict mapping psdids to lists of (psdid, datetype) 2-tuples.
        print_and_log( "Saving the generated table of dates..." )
        loader.save_date_table(schedules, event_name, erase_old=True)
        
        print_and_log( "Scheduling dates to tables..." )
        table_matcher.run_event(event_name)
    except Exception as inst:
#        (type, value, traceback) = sys.exc_info()
        print_and_log( "Scheduler failed with %s" % (inst,) )
        dbstr = traceback.format_exc(inst)
        print_and_log( "Details are:\n%s\n" % ( dbstr, ) )
    
    print_and_log( "Finished scheduling" )

    
#from psd.register.models import DateRecord, TableRecord, RegRecord
#    dates = DateRecord.objects.filter(event=event_name)
#    tables = TableRecord.objects.filter(event=event_name)
#    daters = RegRecord.objects.filter(event=event_name)
#    matcher = TableMatcher(daters, dates, tables)
#    matcher.assign_all_dates(save=False)