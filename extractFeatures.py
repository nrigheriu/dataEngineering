import csv
import pandas as pd
import operator
import datetime
import numpy as np
import ast
from joblib import Parallel, delayed
import multiprocessing
from six.moves import cPickle as pickle
import threading


def getMostReviewedBusinesses(reviewFile, tipFile):
	reviewFile = pd.read_csv(reviewFile, usecols=["user_id", "business_id", "date"])
	tipFile = pd.read_csv(tipFile, usecols=["user_id", "business_id", "date"])
	allBusiness_IDs = {}
	for i in range (len(reviewFile.business_id)):
		currentID = reviewFile.business_id[i]
		if(currentID not in allBusiness_IDs):
			allBusiness_IDs[currentID] = 1
		else:
			allBusiness_IDs[currentID] += 1
	for i in range (len(tipFile.business_id)):
		currentID = tipFile.business_id[i]
		if(currentID not in allBusiness_IDs):
			allBusiness_IDs[currentID] = 1 
		else:
			allBusiness_IDs[currentID] += 1
	
	sorted_businesses = list(sorted(allBusiness_IDs.items(), key = operator.itemgetter(1)))
	writeToFile("sorted_businesses", sorted_businesses)
	most_popular_business_id = sorted_businesses[-1][0]

def extractUsersReviewingImportantBusinesses(business_id):
	reviewDf, tipDf = filterReviewAndTipFilesByBusinessId(business_id)
	reviewingUsers = getDatesOfFirstComment(reviewDf, tipDf)
	targetFilename = "usersReviewingImportantBusinesses_"+ business_id + ".csv"
	writeToFile(targetFilename, list(reviewingUsers.items()))

def getDatesOfFirstComment(filteredReviews, filteredTips):
	reviewingUsers = {}
	for i in range (len(filteredReviews.user_id)):
		currentID = filteredReviews.user_id[i]
		currentDate = filteredReviews.date[i]
		reviewText = filteredReviews.text[i]
		dateOfReview = datetime.datetime.strptime(currentDate, "%Y-%m-%d")
		if currentID not in reviewingUsers:
			reviewingUsers[currentID] = [currentDate, "", reviewText]
		elif(dateOfReview < datetime.datetime.strptime(reviewingUsers[currentID][0], "%Y-%m-%d")):
			reviewingUsers[currentID] = [currentDate, "", reviewText]
	for i in range(len(filteredTips.user_id)):
		currentID = filteredTips.user_id[i]
		currentDate = filteredTips.date[i]
		tipText = filteredTips.text[i]
		dateOfReview = datetime.datetime.strptime(currentDate, "%Y-%m-%d")
		if currentID not in reviewingUsers:
			reviewingUsers[currentID] = ["", currentDate, tipText]
		elif (not reviewingUsers[currentID][1]) or (dateOfReview < datetime.datetime.strptime(reviewingUsers[currentID][1], "%Y-%m-%d")):
			reviewingUsers[currentID][1] = currentDate
			reviewingUsers[currentID][2] = tipText
	return reviewingUsers

def filterReviewAndTipFilesByBusinessId(business_id):
	reviewFile = pd.read_csv("review.csv", usecols=["user_id", "business_id", "date", "text"])
	tipFile = pd.read_csv("tip.csv", usecols=["user_id", "business_id", "date", "text"])
	business_list = [business_id]
	reviewDf = reviewFile[reviewFile['business_id'].isin(business_list)]
	reviewDf = reviewDf.reset_index(drop=True)	
	tipDf = tipFile[tipFile['business_id'].isin(business_list)]
	tipDf = tipDf.reset_index(drop = True)
	return reviewDf, tipDf

def addFirstCommentTextColumn(fileName, business_id):
	csvDataFrame = pd.read_csv(fileName)
	reviewDf, tipDf = filterReviewAndTipFilesByBusinessId(business_id)
	commentText = []

	csvDataFrame.to_csv(fileName, index=False)


def fillListOfInfluencedUsers(i, usersDic, usersReviewingImportantBusinesses):
	listOfFriends = ast.literal_eval(usersDic[usersReviewingImportantBusinesses.user_id[i]])
	firstComment = getFirstCommentOfUser(usersReviewingImportantBusinesses.reviewDate[i], usersReviewingImportantBusinesses.tipDate[i])
	usersWhichCommentedAfter = getListOfUsersWhoCommentedAfter(listOfFriends, firstComment, usersReviewingImportantBusinesses)
	return usersWhichCommentedAfter


