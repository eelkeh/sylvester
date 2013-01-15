import codecs
import base64
import hashlib

def list_to_tab(alist):
    fname = '%s.tab' % base64.urlsafe_b64encode(hashlib.md5(str(alist)).digest())[:-2] 
    f = codecs.open('results/%s' % fname, 'w', encoding='utf-8')
    for d in alist:
        f.write('%s\n' % '\t'.join([unicode(v) for v in d.values()]))  
    f.close()

    return fname
