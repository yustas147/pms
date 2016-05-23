# -*- coding: utf-8 -*-

from openerp import models, fields, api
#import parser
from parser import brandParser




class product_proxy(models.Model):
    _name = 'product.proxy'
    
    name = fields.Char('Name')
    etalon_id = fields.Many2one('product.proxy', string='Etalon product')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    if_etalon = fields.Boolean('Is it etalon?')
    quantity = fields.Integer('Suppliers quantity')
    price = fields.Integer('Suppliers price')
    proxy_ids = fields.One2many('product.proxy', 'etalon_id', string='Supplier`s info')
    
class product_product(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'
    
    proxy_id = fields.Many2one('product.proxy')
    proxy_ids = fields.One2many(related='proxy_id.proxy_ids')
    #proxy_ids = fields.One2many()
    
class mBrand(models.Model):

    _name = 'mbrand'
    name = fields.Char('Brand')
    
class mModel(models.Model):
    _name = 'mmodel'
    
    name = fields.Char('Brand')

class virt_tire(models.Model):
    _name = 'virt.tire'
    _inherits = {'product.proxy':'proxy_id'}
    
    tire_brand = fields.Many2one('mbrand') 
    tire_model = fields.Many2one('mmodel') 
    tire_wsp = fields.Char('Speed idx')
    tire_wpd = fields.Char('Dimensions')
    tire_studness = fields.Selection([('studded','Studded'),('non-studded','Non-studded'),('studdable','Studdable')],string='Studness')
    
    @api.multi
    @api.model
    def get_parser_dict(self, dict_type='brand'):
        
        key_pool = self.env['parse_dict_keys']
#        val_pool = self.env['parse_dict_vals']
        res = {}
        
        for k in key_pool.search([('type','=',dict_type)]):
            k_n = k.name
            res[k_n] = []
            for v in k.value_ids:
                res[k_n].append(v.name)
            #print k.value_ids.name
        print res
        return res

    @api.multi 
    @api.model
    def parse_brand(self):
        parser_dict = self.get_parser_dict('brand')
        parser = brandParser(parser_dict)
        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_brand :
            self.tire_brand = parsed_brand
            self.name_unparsed = name_minus_brand
        else:
            print "########## brand not found in name: "+ unicode(self.name)
        print parser
        pass

    @api.model
    def parse_model(self):
        pass
    def parse_wpd(self):
        pass
    def parse_wsp(self):
        pass
    def parse_studness(self):
        pass
