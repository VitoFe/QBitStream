import requests, re, os
from time import sleep
import qbittorrentapi

qbt_client = qbittorrentapi.Client(host='localhost:8080', username='admin', password='12345678')
try:
    qbt_client.auth_log_in()
except qbittorrentapi.LoginFailed as e:
    print(e)

ENGINES = [ "IlCorsaroNero", "1337x", "RARBG" ]
DL_PATH = qbt_client.app_default_save_path()
PLAYER = 'mpv --really-quiet --loop=no'
# 'vlc -q --play-and-exit'
ROWS = 15 #20

W  = '\033[0m'
R  = '\033[31m' # red
G  = '\033[32m' # green
O  = '\033[33m' # orange
B  = '\033[34m' # blue
P  = '\033[35m' # purple
Y  = '\033[1m' # bold

def get_hash(magnet):
    return re.search('magnet:\?xt=urn:btih:([0-9a-fA-F]{40,})\S[^">]*', magnet).group(1)

def get_magnet(link):
    r2 = requests.get(link)
    return re.search('"(magnet:\?xt=urn:btih:[0-9a-fA-F]{40,}\S[^">]*)"', r2.text).group(1)

def kill_torrent(t_hash):
    qbt_client.torrents_delete(delete_files=True, torrent_hashes=f"{t_hash}")

def run_stream(magnet):
    hashed = get_hash(magnet)
    timer = 0
    print("Running" , end ="", flush = True)
    for i in range(10):
        print("." , end ="", flush = True)
        sleep(2)
    progress = 0.0
    while progress <= 0.01:
        if timer > 60:
            should_wait = input("Torrent Dead/Very Slow! Try another [0] or wait [W]? ")
            if should_wait == "0":
                kill_torrent(hashed)
                return False
            timer = 0 # reset timer
        progress = qbt_client.torrents_info(torrent_hashes=f"{hashed}")[0]['progress']
        sleep(1)
        timer+=1
    timer = 0
    t_files = list()
    while len(t_files) <= 0:
        if timer > 60:
            print("Torrent Dead! Try another!")
            kill_torrent(hashed)
            return False
        sleep(1)
        t_files = qbt_client.torrents_files(torrent_hash=f"{hashed}")
        timer+=1
    for f in t_files:
        f_name = DL_PATH+f['name']
        if re.search('\.(xml|exe|txt|nfo|srt|jpg|jpeg|gif|png)$', f_name) != None or not os.path.isfile(f_name):
            continue
        f_progress = 0.0
        timer = 0
        while f_progress <= 0.025:
            if timer > 70:
                print("Torrent Dead/Too Slow! Try another!")
                kill_torrent(hashed)
                return False
            f_progress = qbt_client.torrents_files(torrent_hash=f"{hashed}")[int(f['index'])]['progress']
            sleep(1)
            timer+=1
        os.system(f'{PLAYER} "{f_name}"')
    kill_torrent(hashed)
    print("Terminated.")
    return True

def stream_torrent(engine_id, query):
    if engine_id == 0: # IlCorsaroNero
        r = requests.get(f'https://ilcorsaronero.link/argh.php?search={query}')
        links = list(dict.fromkeys(re.findall('"(https:\/\/ilcorsaronero.[a-z]{2,6}\/tor\/[a-zA-Z0-9?%-_]*)"', r.text)))
        seeds = list(re.findall('#00CC00.>([0-9]+)<', r.text))
        for i,link in enumerate(links):
            if i >= ROWS:
                break
            if len(seeds) < i+1:
                seed = 0
            else:
                seed = seeds[i]
            print(f"[{O}{i+1}{W}] ({G}{seed}{W}) {link.split('/')[-1].replace('_', ' ')}")
    elif engine_id == 1: # 1337x
        r = requests.get(f'https://1337x.wtf/search/{query}/1/')
        links = list(dict.fromkeys(re.findall('torrent\/[0-9]{6,}\/[a-zA-Z0-9?%-]*/', r.text)))
        seeds = list(re.findall('"seeds">([0-9]+)<', r.text))
        for i in range(len(links)):
            if i >= ROWS:
                break
            print(f"[{O}{i+1}{W}] ({G}{seeds[i]}{W}) {links[i].split('/')[2].replace('_', ' ')}")
            links[i] = "https://1337x.wtf/"+links[i]
    elif engine_id == 2: # RARBG
        r = requests.get(f'https://rarbgproxy.to/torrents.php?search={query}&order=seeders&by=DESC')
        links = list()
        links_t = list(dict.fromkeys(re.findall('href="\/(torrent\/[a-zA-Z0-9]{7})" title="(\S[^">]+)">', r.text)))
        seeds = list(re.findall('#008000.>([0-9]+)<', r.text))
        for i in range(len(links_t)):
            if i >= ROWS:
                break
            print(f"[{O}{i+1}{W}] ({G}{seeds[i]}{W}) {links_t[i][1]}")
            links.append("https://rarbgproxy.to/"+links_t[i][0])
    else:
        print("No engine found by that ID!")
        start_search(get_engine())
        return
    if len(links) <= 0:
        print("No result found for that Query! [Input 0 to change Engine]")
        start_search(engine_id)
        return
    def select_torrent():
        result = "Fails"
        while result.startswith("Fails"):
            chosen = int(input(f"{Y}Select: {W}")) - 1
            magnet = get_magnet(links[chosen])
            print("Downloading...")
            result = qbt_client.torrents_add(urls=f"{magnet}", download_path=DL_PATH, is_sequential_download=True, is_first_last_piece_priority=True)
            if result.startswith("Fails"):
                print("Download Failed! Select a different torrent!")
        sleep(1)
        if run_stream(magnet) == False:
            select_torrent()
    select_torrent()

def get_engine():
    for i, e in enumerate(ENGINES):
        print(f"[{O}{i+1}{W}] {O}{e}{W}")
    e_id = int(input(f"{Y}Select Engine: {W}"))-1
    print(f"{P}Using {ENGINES[e_id]} as Search Engine...{W}")
    return e_id

def start_search(e_id):
    qry = input(f"{Y}Search: {W}").replace(" ",".")
    if qry == "0":
        start_search(get_engine())
    else:
        stream_torrent(e_id, qry)

if __name__ == "__main__":
    start_search(get_engine())
