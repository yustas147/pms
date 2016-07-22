# -*- coding: utf-8 -*-

from openerp import models, fields, api, http
#import parser
from parser import brandParser, modelParser, wpdParser, wspParser, studnessParser, wxrParser, pcdParser, diaParser, etParser, paintParser
from openerp.osv import osv
from openerp.tools.translate import _
import logging
#from openerp.test.magentoerpconnect_pricing.product import product_price_changed

#codecs
#import codecs
#codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)


_logger = logging.getLogger('PMS')

class product_proxy(models.Model):
    _name = 'product.proxy'
    
    name = fields.Char('Name')
    etalon_id = fields.Many2one('product.proxy', string='Etalon product')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    if_etalon = fields.Boolean('Is it etalon?')
    quantity = fields.Integer('Suppliers quantity')
    price = fields.Float('Suppliers price')
#    price = fields.Integer('Suppliers price')
    proxy_ids = fields.One2many('product.proxy', 'etalon_id', string='Supplier`s info')
    uid_spl = fields.Char(string='Unique identifier of price list position', help='Usually, supp_price_list_name+suppliers article the thing')
    default_code = fields.Char('Code in pricelist', help='must be unique inside price list')
    
    @api.multi
    @api.model
    def get_lower_price(self):
        res = False
        try:
            res = min([inst.price for inst in self.proxy_ids if inst.quantity != 0])
            if res < 0.1:
                return False
        except ValueError:
            return res
        #print res
        return res

    @api.one
    def disconnect_etalon(self):
        self.etalon_id = False
            
    
