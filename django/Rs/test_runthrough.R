

# Script hack---define Yes and No variables
Yes = "Yes"
No = "No"

source( "Rs/setup.R" )

source( "Rs/runJavaMatcher.R" )

dopast = readline( "Read past data and build associated tables? (Yes=yes, default is no)\n> " )
No

if ( dopast=="Yes" ) {
	source( "Rs/allPastData.R" )
}



dopast = readline( "Load in the date matrix and results of the event? (Yes=yes, default is no)\n> " )
No

if ( dopast=="Yes" ) {
	source( "Rs/datesToSql.R" )
	source( "Rs/finalMatcher3.R" )
}

# clean up
rm( list=ls() )

# Start from scratch, see what we get!  load.data reads the output of 
# the java file and updates banlist.csv (the list of who is here
# and whether they have paid and what their status is).
source( "Rs/polyDataReadSql.R" )

load.data( INCLUDE_ALL = "NotNo" )

# Make table file
source( "Rs/tableMatcher.R" )
make.table.table( N=100 )


# get demographics for those present.
source( "Rs/demographics.R" )
F = load.demographics( P )
print( F )

match = readline( "Ready to make matches.  How many rounds of dating?  0 for none.\n> " )
3


match = as.integer( match )

if ( match > 0 ) {	
	source( "Rs/polyMatch.R" )
	trials = readline( "How many random trials should be generated?  More trials will find a better solution, in probability.  Try 10, if you have no idea.\n> " )
	make.matches( match, trials=trials )
}


