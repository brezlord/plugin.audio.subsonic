import os
import sys
import urllib
import urlparse

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

# Make sure library folder is on the path
addon = xbmcaddon.Addon("plugin.audio.subsonic")
sys.path.append(xbmc.translatePath(os.path.join(
    addon.getAddonInfo("path"), "lib")))

import libsonic_extra


class Plugin(object):
    """
    Plugin container.
    """

    def __init__(self, addon_url, addon_handle, addon_args):
        self.addon_url = addon_url
        self.addon_handle = addon_handle
        self.addon_args = addon_args

        # Retrieve plugin settings
        self.url = addon.getSetting("subsonic_url")
        self.username = addon.getSetting("username")
        self.password = addon.getSetting("password")

        self.random_count = addon.getSetting("random_count")
        self.bitrate = addon.getSetting("bitrate")
        self.transcode_format = addon.getSetting("transcode_format")

        # Create connection
        self.connection = libsonic_extra.SubsonicClient(
            self.url, self.username, self.password)

    def build_url(self, query):
        """
        """

        parts = list(urlparse.urlparse(self.addon_url))
        parts[4] = urllib.urlencode(query)

        return urlparse.urlunparse(parts)

    def route(self):
        """
        Map a Kodi request to certain action.
        """

        mode = self.addon_args.get("mode", ["main_page"])[0]

        if not mode.startswith("_"):
            getattr(self, mode)()

    def add_track(self, track, show_artist=False):
        """
        Display one track in the list.
        """

        url = self.connection.streamUrl(
            sid=track["id"], maxBitRate=self.bitrate,
            tformat=self.trans_format)

        # Create list item
        if show_artist:
            li = xbmcgui.ListItem(
                "%s - %s" % (
                    track.get("artist", "<Unknown>"),
                    track.get("title", "<Unknown>")))
        else:
            li = xbmcgui.ListItem(track.get("title", "<Unknown>"))

        # Handle cover art
        if "coverArt" in track:
            cover_art_url = self.connection.getCoverArtUrl(track["coverArt"])

            li.setIconImage(cover_art_url)
            li.setThumbnailImage(cover_art_url)
            li.setProperty("fanart_image", cover_art_url)

        # Handle metadata
        li.setProperty("IsPlayable", "true")
        li.setInfo(type="Music", infoLabels={
            "Artist": track["artist"],
            "Title": track["title"],
            "Year": track.get("year"),
            "Duration": track.get("duration"),
            "Genre": track.get("genre")})

        xbmcplugin.addDirectoryItem(
            handle=self.addon_handle, url=url, listitem=li)

    def add_album(self, album, show_artist=False):
        """
        Display one album in the list.
        """

        url = self.build_url({
            "mode": "track_list",
            "album_id": album["id"]})

        # Create list item
        if show_artist:
            li = xbmcgui.ListItem(
                "%s - %s" % (
                    album.get("artist", "<Unknown>"),
                    album.get("name", "<Unknown>")))
        else:
            li = xbmcgui.ListItem(album.get("name", "<Unknown>"))

        # Handle cover art
        if "coverArt" in album:
            cover_art_url = self.connection.getCoverArtUrl(album["coverArt"])

            li.setIconImage(cover_art_url)
            li.setThumbnailImage(cover_art_url)
            li.setProperty("fanart_image", cover_art_url)

        # Handle metadata
        li.setProperty("IsPlayable", "false")

        xbmcplugin.addDirectoryItem(
            handle=self.addon_handle, url=url, listitem=li, isFolder=True)

    def main_page(self):
        """
        Display main menu.
        """

        menu = [
            {"mode": "playlists_list", "foldername": "Playlists"},
            {"mode": "artist_list", "foldername": "Artists"},
            {"mode": "genre_list", "foldername": "Genres"},
            {"mode": "random_list", "foldername": "Random songs"}]

        for entry in menu:
            url = self.build_url(entry)

            li = xbmcgui.ListItem(entry["foldername"])
            xbmcplugin.addDirectoryItem(
                handle=self.addon_handle, url=url, listitem=li, isFolder=True)

        xbmcplugin.endOfDirectory(self.addon_handle)

    def playlists_list(self):
        """
        Display playlists.
        """

        for playlist in self.connection.walk_playlists():
            cover_art_url = self.connection.getCoverArtUrl(
                playlist["coverArt"])
            url = self.build_url({
                "mode": "playlist_list", "playlist_id": playlist["id"]})

            li = xbmcgui.ListItem(playlist["name"], iconImage=cover_art_url)
            xbmcplugin.addDirectoryItem(
                handle=self.addon_handle, url=url, listitem=li, isFolder=True)

        xbmcplugin.endOfDirectory(self.addon_handle)

    def playlist_list(self):
        """
        Display playlist tracks.
        """

        playlist_id = self.addon_args["playlist_id"][0]

        for track in self.connection.walk_playlist(playlist_id):
            self.add_track(track, show_artist=True)

        xbmcplugin.setContent(self.addon_handle, "songs")
        xbmcplugin.endOfDirectory(self.addon_handle)

    def genre_list(self):
        """
        Display list of genres menu.
        """

        for genre in self.connection.walk_genres():
            url = self.build_url({
                "mode": "albums_by_genre_list",
                "foldername": genre["value"].encode("utf-8")})

            li = xbmcgui.ListItem(genre["value"])
            xbmcplugin.addDirectoryItem(
                handle=self.addon_handle, url=url, listitem=li, isFolder=True)

        xbmcplugin.endOfDirectory(self.addon_handle)

    def albums_by_genre_list(self):
        """
        Display album list by genre menu.
        """

        genre = self.addon_args["foldername"][0].decode("utf-8")

        for album in self.connection.walk_album_list_genre(genre):
            self.add_album(album, show_artist=True)

        xbmcplugin.setContent(self.addon_handle, "albums")
        xbmcplugin.endOfDirectory(self.addon_handle)

    def artist_list(self):
        """
        Display artist list
        """

        for artist in self.connection.walk_artists():
            cover_art_url = self.connection.getCoverArtUrl(artist["id"])
            url = self.build_url({
                "mode": "album_list",
                "artist_id": artist["id"]})

            li = xbmcgui.ListItem(artist["name"])
            li.setIconImage(cover_art_url)
            li.setThumbnailImage(cover_art_url)
            li.setProperty("fanart_image", cover_art_url)
            xbmcplugin.addDirectoryItem(
                handle=self.addon_handle, url=url, listitem=li, isFolder=True)

        xbmcplugin.setContent(self.addon_handle, "artists")
        xbmcplugin.endOfDirectory(self.addon_handle)

    def album_list(self):
        """
        Display list of albums for certain artist.
        """

        artist_id = self.addon_args["artist_id"][0]

        for album in self.connection.walk_artist(artist_id):
            self.add_album(album)

        xbmcplugin.setContent(self.addon_handle, "albums")
        xbmcplugin.endOfDirectory(self.addon_handle)

    def track_list(self):
        """
        Display track list.
        """

        album_id = self.addon_args["album_id"][0]

        for track in self.connection.walk_album(album_id):
            self.add_track(track)

        xbmcplugin.setContent(self.addon_handle, "songs")
        xbmcplugin.endOfDirectory(self.addon_handle)

    def random_list(self):
        """
        Display random options.
        """

        menu = [
            {"mode": "random_by_genre_list", "foldername": "By genre"},
            {"mode": "random_by_year_list", "foldername": "By year"}]

        for entry in menu:
            url = self.build_url(entry)

            li = xbmcgui.ListItem(entry["foldername"])
            xbmcplugin.addDirectoryItem(
                handle=self.addon_handle, url=url, listitem=li, isFolder=True)

        xbmcplugin.endOfDirectory(self.addon_handle)

    def random_by_genre_list(self):
        """
        Display random genre list.
        """

        for genre in self.connection.walk_genres():
            url = self.build_url({
                "mode": "random_by_genre_track_list",
                "foldername": genre["value"].encode("utf-8")})

            li = xbmcgui.ListItem(genre["value"])
            xbmcplugin.addDirectoryItem(
                handle=self.addon_handle, url=url, listitem=li, isFolder=True)

        xbmcplugin.endOfDirectory(self.addon_handle)

    def random_by_genre_track_list(self):
        """
        Display random tracks by genre
        """

        genre = self.addon_args["foldername"][0].decode("utf-8")

        for track in self.connection.walk_random_songs(
                size=self.random_count, genre=genre):
            self.add_track(track, show_artist=True)

        xbmcplugin.setContent(self.addon_handle, "songs")
        xbmcplugin.endOfDirectory(self.addon_handle)

    def random_by_year_list(self):
        """
        Display random tracks by year.
        """

        from_year = xbmcgui.Dialog().input(
            "From year", type=xbmcgui.INPUT_NUMERIC)
        to_year = xbmcgui.Dialog().input(
            "To year", type=xbmcgui.INPUT_NUMERIC)

        for track in self.connection.walk_random_songs(
                size=self.random_count, from_year=from_year, to_year=to_year):
            self.add_track(track, show_artist=True)

        xbmcplugin.setContent(self.addon_handle, "songs")
        xbmcplugin.endOfDirectory(self.addon_handle)


def main():
    """
    Entry point for this plugin.
    """

    addon_url = sys.argv[0]
    addon_handle = int(sys.argv[1])
    addon_args = urlparse.parse_qs(sys.argv[2][1:])

    # Route request to action
    Plugin(addon_url, addon_handle, addon_args).route()

# Start plugin from within Kodi
if __name__ == "__main__":
    main()
