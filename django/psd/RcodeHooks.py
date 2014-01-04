""" 
This module has all the functions that are actually calls to R code.

Don't import this module if the rpy stuff is not installed
"""

import sys, os, shlex, subprocess

# for the R related methods 
from psd.settings import DATABASES, R_SOURCE_DIR

import logging
logger = logging.getLogger('psd.register.RcodeHooks')


def runRCode( proc, code ):
    proc.stdin.write( code )
    logger.info( "Dumped R\n-----------------------\n%s\n------------------" % (code, ) )


def whereis(program):
    """ Figure out where a process is (or if it is installed)"""
    for path in os.environ.get('PATH', '').split(':'):
        if os.path.exists(os.path.join(path, program)) and \
           not os.path.isdir(os.path.join(path, program)):
            return os.path.join(path, program)
    return None


    
    
def install_packages_async( ):
    logger.info( "Installing R Packages by an R call" )
    whr = whereis( "R" )
    if whr == None:
        err = "ERROR: R is not installed, or the shell command in python cannot find it.  Failing\n"
        logger.error( err )
        yield err
    else:
        logger.debug( "R process is %s" % (whr,) )

        p = subprocess.Popen( ["R", "--no-save"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    
        try:
            setup_comm = """
    print( .libPaths() )
    .libPaths( "%s" )
    install.packages( "RSQLite", repos="http://cran.cnr.Berkeley.edu" )
    q()
    """ % ( R_SOURCE_DIR, )

            runRCode( p, setup_comm )
    
            while p.poll()==None:
                yield p.stdout.readline()
            retcode = p.poll()
            yield "\n\nExit code = %s\n</pre>" % (retcode, )
        except Exception as detail:
            yield "Exception: " + str(detail)
        


def test_R_async( ):
    logger.info( "Testing R with an R call" )
    whr = whereis( "R" )
    if whr == None:
        err = "ERROR: R is not installed, or the shell command in python cannot find it.  Failing\n"
        logger.error( err )
        yield err
    else:
        logger.debug( "R process is %s" % (whr,) )

        p = subprocess.Popen( ["R", "--no-save"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    
        try:
            setup_comm = """
    print( .libPaths() )
    .libPaths( "%s" )
    rnorm( 10 )
    library( "RSQLite" )
    q()
    """ % ( R_SOURCE_DIR, )
            runRCode( p, setup_comm )
    
            while p.poll()==None:
                yield p.stdout.readline()
            retcode = p.poll()
            yield "\n\nExit code = %s\n</pre>" % (retcode, )
        except Exception as detail:
            yield "Exception: " + str(detail)
        



def start_r_process( event_name ):
    logger.info( "Starting R Process for event '%s'" % (event_name,) )
    whr = whereis( "R" )
    if whr == None:
        logger.error( "ERROR: R is not installed, or the shell command in python cannot find it.  Failing\n" )
        return None
    else:
        logger.debug( "R process is %s" % (whr,) )
    
    p = subprocess.Popen( ["R", "--no-save"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    
    db_location = DATABASES['default']['NAME']
    
    setup_comm = """
.libPaths( "%s" )
R_SOURCE_DIR = "%s"  # where R code is stored
DATABASE_FILENAME = "%s"                                                                
EVENT_NAME = "%s"        
source( paste( R_SOURCE_DIR, "sqliteLoader.R", sep="" ) ) 
cat( "START OF SCRIPT\n" )
""" % (R_SOURCE_DIR, R_SOURCE_DIR, db_location, event_name) 
    runRCode( p, setup_comm )
    
    while p.poll()==None:
        ln = p.stdout.readline()
        #print "|" + ln + ">"
        #print "\n"
        if ln.startswith( "START OF SCRIPT" ):
            break               

    if p.poll() == None:        
        return p
    else:
        logger.error( "ERROR: Failed to setup R engine" )
        ret = p.poll()
        logger.error( "Got poll of %s" % (ret,) )
        return None
    

    
    
def stop_r_process( p ):
    runRCode( p, "\nq()\n" )
    while p.poll()==None:
        print p.stdout.readline(),
    retcode = p.poll()
    logger.info( "Exit code = %s\n" % (retcode, ) )
    

def stop_r_process_async( p ):
    try:
        runRCode( p, "\nq()\n" )
        while p.poll()==None:
            yield p.stdout.readline()
        retcode = p.poll()
        yield "\n\nExit code = %s\n</pre>" % (retcode, )
    except Exception as detail:
        yield "Exception: " + str(detail)

def print_demographics( event_name, who_print="NotNo" ):
    p = start_r_process( event_name )
    if p == None:
        return
        
    runRCode( p, """print_demog( "%s" )\n""" % (who_print, ) )
    stop_r_process( p )
    
    
def print_demographics_async( event_name, who_print="NotNo" ):
     
    p = start_r_process( event_name )
    if p == None:
        return
            
    runRCode( p, """print_demog( "%s" )\n""" % (who_print, ) )
    
    return stop_r_process_async(p)


   
   
def make_nametags_async( event_name, nametag_filename="nametags.csv" ):
    p = start_r_process( event_name )
    if p == None:
        return   
    
    runRCode( p, """
NAMETAGS_FILENAME = "%s"
build.event.environment( INCLUDE_ALL = "NotNo" )
con = open_database()
make_nametag_file( con, "%s", P$personID )
close_database( con )
""" % (nametag_filename, event_name, ) )
    
    return stop_r_process_async( p )
   
   
def makeNametags( event_name, nametag_filename="nametags.csv" ):
    p = start_r_process( event_name )
    if p == None:
        return   
    
    runRCode( p, """
NAMETAGS_FILENAME = "%s"
build.event.environment( INCLUDE_ALL = "NotNo" )
con = open_database()
make_nametag_file( con, "%s", P$personID )
close_database( con )
""" % (nametag_filename, event_name, ) )
    stop_r_process( p )
   


def do_schedule( event_name, rounds, trials, who_include="In"):
    logger.info( """
Scheduling for event %s 
    folks included: %s
    rounds: %s
    trials: %s
    """ % (event_name, who_include, rounds, trials ) )
    
    p = start_r_process( event_name )
    if p == None:
        return None
    
    schedule_comm = """
build.event.environment( INCLUDE_ALL="%s" )                                                                                             
match = %s
trials = %s
con = open_database()
tables = loadTableTable( con, "%s" )
close_database( con )
mysource( "polyMatch.R" )
make.matches( match, target.dates = match - 2, trials=trials, friends=TRUE, scramble=TRUE, tables=tables )
# Finished making matches.  Next step is to save to DateRecords database                                                         
con = open_database()
save_date_table( dts, con, event="%s", erase_old=TRUE )
close_database(con)
# Finished saving to DateRecords database
""" % (who_include, rounds, trials, event_name, event_name )
    
    runRCode( p, schedule_comm )
    
    return p

   

def schedule( event_name, rounds, trials, who_include="In" ):
    p = do_schedule( event_name, rounds, trials, who_include )
    if p == None:
        return
    return stop_r_process(p)
    
    
def schedule_async( event_name, rounds, trials, who_include="In"):
    p = do_schedule( event_name, rounds, trials, who_include )
    if p == None:
        return None
    return stop_r_process_async(p)



