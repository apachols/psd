
#############################################################################
## This code connects all the names in the current database to old names from 
## the pre-database events.  It then translates the new IDs to old IDs to 
## discover who has previously dated whom, and saves all of that.
#############################################################################

# Need to source a setup before running.
#source( "Rs/setup.R" )


library( "RSQLite" )
m <- dbDriver("SQLite")

con <- dbConnect(m, dbname = DATABASE_FILENAME)

print( dbListTables(con) )

# helper method
genfullfile = function( file, path=OLD_DATA_PATH ) {
	paste( path, file, sep="" )
}


################################################################################
# This code goes through all the prior-db world files and makes a sql table
# listing all pairs of IDs (IDs augmented by a -run with run=1,2,... to make
# them unique across all events) that ever dated.
#
# It also adds in all the hand-built "date-breaking" links from the past.
################################################################################

cat( "\nGrabbing all past matches\n" )

if ( "old_past_dates" %in% dbListTables(con) ) {
	dbGetQuery( con, "DROP TABLE old_past_dates;" )
}
	
dbGetQuery( con, "CREATE TABLE old_past_dates( opd_id INTEGER PRIMARY KEY, idA char(10), idB char(10), old_event char(20) )" )
	

## Make a list of all ID pairs that have ever dated in the past.
old_date_finder = function( old_table_name, con, event = "unknown" ) {
  old_table_name=genfullfile( old_table_name )
  
  ## Load old date matrix & personID list
  DT = read.csv( old_table_name, stringsAsFactors=FALSE)
  nms = names(DT)[grep( "Rnd", names(DT) )]
  DTS = DT[nms]
  DTS = as.matrix(DTS)
  pids = DT$personID

  ## write out all matches
  for ( i in 1:nrow(DTS) ) {
  		for ( j in 1:ncol(DTS) ) {
  			mtch = DTS[i,j]
  			if ( mtch != "none" && mtch != "" ) {
	  			qry = sprintf( "INSERT INTO old_past_dates(idA,idB,old_event) VALUES ('%s-%s', '%s-%s', 'run %s');", pids[[i]], event, mtch, event, event )
	  			dbGetQuery( con, qry )
	  		}
  		}
  	}
}
  
old_additional_finder = function( old_table_name, con,
  event = "unknown" ) {

  old_table_name=genfullfile( old_table_name )
  
  ## Load old date matrix & personID list
  DT = read.csv( old_table_name, stringsAsFactors=FALSE)
  #print( head(DT))
  ## write out all entries
  for ( i in 1:nrow(DT) ) {
  		  qry = sprintf( "INSERT INTO old_past_dates(idA,idB,old_event) VALUES ('%s-%s', '%s-%s', 'addl %s/%s');", DT[[i,1]], event, DT[[i,2]], event, event, DT[[i,"WHY"]])
	  		dbGetQuery( con, qry )
	}
}

old_date_finder( "run1_csv/date_table.csv", con, "1" )
old_date_finder( "run2_csv/date_table.csv", con, "2" )
old_date_finder( "run3_csv/date_table.csv", con, "3" )
old_date_finder( "run4_csv/date_table.csv", con, "4" )
old_date_finder( "run5_csv/date_table.csv", con, "5" )

old_additional_finder( "run2_csv/additional.csv", con, "2" )
old_additional_finder( "run3_csv/additional.csv", con, "3" )
old_additional_finder( "run4_csv/additional.csv", con, "4" )
old_additional_finder( "run4_csv/unusedaddl.csv", con, "4" )
old_additional_finder( "run5_csv/additional.csv", con, "5" )






#############################################################################
## Collect IDs of everyone in the past with their name and email and then
## build equivelence classes of IDS based on same email and/or same first1 last1 
## (name)
#############################################################################


