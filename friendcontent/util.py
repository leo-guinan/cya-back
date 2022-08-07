def extract_url_from_text(text):
    url = text.split("http")[1]
    url = url.split(" ")[0]
    return "http" + url

