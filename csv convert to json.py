import requests
from bs4 import BeautifulSoup
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
import re

#  Set up the Selenium web driver
driver = webdriver.Chrome()
url = 'https://www.netflix.com/'
driver.get(url)

# Find the "Sign In" button and click it
sign_in_button = driver.find_element(By.ID, 'signIn')
sign_in_button.click()

# Find the username and password input fields, and the sign-in button
username_field = driver.find_element(By.ID, 'id_userLoginId')
password_field = driver.find_element(By.ID, 'id_password')
login_button = driver.find_element(By.CSS_SELECTOR, '.btn.login-button.btn-submit.btn-small')
# btn login-button btn-submit btn-small

# Enter your Netflix login credentials

username = "maxxxxxx@gmail.com"
password = "Mxxxx@xxxx"

username_field.send_keys(username)
password_field.send_keys(password)

login_button.click()

time.sleep(3)

profile_links = driver.find_elements(By.CLASS_NAME, 'profile-link')
netflixData  =[]
for profile_link in profile_links:
    try:
        profile_name_element = profile_link.find_element(By.CLASS_NAME, 'profile-name')
        if profile_name_element.text == 'Office':
            profile_link.click()
            time.sleep(2)
            url = 'https://www.netflix.com/browse/genre/34399?so=az'
            driver.get(url)

            num_scrolls = 2
            for _ in range(num_scrolls):
                # Simulate scrolling by sending the "END" key to the page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Adjust the delay as needed to let content load

            # Get the page source after navigating to the new URL
            page_source_after_navigation = driver.page_source

            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(page_source_after_navigation, 'html.parser')
            row_data = soup.find_all('div', class_='title-card-container ltr-0')
            for rowIndex,row_container in enumerate(row_data):
                content = row_container.find_all('div', class_='title-card')
                contentData = {}
                for div in content:
                    id_attribute = div.get('id')
                    if id_attribute:
                        contenId = soup.find_all('div',class_="title-card" ,id=id_attribute)
                        for div_with_id in contenId:
                            a_tag = div_with_id.find('a')
                            if a_tag:
                                a_tag_value = a_tag.get_text(strip=True)
                                a_tag_href = a_tag.get('href')
                                match = re.search(r'/watch/(\d+)', a_tag_href)

                                if match:
                                    video_id = match.group(1)
                                    contentData['name' ] = a_tag_value
                                    contentData['id'] = video_id
                                    contentData['movieUrl'] = f'https://www.netflix.com{a_tag_href}'
                                    netflixData.append(contentData)
                                    print(f'index =>{rowIndex} : ID => {video_id}')
                                else:
                                    print("Video ID not found")
                            else:
                                print("No <a> tag found in the element.")
                    else:
                        print("No 'id' attribute found in the element.")

    except StaleElementReferenceException:
        profile_links = driver.find_elements(By.CLASS_NAME, 'profile-link')
        continue
driver.quit()



movie_data = []
for index, movieData in enumerate(netflixData):
    id = movieData['id']
    url = f'https://www.netflix.com/title/{id}'
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the HTML content of the web page
        contentData = BeautifulSoup(response.content, 'html.parser')
        childScripts = contentData.find_all('script', type='application/ld+json')
        duration_span = contentData.find('span', class_='duration')
        movie_Link = contentData.find('span', class_='item-audio')

        contentNetflixData = {}

        for duration_spans in duration_span:
            duration = duration_spans.get_text().strip()
            contentNetflixData["runtime"] = duration
        #
        data = []
        trailerUrl = []
        #
        for detailData in childScripts:
            json_detailData = json.loads(detailData.string)
            if 'trailer' in json_detailData:
                for trl in json_detailData['trailer']:
                    trailerUrl.append(trl['contentUrl'])
            #
            url = json_detailData['url']
            parts = url.split('/')
            id = parts[-1]
            castList = []
            crewList = []
        #
            for actor in json_detailData['actors']:
                castList.append(actor['name'])

            for dire in json_detailData['director']:
                crewList.append(dire['name'])
        #
            contentNetflixData["backdrop_path"] = json_detailData['image'],
            contentNetflixData["genres"] = json_detailData['genre'],
            contentNetflixData["original_title"] = json_detailData['name'],
            contentNetflixData["overview"] = json_detailData['description'],
            contentNetflixData["release_date"] = json_detailData['dateCreated'],
            contentNetflixData["age_rating"] = json_detailData['contentRating'],
            contentNetflixData["title"] = json_detailData['name'],
            contentNetflixData["typeid"] = 4,
            contentNetflixData["poweredby"] = "Netflix",
            contentNetflixData["cast"] = castList,
            contentNetflixData["crew"] = crewList,
            contentNetflixData["id"] = id
            contentNetflixData["trailer"] = trailerUrl
        time_str = contentNetflixData["runtime"]
        time_parts = time_str.split()
        hours = 0
        minutes = 0

        for part in time_parts:
            if 'h' in part:
                hours = int(part[:-1])
            elif 'm' in part:
                minutes = int(part[:-1])
            #
        total_seconds = (hours * 3600) + (minutes * 60)
        audioList = []
        if (contentNetflixData["id"] == movieData['id']):
            id = movieData['id']
            movieUrl = movieData['movieUrl']
            contentNetflixData["playableUrl"] = movieUrl
            response = requests.get(movieUrl)
            if response.status_code == 200:

                contentData = BeautifulSoup(response.content, 'html.parser')
                childData = contentData.find_all('span', class_='more-details-item item-audio')
                for audio in childData:
                    dat = audio.text
                    audioList.append(dat)

        contentNetflixData['backdrop_path'] = contentNetflixData['backdrop_path'][0]
        contentNetflixData['original_title'] = contentNetflixData['original_title'][0]
        contentNetflixData["overview"] = contentNetflixData["overview"][0]
        contentNetflixData['release_date'] = contentNetflixData['release_date'][0]
        contentNetflixData['age_rating'] = contentNetflixData['age_rating'][0]
        contentNetflixData['title'] = contentNetflixData['title'][0]
        contentNetflixData['poweredby'] = contentNetflixData['poweredby'][0]
        contentNetflixData['genres'] = list(contentNetflixData['genres'])
        contentNetflixData['cast'] = contentNetflixData['cast'][0]
        contentNetflixData['crew'] = contentNetflixData['crew'][0]
        contentNetflixData["typeid"] = contentNetflixData["typeid"][0]
        contentNetflixData["runtime"] = total_seconds
        contentNetflixData["original_language"] = audioList
        print(f'{index} => {contentNetflixData}')
        movie_data.append(contentNetflixData)

df = pd.DataFrame(movie_data)
df.to_csv('C:/Users/91829/Desktop/netflixData/netflixdAllMovie.csv', index=False)

