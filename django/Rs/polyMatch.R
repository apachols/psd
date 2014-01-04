#source("sqliteLoader.R")

mysource( "tableMatcher.R" )


####### THE MATCHING ALGORITHM ########

# Some notes:
# The basic element is a matrix of 0s and >0s of who is willing
# to date who.  
# The first step is to symmetrize the matrix by making sure matches are mutual.


testing.load = function() {
  source( Rs/"polyDataRead.R" )
	#	load.data( "Test" )
	load.data( "NotNo" )
}


if ( FALSE) {
	source("Rs/sqliteLoader.R")
	# CODE FOR TESTING IN R
	R_SOURCE_DIR = "/Users/luke/PSD/django/Rs/"  # where R code is stored
	DATABASE_FILENAME = "/Users/luke/PSD/run8/mydb" 
	EVENT_NAME = "revival1"        
	source( paste( R_SOURCE_DIR, "sqliteLoader.R", sep="" ) ) 
	cat( "START OF SCRIPT" )
	
	
	build.event.environment( INCLUDE_ALL="NotNo" )                                                                                             
	match = 12
	trials = 1
	
	con = open_database()
	tables = loadTableTable( con, EVENT_NAME )
	close_database( con )
	                                                               
	mysource( "polyMatch.R" )
	make.matches( match, trials=trials, scramble.rounds=FALSE, tables=tables )
	
	# now save the table to the database                                                               
	con = open_database()
	save_date_table( dts, con, event=EVENT_NAME, erase_old=TRUE )
	close_database(con)
}
	


## Schedule a single round
## Select pairs that will date until there is nothing left to match up
## T - the table of matches (adjacency graph)
## style - a string of what kind of pairing it is 
##         (this is not used, just tacked onto the matches)
## Return - list of pairs of folks IDs
pairOff = function( T, style, N.tables ) {
	
	matches = list()
	on.match = 1
	while( (length(T) > 1) && (on.match <= N.tables) ) {
		LN = nrow(T)
	
		choices = (1:LN)[T[1,]>0]
		if ( length(choices) == 0 ) {
			T = T[-c(1),-c(1)]
		} else {
			if ( length( choices) == 1 ) {
				f = choices
			} else {
				weights = T[1,][T[1,] > 0]
				f = sample(choices,1, prob=weights)
			}
			
			# stash the pair that was matched
			matches[[on.match]] = c( rownames(T)[c(1,f)], style, T[1,f] )  
			on.match = on.match + 1
			#	cat("match = ", matches[[i]], "\n" )
	
			# shrink matrix to cut out the row and col of both matched
			T = T[-c(1,f),-c(1,f)]  
			#print(T)
		}
	}
	matches
}



## Keep doing pairoff for up to 'trials' trials or until everyone gets a match
## Return the match of most folks as list of pairs of folks
## Param T - date matrix
## Param F - friendship date matrix, used for extra folks who did not get dates
pairOff.random = function( T, trials, N.tables, skips=NULL, style="none" ) {
		
	desired = min( floor( nrow(T) / 2 ), N.tables )
	best = c()
	bln = 0
	for ( i in 1:trials ) {

		T = orderByChances(T, skips)

		mt = pairOff( T, style, N.tables )
		ln = length( mt )
		stopifnot( ln <= N.tables )
		if ( ln == desired ) {
			return( mt );
		} else if ( ln > bln ) {
			best = mt
			bln = ln
		}
	}
	#warning( "Failed to find complete seperation." )
	return( best )
}


## Remove all the matches from the matrix so they will not get a match-up
## again.
stripMatches = function( M, matches ) {
	
	for ( mt in matches ) {

		M[[mt[[1]],mt[[2]]]] = M[[mt[[2]],mt[[1]]]] = 0
				
	}

	M
}


## Turn the match list into a String
cleanUpMatches = function( matches ) {
	
	paste( sapply( matches, function( x ) { 
		paste( x[[1]], "-", x[[2]], " (", x[[4]], ")", sep="" ) } ),
		collapse = ", " )
	
}


## Sort the matrix by number of people that are potential matches
orderByChances = function( M, skips, size.rnd=1.5) {

	# first a random shuffle
	rnd = runif(nrow(M), max=size.rnd)
	tots = apply(M, 1, sum )
	if ( is.null( skips ) ) {
		ord = order(pmin(tots,10) + rnd)
	} else {
		ord = order(-skips,pmin(tots,10)+(pmax(tots,10)/2)+rnd)
	}
	
	M = M[ord,]
	M = M[,ord]
		
	#tots = apply(M, 1, sum )
	#cat( "tots= ", tots, "\n" )

	#print( M )

	M
}



