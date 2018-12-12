#!/usr/bin/python

import pickle
import pandas as pd
import numpy as np
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import WhitespaceTokenizer
from nltk.tag import pos_tag
import string
from collections import Counter


def clean_text(text):
    '''remove script specific terms from the text
    '''
    text = text.strip()
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL) #remove html comment
    text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL) #remove style tag and its content
    text = re.sub(r'<.*?>', '', text) #remove all tags in the html file
    text = re.sub(r'(?<=[a-z])-\n|\n.*written by.*(\r?\n\r?\n.*\n)?', '', text, flags=re.I|re.M) #fix word break  with '-' at the end of a line and remove author
    text = re.sub(r' {12,}', '\n', text) #some of the scripts are formated as one-line strings. Break them into multiple lines by break consecutive white spaces(>12 spaces)
    text = re.sub(r'.*\d+[_\.\-\/]\d+[_\.\-\/]\d+.*', '', text, flags=re.I) #remove date
    text = re.sub(r'.*\(?\w+@\w+\.\w+\)?.*', '', text) #remove lines containing emails
    text = re.sub(r'.*DRAFT.*|Sc\s+\d.*', '', text) #remove lines containing DRAFT or word like Sc 11. 
    text = re.sub(r'([A-Z][a-z\'.]*[^a-zA-Z\']){2,}', '', text, flags=re.M) #remove consecutive words with the first letter capitalized like Prince Charming
    text = re.sub(r'(the|a)\s[A-Z][a-z\']*\W', '', text) #remove NNP with the from like 'the King' or 'a King'
    text = re.sub(r'(?<=\W)[A-Z][A-Z\'_:]*(?=[^a-zA-Z\'])', '', text) #remove all words(with at least 2 char) in capitals. Those are mostly likely script specific or charater names.
    text = re.sub(r'\n\s*[a-z]*:', '', text, flags=re.I) # remove a new line with :
    text = re.sub(r'(\w*in)\'(?=\W)', r'\1g', text) #convert ' to g for words like nothin', goin'
    text = re.sub(r'\w*([a-z])\1{2}\w*', '', text, flags=re.I) #remove words with more than 2 repeats of letters, like aaahh
    text = re.sub(r'.*(I N T|E X T|int[^a-z]|ext[^a-z]|close on|angle|high wide|exterior|interior|dissolve to|open on|shooting script|c\.u\.|(med\.|long|close|full) shot|cut( back)? to|superimpose\:?).*',
              '\n', text, flags=re.I) #remove lines containing these script specific terms
    text = re.sub(r'\'s(?= )', '', text)
    # more script specifict words to be removed
    remove_list = [ 'continued:', 'close-?up:?', 'fade in', 'day', 'continued',
            '\(v\.o\.\)', 'scene \(deleted\)?', "cont\'?d", 'beat.', 
          '\(continuing\)', '\(v/o\)', 'camera', 'pans?',  '\(o\.?s\.?\)', 'screen',  'cu', 'pov:?', 'thru', 'omit', 'revision']
    words_to_remove = re.compile('(?= |\n|\r)|(?<= |\n|\r)'.join(remove_list), flags=re.I)
    text = words_to_remove.sub('', text)
    return text

def fix_title(title):
    '''This function is to fix the format of some movie titles'''
    title = re.sub(' Script$', '', title, flags=re.I)
    if ', The' in title:  #'Christmas Toy, The (1986)' shoulb be 'The Christmas Toy'
        title = 'The ' + title.replace(', The', '')
    if ', An' in title:
        title = 'An ' + title.replace(', An', '')   
    if ', A' in title:
        title = 'A ' + title.replace(', A', '')
    if ', Les' in title:
        title = 'Les ' + title.replace(', Les', '')
    if ', Le' in title:
        title =  'Le ' + title.replace(', Le', '')
    if '(final script)' in title:
        title = title.replace(' (final script)', '')
    return title

pos_to_wornet_dict = {
    'JJ': 'a',
    'JJR': 'a',
    'JJS': 'a',
    'RB': 'r',
    'RBR': 'r',
    'RBS': 'r',
    'NN': 'n',
    'NNP': 'n',
    'NNS': 'n'
}


def lemmatize_and_tag(text):
    '''Tokenize the text and lemmatize the word by its tag. Add possible high frequeny character name to a global list nnp_to_remove
    '''
    global nnp_to_remove
    lemmatizer = WordNetLemmatizer()
    words=[]
    for w, p  in pos_tag(WhitespaceTokenizer().tokenize(text)):
        w = w.strip('1234567890"'+string.punctuation).lower()
        if w.lower() in stop_word or not w:
            continue
        if p in pos_to_wornet_dict.keys():
            if p == 'NNP' and 'V' in pos_tag([w.lower()])[0][1]:  #Verbs at the beggining of a sentence is classified as NNP sometimes. Discard it. 
                continue
            words.append((lemmatizer.lemmatize(w, pos_to_wornet_dict[p]).lower(), p))
    # Find words with highest frequency. If they are NNP, add them to a list of words to remove, as those words are most likely character's name
    bow = Counter(words)
    nnp_to_remove.update({x[0][0] for x in sorted(bow.items(), key=lambda x:x[1], reverse=True)[:8] if x[0][1]=='NNP'})
    return ' '.join([x for x in list(zip(*words))[0] if (x not in nnp_to_remove and len(x)>1)])




if __name__=='__main__':
    with open('data/movies.pkl', 'rb') as f:
        movies = pickle.load(f)

    # A few movies need to be removed from the data due to language or format issues.
    movie_to_remove=[
        'Neverending Story, The Script', 'Omega Man Script',#abnormal format
        'Le Diable par la Queue Script', 'Ni vu ni connu Script', 'Les Tontons Flingueurs Script', 'Un Singe en Hiver Script', #not in English
        '9 Script',#weired letters in line
        'Addams Family, The Script', #file abnormally huge
        'Damned United, The Script', 'Awakenings Script',  #weired spaces between words
        'Pretty Woman Script', #duplicate movies
        'Godfather Part III, The Script'  #low quanlity, encoding issue
                ] 
    stop_word = stopwords.words('english')
    stop_word.extend(['dr', 'de', 'san','looks', 'uh', 'huh', 'miss', 'mr', 'guys', 'gov', 'ya', 'sir', 'sr', 'st', "cont'd",
        'cannot', "wouldn't", "i'm", "ain't", 'gotta', 'gonna', 'outta', 'new',  'really', 'ok', 'yeah', 'phone',  'towards', 'pat', 'em',  'x', 'yes', 'no', 'hey', 'ah', 'ahh',
        'somethin', "nothin", 'something', 'nothing', 'wanna', 'gonna', 'goin', 'away',
        'ow', 'um', 'hmm', 'ha', 'ho', 'whoa', 'um', 'wow', 'hee', 'hah', 
        'revision', 'back', 'voice'])
    nnp_to_remove = set()
    
    movies = [movie for movie in movies if movie['title'] not in movie_to_remove]
    i = 0
    for movie in movies:
        movie['title'] = fix_title(movie['title'])
        movie['scripts'] = lemmatize_and_tag(clean_text(movie['scripts']))
        i += 1
        if i%100 == 0:
            print('Processing', str(i), '...')


    movie_df = pd.DataFrame(movies)
    with open('data/script_df.pkl', 'wb') as f:
        pickle.dump(movie_df, f)
    with open('data/nnp.pkl', 'wb') as f:
        pickle.dump(nnp_to_remove, f)






    