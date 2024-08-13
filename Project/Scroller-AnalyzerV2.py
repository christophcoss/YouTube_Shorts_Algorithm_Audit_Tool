import base64
from dotenv import load_dotenv
import os
from googleapiclient.discovery import build
import json
import time
from openai import OpenAI
import numpy as np
from playwright.async_api import Playwright, async_playwright
import asyncio
import dateutil.parser as dp
import isodate
import ollama
import pandas as pd
from Helpers.playwright_helper import initialize, close, login, like_video, dislike_video, next_video, \
    get_video_url_id, share_video
from Helpers.video_metadata_helper import get_video_title, get_video_description, get_video_tags, get_playtime, \
     get_youtube_topics
from Project.Helpers.Classes import User
from Project.Helpers.database import Database

load_dotenv()
#API KEYS
youtube_api_key = os.getenv('YOUTUBE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

#APIS
llm = OpenAI(
  api_key=OPENAI_API_KEY
)
youtube = build('youtube', 'v3', developerKey = youtube_api_key)

#API FUNCTIONS
def get_completion_from_messages(messages, model='gpt-3.5-turbo', temperature=0, max_tokens=500):

    if model == 'llama3':
        response = ollama.chat(model=model, messages=messages)
        return response['message']['content']

    else:
        response = llm.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

def get_video_metadata(video_id):
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics,topicDetails",
        id=video_id
    )
    tries = 5
    while tries > 0:
        try:
            response = request.execute()
            return response
        except:
            tries -= 1

    return None


def get_youtube_category(category_id):
    request = youtube.videoCategories().list(
        part="snippet",
        id=str(category_id)
    )
    snippet = request.execute()
    return snippet['items'][0]['snippet']['title']


#MAIN CLASSIFICATION FUNCTION
def classify_video(video_id, url, model, system_message, user_message, delimiter, screenshot):
    start_time = time.time()

    metadata = get_video_metadata(video_id)
    title = get_video_title(metadata)
    description = get_video_description(metadata)
    tags = get_video_tags(metadata)
    channel_name = metadata['items'][0]['snippet']['channelTitle']
    youtube_category = get_youtube_category(metadata['items'][0]['snippet']['categoryId'])

    try:
        youtube_topics = get_youtube_topics(metadata)
    except:
        youtube_topics = []

    playtime = get_playtime(metadata)
    duration = isodate.parse_duration(playtime).total_seconds()
    database = Database('database.db')
    database.insert_video_metadata(video_id, title, description, str(tags), duration, channel_name, youtube_category, str(youtube_topics))

    image_message = {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot}"}}
    text_message = {"type": "text", "text": f"{delimiter}{user_message.format(title=title, description=description, tags=tags, channel_name=channel_name, youtube_category=youtube_category, youtube_topics=youtube_topics)}{delimiter}"}

    messages =  [
    {'role':'system',
     'content': system_message},
    {'role':'user',
     'content': [
         # image_message,
         text_message
        ],
     }
    ]

    tries = 5
    while tries > 0:
        print('Trying')
        response = get_completion_from_messages(messages, model)
        try:
            category = response.split(',')[0].strip()
            parent_category = response.split(',')[1].strip()
            break
        except:
            tries -= 1



    classification = {'channel_name': channel_name, 'title': title, 'description': description, 'tags': tags, 'url':url, 'youtube_category': youtube_category, 'youtube_topics': youtube_topics, 'category': category, 'parent_category': parent_category}

    end_time = time.time()
    execution_time = end_time - start_time

    return classification, execution_time, duration


#INITIALIZE USER
def initialize_user(user_id):
    with open('Input_data/users.json') as f:
        users = json.load(f)
    #TODO: Change the code when we will have multiple users
    user = User([user for user in users if user['id'] == user_id][0])

    return user


#INITIALIZE DATABASE
def initialize_database():
    database = Database('database.db')
    return database


#MESSAGES
delimiter = "####"





system_classification_message = """\

classify the following video in the most similar category based on the following title, description, tags, channel name, 
youtube category and youtube topics obtained from the youtube data api. 


Sometimes the youtube API does not assign the correct category to the video so please categorize it better if you deem it neccessary.

the youtube topics are a list of topics that youtube has assigned to the video. 

Try not to return generalized categories such as "entertainment" or "lifestyle" be a bit more specific by using the provided information.

Return the category name which should be one to two words as well as the parent category seperated by a comma.

The parent category is a more general category that the specific category falls under and should be one to two words.

Do not return an explanation why you chose a category

If you do not have enough information to categorize return the youtube category

To recap the format that you should return is: specific category, parent category

"""

user_classification_message = """\

title: {title}
description: {description}
tags: {tags}
channel: {channel_name}
youtube category: {youtube_category}
youtube topics: {youtube_topics}

"""
system_image_message = "You also have access to a screenshot of the video 1 second after it started playing."

system_decision_message = """\

Assume that you are a youtube user that has the following user_interests and you have just watched the following video with the following 
title, description, tags, channel name, youtube category and youtube topics obtained from the youtube data api. 

There is also a classification of the video that was made by a model giving the specific category and parent category of the video.

Based on the information provided how would the user react to the video based on his interests? 

Do act strictly based on the user interests and the video classification. Take into account that the user is a human and not a robot. 

The user might be open to watching videos that are not directly related to his interests but can be related in some way.

The possible reactions can we either positive or negative. A reaction can only be one of these two.

You should also return the reason why the user would react in that way in a few words.

The expected format is a JSON object with the keys "reaction" and "reason" with the values being a list of strings and a string respectively.

Example:

{
    "reaction": ["positive"],
    "reason": "The user would like the video because it is about a topic that he is interested in"
}

Example 2:

{
    "reaction": ["negative"],
    "reason": "The user would not like the video because it is about a topic that he is not interested in"
}

Ensure that the response is in JSON format but do not return code, only the JSON object as a string.


"""

