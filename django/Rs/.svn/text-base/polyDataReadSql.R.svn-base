## DEPRICATED!!!


## Load the data from the output of the java files into some R data frames
## Requires the matrix files all-gay.csv, all-str.csv and the allFolks.csv
## Files
## BUT ALSO LOADS DATA FROM THE SQLITE DATABASE!
##
## In particular, load gay, str, all, and friendship matrix into environment
## Also load 'P' dataframe of all people into the environment.
## WARNING: This script makes global variables!

# Some setup needs to be sourced first!
#source( "Rs/setup.R" )
source( "Rs/sqliteLoader.R" )

### read in Java-made files  (matrix.csv and allFolks.csv made by RegParser2)
load.data = function( db = DATABASE_FILENAME, event=EVENT_NAME,
		INCLUDE_ALL = c("NotNo", "Pending", "In","Paid","Test","All"),
		collapse.groups=TRUE ) {
							
	# Set up the database
	con <- open_database()
   	
## Make a matrix of two-way matches out of the one-way match matrix
bidirectional.clean = function( M, avg = FALSE) {
	# match links if they are bi-directional
	if ( avg ) {
		M = (M + t(M)) / 2
	} else {
		M = pmin( M, t(M) )
	}
	diag(M) = 0
	
	M
}


add.hand.links = function( addLinks, mat, no.adding=FALSE, 
						  no.warning=FALSE ) {
  
  warnings = c()
  addMiss = function( warnings, whoA, whoB ) {
  	paste( warnings, paste( whoA, whoB, sep=" or " ), "; " )
  }
  broke = 0
  ## Add links from the addl list
  if ( !is.null( addLinks ) && (nrow(addLinks)>0) ) {
    for ( i in 1:nrow(addLinks) ) {
      tp = addLinks[i,]
      if ( !( tp[[1]] %in% rownames(mat) ) || !( tp[[2]] %in% rownames(mat) ) ) {
        if ( !no.warning ) {
          warnings = addMiss( warnings,  tp[[1]], tp[[2]] )
          cat( "Missing: ", tp[[1]], " or ", tp[[2]], "\n" )
        }
      } else {
        if ( tp[[3]] == "y" ) {
          if ( !no.adding ) {
			 cat( "Adding date possiblity ", tp[[1]], tp[[2]], "\n" )
          	 mat[[ tp[[1]], tp[[2]] ]] = mat[[ tp[[2]], tp[[1]] ]] = 1
          	 
          }
        } else {
          ##cat( "Breaking ", tp[[1]], tp[[2]], "\n" )       
          if ( mat[[ tp[[1]], tp[[2]] ]] != 0 && mat[[ tp[[2]], tp[[1]] ]] != 0 ) {
          	broke = broke + 1
          }
          mat[[ tp[[1]], tp[[2]] ]] = mat[[ tp[[2]], tp[[1]] ]] = 0
        }
      }
    }
  }
  cat( "Added/Broke ", broke, " links out of ", nrow(addLinks), " on list\n" )
 
  if ( !no.warning && length( warnings ) > 0 ) {
  	warning( warnings )
  }
   
  ## return the updated matrix
  mat
}


loadAdditionalLinks = function( forWho ) {

	if (  "additionals" %in% dbListTables(con) ) {

		forWho = paste( forWho, collapse="', '" )
	
		qry = sprintf( "SELECT MatchA, MatchB, include, WHY from additionals WHERE MatchA IN ('%s') AND MatchB IN ('%s')", forWho, forWho )
		rs = dbSendQuery( con, qry )
		dat <- fetch(rs, n = -1)  
	
		dat
	} else {
		warning( "NO ADDITIONALS TABLE" )
		c()
	}
}

loadPastDateLinks = function( forWho ) {

	if (  "register_daterecord" %in% dbListTables(con) ) {

		forWho = paste( forWho, collapse="', '" )
	
		qry = sprintf( "SELECT psdid, other_psdid, round, event FROM register_daterecord WHERE psdid IN ('%s') AND other_psdid IN ('%s')", forWho, forWho )
		rs = dbSendQuery( con, qry )
		dat <- fetch(rs, n = -1)  
		if ( nrow(dat) > 0 ) {
			names(dat) = c( "MatchA","MatchB","include","WHY")
			dat$include = "n"
			dat
		} else {
			warning( "NO DATES FOUND IN DATE RECORD TABLE (register_daterecord)" )
			data.frame( MatchA=c(), MatchB=c(), include=c(), WHY=c() )
		}
		
	} else {
		warning( "NO DATE RECORD TABLE (register_daterecord)" )
		data.frame( MatchA=c(), MatchB=c(), include=c(), WHY=c() )
	}
}

							
							
  	   	
    INCLUDE_ALL = match.arg(INCLUDE_ALL)
    cat( "Inclusion mode = ", INCLUDE_ALL, "\n" )

    P = loadRegRecords( con, include=INCLUDE_ALL )
    cat( "Selected", nrow(P), "records\n" )

  
  matrices = loadMatrices( con, event, P$personID )
  
  gay.mat = matrices$gay.mat
  str.mat = matrices$str.mat
  breakMatrix = loadBreakMatrix( con, P$personID )
  
  gay.mat[breakMatrix] = FALSE
  str.mat[breakMatrix] = FALSE
 
  stopifnot( all( rownames(gay.mat) == colnames(gay.mat) ) )
  stopifnot( all( rownames(P) == rownames(gay.mat) ) )
  stopifnot( all( rownames(str.mat) == rownames(gay.mat) ) )
  stopifnot( all( colnames(str.mat) == colnames(gay.mat) ) )
   
  ## Make nametag and final match lookup file ##
  nt = loadNametags( con, event, rownames(gay.mat) )
  nt = nt[ order(toupper(nt$pubname), nt$personID), ]
  write.csv( nt, file=NAMETAGS_FILENAME, row.names=FALSE,quote=FALSE )
  cat( "Name tag file written\n" )


  all.mat = gay.mat | str.mat
  friend.mat = !( all.mat )
  friend.mat[breakMatrix] = FALSE
  friend.mat[ P$friendship != "yes", ] = 0

  P$oneway = apply( all.mat, 1, sum )
  gay.mat = bidirectional.clean( gay.mat, avg=FALSE )
  str.mat = bidirectional.clean( str.mat, avg=FALSE )
  all.mat = bidirectional.clean( all.mat, avg=FALSE )
  friend.mat = bidirectional.clean( friend.mat, avg=FALSE )

  ## count number of matches people have
  P$matches = apply( all.mat > 0, 1, sum )

  ## and who!
  P$who.gay = apply( gay.mat, 2, function(x) { 
  	paste( rownames(gay.mat)[x > 0], collapse=" ", sep=" " ) } )
  P$who.str = apply( str.mat, 2, function(x) { 
  	paste( rownames(str.mat)[x > 0], collapse=" ", sep=" " ) } )

                                        ## sort for ease of reading
  # P2 = P[ order( P$group, P$isMan1, P$age1, P$matches ), ]
  #  save.file( P, collapse.groups )
  rownames(P) = P$personID

  gay.mat <<- gay.mat
  str.mat <<- str.mat
  all.mat <<- all.mat
  friend.mat <<- friend.mat
  P <<- P

  "exported all variables to global environment - hack"
}






