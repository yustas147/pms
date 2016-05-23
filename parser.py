# -*- coding: utf-8 -*-
#from openerp.osv import fields, osv 
from openerp import models, fields, api

class Parser(object):

    def __init__(self):
        ''' result value found by parser '''
        self.res=False
        ''' string before parser worked'''
        self.parse_string = False
        ''' result string after parser worked '''
        self.res_string = False

    def set_parse_string(self, parse_string):
        self.parse_string = parse_string
        
class brandParser(Parser):
    def __init__(self, ddict):
        super(brandParser,self).__init__()
        ''' ddict is the dictionary for parsing {key_1:[val11, val12, val1n], key_2:[val21,val22,...,val2m], key_d:[val_d1,...]}
        '''
        self.ddict = ddict
        ''' Last matched key from ddict for parsed string'''
        self.cached_key = set([])

    def parse(self):
        rres = False
        ''' Prepair string: remove dupl spaces, lowercase all '''
        strtp = ' '.join(self.parse_string.split()).lower()

        def parse_by_val(psubstr):
            res = False
            psubstr = psubstr.lower()
            if psubstr in strtp:
                res = ' '.join(strtp.split(psubstr)) 
            return res

        def parse_by_key(keyp):
            res = False
            for val in self.ddict[keyp]:
                res = parse_by_val(val)
                if res:
                    ''' Put found key in the parser cache '''
                    self.cached_key.add(keyp)
                    return res
            return res

        for keyp in self.cached_key:
            rres = parse_by_key(keyp)
            if rres: 
                return rres
            else:
                ''' cache of keys did not work '''
                ''' perebor vseh keys in ddict except teh, chto in cached_key'''
                for keyp in self.ddict:
                    if keyp not in self.cached_key:
                         
                
            

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