## Take two matrices and number of rounds, and produce a date matrix
## for each round!  Alternate between matrices with each round.
## Throw in extra dates using M.friend, if there are free-floating folks.
maker.matrix = function( M.A, M.B, M.friend=NULL, rnds, N.tables,
						trials=5, 
						order=TRUE, scramble.rounds=TRUE ) {

	# If no friend matrix, make an empty matrix with no matches.
	if ( is.null( M.friend ) ) {
		M.friend = M.A
		M.friend[] = 0
	}
	
	stopifnot( class( M.friend ) == "matrix" )
	
	matches = c()

	dates = data.frame( matrix( rep( c("none",""), each=nrow(M.A), times=rnds ),
							ncol=2*rnds ), 
			 		 		stringsAsFactors=FALSE)
	names(dates) = paste( rep( c( "Rnd", "Type"), rnds ), 
						floor(0.5 * 2:(2*rnds+1)), sep="" )
	row.names(dates) = rownames(M.A)
	
	dates$skipsA = 0
	dates$skipsB = 0
	
	if ( scramble.rounds ) {
		rndIDs = sample(1:rnds,rnds)
	} else {
		rndIDs = 1:rnds
	}
	
	for ( k in 1:rnds ) {

		rndID = rndIDs[k]
		
		# choose matrix
		if ( rndID %% 2 == 1 ) {
			M = M.A
			skips = dates$skipsA
			skips.alt = dates$skipsB
			cat( "*** Step ", k, ": Processing round ", rndID, ".  Type = A\n", sep="" )
		} else {
			M = M.B
			skips = dates$skipsB
			skips.alt = dates$skipsA
			cat( "*** Step ", k, ": Processing round ", rndID, ".  Type = B\n", sep="" )
		}
		
		tots = apply(M, 1, sum )
				
		mt = pairOff.random( M, trials, N.tables, skips, style="main" )
		
		cat( "# matches =", length(mt), "out of", floor(sum(tots > 0)/2), "\n" )
		
		## Pick up more dates with the alternate matrix (and current one too)
		M.all = pmax( M.A, M.B )
	
		folks = setdiff( rownames( M ), unlist( mt ) )
		M.all = as.data.frame( M.all[folks,folks] )
		
		if ( is.matrix(M.all) && nrow( M.all ) > 1 ) {
			mt2 = pairOff.random( M.all, trials, N.tables - length(mt), skips.alt[folks], style="alt" )
		
			cat( "# bonus matches = ", length(mt2), "\n",sep="" )
			mt = c( mt, mt2 )
			cat( "    matches are ", length(mt), " out of ideal of ", floor(sum(tots > 0)/2), 
							" = ", round(200*length(mt)/floor(sum(tots>0))), "%\n",sep="" )

		}
		
		## Same deal, with friend matrix
		folks = setdiff( rownames( M ), unlist( mt ) )
		M.t = M.friend[folks,folks]

		## Only have some friend dates.  Drop half the rows randomly.
		#Nmt = nrow(M.t)
		#fok = sample( 1:Nmt, Nmt/2 )
		#M.t = M.t[ fok, fok ]
		 
		if ( is.matrix(M.t) && nrow( M.t ) > 1 ) {
			mt2 = pairOff.random( M.t, trials, N.tables-length(mt), skips[folks], style="friend" )
		
			cat( "# friend matches = ", length(mt2), "\n" )
			mt = c( mt, mt2 )
		}

		# remove those dates from all matrices
		M.A = stripMatches( M.A, mt )
		M.B = stripMatches( M.B, mt )
		M.friend = stripMatches( M.friend, mt )
		
		for ( match in mt ) {
			dates[match[[1]],2*rndID-1 ] = match[[2]]
			dates[match[[2]],2*rndID-1 ] = match[[1]]
			dates[match[[1]],2*rndID] = dates[match[[2]],2*rndID] = match[[3]]
		}
		
		#skips = skips + (dates[,i]=="none")[names(dates[[1]]) %in% names(skips)]
		if ( rndID %% 2 == 1 ) {
			dates$skipsA = dates$skipsA + (dates[,2*rndID] != "main")
		} else {
			dates$skipsB = dates$skipsB + (dates[,2*rndID] != "main")
		}
		
		if ( is.null( mt ) ) {
			matches[[rndID]] = list()
		} else {
			matches[[ rndID ]] = mt  #cleanUpMatches(mt)
			#cat( matches[[i]], "\n" )
		}
		#print( dates )
		#readline( "ready?" )	
	} # end rnd loop.

	dates$skips = dates$skipsA + dates$skipsB
	list( matches=matches, dates=dates )
}




#### DO THE MATCHING PROCESS #####



## Attempt to match folks up for given number of rounds
doMatch = function( RNDS, N.tables, target.dates = RNDS, friends=TRUE, scramble.rounds = TRUE ) {
	
  stopifnot( !is.null(P$matches) )

	if ( !friends ) {
		friend.mat = NULL
	}

  #warning( "only gay rounds" )
  res = maker.matrix( gay.mat, str.mat, friend.mat, rnds=RNDS, N.tables, trials=4, scramble.rounds=scramble.rounds )
	
  dates = res[[2]]
  dates$total = RNDS - dates$skips
  dates$theo = P$matches
  
  # change skips to forced skips
  dates$skips = pmin(RNDS, dates$theo) - dates$total
  
  dates$score = ifelse( dates$theo == 0, 0, 
  				round( 100 * (1 - pmin(dates$total,target.dates) / pmin(dates$theo,target.dates))) )
  # erase people with 0 potential dates

  ## badness is a mix of the worst percentage loss and the "standard deviation-esque"
  ## average loss of all the folks dating, with high losses counting more heavily
  bs = max(dates$score) + round( sqrt(mean(dates$score^2)), digits=1 )
  cat( "badness score = ", bs, "\n" )
  
  list( dates=dates, matches=res[[1]], bad=bs )
}
		
		
		

