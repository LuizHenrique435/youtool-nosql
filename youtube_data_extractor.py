from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from conf import YOUTUBE_API_KEY

def build_youtube_service():
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_channel_info(channel_id):
    try:
        youtube = build_youtube_service()
        request = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        response = request.execute()
        items = response.get('items', [])
        if not items:
            return {"error": "Canal não encontrado"}
        channel = items[0]
        snippet = channel['snippet']
        stats = channel['statistics']
        return {
            "title": snippet.get('title'),
            "description": snippet.get('description'),
            "published_at": snippet.get('publishedAt'),
            "subscriber_count": stats.get('subscriberCount'),
            "video_count": stats.get('videoCount'),
            "view_count": stats.get('viewCount'),
        }
    except Exception as e:
        return {"error": f"Erro ao obter dados do canal: {str(e)}"}

def get_channel_videos(channel_id, max_results=5):
    try:
        youtube = build_youtube_service()
        request = youtube.search().list(
            part="id",
            channelId=channel_id,
            maxResults=max_results,
            order="date",
            type="video"
        )
        response = request.execute()
        video_ids = [item['id']['videoId'] for item in response.get('items', [])]
        return video_ids
    except Exception as e:
        return {"error": f"Erro ao listar vídeos do canal: {str(e)}"}

def get_video_metadata(video_id):
    try:
        youtube = build_youtube_service()
        request = youtube.videos().list(
            part="snippet,liveStreamingDetails,statistics",
            id=video_id
        )
        response = request.execute()
        items = response.get('items', [])
        if not items:
            return {"error": "Vídeo não encontrado"}

        video = items[0]
        snippet = video['snippet']
        stats = video.get('statistics', {})
        live_details = video.get('liveStreamingDetails', {})

        return {
            "title": snippet.get('title'),
            "description": snippet.get('description'),
            "channel_title": snippet.get('channelTitle'),
            "published_at": snippet.get('publishedAt'),
            "view_count": stats.get('viewCount'),
            "like_count": stats.get('likeCount'),
            "live_chat_id": live_details.get('activeLiveChatId')
        }
    except Exception as e:
        return {"error": f"Erro ao obter metadados do vídeo: {str(e)}"}

def get_transcript(video_id):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id)
    except Exception:
        return []

def get_comments(video_id, max_results=50):
    try:
        youtube = build_youtube_service()
        comments = []
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=min(max_results, 100),
            textFormat='plainText'
        )
        response = request.execute()
        for item in response.get('items', []):
            top_comment = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'author': top_comment.get('authorDisplayName'),
                'text': top_comment.get('textDisplay'),
                'published_at': top_comment.get('publishedAt')
            })
        return comments
    except Exception:
        return []

def get_live_chat_messages(live_chat_id, max_messages=50):
    try:
        youtube = build_youtube_service()
        messages = []
        request = youtube.liveChatMessages().list(
            liveChatId=live_chat_id,
            part="snippet,authorDetails",
            maxResults=200
        )
        response = request.execute()

        for item in response.get('items', []):
            snippet = item['snippet']
            author = item['authorDetails']

            message_data = {
                'author': author.get('displayName'),
                'message': snippet.get('displayMessage'),
                'timestamp': snippet.get('publishedAt'),
                'type': snippet.get('type'),
            }

            # Verifica se é super chat
            if snippet.get('type') == 'superChatEvent':
                details = snippet.get('superChatDetails', {})
                message_data['amount'] = details.get('amountDisplayString', '')

            messages.append(message_data)

        return messages[:max_messages]
    except Exception as e:
        print("Erro ao buscar live chat:", str(e))
        return []

def get_super_chats(live_chat_messages):
    return [
        {
            "author": msg["author"],
            "message": msg["message"],
            "timestamp": msg["timestamp"],
            "amount": msg.get("amount", "")
        }
        for msg in live_chat_messages
        if msg["type"] == "superChatEvent"
    ]


def get_all_video_data(video_id):
    metadata = get_video_metadata(video_id)
    if isinstance(metadata, dict) and "error" in metadata:
        return metadata

    transcript = get_transcript(video_id)
    comments = get_comments(video_id)

    live_chat = []
    super_chats = []

    live_chat_id = metadata.get('live_chat_id')
    if live_chat_id:
        live_chat = get_live_chat_messages(live_chat_id)
        super_chats = get_super_chats(live_chat)

    return {
        "video_id": video_id,
        "metadata": metadata,
        "transcript": transcript,
        "comments": comments,
        "live_chat": live_chat,
        "super_chats": super_chats
    }

def get_channel_id_from_handle(handle):
    try:
        youtube = build_youtube_service()
        request = youtube.search().list(
            q=handle,
            type="channel",
            part="snippet",
            maxResults=1
        )
        response = request.execute()
        items = response.get('items', [])
        if not items:
            return None
        return items[0]['snippet']['channelId']
    except Exception as e:
        return None

def get_channel_data(identifier):
    # Detectar se é um @handle
    if identifier.startswith("@"):
        channel_id = get_channel_id_from_handle(identifier)
        if not channel_id:
            return {"error": "Não foi possível resolver o handle do canal"}
    else:
        channel_id = identifier

    channel_info = get_channel_info(channel_id)
    if "error" in channel_info:
        return channel_info

    video_ids = get_channel_videos(channel_id)
    if isinstance(video_ids, dict) and "error" in video_ids:
        return video_ids

    videos_data = []
    for vid in video_ids:
        video_data = get_all_video_data(vid)
        if "error" not in video_data:
            videos_data.append(video_data)

    return {
        "channel_id": channel_id,
        "channel_info": channel_info,
        "videos": videos_data
    }
