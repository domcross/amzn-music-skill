# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/headphones.svg' card_color='#E09404' width='50' height='50' style='vertical-align:bottom'/>
AMZN Music Player
Makes Mycroft play your amaz*n music library as if its name was Alexa :-)

## About
This skill requires an Amaz*n Music account and a subscription of type "music unlimited" or "prime music" - even if you want to stream music from your own library only.

WARNING: your Amaz\*n username and password will be stored in clear text in the skills settings.json.
Make sure to protect your Mycroft device (e.g. use secure passwords for ssh-user), otherwise your Amaz\*n account might be comprised - shopping spree for some else on your (bank) account

NOTE: this was tested on Mycroft Mark-1 and PiCroft (both running Debian Jessie) only and will probably run on PiCroft with Debian Stretch. Most likely this will not run on Ubuntu or other OS without tweaking requirements.sh at least (any assistance here is welcome)

NOTE: this will install 'VLC media player' as a requirement, which is a approx. 70MB download an will require additinal 250MB on your sd-card when unpacked...

## Examples
* "Hey ~~Alexa~~ Mycroft, play purple rain by prince on amaz*n music"
* "Hey Mycroft, play the album 25 by adele"
* "Hey Mycroft, play something by the foo fighters"
* "Hey Mycroft, play some jazz"

b.t.w.: German is supported too

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
