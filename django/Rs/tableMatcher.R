

## TABLE SCHEDULER
##
## Miratrix, 2008
##
## Schedule tables for folks to sit at.  Let folks not move, especially
## "stationary" ones.
##
## This schedules tables, trying to leave folks in the same place as much 
## as possible
## Groups and stationary folks have preference for this.  Groups also are 
## scheduled for tables that accomodate them.


# Utility function.
# DEPRECATED
# Make a starting point table list of tables available which can then be edited.
make.table.table = function( file=TABLE_FILENAME, N=55 ) {
	# the tables available
	tables = data.frame( ID = 1:N, 
					name="Table",
					#I(paste( c(rep("Bth",15), rep("Tbl",40)), 1:55, sep="/#" )),
					groupOK = c(rep(FALSE,N) ),					statOK = c(rep(TRUE,N) ),
					quality = 1, stringsAsFactors=TRUE )

	tables$name = paste( tables$name, tables$ID )
	tables = tables[ order(tables$quality, decreasing=TRUE), ]
	tables$groupOK[1:(N/4)] = TRUE
	tables$statOK[(N/8):(3*N/8)] = TRUE
	#head( tables )
	cat( "Table file written to", file, "\n" )
	write.csv( tables, file=file, quote=FALSE, row.names=FALSE )
	invisible(tables)
}


# Utility function.
# DEPRECATED
# Make a starting point table list of tables available which can then be edited.
# This one has different types of table being built.
make.fancy.table = function( file=TABLE_FILENAME, N=75, C=25 ) {
  ## the tables available
  tables = data.frame( ID = 1:N, 
    name=(paste( c(rep("Cch",C), rep("Tbl",N-C)), 1:N, sep=" #" )),
    groupOK = c(rep(FALSE,N) ),
    statOK = c(rep(TRUE,N)),
    quality = 1, stringsAsFactors=TRUE )
  tables$quality[ sample( N, N/3 ) ] = 2
  tables$quality[ sample( N, N/5 ) ] = 3
  tables$groupOK[ sample(N, N/3) ] = TRUE
  tables$statOK[ sample( N, N/4 ) ] = FALSE
  ##  tables$name = paste( tables$name, tables$ID )
  ##	tables = tables[ order(tables$quality, decreasing=TRUE), ]

  write.csv( tables, file=file, quote=FALSE, row.names=FALSE )
  tables
}