save.file = function( P, collapse.groups=FALSE, file=ALLCOUNTS_FILENAME,
				orderBy=c("group","isMan1","matches") ) {
	
    P2 =  P[ do.call( order, P[orderBy] ), ]

                                        ## names(P)[29:48]
                                        ## strip off triads and quads--none in this database.
  #warning( "Removing quads (if any) from allCounts.csv" )
  killCols = c(  pmatch("remarks",names(P2)), #pmatch("email",names(P2)),
  							pmatch("friends",names(P2)),
  							pmatch("referred",names(P2)),
  							pmatch("addList",names(P2)) )
  killCols = killCols[!is.na(killCols)]
  
  if ( collapse.groups ) {
  		
	killCols = c( killCols, grep( "[234]$", names(P2) ),
  						grep("from",names(P2) ) )
  	nm1 = grep( "1$", names(P2) )
	nm2 = grep( "2$", names(P2) )
	nm3 = grep( "3$", names(P2) )
	nonEmpty = function( X ) {
		!is.na(X) & (X != "") & (X != 0)
	}

	for ( i in 1:length(nm1) ) {
		n1 = nm1[i]
		n2 = nm2[i]
		n3 = nm3[i]
		P2[n1] = ifelse( nonEmpty(P2[[n2]]), paste( P2[[n1]], P2[[n2]], sep="/" ), P2[[n1]] )
		P2[n1] = ifelse( nonEmpty(P2[[n3]]), paste( P2[[n1]], P2[[n3]], sep="/" ), P2[[n1]] )
	}
	
	P2$group = ifelse( nonEmpty(P2$group), paste( P2$group, P2$groupStyle, sep="-" ), P2$group )
	# remove specific genders and look genders
	n = as.numeric( unlist( sapply( c( "groupStyle","isMan", "isWoman", "isTransM", "isTransW", "isGQ","lookM", "lookW", "lookTransM", "lookTransW", "lookGQ", "lookNone" ), grep, names(P2), simplify=FALSE ) ) )
	killCols = c( killCols, n )
  }
							
  write.csv( P2[-killCols], file=file, row.names=FALSE,quote=FALSE )
}



## END of Data Cleaning and Organizing ##


