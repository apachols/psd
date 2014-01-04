## Functions to 
## Load the records stored in the sqlite database into a dataframe 'dat' 
## and then print out the demographic information.

## NOTE: a setup.R file must be sourced before running
##       this script


mysource = function( rfile ) {
  source( paste( R_SOURCE_DIR, rfile, sep="" ) )
}

open_database = function() {
  library( "RSQLite" )

  ## create a SQLite instance and create one connection.
  m <- dbDriver("SQLite")
  
  ## initialize a new database to a tempfile and copy some data.frame
  ## from the base package into it
  con <- dbConnect(m, dbname = DATABASE_FILENAME)

  ##dbListTables(con)

  con
}


## VARIABLES EXPECTED/NEEDED BY R CODE
## [1] "personID"   "timestamp"  "group"      "lookGroup"  "friendship"
## [6] "stat"       "noPrimary"  "fromEB"     "fromSB"     "fromNB"    
##[11] "fromSF"     "fromPN"     "fromSE"     "referred"   "friends"   
##[16] "geekCode"   "coming"     "notes"      "oneway"     "matches"   
##[21] "first"      "last"       "isG.M"      "isG.W"    "isTransM"  
##[26] "isTransW"   "isGQ"       "gender"     "age"        "isKinky"   
##[31] "lookM"      "lookW"      "lookTransM" "lookTransW" "lookGQ"    
##[36] "lookNone"   "lookGender" "lookKink"   "minAge"     "maxAge"   


handle_select = function( include=c("NotNo", "Pending", "In","Paid","Test","All")  ) {
  include = match.arg(include)
  select <- switch( include,
                   "NotNo" = "AND cancelled=0",
                   "Paid" = "AND paid=1",
                   "Pending" = "AND (pending=1 OR paid=1) AND cancelled=0",
                   "In" = "AND here=1",
                   "Test" = "LIMIT 20",
                   "All" = {
                     warning( "INCLUDING ALL PEOPLE -- IGNORING PAY AND IN LIST\n" )
                     "" 
                   } )
  select
}




## Load all people
loadPeople = function( con, include ) {
  
  qry = sprintf( "SELECT rr.psdid as personID, rr.event, seek_groups as lookGroup, groups_match_all, friend_dates, rr.event, seeking_primary as noPrimary, location, referred_by, pals, first_name, last_name, gender, age, kinky as isKinky, seek_gender, seek_age_min, seek_age_max, seek_kinkiness as lookKink, rr.oneway, rr.matches
     FROM register_regrecord rr, register_regrecord_people con, register_person p
     WHERE rr.id = con.regrecord_id AND con.person_id = p.id AND  rr.event= '%s' %s",
    EVENT_NAME, handle_select( include ) )
  
  rs <- dbSendQuery(con, qry)
  dat <- fetch(rs, n = -1)      ## extract all remaining data
  
  ## pull locations
  pull.locations = function( G, prefix ) {
  	gends = strsplit( G, "," )
    gends = sapply( gends, function( x ) {
    	gg = strsplit( x, "-" )
    	sapply( gg, function( r ) { r[[1]] } )
    } )
    
    gs = unique( do.call( c, gends ) )
   # print( gs )
	 res = t( sapply( gends, function( X ) { 
     	 !is.na(pmatch( gs, X )) 
    } ) )
    colnames(res) = paste( prefix, gs, sep="" )
    
    res
  }

  gends = pull.locations( dat$gender, "isG." )
  dat = cbind( dat, gends )
  
  lookgends = pull.locations( dat$seek_gender, "lookG." )
  dat = cbind( dat, lookgends )
  
  locs = pull.locations( dat$location, prefix="from")
  dat = cbind( dat, locs )
  
  ## identify groups
  dups = dat$personID[ duplicated( dat$personID ) ]
  dat$group = dat$personID %in% dups

  ## clean up
  dbClearResult(rs)
  
  dat
}



## Load regrecords
loadRegRecords = function( con, include ) {
  
  qry = sprintf( "SELECT rr.psdid as personID, nickname as pubname, event, is_group, count(*) as group_size, seek_groups as lookGroup, groups_match_all, friend_dates, stationary as stat, location, email  FROM register_regrecord rr, register_regrecord_people con, register_person p
     WHERE rr.id = con.regrecord_id AND con.person_id = p.id AND  rr.event= '%s' %s GROUP BY rr.psdid;",
    EVENT_NAME, handle_select( include ) )
  
  rs <- dbSendQuery(con, qry)
  dat <- fetch(rs, n = -1)      ## extract all remaining data

  if ( nrow(dat ) == 0) {
  	stop( "No records pulled given constraints of ", include, " from database\n" )
  }
  
  
  #print( names(dat) )
  
  ## generate genders
  genderparse = function( G, gs=c("M","F","TM","TF","Q") ) {
    gends = strsplit( G, "," )
    t( sapply( gends, function( X ) { 
      !is.na(pmatch( gs, X )) } ) )
  }

  locs = genderparse( dat$location, lss<-c("SF","NB","EB","PN","SB","SE") )
  colnames(locs) = paste("from",lss, sep="")
  dat = cbind( dat, locs )
  
  ## clean up
  dbClearResult(rs)
  
  rownames(dat) = dat$personID
  
  dat
}

