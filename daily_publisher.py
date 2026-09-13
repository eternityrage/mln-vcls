import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        if os.path.exists(specific_video):
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"Error: Specific video {name} not found")
            return None, None

    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Milana's Heavenly Voice Will Give You Chills",
        "Pure Magic: Milana Singing from the Heart",
        "The Most Beautiful Vocal Performance by Milana",
        "Milana's Soulful Melody That Touches the Spirit",
        "Listen to This Angelic Voice - Milana Vocals",
        "Milana Singing This Beautiful Song Will Make Your Day",
        "Raw Talent: Milana's Unforgettable Singing Moment",
        "When Milana Sings, Everything Else Fades Away",
        "An Absolute Vocal Masterpiece by Milana",
        "Milana's Mesmerizing Singing - Pure Acoustic Perfection",
    ]

    fallback_descriptions = [
        "There is something truly captivating about Milana's voice. Every note carries so much emotion, passion, and beauty that it instantly touches your soul. Whether you're unwinding after a long day or looking for musical inspiration, her soulful melodies remind us of the pure power of singing. Drop a ❤️ if Milana's singing made you smile today! #milana #milanavocals #singing #vocalist #beautifulvoice #acousticmusic #singer #soulsinging #coversong #musicvibes #singersongwriter",
        "Milana's vocal control and emotional depth here are out of this world. You can feel every single lyric straight from the heart. Music like this is rare and deserves to be heard around the world. Share this video with someone who needs some beautiful acoustic music today! #milana #milanavocals #singingtalent #vocals #beautifulsong #musiclovers #acousticvibes #soulfulvocals #livemusic",
        "Close your eyes and just listen to Milana sing. Her voice is like a warm embrace on a quiet evening, blending gentle acoustic sweetness with immense emotional strength. Leave a comment below with your favorite song you'd love to hear Milana sing next! #milana #milanavocals #angelicvoice #singersoftiktok #vocalperformance #heartfeltsong #musictherapy #singing",
        "When an artist sings with true authenticity, you don't just hear the melody - you feel it deep inside. Milana brings that exact heartfelt energy in every video she shares with us. Follow Milana Vocals for your daily dose of uplifting, breathtaking singing! #milana #milanavocals #singingvideos #voiceofangels #talentedmusicians #musicreels #beautifulsinging #viralvocals",
        "Milana never fails to blow us away with her effortless range and heartfelt tone. This song showcases the warmth and vulnerability that make her such a special vocalist. Hit that like button and follow for more stunning acoustic performances from Milana! #milana #milanavocals #rawvocals #unplugged #soulfulsinger #beautifulmelody #acousticcover #vocalistlife",
        "From delicate acoustic melodies to powerful soulful belts, Milana's voice has a charm that captivates you from the very first second. Tell us in the comments what emotion this song gave you! #milana #milanavocals #musiclovers #singingreels #acousticvibes #melodicperfection #singingclips #soulmusic",
        "Is there anything more peaceful than listening to Milana singing a gorgeous song? Her tone is so sweet, soothing, and effortlessly expressive. Tag a friend who loves discovering extraordinary singing talent! #milana #milanavocals #singingtalent #acousticlife #vocalsworthsharing #hearttouching #coversong",
        "Pure vocal bliss! Milana delivers another enchanting performance with so much poise and feeling. Her love for music shines through every melody. Make sure to follow Milana Vocals for regular acoustic magic! #milana #milanavocals #goodmusic #vocalpower #singinggirl #acousticmusician #musicforthesoul",
        "Milana's ability to tell stories through song is truly gift. Each verse feels intimate, sincere, and beautifully crafted. Double tap if you could listen to her sing on repeat all day! #milana #milanavocals #songstories #acousticmelodies #voiceofgold #talentedartists #lovesinging",
        "A little musical sanctuary for your feed. Milana sharing her singing gift with the world is exactly what we all need today. Let her stunning vocals brighten your day and inspire your heart. #milana #milanavocals #musicislove #inspiringvocals #acousticsoul #vocalmagic #singers"
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "heartfelt, emotional, and soulful - highlighting how deeply Milana's voice and singing touch the heart",
        "uplifting, inspiring, and joyful - celebrating Milana's incredible singing talent and positive energy",
        "serene, calm, and soothing - emphasizing the peaceful, relaxing, and acoustic beauty of Milana's melodies",
        "mesmerizing, passionate, and awe-inspiring - hyping up Milana's vocal range and raw acoustic performance",
        "warm, intimate, and friendly - inviting music lovers to enjoy and share Milana's song with friends",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"of the singer Milana performing a beautiful song for the Facebook page 'Milana Vocals'. "
        f"The page features Milana singing beautiful, heartfelt, acoustic songs and vocal melodies that touch the heart. "
        f"Speak as a passionate music fan celebrating Milana's singing talent and beautiful voice. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and musical. "
        f"Include engagement calls-to-action such as: "
        f"- Like if you love Milana's voice! "
        f"- Comment your favorite song or what you'd love Milana to sing next! "
        f"- Share this with someone who loves beautiful acoustic singing! "
        f"- Follow Milana Vocals for more breathtaking songs and daily melodies! "
        f"Include relevant hashtags in ALL LOWERCASE such as #milana #milanavocals #singing #vocalist #beautifulvoice #acousticmusic #singer #soulsinging #coversong #musicvibes #singersongwriter. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("DAILY AUTOMATION STARTING - MILANA VOCALS")
    print("=" * 60)

    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("No new videos found to publish. Exiting.")
        return

    print(f"Selected Video: {video_name}")
    print("Generating caption via Pollination AI...")
    title, description = generate_caption()

    print(f"Title: {title}")
    print(f"Description:\n{description}")

    combined_caption = f"{title}\n\n{description}"

    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }

    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"Instagram Reel upload failed: {e}")

    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"Instagram Story upload failed: {e}")

    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"Facebook Reel upload failed: {e}")

    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"Facebook Story upload failed: {e}")

    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"Threads upload failed: {e}")

    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["milana", "milanavocals", "singing", "vocalist", "beautifulvoice", "acousticmusic", "singer", "soulsinging", "coversong", "musicvibes", "singersongwriter"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"YouTube upload failed: {e}")

    print("\nMarking video as published.")

    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)

    if is_recycled:
        print(f"   This is a recycled video (re-publishing)")

    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })

    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)

    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"Moved published video to {dest_path}")
    except Exception as e:
        print(f"Failed to move published video: {e}")

    print("DAILY AUTOMATION COMPLETE - MILANA VOCALS")

if __name__ == "__main__":
    main()
