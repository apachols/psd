## This just makes some global variables 
## For the R scripts.
## Useful for testing


#if ( length( grep( "Rs$", getwd(), perl=TRUE ) ) > 0 ) {
#  setwd( ".." )
#}

R_SOURCE_DIR = "~/PSD/django/Rs/"


# where database is stored and its name
DATABASE_FILENAME = "~/PSD/run8/mydb"


EVENT_NAME = "revival1"
RUN_NUMBER = 7  # needs to be bigger than old data numbers,  6 is fine.

# where old event data is kept
OLD_DATA_PATH = "~/PSD/old_runs/"   # where old run data is kept.

# where current event data is kept
CUR_DATA_PATH = "~/PSD/run8/"

## Hand Files are files the administrator must make by hand
## after talking to folks and reading comments.
HANDFILES_LOCATION = paste( CUR_DATA_PATH, "handfiles/", sep="" )
HANDFILE_TRANSLATIONS_FILENAME=paste(HANDFILES_LOCATION,"id_translations.csv",sep="")
HANDFILE_MENTIONS_FILENAME=paste(HANDFILES_LOCATION,"mention.csv",sep="")
TABLE_FILENAME = paste(HANDFILES_LOCATION,"tables.csv",sep="" )


FINAL_MATCH_TABLE = paste(CUR_DATA_PATH,"final_matches_done.csv",sep="")
DATE_TABLE = paste(CUR_DATA_PATH,"date_table.csv",sep="")

ALL_FOLKS_FILENAME = paste(CUR_DATA_PATH,"allFolks.csv",sep="")
INDIV_FOLKS_FILENAME = paste(CUR_DATA_PATH,"allFolksIndiv.csv",sep="")

NAMETAGS_FILENAME = "nametags.csv"
ALLCOUNTS_FILENAME = "allCounts.csv"

# where downloaded transaction history (as csv) from Paypal is kept
PAYPAL_FILENAME = paste( CUR_DATA_PATH, "Download.csv", sep="" )