loadNametags = function( con, event, psdids, order.tags=TRUE) {
  
  forWho = paste( psdids, collapse="', '" )
  
  qry = sprintf( "SELECT rr.nickname as pubname, rr.psdid as personID, p.first_name, p.last_name, email FROM register_regrecord rr, register_regrecord_people con, register_person p
     WHERE rr.id = con.regrecord_id AND con.person_id = p.id AND  rr.event= '%s' AND rr.psdid IN ('%s') ORDER BY first_name;", event, forWho )
  
  rs <- dbSendQuery(con, qry)
  matches <- fetch(rs, n = -1)      ## extract all remaining data
  dbClearResult(rs)
  
  if ( order.tags ) {
  	matches = matches[ order(toupper(matches $pubname), matches $personID), ]
  }
  
  matches     
}

loadMatrices = function( con, event, psdids ) {

  forWho = paste( psdids, collapse="', '" )
  
  qry = sprintf( "SELECT * from register_matchrecord where event='%s' and psdid1 in ('%s') AND psdid2 IN ('%s');", event, forWho, forWho )
  
  rs <- dbSendQuery(con, qry)
  matches <- fetch(rs, n = -1)      ## extract all remaining data
  
  str_mat = gay_mat = matrix( 0, nrow=length(psdids), ncol=length(psdids) )
  
  pd1 = as.numeric( factor( matches$psdid1, levels=psdids ) )
  pd2 = as.numeric( factor( matches$psdid2, levels=psdids ) )
  
  str_mat[ cbind( pd1, pd2 ) ] = ifelse( matches$str_ok, matches$match, 0 )
  rownames(str_mat) = colnames(str_mat) = psdids
  
  gay_mat[ cbind( pd1, pd2 ) ] = ifelse( matches$gay_ok, matches$match, 0 )
  rownames(gay_mat) = colnames(gay_mat) = psdids		
  list( gay.mat=gay_mat, str.mat=str_mat )
}




loadDateTable = function( con, event ) {
  
  qry = sprintf( "SELECT * from register_daterecord where event='%s';", event )
  
  rs <- dbSendQuery(con, qry)
  dates <- fetch(rs, n = -1)      ## extract all remaining data
  
  nrnd = max(dates$round )
  nrnd
  psdids = unique( dates$psdid )
  psdids = sort(psdids)
  dm = matrix( "none", nrow = length(psdids), ncol=nrnd )
  rownames(dm) = psdids
  colnames(dm) = paste("Rnd", 1:nrnd, sep="")
  dtype = dm
  colnames(dtype) = paste("Type", 1:nrnd, sep="")
  
  for ( i in 1:nrow(dates) ) {
  	  dm[ dates$psdid[i], dates$round[i] ] = dates$other_psdid[i]
	  if (dates$friend_date[i]) {
	  		dtype[ dates$psdid[i], dates$round[i] ] = "(F)"
	  }
  }
  
  dtab = as.data.frame( cbind( dm, dtype ) )
  
  P2 = P[ c("personID","pubname") ]
  dtab$personID = rownames(dtab)
  dtab = merge( P2, dtab, by="personID", all.y=TRUE )
  
  fintab = as.data.frame( dm )
  fintab$personID = rownames(fintab)
  P2 = P[ c("personID","pubname","email") ]
  P2$comments = " "
  ftab = merge( P2, fintab, by="personID", all.y=TRUE )
  
  list( date_table=dtab, final_matches=ftab )
}






## Load break matrix --- this is boolean matrix of
## people to not ever seat next to each other, friend or otherwise.
loadBreakMatrix = function( con, psdids, which_mat=c("both","additionals","datehistory") ) {

	which_mat = match.arg(which_mat)
	
  forWho = paste( psdids, collapse="', '" )
  
  if ( which_mat != "datehistory" ) {
  qry = sprintf( "SELECT psdid as MatchA,other_psdid as MatchB from register_breakrecord where psdid in ('%s') AND other_psdid IN ('%s');", forWho, forWho )
  
  rs <- dbSendQuery(con, qry)
  matches <- fetch(rs, n = -1)      ## extract all remaining data
  }
  
  if ( which_mat != "additionals" ) {
  qry = sprintf( "SELECT psdid as MatchA,other_psdid as MatchB from register_daterecord where psdid in ('%s') AND other_psdid IN ('%s');", forWho, forWho )
  
  rs <- dbSendQuery(con, qry)
  matches2 <- fetch(rs, n = -1)      ## extract all remaining data
  }
  
  if ( which_mat == "both" ) {
	  matches = rbind( matches, matches2 )
  } else if ( which_mat == "datehistory" ) {
  	  matches = matches2
  }
  
  break_mat = matrix( 0, nrow=length(psdids), ncol=length(psdids) )
  
  pd1 = as.numeric( factor( matches$MatchA, levels=psdids ) )
  pd2 = as.numeric( factor( matches$MatchB, levels=psdids ) )
  
  break_mat[ cbind( pd1, pd2 ) ] = 1
  rownames(break_mat) = colnames(break_mat) = psdids
  
  break_mat
}
# Test code:
# b = loadBreakMatrix( con, c( "SP488", "AW245", "LM360", "GB157" ), which_mat="ad" )





## Load table of date tables.
loadTableTable = function( con, event ) {
	
  qry = sprintf( "SELECT tr.id as ID,name,groupOK,statOK,quality from register_tablerecord as tr, register_tablelistrecord as rl where tr.group_id=rl.id and rl.event='%s';", event )


  
  rs <- dbSendQuery(con, qry)
  matches <- fetch(rs, n = -1)      ## extract all remaining data
  dbClearResult(rs)
  matches$groupOK = as.logical(matches$groupOK)
  matches$statOK = as.logical(matches$statOK)
  matches
}
# Test code:
# b = loadBreakMatrix( con, c( "SP488", "AW245", "LM360", "GB157" ), which_mat="ad" )

test_load_table = function() {
  con = open_database()
  dat = loadTableTable( con, event="revival1" )
  head(dat)
  tail(dat)
  close_database( con )
}  



close_database = function( con ) {
  dbDisconnect(con)
}







#########################################################################
# save_data_table
#
# This code goes through a data table and enters all dates into a 
# series of date records
#
# Make a list of all ID pairs that have ever dated in the past, stash 
# them
#
# Param: table_name   csv file for where data table is stored
#                     OR the dts table from the make.matches() function
#########################################################################
save_date_table = function( table_name=paste( OLD_DATA_PATH,"run6_csv/date_table.csv",sep=""),
			 con, event = "macaw1", erase_old = FALSE ) {
	tabs <- dbListTables(con)
	stopifnot( "register_daterecord" %in% tabs )

  if ( is.character(table_name ) ) {
		cat( "Loading dating history from ", table_name, "\n" )
  
	  	## Load date matrix & personID list
	  	DT = read.csv( table_name, stringsAsFactors=FALSE)
  } else {
  	  DT = table_name
  }
  nms = names(DT)[grep( "Rnd", names(DT) )]
  tnms = names(DT)[grep("Type",names(DT) )]
  tbls = names(DT)[grep("table",names(DT) )]
  rnds = names(DT)[grep("Rnd",names(DT))]
  rnds = substr(rnds, 4,10)
  DTS = DT[nms]
  DTS = as.matrix(DTS)
  pids = DT$personID

  if ( erase_old ) {
  	   # remove old records for this event
  	   delqry = sprintf( "DELETE FROM register_daterecord WHERE event = '%s'", event )
  	   dbGetQuery( con, delqry )
  }
  
  ## write out all dates
  for ( i in 1:nrow(DTS) ) {
  		for ( j in 1:ncol(DTS) ) {
  			mtch = DTS[i,j]
  			if ( mtch != "none" && mtch != "" ) {
  				friend = 0 + (DT[ i, tnms[[j]] ] %in% c("friend", "(F)"))
  		
  				tablename = DT[ i, tbls[[j]] ]
	  			qry = sprintf( "INSERT INTO register_daterecord(friend_date, psdid,other_psdid,round,event,'table') VALUES (%s, '%s', '%s', %s, '%s', '%s');", friend, pids[[i]], mtch, rnds[[j]], event, tablename )
	  			dbGetQuery( con, qry )
	  		}
  		}
  	}
}


#############################################################################
## test code.
#############################################################################

print_demog = function( include ) {

  con = open_database()
  dat = loadPeople( con, include=include )
  close_database( con )

  mysource("demographics.R")
  ldem = load.demographics(dat)
  print(ldem)
  
  invisible(ldem)
}  


test_load_people = function() {
  print_demog( include="NotNo" )
}  



#############################################################################
## Match setup code
#############################################################################



### Load the matrices for scheduling from database, symmetrize them
### and get everything ready by writing variables to the global 
### environment. 
build.event.environment = function( db = DATABASE_FILENAME, event=EVENT_NAME,
		INCLUDE_ALL = c("NotNo", "Pending", "In","Paid","Test","All"),
		collapse.groups=TRUE ) {
							
	# Set up the database
	con <- open_database()
   	
	## Make a matrix of two-way matches out of the one-way match matrix
	bidirectional.clean = function( M, avg = c("min", "mean", "product") ) {
		avg = match.arg(avg)
		
		# match links if they are bi-directional
		if ( avg=="mean" ) {
			M = (M + t(M)) / 2
		} else if (avg =="product" ) {
			M = pmin( M, t(M) ) * pmax( M, t(M) )
		} else {
			M = pmin( M, t(M) )
		}
		diag(M) = 0
	
		M
	}
	
	
	## If number of likes in m1 is too small, blend in the likes from
	## m2---NOTE: do by row.
	blend.matrix = function( m1, m2, fix.level=4 ) {
		tots = apply( m1, 1, sum )
		fixs = tots < fix.level
		if ( length( fixs ) > 0 ) {
			m1[ fixs, ] = pmax( 100 * m1[ fixs, ], m2[ fixs, ] )
		}
		m1
	}
	

    INCLUDE_ALL = match.arg(INCLUDE_ALL)
    cat( "Inclusion mode = ", INCLUDE_ALL, "\n" )

    P = loadRegRecords( con, include=INCLUDE_ALL )
    cat( "Selected", nrow(P), "records\n" )

  
  matrices = loadMatrices( con, event, P$personID )

  
  gay.mat = matrices$gay.mat
  str.mat = matrices$str.mat
  breakMatrix = loadBreakMatrix( con, P$personID )
  
	close_database( con )

  
  gay.mat[breakMatrix] = FALSE
  str.mat[breakMatrix] = FALSE
 
  stopifnot( all( rownames(gay.mat) == colnames(gay.mat) ) )
  stopifnot( all( rownames(P) == rownames(gay.mat) ) )
  stopifnot( all( rownames(str.mat) == rownames(gay.mat) ) )
  stopifnot( all( colnames(str.mat) == colnames(gay.mat) ) )
   

  all.mat = gay.mat | str.mat
  friend.mat = !( all.mat )
  friend.mat[breakMatrix] = FALSE
  friend.mat[ P$friend_dates == 0, ] = 0
  
  gm = blend.matrix( gay.mat, str.mat )
  str.mat = blend.matrix( str.mat, gay.mat )
  gay.mat = gm
  
  gay.mat = bidirectional.clean( gay.mat, avg="prod" )
  str.mat = bidirectional.clean( str.mat, avg="prod" )
  all.mat = bidirectional.clean( all.mat, avg="min" )
  friend.mat = bidirectional.clean( friend.mat, avg="min" )

  ## count number of matches people have
  P$matches = apply( all.mat > 0, 1, sum )

  ## and who!
  #P$who.gay = apply( gay.mat, 2, function(x) { 
  #	paste( rownames(gay.mat)[x > 0], collapse=" ", sep=" " ) } )
  #P$who.str = apply( str.mat, 2, function(x) { 
  #	paste( rownames(str.mat)[x > 0], collapse=" ", sep=" " ) } )

                                        ## sort for ease of reading
  # P2 = P[ order( P$group, P$isG.M1, P$age1, P$matches ), ]
  #  save.file( P, collapse.groups )
  rownames(P) = P$personID

  gay.mat <<- gay.mat
  str.mat <<- str.mat
  all.mat <<- all.mat
  friend.mat <<- friend.mat
  P <<- P

  "exported all variables to global environment - hack"
}



make_nametag_file = function( con, event, psdids= rownames(gay.mat) ) {
	  ## Make nametag and final match lookup file ##
  nt = loadNametags( con, event, psdids )
  #write.csv( nt, file=NAMETAGS_FILENAME, row.names=FALSE,quote=FALSE )
  cat( "\n\nINSTRUCTIONS:\nCUT AND PASTE INTO A TEXT FILE, MAKE IT CSV FILE, THEN DO MAIL MERGE IN SOMETHING LIKE MS WORD\n\n" )
  write.csv( nt, row.names=FALSE,quote=FALSE )
  cat( "\n\n\n" )
  
  cat( "Name tag file written\n" )
}

