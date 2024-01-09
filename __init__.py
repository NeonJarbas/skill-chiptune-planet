import random
from os.path import join, dirname

import requests
from json_database import JsonStorageXDG

from ovos_utils.ocp import MediaType, PlaybackType
from ovos_workshop.decorators.ocp import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


class ChiptunePlanetSkill(OVOSCommonPlaybackSkill):
    def __init__(self, *args, **kwargs):
        self.skill_icon = self.default_bg = join(dirname(__file__), "res", "chiptuneplanet_icon.jpg")
        self.supported_media = [MediaType.MUSIC]
        self.n_mixes = 5
        self.archive = JsonStorageXDG("Chiptune Planet", subfolder="OCP")
        super().__init__(*args, **kwargs)

    def initialize(self):
        self._sync_db()
        self.load_ocp_keywords()

    def load_ocp_keywords(self):
        artists = []
        songs = []
        games = []
        genre = ["Chiptune", "chiptune cover"]

        for url, data in self.archive.items():
            t = data["title"].split("/ Chiptune Cover")[0].replace("♬", "").replace("—", "-").replace("–", "-").replace(
                "(8 bit)", "").replace("(8 bit Remix)", "").replace("Chiptune Cover", "").strip()
            if "-" in t:
                artist, song = t.split("-", 1)
                artists.append(artist.strip())
                songs.append(song.strip())
            elif "(Sega Genesis)" in t:
                game, song = t.split("(Sega Genesis)")
                songs.append(song.strip())
                games.append(game.strip())

        self.register_ocp_keyword(MediaType.MUSIC,
                                  "artist_name", artists)
        self.register_ocp_keyword(MediaType.GAME,
                                  "game_name", games)
        self.register_ocp_keyword(MediaType.MUSIC,
                                  "music_genre", genre)
        self.register_ocp_keyword(MediaType.MUSIC,
                                  "song_name", songs)
        self.register_ocp_keyword(MediaType.MUSIC,
                                  "music_streaming_provider",
                                  ["Chiptune Planet", "ChiptunePlanet"])

    def _sync_db(self):
        bootstrap = "https://github.com/JarbasSkills/skill-chiptune-planet/raw/dev/bootstrap.json"
        data = requests.get(bootstrap).json()
        self.archive.merge(data)
        self.schedule_event(self._sync_db, random.randint(3600, 24 * 3600))

    @ocp_search()
    def search_db(self, phrase, media_type):
        base_score = 15 if media_type == MediaType.MUSIC else 0
        entities = self.ocp_voc_match(phrase)
        base_score += 20 * len(entities)

        game = entities.get("game_name")
        artist = entities.get("artist_name")
        song = entities.get("song_name")

        skill = "movie_streaming_provider" in entities or \
                "music_genre" in entities  # generic skill match

        if skill:
            base_score += 35
            pl = self.featured_media()
            for i in range(self.n_mixes):
                random.shuffle(pl)
                yield {
                    "match_confidence": base_score,
                    "media_type": MediaType.MUSIC,
                    "playlist": pl[:25],
                    "playback": PlaybackType.AUDIO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": self.skill_icon,
                    "bg_image": self.default_bg,
                    "title": f"Chiptune Planet (Mix {i + 1})"
                }

        if artist or song or game:
            candidates = self.archive.values()

            # only search db if user explicitly requested a known song
            if artist:
                base_score += 15
                candidates = [video for video in candidates
                              if artist.lower() in video["title"].lower()]
            elif song:
                base_score += 10
                candidates = [video for video in candidates
                              if song.lower() in video["title"].lower()]
            elif game:
                base_score += 15
                candidates = [video for video in candidates
                              if game.lower() in video["title"].lower()]

            for video in candidates:
                yield {
                    "title": video["title"],
                    "artist": video["author"],
                    "match_confidence": min(100, base_score),
                    "media_type": MediaType.MUSIC,
                    "uri": "youtube//" + video["url"],
                    "playback": PlaybackType.AUDIO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["thumbnail"],
                    "bg_image": video["thumbnail"],
                }

    @ocp_featured_media()
    def featured_media(self, num_entries=50):
        return [
                   {
                       "match_confidence": 90,
                       "media_type": MediaType.MUSIC,
                       "uri": "youtube//" + entry["url"],
                       "playback": PlaybackType.AUDIO,
                       "image": entry["thumbnail"],
                       "bg_image": self.default_bg,
                       "skill_icon": self.skill_icon,
                       "skill_id": self.skill_id,
                       "title": entry["title"]
                   } for entry in self.archive.values()
               ][:num_entries]


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus

    s = ChiptunePlanetSkill(bus=FakeBus(), skill_id="t.fake")

    for r in s.search_db("play Megadeth chiptune", MediaType.MUSIC):
        print(r)
        # {'title': 'Megadeth - We’ll Be Back ♬Chiptune Cover♬', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=d9FZ65w6WtQ', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/d9FZ65w6WtQ/sddefault.jpg?sqp=-oaymwEmCIAFEOAD8quKqQMa8AEB-AH-CYAC0AWKAgwIABABGEEgYihlMA8=&rs=AOn4CLBz7pp29jigsiF_pv_9zj2ROFd9cA', 'bg_image': 'https://i.ytimg.com/vi/d9FZ65w6WtQ/sddefault.jpg?sqp=-oaymwEmCIAFEOAD8quKqQMa8AEB-AH-CYAC0AWKAgwIABABGEEgYihlMA8=&rs=AOn4CLBz7pp29jigsiF_pv_9zj2ROFd9cA'}
        # {'title': 'Megadeth - In My Darkest Hour ♬Chiptune Cover♬', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=zyaG1XQH6KY', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/zyaG1XQH6KY/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/zyaG1XQH6KY/sddefault.jpg'}
        # {'title': 'Megadeth - Wake Up Dead ♬Chiptune Cover♬', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=la_fYjztfj0', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/la_fYjztfj0/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/la_fYjztfj0/sddefault.jpg'}
        # {'title': 'Megadeth - Take No Prisoners ♬Chiptune Cover♬', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=lhLcYF-cqbQ', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/lhLcYF-cqbQ/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/lhLcYF-cqbQ/sddefault.jpg'}
        # {'title': 'Megadeth - Sweating Bullets  ♬Chiptune Cover♬', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=Q2IrNE6I5gM', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/Q2IrNE6I5gM/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/Q2IrNE6I5gM/sddefault.jpg'}
        # {'title': 'Megadeth - Trust ♬Chiptune Cover♬', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=3UY0f4dzPgs', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/3UY0f4dzPgs/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/3UY0f4dzPgs/sddefault.jpg'}
        # {'title': 'Megadeth - Tornado Of Souls ♬Chiptune Cover♬', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=huNYLG85Mfg', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/huNYLG85Mfg/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/huNYLG85Mfg/sddefault.jpg'}
        # {'title': 'Megadeth - A Tout Le Monde ♬Chiptune Cover♬', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=Wh7mhaJUmpo', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/Wh7mhaJUmpo/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/Wh7mhaJUmpo/sddefault.jpg'}
        # {'title': 'Megadeth - Hangar 18 ♬Chiptune Cover♬', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=q38GaRE6E7A', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/q38GaRE6E7A/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/q38GaRE6E7A/sddefault.jpg'}
        # {'title': 'Megadeth - Peace Sells  ♬Chiptune Cover♬', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=piVSNO1j2-o', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/piVSNO1j2-o/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/piVSNO1j2-o/sddefault.jpg'}
        # {'title': 'Megadeth - Symphony Of Destruction ♬Chiptune Cover♬', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=YpFpE9qIP-A', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/YpFpE9qIP-A/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/YpFpE9qIP-A/sddefault.jpg'}
        # {'title': 'Megadeth - The Threat Is Real (8 bit Remix)', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=ixwcAotGlXQ', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/ixwcAotGlXQ/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/ixwcAotGlXQ/sddefault.jpg'}
        # {'title': 'Megadeth - Trust (8 bit)', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=EQIwKpqrlrs', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/EQIwKpqrlrs/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/EQIwKpqrlrs/sddefault.jpg'}
        # {'title': 'Megadeth - Wake Up Dead (8 bit)', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=EI6-pd5ii5I', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/EI6-pd5ii5I/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/EI6-pd5ii5I/sddefault.jpg'}
        # {'title': 'Megadeth - Tornado Of Souls (8 bit)', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=_WEDAQrXSWs', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/_WEDAQrXSWs/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/_WEDAQrXSWs/sddefault.jpg'}
        # {'title': 'Megadeth - Take No Prisoners (8 bit)', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=nu3_j9kZ79w', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/nu3_j9kZ79w/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/nu3_j9kZ79w/sddefault.jpg'}
        # {'title': 'Megadeth - Sweating Bullets (8 bit)', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=vS41oaDDPpc', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/vS41oaDDPpc/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/vS41oaDDPpc/sddefault.jpg'}
        # {'title': "Megadeth - Skin O' My Teeth (8 bit)", 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=dUyEnHrshEo', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/dUyEnHrshEo/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/dUyEnHrshEo/sddefault.jpg'}
        # {'title': 'Megadeth - Peace Sells (8 bit)', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=yz0I6RTqO34', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/yz0I6RTqO34/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/yz0I6RTqO34/sddefault.jpg'}
        # {'title': 'Megadeth - In My Darkest Hour (8 bit)', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=LLytmO2WxVM', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/LLytmO2WxVM/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/LLytmO2WxVM/sddefault.jpg'}
        # {'title': 'Megadeth - Hangar 18 (8 bit)', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=Z7b7xpAAW78', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/Z7b7xpAAW78/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/Z7b7xpAAW78/sddefault.jpg'}
        # {'title': 'Megadeth - A Tout Le Monde (8 bit)', 'artist': 'Chiptune Planet', 'match_confidence': 75, 'media_type': <MediaType.MUSIC: 2>, 'uri': 'youtube//https://youtube.com/watch?v=dEkP_zyXebo', 'playback': <PlaybackType.AUDIO: 2>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://i.ytimg.com/vi/dEkP_zyXebo/sddefault.jpg', 'bg_image': 'https://i.ytimg.com/vi/dEkP_zyXebo/sddefault.jpg'}
