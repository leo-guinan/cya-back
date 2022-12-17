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
    Given the transcript of a podcast episode segment, identify the key points of the episode segment.
The transcript:
{transcript}

The key points:
    """
    return key_points


def podcast_transcript_to_links_to_include(transcript):
    links_to_include = f"""
   Given the transcript of a podcast episode segment, identify the links that need to be included in the show notes.

The transcript:
{transcript}
    
The links to include:
"""
    return links_to_include


def summarize_podcast_section_summaries(sections):
    combined_sections = "\n".join(sections)
    summary = f'''
    Given the summaries of the sections of a podcast episode, write a summary of the episode.
    The Section Summaries:
    {combined_sections}
    
    The summary:
    '''
    return summary


def summarize_podcast_section_key_points(sections):
    combined_sections = "\n".join(sections)
    important_key_points = f'''
    Given the key points of the sections of a podcast episode, identify the most important key points of the episode.
    The Section Key Points:
    {combined_sections}
    
    The most important key points:
    '''
    return important_key_points


def summarize_podcast_section_links_to_include(sections):
    combined_sections = "\n".join(sections)
    links_to_include = f'''
    Given the links to include of the sections of a podcast episode, identify the most important links to include in the show notes.
    The Section Links to Include:
    {combined_sections}
    
    The most important links to include:
    '''
    return links_to_include


def generate_show_notes(summary, key_points, links_to_include):
    show_notes = f'''
    Given the summary, key points, and links to include for a podcast episode, write the show notes for the episode.
    The Summary:
    {summary}
    
    The Key Points:
    {key_points}
    
    Links to Include:
    {links_to_include}
    
    The Show Notes:
    
    '''
    return show_notes