user_decision_message = """\
user_interests: {interests}
title: {title}
description: {description}
tags: {tags}
channel: {channel_name}
youtube category: {youtube_category}
youtube topics: {youtube_topics}
parent_category: {parent_category}
specific_category: {specific_category}
"""




#MODEL
model = 'gpt-4o'

runtype = 'new_user_with_screenshots'

runs = [
    {'user_id': 28, 'number_videos_to_watch': 450}
]




async def get_reaction(classification, interests, system_decision_message, user_decision_message, delimiter):

    messages =  [
        {'role':'system',
            'content': system_decision_message},
        {'role':'user',
            'content': f"{delimiter}{user_decision_message.format(interests=interests, title=classification['title'], description=classification['description'], tags=classification['tags'], channel_name=classification['channel_name'], youtube_category=classification['youtube_category'], youtube_topics=classification['youtube_topics'], parent_category=classification['parent_category'], specific_category=classification['category'])}{delimiter}"},
        ]

    response = get_completion_from_messages(messages, model)

    response_dict = json.loads(response)

    return response_dict['reaction'], response_dict['reason']





async def main(user_id, number_videos_to_watch):
    user = initialize_user(user_id)
    user_id, email, password, interests, reactions,  = user.id, user.email, user.password, user.interests, user.reactions
    results = []
    database = initialize_database()
    database.insert_user(user_id, email, password, str(interests))
    same_video_tries = 3


    async with async_playwright() as playwright:
        browser, page = await initialize(playwright)
        await login(page, email, password)
        previous_url, previous_video_id = await get_video_url_id(page)


        for i in range(0, number_videos_to_watch):

            if same_video_tries == 0:
                print("Same video tries exceeded")
                break

            new_url, new_video_id = await get_video_url_id(page)
            same_video = new_url == previous_url
            while '/shorts/' not in previous_url or same_video:
                await asyncio.sleep(1)
                new_url, new_video_id = await get_video_url_id(page)
                same_video = new_url == previous_url
                previous_url = new_url
                previous_video_id = new_video_id
                if same_video:
                    await next_video(page)

            last_video_id_from_database = database.get_last_video_id(user_id)
            if last_video_id_from_database and last_video_id_from_database[0] == new_video_id:
                same_video_tries -= 1
                await next_video(page)
                break
            else:
                same_video_tries = 3

            # is_ad = await is_video_ad(page)
            #
            # if is_ad:
            #     print("Ad detected")
            #     await next_video(page)
            #     continue

            start_time = time.time()

            await asyncio.sleep(1)

            #screenshot to base64
            shorts_container = await page.wait_for_selector('#shorts-container.style-scope.ytd-shorts')
            screenshot = await shorts_container.screenshot()
            base64_screenshot = base64.b64encode(screenshot).decode()

            print(new_video_id)

            classification, execution_time, duration = classify_video(new_video_id, new_url, model, system_classification_message, user_classification_message, delimiter, base64_screenshot)


            print(f"{i:<5} {classification['title'][:20]:<30} Parent category: {classification['parent_category']:<30} Specific category: {classification['category']:<30} Duration: {duration} seconds")

            AIreaction, reason = await get_reaction(classification, interests, system_decision_message, user_decision_message, delimiter)

            print(f"Reaction: {str(AIreaction):<30} Reason: {reason}")

            print("\n")

            end_time = time.time()

            execution_time = end_time - start_time

            print('Execution time:', execution_time)

            if 'positive' in AIreaction:
                for reaction in reactions:
                    if np.random.rand(1) < reaction.probability and reaction.reaction in ['like', 'share', 'watch']:
                        AIreaction.append(f'actually_{reaction.reaction}')

            if 'negative' in AIreaction:
                for reaction in reactions:
                    if np.random.rand(1) < reaction.probability and reaction.reaction in ['skip', 'dislike']:
                        AIreaction.append(f'actually_{reaction.reaction}')

            already_seen = database.has_seen_video(user_id, new_video_id)
            already_liked = database.has_user_liked(user_id, new_video_id)
            already_disliked = database.has_user_disliked(user_id, new_video_id)
            can_like = not already_seen or (already_seen and not already_liked)
            can_dislike = not already_seen or (already_seen and not already_disliked)

            print('inserting')
            results.append({'url': classification['url'], 'title': classification['title'],
                            'parent_category': classification['parent_category'],
                            'specific_category': classification['category'], 'duration': duration,
                            'reaction': AIreaction, 'reason': reason, 'execution_time': execution_time})
            database.insert_video(classification['url'], new_video_id, user_id, classification['parent_category'],
                                  classification['category'], str(AIreaction), reason, execution_time,
                                  dp.parse(time.ctime()))



            if 'actually_like' in AIreaction and can_like:
                await like_video(page)

            if 'actually_share' in AIreaction:
                await share_video(page)

            if 'actually_dislike' in AIreaction and can_dislike:
                await dislike_video(page)

            if 'actually_skip' in AIreaction:
                await next_video(page)
                continue

            if 'actually_watch' in AIreaction:
                await asyncio.sleep(duration-execution_time)

            if 'actually_skip' not in AIreaction and AIreaction[0] == 'negative':
                await asyncio.sleep(duration-execution_time)

            await next_video(page)


        await close(browser=browser)

        df = pd.DataFrame(results)
        df.to_excel(excel_writer=f"results/{user_id}_{number_videos_to_watch}_{runtype}_{model}.xlsx")


for run in runs:
    number_videos_to_watch = run['number_videos_to_watch']
    user_id = run['user_id']
    asyncio.run(main(user_id, number_videos_to_watch))