def addUsersWhichCommentedAfter(fileName, usersDic):
	csv.field_size_limit(1000000)
	usersReviewingImportantBusinesses = pd.read_csv(fileName)
	friendsWhichCommentedAfter = ["" for x in range(len(usersReviewingImportantBusinesses.user_id))]
	#usersDic = getUsersDictionary()
	#usersDic = load_dict('userDicFile')
	
	for i in range(len(usersReviewingImportantBusinesses.user_id)):
		listOfAllFriends = usersReviewingImportantBusinesses.allFriends[i]
		usersWhichCommentedAfter = getListOfUsersWhoCommentedAfter(listOfAllFriends, usersReviewingImportantBusinesses, i)
		friendsWhichCommentedAfter[i] = usersWhichCommentedAfter
	
	# num_cores = multiprocessing.cpu_count()
	# friendsWhichCommentedAfter = Parallel(n_jobs = num_cores)(delayed(fillListOfInfluencedUsers)(i, usersDic, usersReviewingImportantBusinesses) for i in range(len(usersReviewingImportantBusinesses.user_id)))
	
	usersReviewingImportantBusinesses['friendsWhichCommentedAfter'] = friendsWhichCommentedAfter
	usersReviewingImportantBusinesses.to_csv(fileName, index=False)

def getListOfUsersWhoCommentedAfter(listOfAllFriends, usersReviewingImportantBusinesses, indexPosition):
	listOfFriendsWhoCommentedAfter = []
	usersWhichCommentedAfter = list(usersReviewingImportantBusinesses.iloc[indexPosition:, 0])
	usersWhichCommentedAfterDate = list(usersReviewingImportantBusinesses.iloc[indexPosition:, 3])
	for i in range(len(usersWhichCommentedAfter)):
		currentID = str(usersWhichCommentedAfter[i])
		if(currentID in listOfAllFriends):
			influencedFriendsDict = {}
			currentFirstComment = str(usersWhichCommentedAfterDate[i])
			influencedFriendsDict[currentID] = currentFirstComment
			listOfFriendsWhoCommentedAfter.append(influencedFriendsDict)
	return listOfFriendsWhoCommentedAfter

def addFirstCommentColumn(csvFile):
	fileName = csvFile
	csvFile = pd.read_csv(csvFile)
	firstCommentDateList = ["" for x in range(len(csvFile.user_id))]
	for i in range(len(csvFile.user_id)):
		firstCommentDateList[i] = getFirstCommentOfUser(csvFile.reviewDate[i], csvFile.tipDate[i])
		firstCommentDateList[i] = firstCommentDateList[i].strftime("%Y-%m-%d")
	csvFile['firstComment'] = firstCommentDateList
	csvFile.to_csv(fileName, index=False)

def getUsersDictionary():
	usersDic = {}
	with open("user.csv", mode = 'r') as userFile:
		reader = csv.DictReader(userFile)
		for row in reader:
			usersDic[row['user_id']] = row['friends']
	return usersDic

def getFirstCommentOfUser(reviewDate, tipDate):
	firstComment = ""
	if not pd.isnull(reviewDate):
		firstComment = datetime.datetime.strptime(reviewDate, "%Y-%m-%d")
	if not pd.isnull(tipDate) and (not firstComment or datetime.datetime.strptime(tipDate, "%Y-%m-%d") < firstComment):
		firstComment = datetime.datetime.strptime(tipDate, "%Y-%m-%d")
	return firstComment

def addRatioOfInfluencedFriends(usersReviewingImportantBusinesses):
	csv.field_size_limit(1000000)
	usersReviewingImportantBusinesses = pd.read_csv(usersReviewingImportantBusinesses)
	usersDic = getUsersDictionary()
	influencedFriendsRatio = ["" for x in range(len(usersReviewingImportantBusinesses.user_id))]
	totalFriends = ["" for x in range(len(usersReviewingImportantBusinesses.user_id))]
	for i in range(len(usersReviewingImportantBusinesses.user_id)):
		listOfFriends = ast.literal_eval(usersDic[usersReviewingImportantBusinesses.user_id[i]])	
		totalFriends[i] = len(listOfFriends)
		influencedFriends = len(ast.literal_eval(usersReviewingImportantBusinesses.friendsWhichCommentedAfter[i]))
		if (len(listOfFriends) > 0):
			influencedFriendsRatio[i] = influencedFriends / float(len(listOfFriends))
		else:
			influencedFriendsRatio[i] = 0
	usersReviewingImportantBusinesses['totalFriends'] = totalFriends
	usersReviewingImportantBusinesses['influencedFriendsRatio'] = influencedFriendsRatio
	usersReviewingImportantBusinesses.to_csv('usersReviewingImportantBusinesses.csv', index=False)

