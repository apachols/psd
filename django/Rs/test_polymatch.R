# Test the code for making dates.  Does a single matching 
# attempt for a 4 round speed dating event.

source( "polyDataRead.R" )
load.data(TRUE)


# testing maker.matrix
source( "polyMatch.R" )
maker.matrix(  gay.mat, str.mat, friend.mat, trials=1, rnds=4 )
