#Helper functions to get video metadata
def get_video_title(metadata):
    return metadata['items'][0]['snippet'].get('title', '')

def get_video_description(metadata):
    return metadata['items'][0]['snippet'].get('description', '')

def get_video_tags(metadata):
    return metadata['items'][0]['snippet'].get('tags', '')

def get_playtime(metadata):
    return metadata['items'][0]['contentDetails'].get('duration', '')

def get_channel_name(metadata):
    return metadata['items'][0]['snippet'].get('channelTitle', '')

def get_video_category_id(metadata):
    return metadata['items'][0]['snippet'].get('categoryId', '')

def get_youtube_topics(metadata):
    topics = metadata['items'][0]['topicDetails'].get('topicCategories', '')
    return [topic.split('/')[-1] for topic in topics]