def writeToFile(filename, values):
	with open(filename, "wb") as myfile:
		wr = csv.writer(myfile, quoting = csv.QUOTE_ALL)
		wr.writerow(["user_id", "reviewDate", "tipDate", "commentText"])
		#wr.writerow(values)   #this is for sorted Busineses
		for i in range(len(values)):
			wr.writerow([values[i][0], values[i][1][0], values[i][1][1], values[i][1][2]])
	myfile.close()	

def sortByFirstComment(csvFile):
	csvDataFrame = pd.read_csv(csvFile)
	csvDataFrame['firstComment'] = pd.to_datetime(csvDataFrame.firstComment)
	sortedDF = csvDataFrame.sort_values('firstComment')
	sortedDF.to_csv(csvFile, index=False)

def addFriendsColumn(csvFile):
	csv.field_size_limit(1000000)
	csvDataFrame = pd.read_csv(csvFile)
	allFriends = [[] for x in range(len(csvDataFrame.user_id))]
	#usersDic = getUsersDictionary()
	#save_dict(usersDic, 'userDicFile')
	usersDic = load_dict('userDicFile')
	for i in range(len(csvDataFrame.user_id)):
		listOfFriends = ast.literal_eval(usersDic[csvDataFrame.user_id[i]])	
		allFriends[i] = listOfFriends
	csvDataFrame['allFriends'] = allFriends
	csvDataFrame.to_csv(csvFile, index=False)	

def save_dict(di_, filename_):
    with open(filename_, 'wb') as f:
        pickle.dump(di_, f)

def load_dict(filename_):
    with open(filename_, 'rb') as f:
        ret_di = pickle.load(f)
    return ret_di

if __name__ == '__main__':
	#getMostReviewedBusinesses("review.csv","tip.csv")
	#extractUsersReviewingImportantBusinesses("review.csv", "tip.csv")
	#addFriendsColumn("usersReviewingImportantBusinesses_cYwJA2A6I12KNkm2rtXd5g.csv")
	
	#sortByFirstComment("usersReviewingImportantBusinesses_4JNXUYY8wbaaDmk3BPzlWw.csv")
	#addUsersWhichCommentedAfter("usersReviewingImportantBusinesses_cYwJA2A6I12KNkm2rtXd5g.csv")
	#addFirstCommentColumn("usersReviewingImportantBusinesses_4JNXUYY8wbaaDmk3BPzlWw.csv")
	#addRatioOfInfluencedFriends("usersReviewingImportantBusinesses.csv")

	#most_popular_business_id = ["K7lWdNUhCbcnEvI0NhGewg", 
	#"4JNXUYY8wbaaDmk3BPzlWw", "RESDUcs7fIiihp38-d6_6g", 
	#"cYwJA2A6I12KNkm2rtXd5g", "f4x1YBxkLrZg652xt2KR5g"]
	
	most_popular_business_id = ["4JNXUYY8wbaaDmk3BPzlWw", "cYwJA2A6I12KNkm2rtXd5g"]#["f4x1YBxkLrZg652xt2KR5g"]
	averagely_popular_business_id = ["wUKzaS1MHg94RGM6z8u9mw", "r_BrIgzYcwo1NAuG9dLbpg", "JLbgvGM4FXh9zNP4O5ZWjQ", "YPavuOh2XsnRbLfl0DH2lQ", "L2p0vO3fsS2LC6hhQo3CzA"]
	#usersDict = load_dict('userDicFile')
	
	processes = []
	for business_id in most_popular_business_id:
		fileName = "usersReviewingImportantBusinesses_" + business_id + ".csv"
		#t = multiprocessing.Process(target = extractUsersReviewingImportantBusinesses, args=(business_id, ))
		#t = multiprocessing.Process(target = addFirstCommentColumn, args=(fileName, ))
		t = multiprocessing.Process(target = sortByFirstComment, args=(fileName, ))
		#t = multiprocessing.Process(target = addFriendsColumn, args=(fileName, ))
		#t = multiprocessing.Process(target=addUsersWhichCommentedAfter, args=(fileName, usersDict))
		processes.append(t)
		t.start()
	for one_process in processes:
		one_process.join()

		
	#addUsersWhichCommentedAfter(fileName, usersDic)


