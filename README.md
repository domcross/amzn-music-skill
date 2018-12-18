# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/headphones.svg' card_color='#E09404' width='50' height='50' style='vertical-align:bottom'/>
 AMZN Music Player
Makes Mycroft play your amaz*n music library as if its name was Alexa :-)

## About
This skill requires an Amaz*n Music account and a subscription of type "music unlimited" or "prime music" - even if you want to stream music from your own library only.

## Examples
* "Hey ~~Alexa~~ Mycroft, play purple rain by prince on amaz*n music"

## Credits
Dominik (@domcross)

@Jaffa for the [amaz*n music api python library](https://github.com/Jaffa/amazon-music)

@forslund for inspiration and code from [spotify-skill](https://github.com/forslund/spotify-skill/)

## Troubleshooting
In case you receive authentication errors you must go to [Amaz*n Music website](https://music.amazon.com/) and re-confirm your account.

Mycroft-Core has a requirement for python-vlc (version==1.1.2), probably you have to "sudo mycroft-pip uninstall python-vlc" and then again "sudo mycroft-pip install pyhton-vlc==1.1.2"

## Category
**Music**

## Tags
#amzn
#music
