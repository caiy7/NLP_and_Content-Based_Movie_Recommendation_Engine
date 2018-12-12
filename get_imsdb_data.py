#!/usr/bin/python
import requests
from bs4 import BeautifulSoup
import pickle
import time
import random
import re
import string

def get_movie_url():
    '''
    Retrieve the urls that contain the movie info. 
    Return a dictionary with the movie title as the key and the movie url as the title.
    '''
    fail = 0
    movie_url = {}
    for i in '0'+string.ascii_uppercase:
        url = 'http://www.imsdb.com/alphabetical/' + i
        response = requests.get(url)
        page = response.text
        soup = BeautifulSoup(page, 'html.parser')  #lxml cause some encoding issue in this case
        ps = soup.find_all('p')
        for p in ps:
            link = p.find('a')
            try:
                movie_url[link['title']] = link['href']
            except:
                print(link)
                fail+=1
    print('failed to get', fail, 'links')
    return movie_url

def get_info(soup, name):
    '''
    Scrape the movie info from webpage.
    Arguments: a BeautifulSoup object of the movie webpage and the movie title
    Returns: a dictionary containing the movie genre and movie script url and movie name only if the script url is available
    '''
    movie_info=dict(title=name)
    try:
        genre = []
        table = soup.find('table', {'class': 'script-details'})
        all_links = table.find_all('a')
        for l in all_links:
            if l['href'].find('genre') != -1:
                genre.append(l['href'].replace('/genre/', ''))
        movie_info['genre'] = genre
    except:
        print('cannot get genre for movie %s' % name )
    try:
        read_regex = re.compile(r'^Read')
        movie_info['script_url'] = table.find('a', text=read_regex)['href']
    except:
        print('cannot get url for movie script%s' % name )
        return None
    return movie_info

def get_script(url):
    '''
    Get movie script. 
    Arguments: movie script URL
    Returns: movie script text
    Some of the scripts are in PDF form, which will not be retrieved and not used for this project.
    '''
    full_url = 'http://www.imsdb.com' + url
    try:
        response = requests.get(full_url)
        page = response.text
    except:
        print('cannot open website:', full_url)
        raise Exception
    try:
        script = re.search(r'<pre>((.(?!<pre>))*)</pre>', page, flags=re.I|re.DOTALL).group(1) #lxml has some format issue. re works better in this case
        if len(script) > 1000:
            return script
        else:
            raise ValueError('cannot get the script from:', full_url)
    except:
        raise ValueError('cannot get the script from:', full_url)  

def create_movie_list(movie_urls):
    '''
    create a list of movie info. Each element is a dictionary. The keys are movie title, gener, url and movie scripts
    Arguments: movie_urls dictionary
    Returns: movie_list
    '''
    movie_list=[]
    i=0
    for name, url in movie_urls.items():
        full_url = 'http://www.imsdb.com' + url
        response = requests.get(full_url)
        page = response.text
        soup = BeautifulSoup(page, 'lxml')
        movie = get_info(soup, name)
        if movie:
            try:
                movie['scripts'] = get_script(movie['script_url'])
                if len(movie['scripts'])<1000:
                    print('No script found:', movie['title'] )
                    continue
                i += 1
                if i%7 == 0:
                    time.sleep(random.random()*3)
                if i%200 == 0:
                    print('working on ', i)
                    time.sleep(random.random()*100)
                movie_list.append(movie)
            except:
                print('cannot get script for ', movie['title'])
                continue
        else:
            print('cannot get script for ', name)
            continue
    print('Total scripts: %d' % i)
    return movie_list



if __name__ == '__main__':
    movie_urls = get_movie_url()
    print('Total movie urls: ', len(movie_urls))
    movies = create_movie_list(movie_urls)
    with open('data/movies.pkl', 'wb') as f:
        pickle.dump(movies , f)

    

