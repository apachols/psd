################################################################
##  Print out demographic information about the entire group
##  such as age spread, number of women and men, and so forth.
#################################################################


## demographic analysis
load.demographics = function( F, augment.with.finals=FALSE ) {

  GENDERS = c("M","W","TM","TW","GQ")
  
  colneeded = paste( c("isG.","lookG."), rep( GENDERS, each=2), sep="" )
  msg = setdiff( colneeded, names(F) )
  if ( length( msg ) > 0 ) {
  	F[msg] = FALSE
  	warning( "Adding null columns for missing genders in load.demographics" )
  }
 
  ## build gender string
  F$gender = "none"
  F$gender[F$isG.GQ] = "GQ"
  F$gender[F$isG.M | F$isG.TM] = "M"
  F$gender[F$isG.W | F$isG.TW] = "W"
  F$gender[(F$isG.W | F$isG.TW) & (F$isG.M|F$isG.TM)] = "B"
  F$shortGender = F$gender
  F$gender[F$isG.TM] = "TM"
  F$gender[F$isG.TW] = "TW"
  F$gender[(F$isG.W | F$isG.TW) & (F$isG.M|F$isG.TM)] = "B"

  F$sex = ifelse( F$lookG.M, "M", "" )
  F$sex = paste( F$sex, ifelse( F$lookG.TM, "*", "" ), sep="" )
  F$sex = paste( F$sex, ifelse( F$lookG.W, "|W", "|" ), sep="" )
  F$sex = paste( F$sex, ifelse( F$lookG.TW, "*", "" ), sep="" )
  F$sex = paste( F$sex, ifelse( F$lookG.GQ, "!", "" ), sep="" )

  F$shortSex = ifelse( F$lookG.M | F$lookG.TM, "M", "" )
  F$shortSex = paste( F$shortSex, ifelse( F$lookG.W | F$lookG.TW, "|W", "|" ), sep="" )


  if ( augment.with.finals ) {
    ## Add final match info to demographics
    fin = read.csv( "finals.csv" )
    fin = fin[ c("personID","num.matches","num.possible","num.desired","num.cruises") ]
    F = merge( F, fin )
    F
  }

  ##print( "[demog] Demographic information written to indiv_folks.csv\n" )
  ##write.csv( F, file=INDIV_FOLKS_FILENAME, quote=FALSE, row.names=FALSE )

  class(F) <- c( "demographics", class(F) )
  F
} # end compute.demographics





