import csv
import numpy as np

# We only need three fields: user_id, movie_id and rating in Rating dataset
class rating:
    def __init__(self, user_id, movie_id, rating):
        self.user_id = int(user_id)
        self.movie_id = int(movie_id)
        self.rating = float(rating)


# Prepare step
def prepare(rating):
	# Count movies and the appearance position of movie by Movie dataset
	movies = {}
	
	# Count users
	users = set()
	ratings = []
	i = 0
	with open("./app/data/movies.csv") as csvfile:
	    reader = csv.reader(csvfile, delimiter=',')
	    for data in reader:
	    	i += 1
	    	if i==1:
	    		continue
	    	movies[int(data[0])] = i-2

	j = 0
	with open("./app/data/ratings.csv") as csvfile2:
		reader = csv.reader(csvfile2, delimiter=',')
		for data in reader:
			j += 1
			if j==1:
				continue
			users.add(int(data[0]))
			ratings.append(rating(int(data[0]), int(data[1]), float(data[2])))
	
	# Construct rating matrix
	NUM_RATER = len(users)
	matrix = np.zeros((NUM_RATER, i))
	# Average score list for calculating cosine similarity
	avg = np.zeros(NUM_RATER)

	for rating in ratings:
		#print rating.user_id, rating.movie_id, rating.rating, NUM_RATER
		matrix[rating.user_id-1][movies[rating.movie_id]] = rating.rating

	for _dummy in range(NUM_RATER):
	    rated = np.nonzero(matrix[_dummy])
	    n = len(rated[0])
	    if n != 0:
	        avg[_dummy] = np.mean(matrix[_dummy][rated])
	    
	    # if no rating provided, set avg rating as 0
	    else:
	        avg[_dummy] = 0

	# urate is the matrix recording which movies are rated by users (0/1 count)
	urate = matrix.copy()
	urate[urate > 0.01] = 1.0
	return (matrix, urate, avg, movies)

# Prediction step 
# pref: new user ratings for movies
# matrix: prestored user ratings
# urate: urate is the matrix recording which movies are rated by users
# N: number of nearest closest to be included
def predict(pref, matrix, urate, avg, N = 100):
	if pref.size != matrix[0].size:
		return None
	sims = compute(pref, matrix, urate, avg, N)

	c_matrix = matrix[sims[0], :]
	c_rate = urate[sims[0], :]
	c_avg = avg[sims[0]]
	wt = sims[1]
	scores = np.sum((((c_matrix.T-c_avg)*c_rate.T)*wt), axis = 1)
	weights = np.sum((np.absolute(c_rate).T*wt), axis = 1)
	ans = []
	for i in range(pref.size):
		if weights[i] < 1e-9:
			ans.append((0, i))
		else:
			ans.append((scores[i]/weights[i], i))	
	ans.sort(key = lambda x: -x[0])
	return ans[:20]

# Calculation step by cosine similarity
# pref: new user ratings for movies
# matrix: prestored user ratings
# urate: urate is the matrix recording which movies are rated by users
# N: number of nearest closest to be included 
def compute(pref, matrix, urate, avg, N):
	hgt = matrix.shape[0]
	arr = [0 for i in range(hgt)]
	user_rate = np.array([1 if pref[i] > 0 else 0 for i in range(pref.size)])

	# rx is the normalized new-user rating (minus avg)
	rx = (pref-np.mean(pref[np.nonzero(pref)]))*user_rate
	for i in range(hgt):
		# ry is the normalized pre-stored-user rating
		ry = (matrix[i]-avg[i]*urate[i])
		if user_rate.dot(urate[i]) >= 0.01:
			if (rx.dot(rx))**0.5 > 1e-7:
				sumrx = (rx.dot(rx))**0.5
			else:
				sumrx = 1e-7
			sumry = (ry.dot(ry))**0.5

			# cosine similarity a bot b/(|a|*|b|)
			arr[i] = rx.dot(ry)/(sumrx*sumry)
	arr = np.array(arr)
	return (arr.argsort()[::-1][:N], np.sort(arr)[::-1][:N])



'''
#test
matrix, urate, avg = prepare(rating)
ad = np.zeros(matrix[0].size)
ad[1] = 2
ad[[2, 230]] = 5
ad[[100, 500]] = 4
ad[101:105] = 3.5
 
print predict(ad, matrix, urate, avg, N=150)
'''



