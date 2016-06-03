# -*- coding: utf-8 -*-
#from openerp.osv import fields, osv 
from openerp import models, fields, api, http
import re

class Parser(http.Controller):
#class Parser(object):

    def __init__(self, parse_string=False):
#    def __init__(self, parse_string=False, dict_type=False, parent_key=False):
#    def __init__(self, parse_string=False, dict_type=False, parent_key=False):
        ''' result value found by parser '''
        self.res=False
        ''' string before parser worked'''
        self.parse_string = parse_string
        ''' result string after parser worked '''
        self.res_string = False
       # self.dict_type = dict_type
       # self.parent_key = parent_key
#        if dict_type:
#            self.ddict = self.get_parser_dict(dict_type=dict_type, parent_key=parent_key)

    def set_parse_string(self, parse_string):
        self.parse_string = parse_string
    def set_res(self, res):
        self.res = res
    
    
#    @route(auth='public')
    def get_parser_dict(self, dict_type='brand', parent_key=False):
         
        key_pool = http.request.env['parse_dict_keys']
        res = {}
         
        if parent_key:
            #pkid_set = key_pool.search([('name','=',parent_key)])
            pkid = key_pool.search([('name','=',parent_key)])[0].id
#            print unicode(pkid_set)
#            pkid = pkid_set[0].id
            for k in key_pool.search([('type','=',dict_type),('parent_key','=',pkid)]):
                k_n = k.name
                res[k_n] = []
                for v in k.value_ids:
                    res[k_n].append(v.name)
                res[k_n].sort(key=len, reverse=True)    
        else:
         
            for k in key_pool.search([('type','=',dict_type)]):
                k_n = k.name
                res[k_n] = []
                for v in k.value_ids:
                    res[k_n].append(v.name)
                res[k_n].sort(key=len, reverse=True)
        self.ddict = res
        return res

        
class brandParser(Parser):
    def __init__(self, parse_string=False, dict_type='tyre_brand', parent_key=False):
        ''' ddict is the dictionary for parsing {key_1:[val11, val12, val1n], key_2:[val21,val22,...,val2m], key_d:[val_d1,...]}
        '''
        ''' Last matched key from ddict for parsed string'''
        self.cached_key = set([])
        self.parse_string = parse_string
        self.dict_type = dict_type
        self.parent_key = parent_key

    def parse(self):
        self.get_parser_dict(dict_type=self.dict_type, parent_key=self.parent_key)
        rres = False
        ''' Prepair string: remove dupl spaces, lowercase all '''
        strtpg = ' '.join(self.parse_string.split()).lower()
        #self.set_parse_string(False)
        self.set_res(False)
        
        
        def parse_by_val(psubstr):
            res = False
            #print strtpg
            strtp = strtpg
            psubstr = psubstr.lower()
            len_psubstr = len(psubstr)
            hope = True
            psb = psubstr
            while hope:
                fflag = strtp.find(psubstr)
                if psubstr == 's':
                    print 'SSSSS'
                if fflag == -1:
                    break
                else:
                    if fflag == 0:
                        ''' found in the begining'''
                        if fflag + len_psubstr == len(strtp) :
                            ''' patt is string'''
                            '''  Bingo! ''' 
                            res = ' '.join(strtp.split(psubstr))
                            return res
                        else:
                            if strtp[fflag+len_psubstr].rstrip() == '':
                                ''' Bingo! '''
                                res = ' '.join(strtp.split(psubstr))
                                return res
                            else:
                              '''next find need'''
                              strtp = strtp.replace(psubstr, '', 1)
                              continue
                                
                    else:
                        if strtp[fflag - 1].rstrip() == '':
                            ''' nachalo provereno, proverim konets '''
                            if fflag + len_psubstr == len(strtp) :
                                ''' patt at the end of string'''
                                ''' Bingo! '''
                                res = ' '.join(strtp.split(psubstr))
                                return res
                                
                            else:
                                if strtp[fflag+len_psubstr].rstrip() == '':
                                    ''' Bingo!'''
                                    res = ' '.join(strtp.split(psubstr))
                                    return res
                                else:
                                    '''next find need'''
                                    strtp = strtp.replace(psubstr, '', 1)
                                    continue
                            
                        else:
                            '''next find need'''
                            strtp = strtp.replace(psubstr, '', 1)
                            continue
            return res           
                    
            

