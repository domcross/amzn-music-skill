# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/headphones.svg' card_color='#E09404' width='50' height='50' style='vertical-align:bottom'/>
AMZN Music Player
Makes Mycroft play your amaz*n music library as if its name was Alexa :-)

## About
This skill requires an Amaz*n Music account and a subscription of type "music unlimited" or "prime music" - even if you want to stream music from your own library only.

After skill is installed is you must either:

a) enter your login credentials at home.mycroft.ai > Skills > Amzn music
WARNING: with this option your Amaz\*n username and password will be stored i) on a server hosted by mycroft.ai and ii) in clear text in the skills 'settings.json' file.

b) run './credentials.py' in the skills directory and enter your login credentials there.
In this case your credentials will be stored encoded & pickled in file 'credentials.store' - this option is recommended if you care for privacy.
NOTE: file 'credentials.store' must be owned by mycroft:mycroft - either run credentials.py as user 'mycroft' or sudo chown mycroft:mycroft credentals.store afterwards.

NOTE: this was tested only on Mycroft Mark-1 and PiCroft (both running Debian Jessie) and will probably run (not tested yet) on PiCroft with Debian Stretch.
Most likely this will not run on Ubuntu or other OS without tweaking requirements.sh at least (any assistance here is welcome)

NOTE: this will install 'VLC media player' as a requirement, which is a approx. 70MB download an will require additinal 250MB on your sd-card when unpacked...

## Examples
* "Hey ~~Alexa~~ Mycroft, play the song purple rain by prince on amaz*n music"
* "Hey Mycroft, play the album 25 by adele"
* "Hey Mycroft, play something by the foo fighters"
* "Hey Mycroft, play some jazz"

b.t.w.: German is supported too

## Credits
Dominik (@domcross)

@Jaffa for the [amaz*n music api python library](https://github.com/Jaffa/amazon-music)

@forslund and the rest of the Mycroft Dev team for inspiration and code from [spotify-skill](https://github.com/forslund/spotify-skill/)

## Troubleshooting
In case you receive authentication errors you must go to [Amaz*n Music website](https://music.amazon.com/) and re-confirm your account.

## Known issues
Mycroft-Core has a requirement for python-vlc (version==1.1.2), probably you have to "sudo mycroft-pip uninstall python-vlc" and then again "sudo mycroft-pip install pyhton-vlc==1.1.2"

The MP3-stream is encoded with 22KHz sampling rate. The same stream-URL played with VLC on my desktop (iMac) plays with 44KHz.

Sometimes the audio service gets broken and Mycroft will no longer play the MP3 stream. A reboot of your Mycroft device helps in that case...

The Amaz*n music service seems to have a limit on maximum concurrent connections and/or number of request over a certain time period.
If no music is played watch your logs for error messages...


## Category
**Music**

## Tags
#amzn
#music
