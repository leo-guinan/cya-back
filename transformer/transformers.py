def podcast_components_to_shownotes(summary, key_points, links_to_include):
    shownotes = f"""
    Given the key points, summary, and links to include for a podcast episode, write the show notes for the episode.
    The Key Points:
    {'''
    '''.join(key_points)}
    
    Summary:
    {summary}

    Links to Include:
    {'''
    '''.join(links_to_include)}
    
    The Show Notes:
    
    """
    return shownotes


def podcast_transcript_to_summary(transcript):
    summary = f"""
    Given the transcript of a podcast episode segment, write a summary of the episode segment.

    The transcript:
    {transcript}
    
    The summary:
    """
    return summary


def podcast_transcript_to_key_points(transcript):
    key_points = f"""
    Given the transcript of a podcast episode segment, identify the key points of the episode segment in the given JSON format.
The Format: 
{{
    "keyPoints": [
"keyPoint1",
 "keyPoint2",
 ... ,
"keyPointN"
]
}}

The transcript:
{transcript}

The key points:
    """
    return key_points


def podcast_transcript_to_links_to_include(transcript):
    links_to_include = f"""
   Given the transcript of a podcast episode segment, identify the links that need to be included in the show notes and return them in the given JSON format.
The Format: 
{{
"linksToInclude": [
{{
"name": "<name of link1>",
"url": "<url of link1>"
}},
{{
"name": "<name of link2>",
"url": "<url of link2>"
}},
... ,
{{
"name": "<name of linkN>",
"url": "<url of linkN>"
}},
]
}}

The transcript:
{transcript}
    
The links to include:
"""
    return links_to_include

