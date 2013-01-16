import codecs
import base64
import hashlib
import operator

def list_to_tab(alist):
    fname = '%s.csv' % base64.urlsafe_b64encode(hashlib.md5(str(alist)).digest())[:-2] 
    f = codecs.open('results/%s' % fname, 'w', encoding='utf-8')
    f.write('%s\n' % '\t'.join([unicode(v) for v in alist[0].keys()]))  
    for d in alist:
        f.write('%s\n' % '\t'.join([unicode(v).replace("\n", '') for v in d.values()]))  
    f.close()   

    return fname

def countdict_to_tab(countdict):
    fname = '%s.csv' % base64.urlsafe_b64encode(hashlib.md5(str(countdict)).digest())[:-2] 
    f = codecs.open('results/%s' % fname, 'w', encoding='utf-8')
    for key, count in countdict.iteritems():
        f.write('%s\t%s\n' % (key, count))
    f.close()

    return fname