#         def parse_by_val2(psubstr):
#             res = False
#             #print strtpg
#             strtp = strtpg
#             psubstr = psubstr.lower()
#             hope = True
#             psb = psubstr
#             while hope:
#                 if psubstr in strtp:
#                     print unicode(psubstr)+' is found'
#                     ''' here we need to check if found sequence is a word'''
#     #                for sign in ['\\', '\/','(',')']:
#                     psub = ''
#     #                for sign in ['\\', r'.', r'+',  '/', '(',')']:
#     #                for sign in [r'+', '\\', '/','(',')']:
#     #                     if sign in psub:
#     #                         psub = psub.replace(sign, r'\\'[0:-1]+sign)
#     #                         print "sign is: "+sign
#     #                         break
#                     for smbl in psubstr:
#                         if smbl in ['\\', r'.', r'+',  '/', '(',')']:
#                             smbl = smbl.replace(smbl, r'\\'[0:-1]+smbl)
#                         psub += smbl
#     #                        psubstr = psubstr.replace(sign, '\\'+unicode(sign))
#                     psb = psub
# #                    psubstr = psub
#                     patt = '(.*)('+psb+')'+'(.*)'
#                     print unicode(patt)
#                     rx_compiled = re.compile(patt, re.U | re.I)
#                     m = rx_compiled.match(strtp)
#                     if m:
#                         print unicode(m)
#                         print '#'+unicode(m.group(1))+'#'
#                         print '#'+unicode(m.group(2))+'#'
#                         print '#'+unicode(m.group(3))+'#'
#                         if (m.group(1) =='' or m.group(1)[-1].isspace() == True) and (m.group(3) == '' or m.group(3)[0].isspace() == True):
#     #                    if m.group(1) =='' or m.group(1)[-1] == '\t':
#                             res = ' '.join(strtp.split(psb)) 
#                             #res = ' '.join(strtp.split(psubstr)) 
#                             break
#                         else:
#                             strtp = strtp.replace(psubstr, '')
#                             print 'Strtp:'+unicode(strtp)
#                     else:
#                         res = False
#                 else:
#                     hope = False
#                 print 'NextWhile!!!'
#             return res

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

class wpdParser(Parser):
    def __init__(self, parse_string=False):
        super(wpdParser,self).__init__(parse_string=parse_string)
    def parse(self):
        #self.get_parser_dict()
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
            
class wxrParser(Parser):
    def __init__(self, parse_string=False):
        super(wxrParser,self).__init__(parse_string=parse_string)
    def parse(self):
        def wxr_repl(matched):
            return (matched.group(2)+'x'+matched.group(4)+'__'+ matched.group(1)+' '+matched.group(5)) 

        def wxr(cell):
            re_list = [ur'(.*\s)(\d{1}[\./,]?\d?)([\s,x,х,\\]{1})(1\d\s+)(.*)', ur'(.*)(1\d)([\s,x,х,\\])(\d[\./,]?\d?)(\s.*)']
            for regxp in re_list:
                rx_compiled = re.compile(regxp, re.U)    
#            rx_compiled = re.compile(ur'(.*\s)(\d{1}[\./,]?\d?)([\s,x,\\]{1})(1\d{1}\s+)(.*)', re.U)    
#            rx_compiled = re.compile(ur'(.*\s)(\d{1}[\./,]?\d?)([\s,x,\\]{1})(\d{2}\s+)(.*)', re.U)    
                res1 = re.sub(rx_compiled, wxr_repl, cell)
                res = res1.split('__')
                if len(res) > 1:
                    return res
            if len(res) == 1:
                return (['', res[0]])
            else:
                return(['', ''])
        self.res, self.res_string = wxr(self.parse_string)
        return self.res, self.parse_string
    
