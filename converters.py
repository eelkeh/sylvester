import codecs
import base64
import hashlib
import operator

def list_to_tab(alist):
    fname = '%s.csv' % base64.urlsafe_b64encode(hashlib.md5(str(alist)).digest())[:-2] 
    f = codecs.open('static/download/%s' % fname, 'w', encoding='utf-8')
    keylist = alist[0].keys()
    keylist.sort()
    f.write('%s\n' % '\t'.join([unicode(k) for k in keylist]))  
    
    for d in alist:
        f.write('%s\n' % '\t'.join([unicode(d[k]).replace("\n", '') for k in keylist]))  
    
    f.close()   

    return fname

def countdict_to_tab(countdict):
    fname = '%s.csv' % base64.urlsafe_b64encode(hashlib.md5(str(countdict)).digest())[:-2] 
    f = codecs.open('static/download/%s' % fname, 'w', encoding='utf-8')
    for key, count in countdict.iteritems():
        f.write('%s\t%s\n' % (key, count))
    f.close()   

    return fname