### A decent summary to just pump out some basic stats
print.demographics = function( F ) {

  g = length( unique( F$personID[ duplicated(F$personID) ] ) )
  du = length( unique( F$personID ) )
  cat( "# People = ", nrow(F),  "  # entities = ", du, "  # groups = ", g,
      "  # in groups = ", (g + nrow(F)-du), "\n" )
  
  if ( is.character(F$noPrimary ) ) {
    F$noPrimary = F$noPrimary 
  }
  cat ( "     % seek primary = ", round( 100 * mean( F$noPrimary )), "%\n\n" )
  
  ## if we have string stuff, then turn to factors
  if ( is.character(F$group) ) {
    F$group = as.factor( F$group )
    F$gender = as.factor(F$gender)
  }
  if ( is.logical(F$group)) {
  	F$group = factor( F$group, levels=c(TRUE,FALSE), labels=c("yes","no"))
  }
  stopifnot( levels(F$group) == c("yes","no"))
  print( gtab<-with( F, table( group, gender ) ) )
  nongrp = table( subset( F$shortGender, F$group!="yes") )
  cat( sprintf( "     Ratio of men to woman = %.2f\n", nongrp["M"]/nongrp["W"] ) )
  
  cat( "\nTable of Folks by Gender and Sexual Orientation (%)\n")
  pers = round( 100 * prop.table( with( F, table( gender, shortSex ) ), margin=1 ) )
  cnts =  with( F, table( gender, shortSex ) )
  colnames(pers) = paste(colnames(pers), "%", sep="")
  pers = rbind( pers, rep(0, ncol(pers) ) )
  
  print( as.table( cbind( addmargins( cnts ), rep(0,nrow(pers+1)), pers)), zero.print=".")

  ##	cat( "Full Counts (#)\n")
  ##	print( with( F, table( gender, sex ) ), margin=1, zero.print="." )

  cat( "# Trans = ", sum(F$isG.TM),  "/" , sum(F$isG.TW), 
      "\tTrans friendly = ", sum(F$lookG.TM), "/", sum(F$lookG.TW),"\n", sep="" )
  cat( "# GQ = ", sum(F$isG.GQ), 
      "\t\tGQ friendly = ", sum(F$lookG.GQ), "\n", sep="" )
  
  cat( "\nAges (by decade): " )
  tab <-  with( F, table( gender, 10*floor(age/10) ) )
  colnames(tab) = paste( colnames(tab), "s", sep="" )
  print( tab, zero.print="." )
  
                                        #with(F, table( lookGroup, group ) )
  
  if ( !is.null( F$matches ) ) {

 	  cat( "\n" )
	  mt = F$matches 
	  mt[ mt >= 10 ] = 5 * floor( mt[ mt >= 10] / 5 )
	  mtc = as.character(mt)
	  mtc[ mt >= 10 ] = paste( mtc[ mt >= 10 ], "+", sep="" )
	  mtc[ mt < 10 ] = paste( " ", mtc[ mt < 10], sep="" )

	  tab <- table( F$gender, mtc, dnn=c("gender", "number of matches") )
	  tabblk = cbind( tab, median=tapply( F$matches, F$gender, median ) )
	  tabblk[ tabblk == 0 ] = "."
	  cat( "Table of number of potential (two-way) matches by gender\n" )
	  print.table( tabblk, zero.print="." )
	  
	  tab <- table( 10*floor(F$age/10), mtc, dnn=c("age", "number of matches") )
	  tabblk = cbind( tab, median=tapply( F$matches,10*floor(F$age/10), median ) )
	  tabblk[ tabblk == 0 ] = "."
	  cat( "\nTable of number of potential (two-way) matches by age\n" )
	  rownames(tabblk) = paste( rownames(tabblk), "s", sep="")
	  print.table( tabblk, zero.print="." )
	  
  }
  
  cat( "\nKinkiness and looking for kinkiness\n" ) 
  print( with( F, table( isKinky, lookKink ) ) )
  
  cat( "\nLocation\n" )
  
  locs = grep( "^from", names(F) )
  locs = names(F)[locs]
  
  print(	sapply( locs, function( L ) { 
    paste( round( 100 * mean(F[[L]]) ), "%", sep="") } ) , quote=FALSE)
  invisible(0)
} 




showFinalMatchings = function( F ) {
  
  ## Add final match info to demographics
  fin = read.csv( "finals.csv" )
  ##	fin = fin[ c("personID","num.matches","num.cruises") ]
  F = merge( F, fin )
  
  cat( "Summary of final match numbers\n" )
  print( with( F, table( gender, num.matches ) ) )
  
  cat( "Summary of final desired numbers\n" )
  print( with( F, table( gender, num.desired ) ) )
  
  cat( "Summary of final possible numbers\n" )
  print( with( F, table( gender, num.possible ) ) )
  
  F$satisfaction = F$num.matches / pmax( F$num.desired, 1 )
  boxplot( satisfaction ~ gender , data=F)

  F$gender[F$group] = "group"
  stripchart( num.desired ~ gender , data=F, offset=0.15, method="stack")
  stripchart( num.possible ~ gender , data=F, offset=0.15, method="stack")
  
  print( with( F, table( gender, num.cruises ) ) )
}


showFolks = function( F, who ) {
  print( as.data.frame( F[who,] ) )
}



#####################################################################################
### Other plots and what-not

extras = function() {

  FF = F[ !(names(F) %in% c("first","last","personID")) ]
  summary(FF)


  plot( minAge ~ age, data=F, ylim=c(0,100) )
  points( maxAge ~ age, data=F, pch=19 )
  abline( lm( minAge ~ age, data=F ) )
  abline( lm( maxAge ~ age, data=F ) )

  stripchart( F$age, method="stack", main="Ages of participants" )

  stripchart( F$age ~ F$gender, method="stack", main="Ages of participants (by gender)" )

  byGen = split(F, F$gender )
  sapply( byGen, function( x ) { summary(x$age) } )

  table(F$gender, F$isG.GQ)
  table(F$isG.GQ )


  with( F, table( sex, gender ) )

  with( subset( F, age <= 40 ), table( sex, gender ) )





### Looking at matching

  sapply( byGen, function( x ) { summary(x$matches) } )



  ## once final results are in...
  res$personID = rownames(res)

  F = merge( F, res, by="personID" )

}
############################# end junk #################################################
