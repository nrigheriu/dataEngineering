import pandas as pd
import numpy as np
import ast
import networkx as nx
import json
from scipy import stats
from math import sin, cos, sqrt, atan2, radians

def filterBusinessesWithManyReviews(csvFile):
	csvDataFrame = pd.read_csv(csvFile)
	businessesWithManyReviews = csvDataFrame[csvDataFrame['review_count'] >= 100]
	businessesWithManyReviews = businessesWithManyReviews.reset_index(drop=True)	
	businessesWithManyReviews.to_csv("sinaBusinessFile.csv", index=False)
	return businessesWithManyReviews

def filterByRating(csvDataFrame, reviewFile):
	reviewFile = pd.read_csv(reviewFile, usecols=["user_id", "business_id", "date", "stars"])
	reviewFile = reviewFile[reviewFile['business_id'].isin(csvDataFrame.business_id)]
	reviewFile = reviewFile[reviewFile['stars'] >= 4]
	reviewFile = reviewFile.reset_index(drop=True)	
	reviewFile.to_csv("sinaReviewFile.csv", index=False)
	return reviewFile

def addColumnUsersWhichReviewed(highRatedReviews, businessesWithManyReviews):
	satisfiedUsers =  [[] for x in range(len(businessesWithManyReviews.review_count))]
	for i in range(len(businessesWithManyReviews.business_id)):
		currentBusinessID = businessesWithManyReviews.business_id[i]
		reviewsForCurrentBusiness = highRatedReviews[highRatedReviews['business_id'] == currentBusinessID]
		satisfiedUsers[i] = list(reviewsForCurrentBusiness.user_id)
	businessesWithManyReviews['satisfiedUsers'] = satisfiedUsers
	businessesWithManyReviews.to_csv('businessesWithSatisfiedUsers.csv', index=False)
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
	saveGraphToFile('jsonGraph.json', G)
		
def loadGraphFromJson(jsonFile):
	graphJson = json.loads(open(jsonFile).read())
	G = nx.readwrite.json_graph.node_link_graph(graphJson, multigraph=False)
	#pr = nx.pagerank(G, alpha = 0.15)
	return G
def addLocationAttributes(G, businessesWithSatisfiedUsers):
	businessesWithSatisfiedUsersDf = pd.read_csv(businessesWithSatisfiedUsers)
	for i in range(len(businessesWithSatisfiedUsersDf.business_id)):
		currentBusinessID = businessesWithSatisfiedUsersDf.business_id[i]
		currentLatitude = businessesWithSatisfiedUsersDf.latitude[i]
		currentLongitude = businessesWithSatisfiedUsersDf.longitude[i]
		G.nodes[currentBusinessID]['longitude'] = currentLongitude
		G.nodes[currentBusinessID]['latitude'] = currentLatitude
	saveGraphToFile('jsonEnrichedGraph.json', G)

def addNameAttribute(G, businessesWithManyReviews):
	businessesWithManyReviewsDf = pd.read_csv(businessesWithManyReviews)
	for i in range(len(businessesWithManyReviewsDf.business_id)):
		currentBusinessID = businessesWithManyReviewsDf.business_id[i]
		currentName = businessesWithManyReviewsDf.name[i]
		G.nodes[currentBusinessID]['name'] = currentName
	saveGraphToFile('jsonEnrichedGraph.json', G)

def createSubGraphToVisualize(G):
	firstNodes = list(G.nodes())[:30]
	subGraph = G.subgraph(firstNodes)
	saveGraphToFile('subGraph.json', subGraph)

def computeAverageGeographicalDistance(G): 
	nodesList = list(G.nodes())
	for i in range(len(nodesList)):
		currentNode = nodesList[i]
		distance = 0.			
		lat1 = G.nodes[currentNode]['latitude']
		lon1 = G.nodes[currentNode]['longitude']
		for j in range(len(nodesList)):
			lat2 = G.nodes[nodesList[j]]['latitude']
			lon2 = G.nodes[nodesList[j]]['longitude']
			distance += computeGeographicalDistance(lat1, lon1, lat2, lon2)
		averageDistance = distance / len(nodesList)
		G.nodes[currentNode]['averageDistance'] = averageDistance
	saveGraphToFile('jsonEnrichedGraph.json', G)

def saveGraphToFile(fileName, graphToSave):
	savedData = nx.readwrite.json_graph.node_link_data(graphToSave)
	with open(fileName, 'w') as outfile:
		json.dump(savedData, outfile)

def computeGeographicalDistance(lat1, lon1, lat2, lon2):		#scale is km
	R = 6373.0
	lat1 = radians(lat1)
	lat2 = radians(lat2)
	lon1 = radians(lon1)
	lon2 = radians(lon2)
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))
	distance = R * c
	return distance

def computePearsonCorrelation(G):
	nodesList = list(G.nodes())
	averageDistanceList = []
	pagerankValuesList = []
	weightedDegreeList = []
	for i in range(len(nodesList)):
		currentNode = nodesList[i]
		averageDistanceList.append(G.nodes[currentNode]['averageDistance'])
		pagerankValuesList.append(G.nodes[currentNode]['pagerank'])
		weightedDegreeList.append(G.nodes[currentNode]['weighted_degree'])
	print "averageDistance, pagerank correlation: ", stats.pearsonr(averageDistanceList, pagerankValuesList)	
	print "averageDistance, weighted_degree correlation: ", stats.pearsonr(averageDistanceList, weightedDegreeList)	

def sortByWeights(G):
	nodesList = list(G.nodes())
	weightedDegreeList = []
	nodeNames = []
	for i in range(len(nodesList)):
		currentNode = nodesList[i]	
		weightedDegreeList.append(G.nodes[currentNode]['weighted_degree'])
		nodeNames.append(G.nodes[currentNode]['name'])
	df = pd.DataFrame({
		'name' : nodeNames,
		'weighted_degree': weightedDegreeList
	})	
	df = df.sort_values(by=['weighted_degree'])
	print df.name[:10]
if __name__ == '__main__':
	#businessesWithManyReviews = filterBusinessesWithManyReviews("filteredCity.csv")
	#highRatedReviews = pd.read_csv("sinaReviewFile.csv")
	#businessesWithManyReviews = pd.read_csv("sinaBusinessFile.csv")
	#highRatedReviews = filterByRating(businessesWithManyReviews, 'review.csv')
	#businessesWithSatisfiedUsersDf = addColumnUsersWhichReviewed(highRatedReviews, businessesWithManyReviews)
	#createBusinessWeightMatrix(businessesWithSatisfiedUsersDf)
	
	#loadedMatrix = loadMatrixFromTxt("weightMatrix.txt", 3126)
	#createGraphFromMatrix(loadedMatrix, "businessesWithSatisfiedUsers.csv")

	G = loadGraphFromJson("jsonEnrichedGraph.json")
	#addLocationAttributes(G, "businessesWithSatisfiedUsers.csv")
	#addNameAttribute(G, "sinaBusinessFile.csv")
	#createSubGraphToVisualize(G)
	#computeAverageGeographicalDistance(G)
	#computePearsonCorrelation(G)
	sortByWeights(G)
