#!/usr/bin/env python
"""
Auto-loads the Ultimate Guitar tabs to the currently-playing iTunes song.

Opens a new window if the old window was closed. 

Maybe:  Tweak how many guitar tabs are opened (maybe one tab and one chord)
        Find how to incorporate the iTunes event listener

Created and complete for usage. (November 24, 2011)
"""
__author__ = 'Sophia Westwood'


import urllib
import urllib2
import time
from appscript import *
from appscript.reference import CommandError
from BeautifulSoup import BeautifulSoup


def no_results_page(search_soup):
    """Returns true if search_soup is the "No results could be found" page.
    Params:
        search_soup: BeautifulSoup set up with the html of the search results page."""
    return search_soup.find('div', {'class': 'not_found'})

def tab_searchpage(song, artist):
    """Searches for songs matching the song and artist."""
    # Extra parameters are songs in Standard tuning, Chords or Tab (excludes Bass tabs, etc).
    first_part_url = r'http://www.ultimate-guitar.com/search.php?view_state=advanced&'
    last_part_url = r'&type%5B%5D=200&type%5B%5D=300&tuning%5B%5D=Standard&version_la='
    search_params = urllib.urlencode({'band_name' : artist, 'song_name' : song})
    search_url = (first_part_url + search_params + last_part_url)
    search_soup = BeautifulSoup(urllib2.urlopen(search_url))
    if no_results_page(search_soup):  
        # If there are no results, then remove the artist filter
        search_params = urllib.urlencode({'song_name' : song})
        search_url = (first_part_url + search_params + last_part_url)
        search_soup = BeautifulSoup(urllib2.urlopen(search_url))
    return search_url, search_soup  # Note: for performance, consider passing search_soup by parameter

def best_rated_result(search_soup):
    """Returns the URL of the best rated result of the search for guitar tabs.
    Params:
        search_soup: BeautifulSoup set up with the html of the search results page.
    """
    if no_results_page(search_soup):
        # There are no results on this page, so there is no best url.
        return ''
    results = search_soup.find('table', {'class':'tresults'}).findAll('tr')
    best_rating = 0 
    best_num_votes = 0
    best_url = ''
    for result in results[1:]:  # skip the table heading
        rating_span = result.find('span', {'class': 'rating'})
        if not rating_span:
            # This tab received no votes, so we count it as average
            rating = 2.5
            num_votes = 0
        else:
            # Parse ultimate-guitar html formatting to find the ratings
            rating = int(rating_span.findAll('span')[0].get('class')[-1])
            num_votes = int(result.find('b', {'class':'ratdig'}).text)
        # This tab is the best if 1) it has the highest rating we've seen so far or 
        #                         2) it has the same rating as the best rating, and has more votes
        if rating > best_rating or (rating == best_rating and num_votes > best_num_votes):
            best_rating = rating
            best_num_votes = num_votes
            best_urls = result.findAll('a', {'class': 'song'})
            # The first row of each table additionally has the artist name link as the first 'song' anchor tag.
            best_url = best_urls[0]['href'] if len(best_urls) < 2 else best_urls[1]['href']  
    return best_url

def new_song_played(old_song, itunes):
    """Returns True when a new song is played, otherwise runs forever."""
    curr_song = itunes.current_track.name()
    if not old_song or curr_song != old_song:
        return True
    time.sleep(1)  # Note: This is an awful hack for identifying when the song has changed. 
                   # Unfortunately, iTunes makes event listening difficult for appscript. 

def display_new_tab(curr_song, curr_artist, window):
    """Loads guitar tab search page and then the best tab page into Chrome."""
    search_url, search_soup = tab_searchpage(curr_song, curr_artist)
    # Load the search url
    window.active_tab.URL.set(search_url)
    # Load the best-rated tab if tabs exist
    best_tab_url = best_rated_result(search_soup)
    if best_tab_url:
        # After the search results page loads, load the best tab.
        # We wait so that the browser "Back" button leads to the search page.
        while window.active_tab.loading():
            time.sleep(.25)
        window.active_tab.URL.set(best_tab_url)

def fetch_tabs_for_itunes():
    """Loads guitar tabs into Chrome when new songs are played in iTunes."""
    itunes = app(u'/Applications/iTunes.app')
    # Create a new chrome window
    chrome = app(u'/Applications/Google Chrome.app')
    window = chrome.make(new=k.window)
    curr_song = ''  # Initialize to empty
    # Continuously find tabs as new songs are played
    while True:
        # Check if a new song is playing
        try:
           if new_song_played(curr_song, itunes):
              curr_song = itunes.current_track.name()
              curr_artist = itunes.current_track.artist()
              try:
                  display_new_tab(curr_song, curr_artist, window)
              except CommandError:  # The user closed our Chrome window. 
                  window = chrome.make(new=k.window)  # Open a new window.
                  display_new_tab(curr_song, curr_artist, window)  # Retry
        except CommandError:  # iTunes is not open
         time.sleep(2)  # Wait


# Run the script
if __name__ == '__main__':
    fetch_tabs_for_itunes()
