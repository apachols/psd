
# Looking at dating results-- this file is just for fun and 
# not needed for the event.

# getting overview data on psd folks

# gender 

ap2$age = jitter(ap2$age)
ss = split( ap2, ap2$gender )

plot( got ~ age, data=ss[[2]], main="# Final Matches by Individual's Age (no groups)",ylab="# Final Matches", ylim=c(0,6), pch=25, bg="grey", xlim=c(20,60),cex=2 )

points( got ~ age, data=ss[[1]],pch=24, bg="red", cex=2 )

abline( lm( got ~ age, data=ap2 ) )



plot( wanted ~ age, data=ss[[2]], main="# Folks Wanting Individual by Individual's Age (no groups)",ylim=c(0,12), pch=25, bg="grey", xlim=c(20,60),cex=2 )

points( wanted ~ age, data=ss[[1]],pch=24, bg="red", cex=2 )

ss = split( ap3, ap3$gender )
ss[[3]] = ap[ ap$group=="yes", ]

plot( satisfaction ~ age, data=ss[[2]], main="Satisfaction by Individual's Age",ylim=c(0,100), ylab="% Satisfaction", pch=25, bg="grey", xlim=c(20,60),cex=2 )

points( satisfaction ~ age, data=ss[[1]],pch=24, bg="red", cex=2 )
points( satisfaction ~ age, data=ss[[3]],pch=23, bg="blue", cex=2 )


women = ap$personID[ ap$gender=="woman" ]
men = ap$personID[ ap$gender=="man" ]

v = sapply( allL, function( x ) { n = x[[2]]
	sum( n %in% women )
} )
v2 = sapply( allL, function( x ) { n = x[[2]]
	sum( n %in% men )
} )

dd = data.frame( personID = names(v), gotW=v, gotM=v2 )
dd$got = ap$got
dd$gender = ap[ dd$personID, ]$gender




v = sapply( allL, function( x ) { n = x[[2]]
	sum( n %in% women )
} )
v2 = sapply( allL, function( x ) { n = x[[2]]
	sum( n %in% men )
} )

dd = data.frame( personID = names(v), gotW=v, gotM=v2 )
a2 = ap[ c("personID","age", "gender","group") ]
dd = merge( dd, a2, by="personID" )
dd = dd[ dd$group!="yes",]
