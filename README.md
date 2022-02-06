<h1 align="center">QBitStream</h1>
<p align="center">Browse and stream torrents with qBittorrent API</p>

##

### How?

This is a Python script. It scrapes a torrent engine to get the magnet link, then uses [qBittorrent](https://github.com/qbittorrent/qBittorrent) to sequentially download the video while playing it with your player of choice (mpv by default).

## Dependencies

* [qBittorrent](https://github.com/qbittorrent/qBittorrent) - Torrent Client, with WebUI enabled (check bypass auth for clients on localhost or edit the credentials in the script). `sudo pacman -S qbittorrent`
* [qbittorrentapi](https://pypi.org/project/qbittorrent-api/) - `pip install qbittorrent-api`
