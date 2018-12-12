import flask
import numpy as np
import pandas as pd
import pickle
from sklearn.preprocessing import normalize
from scipy.spatial.distance import cdist

with open('recommendation_model.pkl', 'rb') as f:
    nmf_topic_vec_normalized, genre_vec, tfidf, genre_tfidf, nmf = pickle.load(f)
with open('movie_titles.pkl', 'rb') as f:
    movie_titles = pickle.load(f)


def similar_movie_by_title(movie_ind, topic_vec, genre_vec, scale=0.5):
    '''recommend top5 similiar movie to the input. 
    This function combines the topic vector with the genre vector 
    and return 5 movies with the smallest eucliean distance.
        Parameters
    ----------
    movie_ind : index of the movie in the matrix, int.

    topic_vec: The normalized nmf topic vector, shape[m,n]. m is movie number, n is topic number.
    
    genre_vec: tfidf transformed genre_vec, shape[m, k]. k is genre number
    
    scale: scale of the genre vec before combination. float.

    Returns
    -------
    movie_inds : indexs of the top movies, array, shape[5]
    '''
    movie_matrix = np.concatenate([topic_vec, genre_vec.toarray()*scale], axis=1)
    dist_array = cdist(movie_matrix[movie_ind].reshape(1, movie_matrix.shape[1]), movie_matrix, metric='euclidean')
    return np.argsort(dist_array)[0,1:6]


def similar_movie_by_text(text, query_genre, topic_vec, genre_vec, tfidf, genre_tfidf, nmf,  scale=0.5):
    '''recommend top5 similiar movie to the input text. 
    This function transform input text and genre using the same tfidf transformation for the database.
    Combines the topic vector with the genre vector 
    and return 5 movies with the smallest eucliean distance.
        Parameters
    ----------
    text: Text descript of the movie. String. 
    
    query_genre: binary 1D-array of the movie genry, shape(k). k is the genre number.

    topic_vec: The normalized nmf topic vector, shape[m,n]. m is movie number, n is topic number.
    
    genre_vec: tfidf transformed genre_vec, shape[m, k]. k is genre number
    
    tfidf: tfidf used in movie script transformation
    
    genre_tfidf: genre_tfidf used in genre transformation
    
    nmf: nmf used in topic formation
    
    scale: scale of the genre vec before combination. float.

    Returns
    -------
    movie_inds : indexs of the top movies, array, shape[5]
    '''
    query_vec = normalize(nmf.transform(tfidf.transform([text])), norm='l1').flatten()
    query_genre = genre_tfidf.transform(query_genre).toarray().flatten()
    query_vec_with_genre = np.concatenate([query_vec, query_genre*scale])
    movie_matrix= np.concatenate([topic_vec, genre_vec.toarray()*scale], axis=1)
    dist_array = cdist(query_vec_with_genre.reshape(1,-1), movie_matrix, metric='euclidean')
    return np.argsort(dist_array)[0,0:5]
    

app = flask.Flask(__name__)
@app.route("/")
def viz_page():
    """
    Homepage: serve the visualization page
    """
    with open("movie_rec.html", 'r') as viz_file:
        return viz_file.read()

@app.route("/rec_title", methods=["POST"])
def rec_title():
    """
    Read the movie title from the json, get top5 similar movies
    send it with a response
    """
    data = flask.request.json
    t = data["title"][0]
    movie_ind = movie_titles.index[movie_titles.str.lower()==t.lower()]
    rec_ind = similar_movie_by_title(movie_ind, nmf_topic_vec_normalized, genre_vec)
    rec_movies = movie_titles[rec_ind]
    results = {"movies": list(rec_movies)}
    return flask.jsonify(results)


@app.route("/rec_text", methods=["POST"])
def rec_text():
    '''
    Read movie description and genre info, get top5 similar movies
    send it with a response
    '''
    data = flask.request.json
    text=data["doc"][0]
    genre = data["genre_list"]
    rec_ind = similar_movie_by_text(text, genre, nmf_topic_vec_normalized, genre_vec, tfidf, genre_tfidf, nmf)
    rec_movies = movie_titles[rec_ind]
    results = {"movies": list(rec_movies)}
    return flask.jsonify(results)


#--------- RUN WEB APP SERVER ------------#

# Start the app server 
# (The default website port)
app.run(host='0.0.0.0')
app.run(debug=True)