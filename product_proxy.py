# -*- coding: utf-8 -*-

from openerp import models, fields, api
#import parser
from parser import brandParser, modelParser, wpdParser, wspParser, studnessParser   
from openerp.osv import osv     




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
    
    tire_brand = fields.Char('Brand') 
#    tire_brand = fields.Many2one('mbrand') 
    tire_model = fields.Char('Model') 
    #tire_model = fields.Many2one('mmodel') 
    tire_wsp = fields.Char('Speed idx')
    tire_wpd = fields.Char('Dimensions')
    tire_studness = fields.Selection([('n/s','Non-studded'),('studded','Studded'),('studdable','Studdable')],string='Studness')
    name_unparsed = fields.Char('Left for parsing')
    
#     @api.multi
#     @api.model
#     def parse_name_all_sel_ids(self):
#         ids = context.get('active_ids',[])
    
    def parse_name_all_sel_ids(self, cr, uid, ids, context=False):
        for instid in ids:
            inst = self.browse(cr, uid, [instid])[0]
            inst.parse_all_name()
            print unicode(inst.name)+"         parsed successfully!"
    
    @api.multi
    @api.model
    def parse_all_name(self):
        self.parse_brand()
        self.parse_model()
        self.parse_wpd()
        self.parse_wsp()
        self.parse_studness()
    
    @api.multi
    @api.model
    def get_parser_dict(self, dict_type='brand', parent_key=False):
#    def get_parser_dict(self, dict_type='brand'):
        
        key_pool = self.env['parse_dict_keys']
#        val_pool = self.env['parse_dict_vals']
        res = {}
        
        if parent_key:
            pkid = key_pool.search([('name','=',parent_key)])[0].id
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
        return res

    @api.multi 
    @api.model
    def parse_brand(self, dt='tyre_brand'):
        parser_dict = self.get_parser_dict(dt)
        parser = brandParser(parser_dict, self.name)
        parsed_brand, name_minus_brand = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_brand :
            self.tire_brand = parsed_brand
            self.name_unparsed = name_minus_brand
        else:
            print "########## brand not found in name: "+ unicode(self.name)
        return True

    @api.multi 
    @api.model
    def parse_studness(self, dt='studness'):
        parser_dict = self.get_parser_dict(dt)
        parser = studnessParser(parser_dict, self.name)
        parsed_brand, name_minus_brand = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_brand :
            self.tire_studness = parsed_brand
            self.name_unparsed = name_minus_brand
        else:
            print "########## studness not found in name: "+ unicode(self.name)
            self.tire_studness = 'n/s'
        return True
    
    @api.multi 
    @api.model
    def parse_model(self, dt='tyre_model'):
        parser_dict = self.get_parser_dict(dt,parent_key=self.tire_brand)
        parser = modelParser(parser_dict, self.name)
        parsed_model, name_minus_model = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_model :
            self.tire_model = parsed_model
            self.name_unparsed = name_minus_model
        else:
            print "########## model not found in name: "+ unicode(self.name)
        return True
    
    @api.multi 
    @api.model
    def parse_wpd(self):
        parser = wpdParser(self.name)
        parsed_wpd, name_minus_wpd = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_wpd :
            self.tire_wpd = parsed_wpd.upper()
            self.name_unparsed = name_minus_wpd
        else:
            print "########## wpd not found in name: "+ unicode(self.name)
        #print parser
        return True

    @api.multi 
    @api.model
    def parse_wsp(self):
        parser = wspParser(self.name)
        parsed_wpd, name_minus_wpd = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_wpd :
            self.tire_wsp = parsed_wpd.upper()
            self.name_unparsed = name_minus_wpd
        else:
            print "########## wsp not found in name: "+ unicode(self.name)
        #print parser
        return True