#         def wxr(cell):
#             re_list = list('(.*\s)(\d{1}[\./,]?\d?)([\s,x,\\]{1})(1\d\s+)(.*)', '(.*\s)(\d{1}[\./,]?\d?)([\s,x,\\]{1})(1\d\s+)(.*)')
#             rx_compiled = re.compile(ur'(.*\s)(\d{1}[\./,]?\d?)([\s,x,\\]{1})(1\d\s+)(.*)', re.U)    
# #            rx_compiled = re.compile(ur'(.*\s)(\d{1}[\./,]?\d?)([\s,x,\\]{1})(1\d{1}\s+)(.*)', re.U)    
# #            rx_compiled = re.compile(ur'(.*\s)(\d{1}[\./,]?\d?)([\s,x,\\]{1})(\d{2}\s+)(.*)', re.U)    
#             res1 = re.sub(rx_compiled, wxr_repl, cell)
#             res = res1.split('__')
#             if len(res) > 1:
#         #    if len(res) > 0:
#                 return res
#             else:
#                 if len(res) == 1:
#                     return (['', res[0]])
#                 else:
#                     return(['', ''])
#         self.res, self.res_string = wxr(self.parse_string)
#         return self.res, self.parse_string

class pcdParser(Parser):
    def __init__(self, parse_string=False):
        super(pcdParser,self).__init__(parse_string=parse_string)
    def parse(self):
        def wxr_repl(matched):
            return (matched.group(2)+'x'+matched.group(4)+'__'+ matched.group(1)+' '+matched.group(5)) 

        def wxr(cell):
            rx_compiled = re.compile(ur'(.*\s)([3-9]{1})([/\s,x,\\]{1})(\d{2,3}[\.,]?\d?)(.*)', re.U)    
#            rx_compiled = re.compile(ur'(.*\s)(\d{1}[\./,]?\d?)([\s,x,\\]{1})(\d{2}\s+)(.*)', re.U)    
            res1 = re.sub(rx_compiled, wxr_repl, cell)
            res = res1.split('__')
            if len(res) > 1:
        #    if len(res) > 0:
                return res
            else:
                if len(res) == 1:
                    return (['', res[0]])
                else:
                    return(['', ''])
        self.res, self.res_string = wxr(self.parse_string)
        return self.res, self.parse_string 

class diaParser(Parser):
    def __init__(self, parse_string=False):
        super(diaParser,self).__init__(parse_string=parse_string)
    def parse(self):
        def wxr_repl(matched):
            return (matched.group(3)+'.'+matched.group(5)+'__'+ matched.group(1)+matched.group(2)+' '+matched.group(6)) 

        def wxr(cell):
            rx_compiled = re.compile(ur'(.*)([\s/]{1})([4-91]\d{1,2})([\.,])(\d)(.*)', re.U)    
#            rx_compiled = re.compile(ur'(.*\s)(\d{1}[\./,]?\d?)([\s,x,\\]{1})(\d{2}\s+)(.*)', re.U)    
            res1 = re.sub(rx_compiled, wxr_repl, cell)
            res = res1.split('__')
            if len(res) > 1:
        #    if len(res) > 0:
                return res
            else:
                if len(res) == 1:
                    return (['', res[0]])
                else:
                    return(['', ''])
        self.res, self.res_string = wxr(self.parse_string)
        return self.res, self.parse_string  
   
class etParser(Parser):
    def __init__(self, parse_string=False):
        super(etParser,self).__init__(parse_string=parse_string)
    def parse(self):
        def wxr_repl(matched):
            return (matched.group(3)+'__'+ matched.group(1)+' '+ matched.group(2) + ' ' + matched.group(4)) 

        def wxr(cell):
            re_list = [ur'(.*\s)([eEеЕ][tTтТ])\s?(\d\d\d?)(.*)', ur'(.*)(\s)(\d\d\d?)(.*)', ur'(.*)(\d+[.,]?\d)\/(\d\d\d?)\/(\d+[.,]?\d?.*)']
            for regxp in re_list:
                rx_compiled = re.compile(regxp, re.U)    
#            rx_compiled = re.compile(ur'(.*\s)(\d{1}[\./,]?\d?)([\s,x,\\]{1})(1\d{1}\s+)(.*)', re.U)    
#            rx_compiled = re.compile(ur'(.*\s)(\d{1}[\./,]?\d?)([\s,x,\\]{1})(\d{2}\s+)(.*)', re.U)    
                res1 = re.sub(rx_compiled, wxr_repl, cell)
                res = res1.split('__')
                if len(res) > 1:
                    return res
            if len(res) == 1:
                return (['', res[0]])
            else:
                return(['', ''])
        self.res, self.res_string = wxr(self.parse_string)
        return self.res, self.parse_string   

class modelParser(brandParser):                   
#class modelParser(brandParser):                   
    pass

class studnessParser(brandParser):

    pass
class paintParser(brandParser):
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
