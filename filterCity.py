from scipy import stats
import csv
import pandas as pd
import operator
import ast


def filter_city(csvFile):
	csvFile = pd.read_csv(csvFile)
	#print csvRead.city.unique
	cities = ["Las Vegas"] #, "Madison", "Phoenix", Montreal", "Toronto", "Nottingham", "Sidney"]
	df = csvFile[csvFile['city'].isin(cities)]
	pearsonDf = df[['business_id', 'review_count', 'latitude', 'longitude', 'name']]
	pearsonDf.to_csv("filteredCity.csv", index=False)

def getReviewingUsers(csvFile):
	csvFile = pd.read_csv(csvFile)
	allBusiness_IDs = {}
	for i in range (len(csvFile.business_id)):
		currentID = csvFile.business_id[i]
		if(currentID not in allBusiness_IDs):
			allBusiness_IDs[currentID] = 1
		else:
			allBusiness_IDs[currentID] += 1
	
	sorted_businesses = sorted(allBusiness_IDs.items(), key = operator.itemgetter(1))
	print sorted_businesses
	#df.to_csv("reviewingUsers.csv")

def filter_category(csvFile):
	csvFile = pd.read_csv(csvFile)
	categories = ["Restaurant", "Food", "Restaurants", "Coffee", "Tea", "Bar", 
	"Bars", "Nightclub", "Club", "Nightlife", "Festivals", "Clubs"]
	df = csvFile[csvFile['categories'].str.contains('|'.join(categories))]
	df.to_csv("filteredCategories.csv")
def filter_reviews(reviewFile, businessFile):
	reviewFile = pd.read_csv(reviewFile)
	columnsList = list(reviewFile)
	businessFile = pd.read_csv(businessFile)
	reviewFile = pd.merge(reviewFile, businessFile, on="business_id", suffixes=['', '_'])
	reviewFile = reviewFile[columnsList]
	reviewFile.to_csv("filteredReview.csv")

def filter_users(userFile, reviewFile):
	userFile = pd.read_csv(userFile)
	reviewFile = pd.read_csv(reviewFile)

	userList = userFile.user_id
	reviewUserList = reviewFile.user_id
	userFile = userFile.loc[userFile['user_id'].isin(reviewUserList)]
	userFile.to_csv("filteredUser.csv")	

def addTipCount(businessFile, tipFile):
	tipFile = pd.read_csv(tipFile)
	businessFile = pd.read_csv(businessFile)
	print "businessFile length:", len(businessFile.business_id)
	businessFileIds = businessFile.business_id
	print len(tipFile.business_id)
	tipCount = [0 for x in range(len(businessFile.business_id))]
	tipFile = tipFile.loc[tipFile['business_id'].isin(businessFileIds)]
	tipFile = tipFile.reset_index(drop = True)
	print len(tipFile.business_id)
	for i in range (len(businessFile.business_id)):
		currentBusinessID = businessFile.business_id[i]
		for j in range(len(tipFile.business_id)):
			currentBusinessTipID = tipFile.business_id[j]
			if (currentBusinessID == currentBusinessTipID):
				tipCount[i] += 1
	businessFile['tipCount'] = tipCount
	businessFile.to_csv("businessWithTipCount.csv")
def addCheckinCount(businessFile, checkinFile):
	businessFile = pd.read_csv(businessFile)
	checkinFile = pd.read_csv(checkinFile)
	businessFileIds = businessFile.business_id
	checkinCount = [0 for x in range(len(businessFile.business_id))]
	# checkinFile = checkinFile.loc[checkinFile['business_id'].isin(businessFileIds)]
	# checkinFile = checkinFile.reset_index(drop = True)
	# checkinFile.to_csv("MadisonCheckin.csv")

	for i in range (len(businessFile.business_id)):
		currentBusinessID = businessFile.business_id[i]
		for j in range(len(checkinFile.business_id)):
			currentBusinesscheckinID = checkinFile.business_id[j]
			if (currentBusinessID == currentBusinesscheckinID):
				checkinCount[i] = checkinFile.checkinSum[j]
	businessFile['checkinCount'] = checkinCount
	businessFile.to_csv("businessWithCheckinCount.csv")

def computePearsonCorrelation(businessFile):
	businessFile = pd.read_csv(businessFile)
	print "Review, checkin correlation: ", stats.pearsonr(businessFile.reviewCount, businessFile.checkinCount)
	print "tip, checkinCount correlation: ", stats.pearsonr(businessFile.tipCount, businessFile.checkinCount)
	print "review+ tip, checkinCount correlation: ", stats.pearsonr(businessFile.reviewPlusTips, businessFile.checkinCount)

def findUniqueCategories(csvFile):
	csvFile = pd.read_csv(csvFile)
	uniqueCategories = []
	for i in range(len(csvFile.categories)):
		currentList = ast.literal_eval(csvFile.categories[i])
		for j in range(len(currentList)):
			if currentList[j] not in uniqueCategories:
				uniqueCategories.append(currentList[j])
	print uniqueCategories
if __name__ == '__main__':
	filter_city("business.csv")
	#filter_category("business.csv")
	#filter_reviews("review.csv", "businessfilteredCategories.csv")
	#filter_users("user.csv", "filteredReview.csv")
	#getReviewingUsers("review.csv")
	#addTipCount("filtered.csv", "tip.csv")
	#addCheckinCount("businessWithTipCount.csv", "MadisonCheckin.csv")
	#computePearsonCorrelation("businessWithCheckinCount.csv")
	#interestingCategories = ["japanese", "Gluten-Free", "Thai", "Vietnamese", "Fast Food", "Chinese", "american", "donuts", "burgers", "pizza", "italian", "vegan", "vegetarian", "mexican", "Mediterranean", "german", ""]
	#findUniqueCategories("filteredCategories.csv")