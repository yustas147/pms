# -*- coding: utf-8 -*-
#from openerp.osv import fields, osv 
from openerp import models, fields, api
import re

class Parser(object):

    def __init__(self, parse_string):
        ''' result value found by parser '''
        self.res=False
        ''' string before parser worked'''
        self.parse_string = parse_string
        ''' result string after parser worked '''
        self.res_string = False

    def set_parse_string(self, parse_string):
        self.parse_string = parse_string
    def set_res(self, res):
        self.res = res

class wpdParser(Parser):
    def __init__(self, parse_string=False):
        super(wpdParser,self).__init__(parse_string=parse_string)
    def parse(self):
        def wpd_repl(matched):
            return (matched.group(2)+'/'+matched.group(3)+'r'+matched.group(4)).lower()+'__'+ matched.group(1)+' '+matched.group(5) 

        def wpd(cell):
            rx_compiled = re.compile(ur'(.*)(\d{3})/(\d\d)\s*[zZ]*[rR/](\d\d[RF|C]*)(.*)', re.U)    
#            rx_compiled = re.compile(ur'(.*)(\d{3})/(\d\d)\s*[R/](\d\d[RF|C]*)(.*)', re.U)    
            res1 = re.sub(rx_compiled, wpd_repl, cell)
            res = res1.split('__')
            if len(res) > 1:
        #    if len(res) > 0:
                return res
            else:
                if len(res) == 1:
                    return (['', res[0]])
                else:
                    return(['', ''])
        self.res, self.res_string = wpd(self.parse_string)
        return self.res, self.parse_string

class wspParser(wpdParser):

    def parse(self):
        def chk(val):
            if val:
                return val
            else:
                return ''

        def wsp_repl(matched):
            return chk(matched.group(2))+chk(matched.group(3))+chk(matched.group(4))+'__'+' '+chk(matched.group(1))+' ' + chk(matched.group(5))

        def wsp(cell):
            rx_compiled = re.compile(ur'(.*)\s+(\d{2,3}/)*(\d{2,3})\s*([A-Z])\s*(.*)', re.U)
            res1 = re.sub(rx_compiled, wsp_repl, cell)
            res = res1.split('__')
            if len(res) > 1:
                res[1] = ' '+unicode(res[1])+' '
                return res
            else:
                if len(res) == 1:
                    return (['', res[0]])
                else:
                    return(['', ''])
            #return re.sub(rx_compiled, wsp_repl, cell).split('__')
        self.res, self.res_string = wsp(self.parse_string)
        return self.res, self.parse_string
            
class brandParser(Parser):
    def __init__(self, ddict=False, parse_string=False):
        super(brandParser,self).__init__(parse_string=parse_string)
        ''' ddict is the dictionary for parsing {key_1:[val11, val12, val1n], key_2:[val21,val22,...,val2m], key_d:[val_d1,...]}
        '''
        self.ddict = ddict
        ''' Last matched key from ddict for parsed string'''
        self.cached_key = set([])
        self.parse_string = parse_string

    def parse(self):
        rres = False
        ''' Prepair string: remove dupl spaces, lowercase all '''
        strtp = ' '.join(self.parse_string.split()).lower()
        #self.set_parse_string(False)
        self.set_res(False)

        def parse_by_val(psubstr):
            res = False
            psubstr = psubstr.lower()
            if psubstr in strtp:
                print unicode(psubstr)+' is found'
                ''' here we need to check if found sequence is a word'''
#                for sign in ['\\', '\/','(',')']:
                psub = ''
#                for sign in ['\\', r'.', r'+',  '/', '(',')']:
#                for sign in [r'+', '\\', '/','(',')']:
#                     if sign in psub:
#                         psub = psub.replace(sign, r'\\'[0:-1]+sign)
#                         print "sign is: "+sign
#                         break
                for smbl in psubstr:
                    if smbl in ['\\', r'.', r'+',  '/', '(',')']:
                        smbl = smbl.replace(smbl, r'\\'[0:-1]+smbl)
                    psub += smbl
