def prefquality(video_list, qualityask):
    maxquality = int(qualityask)
    if maxquality == 4:
        return "selector called"

    vidurl = None
    if isinstance(video_list, dict):
        qualities = [2160, 1080, 720, 576]
        quality = qualities[maxquality]
        print(f"DEBUG: maxquality={maxquality}, target_quality={quality}")
        
        # Normalization
        for key in list(video_list.keys()):
            if key.lower().endswith("p60"):
                video_list[key.replace("p60", "")] = video_list[key]
                video_list.pop(key)
            else:
                if key.lower() == "4k":
                    video_list["2160"] = video_list[key]
                    video_list.pop(key)

        print(f"DEBUG: Normalized video_list={video_list}")

        parsed_video_list = []
        for key, value in list(video_list.items()):
            digits = "".join([y for y in key if y.isdigit()])
            parsed_video_list.append((int(digits) if digits else -1, value))
        
        parsed_video_list = sorted(parsed_video_list, reverse=True)
        print(f"DEBUG: Parsed and sorted video_list={parsed_video_list}")

        for video in parsed_video_list:
            print(f"DEBUG: Checking video={video}")
            if quality >= video[0]:
                print(f"DEBUG: quality {quality} >= video[0] {video[0]} - MATCH")
                vidurl = video[1]
                break
            else:
                print(f"DEBUG: quality {quality} < video[0] {video[0]}")
                if str(quality) in str(video[0]):
                    print(f"DEBUG: str(quality) {quality} in str(video[0]) {video[0]} - MATCH (substring)")
                    vidurl = video[1]
                    break
        if not vidurl and parsed_video_list:
            vidurl = parsed_video_list[-1][1]
            print(f"DEBUG: Fallback to lowest quality: {vidurl}")
    return vidurl

sources = {
    "2160p": "https://cdn.example.com/video-4k.mp4",
    "1080p": "https://cdn.example.com/video-1080p.mp4",
    "720p": "https://cdn.example.com/video-720p.mp4",
}
print("Testing with qualityask=0")
result = prefquality(sources.copy(), "0")
print(f"RESULT: {result}")

sources2 = {
    "2160p": "https://cdn.example.com/video-4k.mp4",
    "1080p": "https://cdn.example.com/video-1080p.mp4",
    "720p": "https://cdn.example.com/video-720p.mp4",
    "480p": "https://cdn.example.com/video-480p.mp4",
}
print("\nTesting with qualityask=2")
result = prefquality(sources2.copy(), "2")
print(f"RESULT: {result}")
