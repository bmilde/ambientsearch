import time
from bridge import KeywordClient, KeywordClientHacky

std_spk = "You"
utt = ""
old_utt = ""

ks = KeywordClient(server_url="http://localhost:5000/")
old_utt = utt
utt = "This"
ks.addUtterance(utt,std_spk)
time.sleep(0.5)

old_utt = utt
utt = "This is"
ks.replaceLastUtterance(old_utt,utt,std_spk)
time.sleep(0.4)

old_utt = utt
utt = "This is a"
ks.replaceLastUtterance(old_utt,utt,std_spk)
time.sleep(0.2)

old_utt = utt
utt = "This is a test"
ks.replaceLastUtterance(old_utt,utt,std_spk)
time.sleep(0.5)