# Generate table schedules given a collection of matches (from the match 
# program
generate.tables = function( matches, tables ) {
	
	stopifnot( !is.null( tables )) 
	stopifnot( sum( duplicated( tables$name ) ) == 0 )
	
	cat( "We have this many tables: ", nrow(tables), "\n" )
	cat( "We have this many groupOK tables: ", sum(tables$groupOK), "\n" )
	tables = tables[ order(tables$quality,decreasing=TRUE), ]
	
	# return rownumbers of daters still left to assign
	daters.left = function( df ) {
		(1:nrow(df))[ df$table == "" ]
	}
	
	# return rownumbers of tables still left to assign
	tables.left = function( tables, cur ) {
		(1:nrow(tables))[ !(tables$name %in% cur) ]
	}
	
	checkStat = function( df ) {
		tbles = df$table[ df$stat.x | df$stat.y ]
		all( tables$statOK[ tables$name %in% tbles ] == TRUE )
	}
	checkGroup = function( df ) {
		tbles = df$table[ df$is_group.x | df$is_group.y ]
		all( tables$groupOK[ tables$name %in% tbles ] == TRUE )
	}
	
	
	# return list of N table names that are not assigned to cur
	# groupOnly if tables need to be group tables
	# param: cur -- current assignment of tables for the round.  I.e, list of tables 
	#              already assigned (with several "" for unassigned slots)
	grab.tables = function( tables, cur, forwho, group.only=FALSE, stat.only=FALSE ) {
		if ( is.logical(forwho) ) {
			N = sum(forwho)
		} else {
			N = length(forwho)
		}
		if ( N > 0 ) {
#			browser()
			tables = tables[ !(tables$name %in% cur), ]  # ditch taken tables
			if ( group.only ) {
				tables = subset( tables, groupOK )
			}
			if ( stat.only ) {
				tables = subset( tables, statOK )
			}
			if ( nrow(tables) < N ) {
                          cat( "\nTABLE FILE ERROR\n# tables of given type too few: Open tables: ", nrow(tables), " N=", N,
                              " group=", group.only,
                              " stat=", stat.only, "\n" )
                          cat( "Most likely fix: add some group tables or stationary-ok tables to table file\n" )
			}
			stopifnot( nrow(tables) >= N )
		
			# take top N of remaining tables.  Return their names
			tables[1:N,"name"]
		} else {
			# No tables needed.  Return empty list.
			as.character( c() )
		}
	}

	# pull folks that need to get tables.  
	# param: col is which columns of the date table to look at. 
	#        (dater A or dater B)
	#        stat, group: to only look at people who are stationary or 
	#                        groups
	#        seated: true if only interested in folks who had
	#             a seat in the previous round.
	# return: list with up to two elements:
	#     folks: the row numbers in dt to give tables to next
	#     seats: if seated=TRUE, will return the tables of the people
	#            found (so they inherit their old table)
	grab.folks = function( dt, col=c("A","B"), 
				stat=FALSE, group=FALSE, seated=FALSE) {
		col = match.arg(col)
		
		if ( col=="A" ) {
			dt = dt[ c( "A", "stat.x", "is_group.x", "oldSeat.x", "table" ) ]
		} else {
			dt = dt[ c( "B", "stat.y", "is_group.y", "oldSeat.y", "table" ) ]		}
		names(dt) = c("P", "stat", "is_group", "oldSeat", "table" )
		
		# First we figure out who we are getting tables for
		# List of folks we are looking for tables for
		okay = rep( TRUE, nrow(dt) )
		
		# Keep only stat folks if desired.
		if ( stat ) {
			okay[!dt$stat] = FALSE
		}
		# Keep only groups if desired
		if ( group ) {
			okay[!dt$is_group] = FALSE
		}
		
		# drop folks who already have a table
		okay[ dt$table != "" ] = FALSE
		
		# drop folks who weren't seated prev round, if desired
		if ( seated ) {
			okay[dt$oldSeat == ""] = FALSE
			# if old seat gone
			okay[dt$oldSeat %in% dt$table] = FALSE 			# no simultanious assigning, so if we have two folks
			# with same table in prev round, we drop the second folk
			okay[ okay ] = !duplicated( dt$oldSeat[okay] ) 
		}
		
		folks=(1:nrow(dt))[ okay ]
		if ( seated ) {
			list( folks=folks, seats=dt$oldSeat[folks] )
		} else {
			list( folks=folks, seats=NULL )
		}
	}
	
	# run the grab folks and grab tables thing for both A and B
	# If seated=TRUE the get old seats back from grab.folks and use those,
	#                otherwise get fresh tables from the pool
	# This method passes along stat and group flags.
	# Return: updated df with table names filled in.
	two.step = function( df, stat=FALSE, group=FALSE, seated=FALSE ) {
		f = grab.folks(df, "A", stat=stat, group=group, seated=seated )
   	seats=f$seats
   	f = f$folks
   	if ( length(f) > 0 ) {
   			if ( seated ) {
   				stopifnot( length(f) == length(seats) )
   				df$table[f] = seats
   			} else {
   				df$table[f] = grab.tables(tables, df$table, f, 
   										group.only=group, stat.only=stat)
   			}
		}
		f = grab.folks(df, "B", stat=stat, group=group, seated=seated )
   	seats=f$seats
   	f = f$folks
   	if ( length(f) > 0 ) {
   			if ( seated ) {
   				stopifnot( length(f) == length(seats) )
   				df$table[f] = seats
   			} else {
   				df$table[f] = grab.tables(tables,df$table,f, 
   										group.only=group, stat.only=stat)
   			}
   	}
   	df
	} # end two.step
	
	stopifnot( !is.null( P$stat ) )
	stopifnot( !is.null( P$is_group ) )
	stopifnot( all( P$stat %in% c(0,1) ) )
	stopifnot( all( P$is_group %in% c(0,1) ) )
	
		
	tbles = list()
	# Iterate through the rounds of dating
  	for ( nx in 1:length(matches) ) {

		x = matches[[nx]]
   	if ( (num.dates <- length( x )) != 0 ) {
    		df = as.data.frame( matrix( unlist(x), ncol=4, byrow=TRUE ),
        						stringsAsFactors=FALSE )
      		names(df) = c("A","B","type","bond")
       	
       		# who are on the dates?
       		df = merge( df, P[c("personID","is_group","stat")], by.x = "A", by.y="personID", all.x=TRUE )
      		df = merge( df, P[c("personID","is_group","stat")], by.x = "B", by.y="personID", all.x=TRUE )
     		     		
     		df$table = ""
     		if ( num.dates > nrow(tables) ) {
     			stop( "We have this many dates", num.dates, ", i.e. more dates than tables.\n")
     		}
     	
     	if ( nx == 1 ) {  # first round
			needStat = df$stat.x | df$stat.y
			df$table[needStat] = grab.tables(tables, df$table, needStat, stat.only=TRUE)
			needGrp = !needStat & (df$is_group.x | df$is_group.y)
			df$table[needGrp] = grab.tables(tables, df$table, needGrp, group.only=TRUE)
			rest = !(needStat | needGrp) 
			df$table[rest] = grab.tables(tables,df$table,rest)
			      	
     	} else {
 		 	# match tables, try to keep folks in seats from previous rounds
     		pv = tbles[[nx-1]][c("A","B","table")]
     		pvA = pv[c(1,3)]
     		pvB = pv[c(2,3)]
     		names(pvA) <- names(pvB) <- c("P","oldSeat")  
     		pv = rbind(pvA,pvB)   
     		df = merge( df, pv, by.x="A",by.y="P", all.x=TRUE)
     		df = merge( df, pv, by.x="B",by.y="P", all.x=TRUE )

     		# stat folks who had seats in prior get to stay.
     		#  By end of this, stat folks will be
     		#  assigned seats, if they had dated previous round.
     		df = two.step( df, stat=TRUE, seated=TRUE )
     		
     		# Same as above, but for groups
     		df = two.step( df, group=TRUE, seated=TRUE )
	
			# now assign to any stationary folks who did not get 
			# a table.
			df = two.step( df, stat=TRUE, seated=FALSE )
   		
   		# now assign any free-floating groups who did not get
   		# a table.
   		df = two.step( df, group=TRUE, seated=FALSE )
   			
   		# Now seat any previously seated folks.
   		df = two.step( df, seated=TRUE )
   			
   		# now assign everyone else.
   		df = two.step( df, seated=FALSE )
  		 } 
    } else {
   		# no tables needed.
    		df = data.frame( A=c(), B=c(), type=c(), table=c() )
    }
    stopifnot( all( df$table != "" ) )
    stopifnot( all( !duplicated(df$table) ) )
    stopifnot( checkStat(df) )
    stopifnot( checkGroup(df) )
    tbles[[nx]] = df[ c("A","B","type","table") ]
  }

  num.tables = max( sapply( tbles, nrow ) )

  cat( "NUMBER OF TABLES USED = ", num.tables, ".\n" )
  
  tbles
}


