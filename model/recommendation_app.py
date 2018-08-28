import flask
import numpy as np
import pandas as pd
import pickle

with open('recommendation_mv_df.pkl', 'rb') as f:
    recommendation_mv_df= pickle.load(f)

with open('tfidf.pkl', 'rb') as f:
    tag_tfidf = pickle.load(f)

with open('nmf_model.pkl', 'rb') as f:
    _, tag_nmf, _ = pickle.load(f) 

with open('topic_genre_matrix.pkl', 'rb') as f:
    movie_matrix=pickle.load(f)

def recommendation(text, genre, movie_matrix=movie_matrix):
    genre_vector = np.array(genre)
    query_vector = tag_tfidf.transform([text])
    nmf_res = tag_nmf.transform(query_vector)
    vec = np.append(nmf_res[0], genre_vector/15)
    dist = np.linalg.norm((movie_matrix - vec), axis=1)
    return np.argsort(dist)[:5]

app = flask.Flask(__name__)
@app.route("/")
def viz_page():
    """
    Homepage: serve our visualization page, awesome.html
    """
    with open("test.html", 'r') as viz_file:
        return viz_file.read()

@app.route("/score", methods=["POST"])
def score():
    """
    When A POST request with json data is made to this url,
    Read the example from the json, predict probability and
    send it with a response
    """
    # Get decision score for our example that came with the request
    data = flask.request.json
    x = data["title"][0]
    #movies = recommendation_mv_df.index[recommendation_mv_df.loc[recommendation_mv_df.index ==x, :5]]
    m = list(recommendation_mv_df.index[recommendation_mv_df.loc[recommendation_mv_df['title_lower']==x.lower(), range(1,6)]])
    movies = [i for i in m[0] if i.lower() != x.lower()]
    # Put the result in a nice dict so we can send it as json
    results = {"movies": movies}
    return flask.jsonify(results)

@app.route("/rec_text", methods=["POST"])
def rec_text():
    data = flask.request.json
    text=data["doc"][0]
    genre = data["genre_list"]
    ind = recommendation(text, genre, movie_matrix=movie_matrix)
    results = {"movies": list(recommendation_mv_df.index[ind])}
    return flask.jsonify(results)


#--------- RUN WEB APP SERVER ------------#

# Start the app server on port 80
# (The default website port)
app.run(host='0.0.0.0')
app.run(debug=True)