class product_product(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'
    
    proxy_id = fields.Many2one('product.proxy', domain="[('if_etalon', '=', True)]")
    proxy_ids = fields.One2many(related='proxy_id.proxy_ids')
    virtual_type = fields.Selection([('virt.tire','AutoTire'), ('virt.disk','AutoDisk')], string='Select product type' )
    #proxy_ids = fields.One2many()
    
    
    @api.multi
    @api.model
    def update_magento_price(self):
        #self.list_price = self.standard_price
        pr_list = self.pricelist_id
        res = pr_list.price_get(self.id, 1)
        _logger.info("RESULT is: "+unicode(res))
        self.list_price = res.values()[0]
        
    def upd_prod_price_sel_ids(self, cr, uid, ids, context=False):
        for instid in ids:
            inst = self.browse(cr, uid, [instid])[0]
            inst.update_magento_price()
            _logger.info(unicode(inst.name)+"         price updated!")
        

        
#    def set_list_price_new(self, cr, uid, ids, context):

    
    @api.multi
    @api.model
    def set_lowest_lst_price(self):
       newprice = self.proxy_id.get_lower_price() 
       if newprice:
           self.lst_price = newprice
        
        
        
    @api.multi
    @api.model
    def create_proxy(self):
        #print unicode(self.proxy_id)
        if not self.virtual_type:
            return {
                    'warning':{
                               'title': _("Achtung!!!!"),
                               'message': _("Virtual type must be selected!!!")
                               }
                    }
        if not self.proxy_id:
            rset_proxy = self.env[self.virtual_type].create({'name':self.name, 'if_etalon':True})
            #print unicode(rset_proxy)
            rset_proxy.ensure_one()
            
            self.proxy_id = rset_proxy[0].proxy_id.id
    
    @api.multi
    @api.model
    def create_proxy_type(self, product_type=None):
        if self.virtual_type and product_type:
            _logger.warning("Changing product type from "+unicode(self.virtual_type)+"to "+unicode(product_type))
        self.virtual_type = product_type
        self.create_proxy()
        
        
    def create_proxy_tires_sel_ids(self, cr, uid, ids, context=False):
        for instid in ids:
            inst = self.browse(cr, uid, [instid])[0]
            inst.create_proxy_type(product_type="virt.tire")
            _logger.info(unicode(inst.name)+"         proxy created!")

    def create_proxy_disks_sel_ids(self, cr, uid, ids, context=False):
        for instid in ids:
            inst = self.browse(cr, uid, [instid])[0]
            inst.create_proxy_type(product_type="virt.disk")
            _logger.info(unicode(inst.name)+"         proxy created!")
            
    @api.multi
    @api.model
    def get_virt_id(self, virt_model):
        virt_pool = http.request.env[virt_model]
        return virt_pool.search([('proxy_id','=',self.proxy_id.id)])[0].id
        
    
    @api.multi
    @api.model
    def open_virt(self):
    #Define model name of agreement:
        mod_name=self.virtual_type
        #print mod_name
        return {
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': mod_name,
        'res_id': self.get_virt_id(mod_name),
        "views": [[False, "form"]],
        }
            
            
        
    
    
class mBrand(models.Model):

    _name = 'mbrand'
    name = fields.Char('Brand')
    
class mModel(models.Model):
    _name = 'mmodel'
    
    name = fields.Char('Brand')


class virt_disk(models.Model):
    _name = 'virt.disk'
    _inherits = {'product.proxy':'proxy_id'}
    
    brand = fields.Char('Brand') 
#    tire_brand = fields.Many2one('mbrand') 
    model = fields.Char('Model') 
    wrsize = fields.Char('WRSize', help='width of wheel in inches x radius oboda (6,5j x 15)')
    pcd = fields.Char('PCD', help='quantity and diameter of mounting bores (4х98)') 
    et = fields.Char('ET', help='Vylet diska (32)')
    dia = fields.Char('DIA', help='diameter centrovochnogo otverstiya na diske (67.1)')
    paint = fields.Char('Paint')
    country = fields.Char('Country')
    type = fields.Selection([("l","Legkovy"),("lv", "Legkovantazhny"),("4x4","4x4"),("v","Vantazhny")],string='Type')
    etalonic_select = fields.Many2one('virt.disk', domain="[('wrsize', '=', wrsize),('dia', '=', dia),('et', '=', et),('pcd', '=', pcd), ('brand','=',brand),('model','=',model),('if_etalon','=',True)]", string = 'Select etalonic tire')
    etalonic_list = fields.One2many(compute='_get_etalonic_ids', comodel_name='virt.disk', string = 'Possible etalon virt disks')
    #tire_model = fields.Many2one('mmodel') 
    
    @api.one
    def _get_etalonic_ids(self):
        et_rset = self.search([('wrsize', '=', self.wrsize), ('pcd', '=', self.pcd), ('brand', '=', self.brand), ('model','=',self.model),('et','=',self.et),('dia','=',self.dia),('if_etalon', '=', True)])
        self.etalonic_list = et_rset
    
    @api.one
    def autoconnect(self):
        et_rset = self.search([('wrsize', '=', self.wrsize), ('pcd', '=', self.pcd), ('brand', '=', self.brand), ('model','=',self.model),('et','=',self.et),('dia','=',self.dia),('if_etalon', '=', True)])
        if len(et_rset):
            self.etalonic_select = et_rset[0].id
            self.etalon_id = et_rset[0].proxy_id.id
        
    
    def parse_name_all_sel_ids(self, cr, uid, ids, context=False):
        for instid in ids:
            inst = self.browse(cr, uid, [instid])[0]
            inst.parse_all_name()
            _logger.info(unicode(inst.name)+"         parsed successfully!")
    
    @api.one
    def clear_parsed_fields(self):
        self.write({'brand':False,'model':False,'wrsize':False,'pcd':False,'et':False,'dia':False,'paint':False,'country':False})

    @api.one
    def disconnect_etalon(self):
        self.write({'etalon_id':False})

    
    @api.multi
    @api.model
    def parse_all_name(self):
        self.parse_brand()
        self.parse_model()
        self.parse_wrsize()
        self.parse_et()
        self.parse_dia()
        self.parse_pcd()
        self.parse_paint()
    
    @api.multi 
    @api.model
    def parse_paint(self):
        parser = paintParser(parse_string=self.name, dict_type='disk_color' )
        parsed_brand, name_minus_brand = parser.parse()
        if parsed_brand :
            self.paint = parsed_brand
            self.name_unparsed = name_minus_brand
        else:
            _logger.warning( "########## Painting not found in name: "+ unicode(self.name))
        return True
    
    @api.multi 
    @api.model
    def parse_brand(self):
        parser = brandParser(parse_string=self.name, dict_type='disk_brand' )
        parsed_brand, name_minus_brand = parser.parse()
        if parsed_brand :
            self.brand = parsed_brand
            self.name_unparsed = name_minus_brand
        else:
            _logger.warning("########## Brand not found in name: "+ unicode(self.name))
        return True
    
    @api.multi 
    @api.model
    def parse_model(self):
        parser = modelParser(parse_string=self.name, dict_type='disk_model', parent_key=self.brand, parent_key_dict_type='disk_brand')
        parsed_model, name_minus_model = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_model :
            self.model = parsed_model
            self.name_unparsed = name_minus_model
        else:
            _logger.warning("########## model not found in name: "+ unicode(self.name))
        return True 
    
    @api.multi 
    @api.model
    def parse_wrsize(self):
        parser = wxrParser(self.name)
        parsed_wpd, name_minus_wpd = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_wpd :
            self.wrsize = parsed_wpd.lower()
            self.name_unparsed = name_minus_wpd
        else:
            _logger.warning("########## wrsize not found in name: "+ unicode(self.name))
        return True
    
    @api.multi 
    @api.model
    def parse_pcd(self):
        parser = pcdParser(self.name)
        parsed_wpd, name_minus_wpd = parser.parse()
        if parsed_wpd :
            self.pcd = parsed_wpd.lower()
            self.name_unparsed = name_minus_wpd
        else:
            _logger.warning( "########## pcd not found in name: "+ unicode(self.name))
        return True
    
    @api.multi 
    @api.model
    def parse_dia(self):
        parser = diaParser(self.name)
        parsed_wpd, name_minus_wpd = parser.parse()
        if parsed_wpd :
            self.dia = parsed_wpd.lower()
            self.name_unparsed = name_minus_wpd
        else:
            _logger.warning("########## dia not found in name: "+ unicode(self.name))
        return True
    
    @api.multi 
    @api.model
    def parse_et(self):
        parser = etParser(self.name)
        parsed_wpd, name_minus_wpd = parser.parse()
        if parsed_wpd :
            self.et = parsed_wpd.lower()
            self.name_unparsed = name_minus_wpd
        else:
            _logger.warning( "########## dia not found in name: "+ unicode(self.name))
        return True


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
    etalonic_select = fields.Many2one('virt.tire', domain="[('tire_wpd', '=', tire_wpd),('tire_wsp', '=', tire_wsp), ('tire_brand','=',tire_brand),('tire_model','=',tire_model),('if_etalon','=',True)]", string = 'Select etalonic tire')
    etalonic_list = fields.One2many(compute='_get_etalonic_ids', comodel_name='virt.tire', string = 'Possible etalon virt tires')
#    etalonic_list = fields.One2many(compute='_get_etalonic_ids', comodel_name='virt.tire', string = 'Possible etalon virt tires')

    
    @api.one
    def _get_etalonic_ids(self):
        et_rset = self.search([('tire_wpd', '=', self.tire_wpd), ('tire_wsp', '=', self.tire_wsp), ('tire_brand', '=', self.tire_brand), ('tire_model','=',self.tire_model),('tire_studness','=',self.tire_studness),('if_etalon', '=', True)])
        self.etalonic_list = et_rset
    
    def parse_name_all_sel_ids(self, cr, uid, ids, context=False):
        for instid in ids:
            inst = self.browse(cr, uid, [instid])[0]
            inst.parse_all_name()
            _logger.info( unicode(inst.name)+"         parsed successfully!")
    
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
        
        key_pool = self.env['parse_dict_keys']
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
# 
#     @api.multi 
#     @api.model
#     def parse_brand(self, dt='tyre_brand'):
#         parser_dict = self.get_parser_dict(dt)
#         parser = brandParser(parser_dict, self.name)
#         parsed_brand, name_minus_brand = parser.parse()
# #        parsed_brand, name_minus_brand = parser.parse(self.name)
#         if parsed_brand :
#             self.tire_brand = parsed_brand
#             self.name_unparsed = name_minus_brand
#         else:
#             print "########## brand not found in name: "+ unicode(self.name)
#         return True

    @api.multi 
    @api.model
    def parse_brand(self):
        parser = brandParser(parse_string=self.name)
        parsed_brand, name_minus_brand = parser.parse()
        if parsed_brand :
            self.tire_brand = parsed_brand
            self.name_unparsed = name_minus_brand
        else:
            _logger.warning( "########## brand not found in name: "+ unicode(self.name))
        return True
    
    @api.multi 
    @api.model
    def parse_studness(self):
        parser = studnessParser(parse_string=self.name, dict_type='studness')
        parsed_brand, name_minus_brand = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_brand :
            self.tire_studness = parsed_brand
            self.name_unparsed = name_minus_brand
        else:
            _logger.warning( "########## studness not found in name: "+ unicode(self.name))
            self.tire_studness = 'n/s'
        return True
    
#     @api.multi 
#     @api.model
#     def parse_model(self, dt='tyre_model'):
#         parser_dict = self.get_parser_dict(dt,parent_key=self.tire_brand)
#         parser = modelParser(parser_dict, self.name)
#         parsed_model, name_minus_model = parser.parse()
# #        parsed_brand, name_minus_brand = parser.parse(self.name)
#         if parsed_model :
#             self.tire_model = parsed_model
#             self.name_unparsed = name_minus_model
#         else:
#             print "########## model not found in name: "+ unicode(self.name)
#         return True

    @api.multi 
    @api.model
    def parse_model(self):
        parser = modelParser(parse_string=self.name, dict_type='tyre_model', parent_key=self.tire_brand, parent_key_dict_type='tyre_brand')
        parsed_model, name_minus_model = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_model :
            self.tire_model = parsed_model
            self.name_unparsed = name_minus_model
        else:
            _logger.warning( "########## model not found in name: "+ unicode(self.name))
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
            _logger.warning("########## wpd not found in name: "+ unicode(self.name))
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
            _logger.warning( "########## wsp not found in name: "+ unicode(self.name))
        return True