cat( "\nCollecting past IDs\n" )

	dat1 = read.csv( genfullfile( "run1_csv/allFolks.csv") , as.is=TRUE )
	dat1 = dat1[ c("personID","pubname","email", "first1","last1") ]
	dat1$run = 1
	head(dat1)
	
	dat2 = read.csv( genfullfile("run2_csv/namelist.csv") , as.is=TRUE )

	dat2 = dat2[ c("personID","pubname","email", "first1","last1") ]
	dat2$run = 2
	head(dat2)
	
	dat3 = read.csv( genfullfile("run3_csv/allFolks.csv") , as.is=TRUE )

	dat3 = dat3[ c("personID","pubname","email", "first1","last1") ]
	dat3$run = 3
	head(dat3)
	
	dat4 = read.csv( genfullfile("run4_csv/allRegistered.csv"), as.is=TRUE )

	dat4 = dat4[ c("personID","pubname","email", "first1","last1") ]
	dat4$run = 4
	head(dat4)
	
	dat5 = read.csv( genfullfile("run5_csv/allRegistered.csv") , as.is=TRUE )

	dat5 = dat5[ c("personID","pubname","email", "first1","last1") ]
	dat5$run = 5
	head(dat5)
	
	
	
	#### SQL LITE  -- GET CURRENT IDS
	qry = sprintf( "SELECT rr.psdid as personID, nickname as pubname, email, first_name as first1, last_name as last1 
	   FROM register_regrecord rr, register_regrecord_people con, register_person p
      WHERE rr.id = con.regrecord_id AND con.person_id = p.id AND  rr.event= '%s'", EVENT_NAME )
   rs <- dbSendQuery(con, qry)
   dat <- fetch(rs, n = -1)      # extract all remaining data
	dat$run = RUN_NUMBER

	alldat = rbind( dat1, dat2, dat3, dat4, dat5, dat )
	dd = alldat[ order( alldat$email, -alldat$run ), ]
	nrow(dd)
	
		
	dd$pureID = ifelse( dd$run == RUN_NUMBER, dd$personID, "" )
	dd$personID = paste(dd$personID, dd$run, sep="-" )
	
# Write all the old info, sorted for easy comparison (hopefully)
write.csv(dd, file=paste(CUR_DATA_PATH,"fullhistory.csv",sep=""), quote=FALSE)
ddfull = dd
 

################################################################################
cat( "Merge records based on identical email and identical 'first last' name\n" )
################################################################################

# Implementation note: the sorting is very important because it puts the 
# _real_ psdid first due to sorting by run number (and the real run has
# the largest number).

## If clumps of identical folks are in order then this will merge them 
## into single records (keeping the info from the _first_ of the clump).
## It will make a field which is a list of all the PSD IDs associated with
## that entity, seperated by a "/"
mergedups = function( dd, dupindex ) {
	dd$keep = FALSE
	idlist = list()
	ids = list( dd$personID[[1]] )
	dd$keep[[1]] = TRUE
	for ( i in 2:nrow(dd) ) {
		if ( dupindex[[i]] ) {
			ids = c( ids, dd$personID[[i]] )
		} else {
			idlist = c( idlist, list(ids) )
			ids = list( dd$personID[[i]] )
			dd$keep[[i]] = TRUE
		}
	}
	idlist = c(idlist, list(ids))
	id2l = sapply( idlist, paste, collapse="/" )
	
	dd = dd[dd$keep,]
	dd$personID = id2l
	dd$keep = NULL
	dd
}	

	cat( "Number of rows of full history:", nrow(dd), "\n" )
	
	dd$email[  dd$email == ""] = 1:(sum(dd$email==""))
	dd = dd[ order( dd$email, -dd$run ), ]
	dd = mergedups( dd, duplicated(dd$email))

	cat( "Number of rows of history post email merge:", nrow(dd), "\n" )
	
	dd$fullname = tolower( paste( dd$first1, dd$last1 ) )
	dd$first1 = dd$last1 = NULL
	dd$fullname = gsub( "[\\W]*", "", dd$fullname, perl=TRUE )
	dd = dd[ order( dd$fullname, -dd$run ), ]
	dd = mergedups( dd, duplicated(dd$fullname) )

	cat( "Number of rows of history post email and name merge:", nrow(dd), "\n" )
	
	dd = dd[ order( dd$pubname, -dd$run ), ]
	write.csv(dd, file=paste( CUR_DATA_PATH,"allhistory.csv",sep=""), quote=FALSE)


	
if  (FALSE) {
	# merge on same public name
	dd$duppub = duplicated(dd$pubname)
	sum(dd$duppub)
	table(dd$dupemail,dd$duppub)
	getwd()
	
}



################################################################################
cat( "\n  Saving the old IDs in sql\n" )
# Read in the previously generated allhistory.csv and then figure out
# who has dated whom in terms of the modern, real, psdids using the allhistory
# as a translator.
################################################################################

	library( "RSQLite" )
   m <- dbDriver("SQLite")
   tfile <- "mydb"
   con <- dbConnect(m, dbname = tfile)


	if ( "old_ids" %in% dbListTables(con) ) {
		dbGetQuery( con, "DROP TABLE old_ids;" )
	}
	
	dbGetQuery( con, "CREATE TABLE old_ids( oid_id INTEGER PRIMARY KEY, cur_id char(10), old_id char(10) )" )
 
	dl = dd #read.csv( "allhistory.csv", as.is=TRUE )
	dl = subset(dl, pureID != "" )
	nrow(dl)
	ids = strsplit( dl$personID, '/' )
	
	for ( i in 1:nrow(dl) ) {
		#cat( "Working on:\n" )
		#print( dl[i,] )
		if ( length( ids[[i]] ) > 1 ) {
			sapply( ids[[i]], function( X ) {
				if ( length( grep( paste("-",RUN_NUMBER,sep=""), X  ) ) == 0 ) {
					qry = sprintf( "INSERT INTO old_ids(cur_id, old_id) VALUES ('%s','%s')",
								dl$pureID[[i]], X )
					#print( qry )
					dbGetQuery( con, qry )
				} 
			} )
		}
	}
	
 
 	# and any extra hand-made ones
 	extras = read.csv( HANDFILE_TRANSLATIONS_FILENAME )
 	for ( i in 1:nrow(extras) ) {
		qry = sprintf( "INSERT INTO old_ids(cur_id, old_id) VALUES ('%s','%s')",
								extras$cur_id[i], extras$old_id[i] )
		dbGetQuery( con, qry )
	}
	
	



################################################################################
cat( "\n Make the additionals database\n" )
#
# This lists all links to break due to past dating history in pre-django
# times or other reasons such as friendship, etc.
################################################################################

	
	if ( "additionals" %in% dbListTables(con) ) {
		dbGetQuery( con, "DROP TABLE additionals;" )
	}

#CREATE TABLE "register_breakrecord" (
#    "id" integer NOT NULL PRIMARY KEY,
#    "friend_ok" bool NOT NULL,
#    "psdid" varchar(6) NOT NULL,
#    "other_psdid" varchar(6) NOT NULL,
#    "notes" text
#);


	qry = "INSERT INTO register_breakrecord SELECT NULL as id, 0 as friend_ok, oid1.cur_id as psdid, oid2.cur_id as other_psdid, opd.old_event as notes FROM old_past_dates opd, old_ids oid1, old_ids oid2
WHERE opd.idA=oid1.old_id AND opd.idB=oid2.old_id;"

	dbGetQuery( con, qry )
	
	# Finally, from post-database era, list of folks who mentioned other folks
	# stored in the hand-built (sigh) mention.csv
#	ext = read.csv( HANDFILE_MENTIONS_FILENAME, as.is=TRUE )
#	for ( i in 1:nrow(ext) ) {
#		qry = sprintf( "INSERT INTO register_breakrecord (friend_ok,psdid,other_psdid,notes) VALUES (0, '%s', '%s', '%s');", 
#				ext$WhoID[[i]], ext$FriendID[[i]], "mention.csv file" )
#		cat( qry, "\n" )
#		dbGetQuery( con, qry )
#	}
	
#############################################################################
## Throw out multiple records
#############################################################################
qry = "SELECT * FROM register_breakrecord"
rs <- dbSendQuery(con, qry)
   dat <- fetch(rs, n = -1)      # extract all remaining data
dbClearResult(rs)
head(dat)
ids = (dat[ duplicated(dat[c(3,4)]), ])$id
qry = paste( "DELETE FROM register_breakrecord WHERE id IN (", paste(ids,collapse=","), ")" )
qry
res = dbSendQuery(con, qry)
summary(res)
dbClearResult(rs)


#############################################################################
## Close sql connection
#############################################################################
cat( "Closing the connection\n" )
dbDisconnect( con )
