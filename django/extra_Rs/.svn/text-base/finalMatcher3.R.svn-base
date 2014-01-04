
## This makes a CSV file with the matches so it can be
## easily merged into form letters to send out to 
## participants
#source( "setup.R" )

source( "Rs/setup.R" )




MT = read.csv( FINAL_MATCH_TABLE, stringsAsFactors=FALSE )
rp = read.csv( DATE_TABLE, as.is=TRUE )

if ( nrow(MT) > nrow(rp) ) {
	warning( "FINAL MATCH has more rows than original date table" )
	MT = MT[1:nrow(rp),]
}
stopifnot( all( rp$personID == MT$personID ) )
schedule = rp[ grep( "Rnd", names(rp) ) ]

rp = rp[ grep( "Type", names(rp) ) ]

MT[ MT==" " ] = ""
MT[is.na(MT)] = ""

## Format of MT is:
## personID pubname email comments Rnd1, Rnd2, Rnd3, Rnd4 ..., Cruise1, Cruise2, Cruise3, ...

## general idea for dates--
## make a 2d matrix of boolean matches.  
## Do this by cruising through the list and marking true for any id 
## that is in the row of the owner id.
## Do a transposition and a 'and,' 
## Look for remaining mutual matches.  Then prettify.

## general idea for cruises--make sure the cruised people get the email addrs 
## of who cruised them.

## WARNING: some limits for number of matches and cruises received are
##   hardcoded.   Data structures will probably stretch to work, as needed.

rndCols = grep( "Rnd", names(MT) )
cruiseCols = grep( "Cruise", names(MT) )

for( i in c(rndCols,cruiseCols) ) {
	MT[[i]] = toupper(MT[[i]])
	unknown = !(MT[[i]] %in% MT$personID) & (MT[[i]] != "") & (MT[[i]] != "NONE")
	if ( sum(unknown) > 0 ) {
		cat( "Unknown folks in", names(MT)[i], "\n" )
		print( cbind( MT$personID[unknown], MT[unknown,i]) )
	}
}

N = nrow(MT)

##############################################################################
###                  Compute the actual dating matches 
##############################################################################


# Utility function that assembles information into an appropriate String.  
# Returns that string.
makeNameList = function(nms, rnms, email, nope.text= "Sorry!  No matches this time.") {
	folks = paste( rnms, " (", nms, ") ", email, sep="", collapse=";  " )
	
	if ( folks[1] == " () " ) {
		folks = nope.text
	}
	folks
}


matchUp = function( MT, nope.text="Sorry!  No matches this time." ) {

	mat = matrix( rep( FALSE, N^2 ), nrow=N )

	## For each row, mark off any ids that are left in the matrix
	## These are the people that row wanted.
	for ( i in 1:N ) {
		mat[i,] = MT$personID %in% MT[i, rndCols] 
	}

	m2 = mat & t(mat)
	rownames(m2) = MT$personID
	colnames(m2) = MT$personID

	allL = rep( "", N )

	for ( i in 1:N ) {

		r = m2[,i]  # pull out matches as boolean vector
		
		# now grab id, name, and email of all TRUE matches.
		nms = MT$personID[r]
		rnms = MT$pubname[r]
		email = MT$email[r]
		
		# pack into our matrix of matches.  Empty spots will be ""
		allL[ i ] = makeNameList( nms, rnms, email, nope.text=nope.text )
	}

	names(allL) = MT$personID
	
	list( dates=allL, mat=mat, mutual=m2 )
}

ff = (rp == "(F)")
MTboth = MTf = MTd = MT[ rndCols ]

# kill the friend vs. non-friend dates
MTf[!ff & MTd != ""] = "XXXXX"
MTd[ff & MTd != ""] = "XXXXX"

MT[rndCols] = MTd
dates = matchUp( MT )


allL = data.frame( personID= MT$personID, email=MT$email, 
					pubname=MT$pubname, comments=MT$comments, 
					dates=dates$dates )

allL$num.matches = apply(dates$mutual, 1, sum )
allL$num.desired = apply( dates$mat, 1, sum )
allL$num.possible = apply( dates$mat, 2, sum )

MT[rndCols] = MTf
friends = matchUp( MT, nope.text="No friendship matches." )
allL$friends = friends$dates
allL$num.friends = apply(friends$mutual,1,sum)

cat( "* Matching complete\n" )


##############################################################################
### Save to sql database
##############################################################################


library( "RSQLite" )
m <- dbDriver("SQLite")

con <- dbConnect(m, dbname = DATABASE_FILENAME)

# pickedIDs---people who said s/he liked.
# matchIDs---mutual matches
saveDateResultsToSql = function( who, dateIDs, pickedIDs, likedIDs ) {
	for ( othr in dateIDs ) {
		liked = 0+(othr %in% pickedIDs )
		they_liked = 0+(othr %in% likedIDs)
		qry = sprintf( "UPDATE register_daterecord SET said_yes=%s, they_said_yes=%s WHERE psdid='%s' AND other_psdid='%s';", liked, they_liked, who, othr )
		dbGetQuery( con, qry )

	}
}


MT[rndCols] = MTboth
allnames = MT$personID
date_info = matchUp( MT )
liked_info = date_info$mat
mut_info = date_info$mutual
rownames(liked_info) = colnames(liked_info) = allnames
rownames(mut_info) = colnames(mut_info) = allnames


for ( i in 1:nrow(schedule) ) {
	#cat( "working on ", i, "\n" )
	who = allnames[[i]]
	dates = schedule[ i, ]
	dates = dates[ dates != "none" & dates != "" ]
	liked = dates[ liked_info[i,dates] ]
	they_liked = dates[ liked_info[dates,i] ]
	
	saveDateResultsToSql( who, dates, liked, they_liked )
}



cat( "* Saving to database complete\n" )


cat( "Closing the connection\n" )
dbDisconnect( con )




##############################################################################
### The CRUISES are next...
##############################################################################

crz = rep( "", N )
num.cruises = rep(0,N)

for ( i in 1:N ) {
	ID = MT$personID[i]
#	if ( ID == "BL564" ) {
#		browser()
#	}
	
	# did anyone cruise ID?  If so, get who they are.
	gotF = MT[[cruiseCols[1]]]== ID
	for ( j in cruiseCols ) {
		gotF = gotF | (MT[[j]] == ID)
	}
	
	ids = MT$personID[gotF]
	emails = MT$email[gotF]
	names = MT$pubname[gotF]
	num.cruises[[i]] = length(ids)
	crz[[i]] = makeNameList( ids, names, emails, nope.text="No cruises." )
}

#browser()

cruised = do.call( paste, c( MT[ cruiseCols ], sep=" " ) )

cruised = sub('\\s+$', '', cruised, perl = TRUE) ## Perl-style white space
cruised = ifelse( cruised=="", "no one", cruised )

allC = data.frame( cruises=crz, num.cruises=num.cruises, cruised=cruised )

cat( "* Cruise calculations complete.\n" )



##############################################################################
# combine the normal dates and the cruise dates
##############################################################################

allL = cbind( allL, allC )
allL$num.cruises= num.cruises

allL$comments = ifelse( allL$comments=="", "", paste( "Also: ", allL$comments, "  ", sep="" ) )


write.csv( allL, file="finals.csv", quote=FALSE )

cat( "* Final results written to finals.csv.\n" )