#                        psubstr = psubstr.replace(sign, '\\'+unicode(sign))
                psubstr = psub
                patt = '(.*)('+psubstr+')'+'(.*)'
                print unicode(patt)
                rx_compiled = re.compile(patt, re.U | re.I)
                m = rx_compiled.match(strtp)
                if m:
                    print unicode(m)
                    print '#'+unicode(m.group(1))+'#'
                    print '#'+unicode(m.group(2))+'#'
                    print '#'+unicode(m.group(3))+'#'
                    if (m.group(1) =='' or m.group(1)[-1].isspace() == True) and (m.group(3) == '' or m.group(3)[0].isspace() == True):
#                    if m.group(1) =='' or m.group(1)[-1] == '\t':
                        res = ' '.join(strtp.split(psubstr)) 
                else:
                    res = False
            return res

        def parse_by_key(keyp):
            res = False
            for val in self.ddict[keyp]:
                res = parse_by_val(val)
                if res:
                    ''' Put found key in the parser cache '''
                    self.cached_key.add(keyp)
                    return keyp, res
            return res
        keylist = self.cached_key
        if len(keylist) > 0:
            keylist.sort(key=len,reverse=True)
        for keyp in keylist:
            rres = parse_by_key(keyp)
            if rres: 
                self.set_res(rres[0])
                self.set_parse_string(rres[1])
                return rres
            else:
                ''' cache of keys did not work '''
                ''' perebor vseh keys in ddict except teh, chto in cached_key'''
        keylist = self.ddict.keys()
        if len(keylist) > 0:
            keylist.sort(key=len,reverse=True)
        for keyp in keylist:
            if keyp not in self.cached_key:
                rres = parse_by_key(keyp)
                if rres:
                    self.set_res(rres[0])
                    self.set_parse_string(rres[1])
                    return rres
                else:
                    pass
            else:
                pass
        return self.res, self.parse_string
    
class modelParser(brandParser):                   
    pass

class studnessParser(brandParser):
    pass
                         
                
            

class parse_dict_keys(models.Model):
    _name = 'parse_dict_keys'
    
    @api.multi
    @api.model
    def remove_empty(self):
#    def remove_empty(self, cr, uid, ids, context=False):
        remids = self.search(['|',('name','=',' '),
                                     '|',('name','=',False),
                                     '|',('name','=','  '),
                                     '|',('name','ilike','   '),
                                     ('type','=',False)])
        self.unlink(remids)

    name = fields.Char('Keys for parsing')
    value_ids = fields.One2many('parse_dict_vals', 'parse_key_id')
    type = fields.Char('Type of dict: tyre_model_tyre_brand_or_etc', size=128)
    parent_key = fields.Many2one('parse_dict_keys',string='Parent key', help = 'fex: name of brand to which the model belongs. used for faster parsing')
    child_keys = fields.One2many('parse_dict_keys','parent_key', string='child keys', help = 'fe: name of models  which are belong to the brand. used for faster parsing')
#yustas 
#     def upd_dict_from_etalon(self, cr, uid, ids, context=False):
#         #good_ids = [1,2,4,5]
#         prodpool = self.pool.get('product.product')
#         good_ids = prodpool.search(cr, uid, ['&',('tyre_brand', '!=', False),('tyre_model', '!=', False)])
#         #raise osv.except_osv('Warning','prepared etalons are :' + str(sorted(good_ids)))
#         product_product.upd_parse_dict_key_group(prodpool, cr, uid, good_ids, context=False, updating_field='tyre_brand' )
#         product_product.upd_parse_dict_key_group(prodpool, cr, uid, good_ids, context=False, updating_field='tyre_model' )

class parse_dict_vals(models.Model):
    _name = 'parse_dict_vals'
    
    name = fields.Char('Dict values for parsing')
    parse_key_id = fields.Many2one('parse_dict_keys', string="Key")
    type = fields.Char('Type of dict: tyre_brand or etc')
#                'saved_key_value': fields.char('Saved value in key dict.', size=128),
