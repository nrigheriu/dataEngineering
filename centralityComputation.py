import pandas as pd
import numpy as np
import ast
import networkx as nx
import json

def filterBusinessesWithManyReviews(csvFile):
	csvDataFrame = pd.read_csv(csvFile)
	businessesWithManyReviews = csvDataFrame[csvDataFrame['review_count'] >= 100]
	businessesWithManyReviews = businessesWithManyReviews.reset_index(drop=True)	
	#businessesWithManyReviews.to_csv("sinaBusinessFile.csv", index=False)
	return businessesWithManyReviews

def filterByRating(csvDataFrame, reviewFile):
	reviewFile = pd.read_csv(reviewFile, usecols=["user_id", "business_id", "date", "stars"])
	reviewFile = reviewFile[reviewFile['business_id'].isin(csvDataFrame.business_id)]
	reviewFile = reviewFile[reviewFile['stars'] >= 4]
	reviewFile = reviewFile.reset_index(drop=True)	
	return reviewFile
	#reviewFile.to_csv("sinaReviewFile.csv", index=False)
	#print reviewFile

def addColumnUsersWhichReviewed(highRatedReviews, businessesWithManyReviews):
	satisfiedUsers =  [[] for x in range(len(businessesWithManyReviews.review_count))]
	for i in range(len(businessesWithManyReviews.business_id)):
		currentBusinessID = businessesWithManyReviews.business_id[i]
		reviewsForCurrentBusiness = highRatedReviews[highRatedReviews['business_id'] == currentBusinessID]
		satisfiedUsers[i] = list(reviewsForCurrentBusiness.user_id)
	businessesWithManyReviews['satisfiedUsers'] = satisfiedUsers
	#businessesWithManyReviews.to_csv('businessesWithSatisfiedUsers.csv', index=False)
	return businessesWithManyReviews

def createBusinessWeightMatrix(businessesWithSatisfiedUsers):
	csvDataFrame = businessesWithSatisfiedUsers #pd.read_csv(businessesWithSatisfiedUsers)
	weightMatrix = np.zeros((len(csvDataFrame.business_id), len(csvDataFrame.business_id)))
	for i in range(len(weightMatrix)):
		iList = []
		try:
			iList = csvDataFrame.satisfiedUsers[i]
		except ValueError:
			print csvDataFrame.satisfiedUsers[i]
		iCount = len(iList)
		for j in range(len(weightMatrix)):
			jList = []
			if(i < j):
				jList = csvDataFrame.satisfiedUsers[j]
				jCount = len(jList)
				intersectIJ = list(set(iList) & set(jList))
				intersectIJCount = len(intersectIJ)
				weightMatrix[i][j] = (intersectIJCount/float(iCount) + intersectIJCount/float(jCount))/2.

	with open('weightMatrix.txt', 'wb') as f:
		for line in weightMatrix:
			np.savetxt(f, line, fmt='%.5f')
	f.close() 

def loadMatrixFromTxt(matrixFile, lengthOfRow):
	matrixFile = open(matrixFile, "r")
	read_lines = matrixFile.readlines()
	read_lines = [line.rstrip('\n') for line in read_lines]
	loadedMatrix = np.zeros((lengthOfRow, lengthOfRow))
	for i in range(lengthOfRow):
		loadedMatrix[i][:lengthOfRow-1] = read_lines[i*lengthOfRow:(lengthOfRow*(i+1))-1]
	return loadedMatrix

def createGraphFromMatrix(matrix, businessesWithSatisfiedUsers):
	businessesWithSatisfiedUsersDf = pd.read_csv(businessesWithSatisfiedUsers)
	G = nx.Graph()

	for i in range(len(matrix)):
		iBusinessID = businessesWithSatisfiedUsersDf.business_id[i]
		G.add_node(iBusinessID)
		for j in range(len(matrix)):
			if(i<j):
				if(matrix[i][j] > 0.):
					jBusinessID = businessesWithSatisfiedUsersDf.business_id[j]
					G.add_weighted_edges_from([(iBusinessID, jBusinessID, matrix[i][j])])
	savedData = nx.readwrite.json_graph.node_link_data(G)
	
	#s1 = json.dumps(savedData)
	#print(s1)
	with open('jsonGraph.json', 'w') as outfile:
		json.dump(savedData, outfile)
		
def loadGraphFromJson(jsonFile):
	graphJson = json.loads(open(jsonFile).read())
	G = json_graph.node_link_graph(graphJson, multigraph=False)
	pr = nx.pagerank(G, alpha = 0.15)
	#return G



if __name__ == '__main__':
	#businessesWithManyReviews = filterBusinessesWithManyReviews("filtered.csv")
	#highRatedReviews = filterByRating(businessesWithManyReviews, 'review.csv')
	#highRatedReviews = pd.read_csv("sinaReviewFile.csv")
	#businessesWithManyReviews = pd.read_csv("sinaBusinessFile.csv")
	#businessesWithSatisfiedUsersDf = addColumnUsersWhichReviewed(highRatedReviews, businessesWithManyReviews)
#	createBusinessWeightMatrix(businessesWithSatisfiedUsersDf)
	
	#loadedMatrix = loadMatrixFromTxt("weightMatrix.txt", 3126)
	#createGraphFromMatrix(loadedMatrix, "businessesWithSatisfiedUsers.csv")
	loadGraphFromJson("jsonGraph.json")

	#intersect = list(set(ast.literal_eval(first_rows.satisfiedUsers[0])) & set(ast.literal_eval(first_rows.satisfiedUsers[1])))