## Run doMatch multiple times, scoring each run and taking
## the most successful.
## Take the results, schedule tables, and write out the results
## to the various files.
make.matches = function( RNDS = 8, target.dates = RNDS, trials=10, friends=TRUE, scramble.rounds=FALSE, tables ) {

  N.tables = nrow(tables)
  
  if ( !scramble.rounds ) {
  	  warning( "Not scrambling rounds -- will alternate gay/str!  Later rounds will suck!" )
  }
  
  ## run the match program multiple times, score each round, and take the best
  ## (least bad)
  mtc =  doMatch( RNDS, N.tables, target.dates, friends, scramble.rounds=scramble.rounds )
  bads = c(mtc$bad)
  if ( trials > 1 ) {
  	for ( i in 1:(trials-1) ) {    
   	 m2 = doMatch( RNDS, target.dates )
   	 bads = c( bads, m2$bad )
   	 if ( m2$bad < mtc$bad ) {
   	   mtc = m2;
   	 }
  	}
  }
  
  cat( "Scores: ", paste( bads, collapse=", " ), "\n" )
  
  cat( "FINALIZED MATCHING -- PROCESSING BEST GENERATED - ", mtc$bad, "/", mtc$bad - max(mtc$dates$score), "\n" )

  ## print out the best results
  dts = mtc$dates
  matches = mtc$matches

  #print( dts )
  
  # save the raw matches to global environment
  matches <<- matches

  # Save copy of date people only for the final matching
  # record sheet.
  cat( "Writing the entry sheet for the final matches.\n" )
  FM_tab = dts[2*(1:RNDS)-1]
  tmp.T = P[c("personID","pubname","email")]
  tmp.T$comments = " "
  FM_tab$personID = rownames(FM_tab)
  FM_tab = merge(tmp.T, FM_tab )
  FM_tab$Cruise1 = " "
  FM_tab$Cruise2 = " "
  FM_tab$Cruise3 = " "
#  write.csv( FM_tab, file="final_matches.csv", 
#  					quote=FALSE )
  
 
  cat( "Generating table assignments.\n" )
  tbles = generate.tables(matches, tables)
  
  cat( "Adding table assignments to date matrix and cleaning matrix.\n" )
  for ( i in 1:RNDS ) {
    tblname = paste("table",i, sep="")
    dts[[tblname]] = "none"
    dts[[tblname]] = as.character( dts[[tblname]] )
    tb = tbles[[i]]
    if ( nrow( tb ) ) {
      dts[ tb$A, tblname ] = tb$table
      dts[ tb$B, tblname ] = tb$table 
    }
  }

  ## change friendship lines to (F) for the final schedules
  nms = paste( "Type", 1:RNDS, sep="" )
  dts[nms][ dts[nms]=="friend" ] = "(F)"
  dts[nms][ dts[nms]=="none" ] = ""

  cat( "Writing data table.\n" )
  dts$personID = rownames(dts)  # for merge
  dts = merge(P[c("personID","pubname")], dts, by="personID")
#  write.csv( dts, file="date_table.csv", quote=FALSE )

  cat( "Exported 'dts' to global environment\n" )
  dts <<- dts
  
  cat( "Table of quality scores for all participants. (quality = %missed of potential.  0 is good.)" )
  print( table( dts$score ) )
  cat( "Table of total numbers of non-friend dates" )
  print( table( dts$total ) )
  cat( "Table of total numbers of skips" )
  print( table( dts$skips ) )
  
  cat( "List of screwed folks\n" )
#browser()
 print(  dts[ (dts$total < 5) | (dts$score >= 60), c("personID", "total", "theo", "score") ] )
  
  invisible(dts)
}





print.results = function( dts, RNDS ) {
  
  w.out = function( ... ) {
	  cat( ..., file="schedules.txt", append=TRUE ) 
  }

  cat( "Schedules\n", file="schedules.txt" )
  
  rnds = dts[ paste( "Rnd", 1:RNDS, sep="" ) ]
  types = dts[ paste( "Type", 1:RNDS, sep="" ) ]
  tables = dts[ paste( "table", 1:RNDS, sep="" ) ]
  
  folks = as.character( dts$personID )
  
  for ( f in folks ) {
    w.out( "\f\nDate Schedule for\n", f, "\n" )
    tb = data.frame( Date=as.vector(rnds[f,]), Type=as.vector(types[f,]), Table=as.vector(tables[f,]) )
    write.table( tb, file="schedules.txt", append=TRUE )		
  }
  
}

