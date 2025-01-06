

def link2testclient(link, ui=False):
    base_string = "https://127.0.0.1:5000/api/" if not ui else "https://127.0.0.1:5000/"
    return link[len(base_string) - 1 :]
