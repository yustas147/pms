# -*- coding: utf-8 -*-

from openerp import models, fields, api, http
#import parser
from parser import brandParser, modelParser, wpdParser, wspParser,\
                   seasonParser, lg_weightnessParser, studnessParser, wxrParser, pcdParser, diaParser, etParser, paintParser, RParser
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
    
    @api.multi
    @api.model
    def open_product_template(self):
    #Define model name of agreement:
        sid = self.id
      #  print "########################################## sid:      "+unicode(sid)
        senv = http.request.env['product.template']
        senv = self.env['product.template']
        product_template_id=senv.search([('proxy_id.id','=',sid)])
        if len(product_template_id):
            product_template_id = product_template_id[0].id
     #   print "########################################## product_template_id:      "+unicode(product_template_id)
        #print mod_name
            return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.template',
            'res_id': product_template_id,
            "views": [[False, "form"]],
            }
            
    
class product_template(models.Model):
#class product_product(models.Model):
# i decided to change product.product on product_template
    _name = 'product.template'
    _inherit = 'product.template'
    
    proxy_id = fields.Many2one('product.proxy', domain="[('if_etalon', '=', True)]")
    proxy_ids = fields.One2many(related='proxy_id.proxy_ids')
    virtual_type = fields.Selection([('virt.tire','AutoTire'), ('virt.disk','AutoDisk')], string='Select product type' )
    virt_stock = fields.Integer(string='Virtual stock quantity', compute='_set_virtual_stock')


    @api.multi
    @api.model
    def get_prox(self):
        _logger.info('prox_id is: '+unicode(self.proxy_id))
        _logger.info('prox_id.id is: '+unicode(self.proxy_id.id))
    
    @api.multi
    @api.model
    def _set_virtual_stock(self):
        _logger.info('proxy_ids are: '+unicode(self.proxy_ids))
        res = 0
        for prx in self.proxy_ids:
            res += prx.quantity
        _logger.info('virtual stock is : '+unicode(res))
        self.virt_stock = res
        return res

    
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
#            inst.update_magento_price()
            _logger.info(unicode(inst.name)+"         price updated!")
        

        
#    def set_list_price_new(self, cr, uid, ids, context):

    
    @api.multi
    @api.model
    def set_lowest_lst_price(self):
        newprice = self.proxy_id.get_lower_price() 
        if newprice:
            self.standard_price = newprice
#           self.lst_price = newprice
        
        
        
    @api.multi
    @api.model
    def create_proxy(self):
        #print unicode(self.proxy_id)
        if not self.virtual_type:
            return False
#             return {
#                     'warning':{
#                                'title': _("Achtung!!!!"),
#                                'message': _("Virtual type must be selected!!!")
#                                }
#                     }
        if not self.proxy_id:
            rset_proxy = self.env[self.virtual_type].create({'name':self.name, 'if_etalon':True})
            #print unicode(rset_proxy)
            rset_proxy.ensure_one()
            
            self.proxy_id = rset_proxy[0].proxy_id.id
            return self.proxy_id
    
    @api.multi
    @api.model
    def create_proxy_type(self, product_type=None):
        if self.virtual_type and product_type:
            _logger.warning("Changing product type from "+unicode(self.virtual_type)+"to "+unicode(product_type))
        self.virtual_type = product_type
        return self.create_proxy()
        
        
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

    def create_proxy_disks_and_parse_sel_ids(self, cr, uid, ids, context=False):
        pool = self.pool.get('virt.disk')
        for instid in ids:
            inst = self.browse(cr, uid, [instid])[0]
            inst_prx = inst.create_proxy_type(product_type="virt.disk")
            if inst_prx:
                v_id = pool.search(cr, uid, [('proxy_id','=',inst_prx.id)])[0]
                inst_virt = pool.browse(cr, uid, [v_id])
                inst_virt.parse_all_name()
            _logger.info(unicode(inst.name)+"         proxy created and parsed!")
            
    def create_proxy_and_parse_sel_ids(self, cr, uid, ids, virt_type='VIRT_TYPE_MUST_BE_SET', context=False):
        pool = self.pool.get(virt_type)
        for instid in ids:
            inst = self.browse(cr, uid, [instid])[0]
            inst_prx = inst.create_proxy_type(product_type=virt_type)
            if inst_prx:
                v_id = pool.search(cr, uid, [('proxy_id','=',inst_prx.id)])[0]
                inst_virt = pool.browse(cr, uid, [v_id])
                inst_virt.parse_all_name()
            _logger.info(unicode(inst.name)+"         proxy created and parsed!")
    
            
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
    etalonic_select = fields.Many2one('virt.disk',  string = 'Select etalonic tire') 
#    etalonic_select = fields.Many2one('virt.disk', domain="[('dia', '=', dia),('et', '=', et),('pcd', '=', pcd), ('brand','=',brand),('model','=',model),('if_etalon','=',True)]", string = 'Select etalonic tire') 
##    etalonic_select = fields.Many2one('virt.disk', domain="[('wrsize', '=', wrsize),('dia', '=', dia),('et', '=', et),('pcd', '=', pcd), ('brand','=',brand),('model','=',model),('if_etalon','=',True)]", string = 'Select etalonic tire') 
    reverse_etalonic_select = fields.Many2one('virt.disk', domain="[('wrsize', '=', wrsize),('dia', '=', dia),('et', '=', et),('pcd', '=', pcd), ('brand','=',brand),('model','=',model),('if_etalon','=',False)]", string = 'Select non-etalonic tire')
    etalonic_list = fields.One2many(compute='_get_etalonic_ids2', comodel_name='virt.disk', string = 'Possible etalon virt disks')
    reverse_etalonic_list = fields.One2many(compute='_get_reverse_etalonic_ids2', comodel_name='virt.disk', string = 'Possible non-etalon virt disks')
    #etalonic_list_domain = fields.Text(string="Etalonic list domain", 
    #                                   help="Set this field for etalonic select criteria in a style as odoo domain: [('wrsize', '=', wrsize),('dia', '=', dia)....]",
    #                                   default="['brand','model','pcd','wrsize','et','dia','paint']")
    chkF_brand = fields.Boolean("Brand")
    chkF_model = fields.Boolean("Model")
    chkF_wrsize = fields.Boolean("WxD")
    chkF_pcd = fields.Boolean("PCD")
    chkF_dia = fields.Boolean("DIA")
    chkF_et = fields.Boolean("ET")
    chkF_paint = fields.Boolean("Paint")
                                                                            
    
    
                    

    
    @api.one
    def set_default_etalonic_list_domain(self):
        self.etalonic_list_domain = "['brand','model','pcd','wrsize','et','dia','paint']"
    
    @api.multi
    @api.model
    def open_brand_dict(self):
    #Define model name of agreement:
        mod_name = 'parse_dict_keys'
        mod_env = http.request.env[mod_name]
        rec_id = mod_env.search([('type','=','disk_brand'),('name','=',self.brand)])
        if len(rec_id):
            rec_id = rec_id[0].id
        #print mod_name
            return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': mod_name,
            'res_id': rec_id,
            "views": [[False, "form"]],
            }
        return False
    
    
    
    @api.multi
    @api.model
    def conn_to_me(self):
        if self.reverse_etalonic_select == False:
            return False
        n_inst = self.browse([self.reverse_etalonic_select.id])
        _logger.info('self is:  '+unicode(self))
        _logger.info('n_inst is:  '+unicode(n_inst))
        n_inst.write({'etalon_id':self.proxy_id.id})
    
#     @api.one
#     def _get_etalonic_ids(self):
#         et_rset = self.search([('wrsize', '=', self.wrsize), ('pcd', '=', self.pcd), ('brand', '=', self.brand), 
#                                ('model','=',self.model),('et','=',self.et),('dia','=',self.dia),('paint','=',self.paint),('if_etalon', '=', True)])
#         _logger.info('_get_etalonic_ids: '+unicode(et_rset))
#         self.etalonic_list = et_rset
#     
#     @api.one
#     def _get_reverse_etalonic_ids(self):
#         et_rset = self.search([('wrsize', '=', self.wrsize), ('pcd', '=', self.pcd), ('brand', '=', self.brand), 
#                                ('model','=',self.model),('et','=',self.et),('dia','=',self.dia),('paint','=',self.paint),('if_etalon', '=', False)])
#         _logger.info('_get_reverse_etalonic_ids: '+unicode(et_rset))
#         self.reverse_etalonic_list = et_rset

    @api.one
    def get_chkF(self):
        res = []
        res_def = []
        for fld in self.fields_get_keys():
            if 'chkF' in fld:
                print fld
                fval = eval('self.'+fld)
                res_def.append(fld[5:])
                if fval:
                    res.append(fld[5:])
        print 'res: '+unicode(res)
        print 'res_def :'+unicode(res_def)
        if len(res) > 0:
            return res
        return res_def


    @api.one
    @api.depends('chkF_brand','chkF_model','chkF_wrsize','chkF_dia','chkF_et','chkF_pcd','chkF_paint')
    def _get_etalonic_ids2(self):
        if self.if_etalon:
            return []
        domlist = self.get_chkF()[0]
        print 'domlist: '+unicode(domlist)
        dyndom_lst = ["('if_etalon', '=', True)"] 
        et_rset=False
        for fld in domlist:
            print "fld : "+unicode(fld)
 #           spar = '('+ "'"+fld+"'" +","+ "'='" +","+ "'"+eval('self.'+fld)+"'" + ')'
            print 'self.fld: '+unicode(eval('self.'+fld))
            spar = '('+ "'"+fld+"'" +","+ "'='" +","+ 'self.'+fld + ')'
            _logger.info("spar is:"+unicode(spar))
            dyndom_lst.append(spar)
        dyndom_str = ",".join(dyndom_lst)
        print 'dyndom_str: '+unicode(dyndom_str)
        try:
            et_rset = self.search([i for i in eval(dyndom_str)])
        except:
            _logger.error("search error: "+unicode(dyndom_str))
        self.etalonic_list = et_rset
        
    @api.one
    @api.depends('chkF_brand','chkF_model','chkF_wrsize','chkF_dia','chkF_et','chkF_pcd','chkF_paint')
    def _get_reverse_etalonic_ids2(self):
        if not self.if_etalon:
            return []
        domlist = self.get_chkF()[0]
        print 'domlist: '+unicode(domlist)
        dyndom_lst = ["('if_etalon', '=', False)"] 
        et_rset=False
        for fld in domlist:
            print "fld : "+unicode(fld)
 #           spar = '('+ "'"+fld+"'" +","+ "'='" +","+ "'"+eval('self.'+fld)+"'" + ')'
            print 'self.fld: '+unicode(eval('self.'+fld))
            spar = '('+ "'"+fld+"'" +","+ "'='" +","+ 'self.'+fld + ')'
            _logger.info("spar is:"+unicode(spar))
            dyndom_lst.append(spar)
        dyndom_str = ",".join(dyndom_lst)
        print 'dyndom_str: '+unicode(dyndom_str)
        try:
            et_rset = self.search([i for i in eval(dyndom_str)])
        except:
            _logger.error("search error: "+unicode(dyndom_str))
        self.reverse_etalonic_list = et_rset
        
        
#    @api.onchange('etalonic_list')
    @api.onchange('chkF_brand','chkF_model','chkF_wrsize','chkF_dia','chkF_et','chkF_pcd','chkF_paint','etalonic_list')
    def onchange_mult_etalonic_select(self):

#         def check_cur_state(self,f_list):
#             res = True
#             v_list = [eval('self.'+x) for x in f_list]
#             return res
        
        #flist = ['etalonic_select']
        
        #check_cur_state(self,flist)
        res = {}
        res['domain'] = { 'etalonic_select':[] }
        res['domain']['etalonic_select'].append(('id','in', self.etalonic_list.mapped('id')))
#        res['domain'] = { x:[] for x in flist }
#        res['value'] = {}
        print "UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU: "+unicode(res)
        return res

    
        
#     @api.one
#     def _get_etalonic_ids(self):
#         possible_field_list = ['brand','model','pcd','wrsize','et','dia','paint']
#         if self.etalonic_list_domain and self.etalonic_list_domain.strip()[0] == '[' and self.etalonic_list_domain.strip()[-1] == ']':
#  
#             try:
#                 domlist = eval(self.etalonic_list_domain) 
# 
#             except:
#                 _logger.error("wrong self.etalonic_list_domain: "+unicode(self.etalonic_list_domain))
#                 domlist = []
#             try:
#                 for fld in domlist:
#                     if fld not in possible_field_list:
#                         domlist = []
#                         break
#             except:
#                 _logger.error("Something wrong with domlist: "+unicode(self.etalonic_list_domain))
#                 
#                     
#                  
#             dyndom_lst = ["('if_etalon', '=', True)"] 
#             et_rset=False
#             len_domlist = len(domlist)
#             if len_domlist == 0:
#                 return False
#             else:
#                 for fld in domlist:
#                     spar = '('+ "'"+fld+"'" +","+ "'='" +","+ "'"+eval('self.'+fld)+"'" + ')'
#                     _logger.info("spar is:"+unicode(spar))
#                     dyndom_lst.append(spar)
#                 dyndom_str = ",".join(dyndom_lst)
#                 try:
#                     et_rset = self.search([i for i in eval(dyndom_str)])
#                 except:
#                     _logger.error("search error: "+unicode(dyndom_str))
#                  
#         else:
#             et_rset = self.search([('wrsize', '=', self.wrsize), ('pcd', '=', self.pcd), ('brand', '=', self.brand), 
#                                ('model','=',self.model),('et','=',self.et),('dia','=',self.dia),('if_etalon', '=', True)])
#         self.etalonic_list = et_rset
#         
#         
#     @api.one
#     def _get_reverse_etalonic_ids(self):
#         possible_field_list = ['brand','model','pcd','wrsize','et','dia','paint']
#         if self.etalonic_list_domain and self.etalonic_list_domain.strip()[0] == '[' and self.etalonic_list_domain.strip()[-1] == ']':
#  
# #     _logger.info('self is:  '+unicode(self))
# #     _logger.info('self wrsize is:  '+unicode(self.wrsize))
# #     _logger.info(unicode(self.etalonic_list_domain))
#             try:
#                 domlist = eval(self.etalonic_list_domain) 
#             except:
#                 _logger.error("wrong self.etalonic_list_domain: "+unicode(self.etalonic_list_domain))
#                 domlist = []
# 
#             try:
#                 for fld in domlist:
#                     if fld not in possible_field_list:
#                         domlist = []
#                         break
#             except:
#                 _logger.error("Something wrong with domlist: "+unicode(self.etalonic_list_domain))
#                  
# #     _logger.info("domlist: "+unicode(domlist))
#             dyndom_lst = ["('if_etalon', '=', False)"] 
#             et_rset=False
#             len_domlist = len(domlist)
#             if len_domlist == 0:
#                 return False
#             else:
#                 for fld in domlist:
#                     spar = '('+ "'"+fld+"'" +","+ "'='" +","+ "'"+eval('self.'+fld)+"'" + ')'
#                     _logger.info("spar is:"+unicode(spar))
#                     dyndom_lst.append(spar)
#                 #_logger.info("dyndom_lst: "+unicode(dyndom_lst))
#                 dyndom_str = ",".join(dyndom_lst)
#                 #_logger.info("dyndom_str: "+unicode(dyndom_str))
#                 try:
#                     et_rset = self.search([i for i in eval(dyndom_str)])
#                 except:
#                     _logger.error("search error: "+unicode(dyndom_str))
#                  
#         else:
#             et_rset = self.search([('wrsize', '=', self.wrsize), ('pcd', '=', self.pcd), ('brand', '=', self.brand), 
#                                ('model','=',self.model),('et','=',self.et),('dia','=',self.dia),('if_etalon', '=', False)])
#         self.reverse_etalonic_list = et_rset
#     
    @api.one
    def autoconnect(self):
        if (self.wrsize and self.pcd and self.brand and self.model and self.dia and self.et and self.paint):
            et_rset = self.search([('wrsize', '=', self.wrsize), ('pcd', '=', self.pcd), ('brand', '=', self.brand), ('model','=',self.model),
                                   ('et','=',self.et),('dia','=',self.dia),('paint','=',self.paint),('if_etalon', '=', True)])
            if len(et_rset):
                self.etalonic_select = et_rset[0].id
                self.etalon_id = et_rset[0].proxy_id.id
    @api.one
    def manual_connect(self):
        if self.etalonic_select:
            self.etalon_id = self.etalonic_select.proxy_id.id
        
    def autoconnect_all_sel_ids(self, cr, uid, ids, context=False):
        for instid in ids:
            inst = self.browse(cr, uid, [instid])[0]
            inst.autoconnect()
            _logger.info(unicode(inst.name)+"         autoconnected!")

    
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
        if not self.brand:
            _logger.error( "########## NOT set BRAND for model parsing in: "+ unicode(self.name))
            return False
        parser = modelParser(parse_string=self.name, dict_type='disk_model', parent_key=self.brand, parent_key_dict_type='disk_brand')
        parsed_model, name_minus_model = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_model :
            self.model = parsed_model
            self.name_unparsed = name_minus_model
        else:
            _logger.warning("########## model not found in name: "+ unicode(self.name))
        return parsed_model 
    
    
    
    
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
    country = fields.Char('Country')
    season = fields.Selection([('summer','Summer'),('winter','Winter'),('all-season','All Season')],string='Season')
    lg_weightness = fields.Selection([('special','Special'),('agricultural','Agricultural'),('industrial','Industrial'),('4x4','4x4'),('light_car','Light car'),('truck','Truck'),('light_truck','Light truck')],string='Weightness')
    R = fields.Char('R') 
    
    name_unparsed = fields.Char('Left for parsing')
    etalonic_select = fields.Many2one('virt.tire', domain="[('tire_wpd', '=', tire_wpd),('tire_wsp', '=', tire_wsp), ('tire_brand','=',tire_brand),('tire_model','=',tire_model),('if_etalon','=',True)]", string = 'Select etalonic tire')
    reverse_etalonic_select = fields.Many2one('virt.tire', domain="[('tire_wpd', '=', tire_wpd),('tire_wsp', '=', tire_wsp), ('tire_brand','=',tire_brand),('tire_model','=',tire_model),('if_etalon','=',False)]", string = 'Select non-etalon tire')
    etalonic_list = fields.One2many(compute='_get_etalonic_ids2', comodel_name='virt.tire', string = 'Possible etalon virt tires')
    reverse_etalonic_list = fields.One2many(compute='_get_reverse_etalonic_ids2', comodel_name='virt.tire', string = 'Possible non-etalon virt tires')
#    etalonic_list = fields.One2many(compute='_get_etalonic_ids', comodel_name='virt.tire', string = 'Possible etalon virt tires')
    chkF_tire_brand = fields.Boolean("Brand")
    chkF_tire_model = fields.Boolean("Model")
    chkF_tire_wsp = fields.Boolean("WSP")
    chkF_tire_wpd = fields.Boolean("WPD")
    chkF_tire_studness = fields.Boolean("Studness")
    
    #smart selector
    @api.one
    def get_chkF(self):
        res = []
        res_def = []
        for fld in self.fields_get_keys():
            if 'chkF' in fld:
                print fld
                fval = eval('self.'+fld)
                res_def.append(fld[5:])
                if fval:
                    res.append(fld[5:])
        print 'res: '+unicode(res)
        print 'res_def :'+unicode(res_def)
        if len(res) > 0:
            return res
        return res_def


    @api.one
    @api.depends('chkF_tire_brand','chkF_tire_model','chkF_tire_wsp','chkF_tire_wpd','chkF_tire_studness')
    def _get_etalonic_ids2(self):
        if self.if_etalon:
            return []
        domlist = self.get_chkF()[0]
        print 'domlist: '+unicode(domlist)
        dyndom_lst = ["('if_etalon', '=', True)"] 
        et_rset=False
        for fld in domlist:
            print "fld : "+unicode(fld)
 #           spar = '('+ "'"+fld+"'" +","+ "'='" +","+ "'"+eval('self.'+fld)+"'" + ')'
            print 'self.fld: '+unicode(eval('self.'+fld))
            spar = '('+ "'"+fld+"'" +","+ "'='" +","+ 'self.'+fld + ')'
            _logger.info("spar is:"+unicode(spar))
            dyndom_lst.append(spar)
        dyndom_str = ",".join(dyndom_lst)
        print 'dyndom_str: '+unicode(dyndom_str)
        try:
            et_rset = self.search([i for i in eval(dyndom_str)])
        except:
            _logger.error("search error: "+unicode(dyndom_str))
        self.etalonic_list = et_rset
        
    @api.one
    @api.depends('chkF_tire_brand','chkF_tire_model','chkF_tire_wsp','chkF_tire_wpd','chkF_tire_studness')
    def _get_reverse_etalonic_ids2(self):
        if not self.if_etalon:
            return []
        domlist = self.get_chkF()[0]
        print 'domlist: '+unicode(domlist)
        dyndom_lst = ["('if_etalon', '=', False)"] 
        et_rset=False
        for fld in domlist:
            print "fld : "+unicode(fld)
 #           spar = '('+ "'"+fld+"'" +","+ "'='" +","+ "'"+eval('self.'+fld)+"'" + ')'
            print 'self.fld: '+unicode(eval('self.'+fld))
            spar = '('+ "'"+fld+"'" +","+ "'='" +","+ 'self.'+fld + ')'
            _logger.info("spar is:"+unicode(spar))
            dyndom_lst.append(spar)
        dyndom_str = ",".join(dyndom_lst)
        print 'dyndom_str: '+unicode(dyndom_str)
        try:
            et_rset = self.search([i for i in eval(dyndom_str)])
        except:
            _logger.error("search error: "+unicode(dyndom_str))
        self.reverse_etalonic_list = et_rset
        
        
#    @api.onchange('etalonic_list')
    @api.onchange('chkF_tire_brand','chkF_tire_model','chkF_tire_wsp','chkF_tire_wpd','chkF_tire_studness')
    def onchange_mult_etalonic_select(self):

#         def check_cur_state(self,f_list):
#             res = True
#             v_list = [eval('self.'+x) for x in f_list]
#             return res
        
        #flist = ['etalonic_select']
        
        #check_cur_state(self,flist)
        res = {}
        res['domain'] = { 'etalonic_select':[] }
        res['domain']['etalonic_select'].append(('id','in', self.etalonic_list.mapped('id')))
#        res['domain'] = { x:[] for x in flist }
#        res['value'] = {}
        print "UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU: "+unicode(res)
        return res
    
    
    
    
    
    
    #/smart selector

    @api.one
    def set_cat2(self):
        self.parse_lg_weightness()
        self.parse_R()
        self.setCatIdBy_lg_weightness_and_R()
    
    def set_cat2_all_sel_ids(self, cr, uid, ids, context=False):
        for instid in ids:
            inst = self.browse(cr, uid, [instid])[0]
            inst.set_cat2()
            _logger.info( unicode(inst.name)+"  categ processed!")

    @api.one
    def setCatIdBy_lg_weightness_and_R(self):
        cpt = self.get_connected_product_template() 
        if cpt:
            _logger.info('cpt name: '+ unicode(cpt.name))
            res = self.getCatIdBy2(parent_categ_name=self.lg_weightness, categ_name=self.R)[0]
            _logger.info('res : '+ unicode(res))
            if res:
                cpt.categ_id = res 
#                cpt.categ_id = res.id 
                _logger.info('cpt.categ_id_name : '+ unicode(cpt.categ_id.name))
                return cpt.categ_id
            else:
                _logger.info('category not set : not found')
                return False


    @api.one
    def getCatIdBy2(self, parent_categ_name=False, categ_name=False):
        if not (parent_categ_name and categ_name):
            _logger.warn('Error:  possibly lg_WR or R fields not set ')
            return False
        cat_env = http.request.env['product.category']
        try:
            res = cat_env.search([('parent_id.name','=',parent_categ_name),('name','=',categ_name)]).mapped('id')[0]
        except:
            #raise osv.except_osv(('Error'), ('Error:  category '+unicode(parent_categ_name)+' / '+unicode(categ_name)+ ' not found'))
            #raise osv.except_osv(('Error'), ('Error:  category '+unicode(parent_categ_name)+' / '+unicode(categ_name)+ ' not found'))
            _logger.error('Error:  category '+unicode(parent_categ_name)+' / '+unicode(categ_name)+ ' not found')
            res = False

        #if res:
        #    res = cat_env.browse([res])
        _logger.info('result categ id: '+ unicode(res))
        return res
    
#    getCatByWR = lambda self,cr,uid,parent_categ_name,categ_name: self.getCatIdBy2(parent_categ_name=self.lg_weightness, categ_name=self.R) 

#     @api.one    
#     def getCatByWR(self):
#         cat_env = http.request.env['product.category']
#         res = cat_env.search([('parent_id.name','=',self.lg_weightness),('name','=',self.R)])
# #        res = cat_env.search([('parent_id.name','=',self.lg_weightness),('name','=',self.R)]).mapped('id')
#         _logger.info('result categ name: '+ unicode(res[0].name))
#         _logger.info('result categ id: '+ unicode(res))
        
    
    @api.multi
    @api.model
    def get_connected_product_template(self):
        pt_env = self.env['product.template']
        prox_id = self.proxy_id.id
#        prox_id = self.proxy_id.id
        _logger.info(" prox_id is: " + unicode(prox_id))
        _logger.info(" pt_env is: " + unicode(pt_env))
        res = pt_env.search([('proxy_id.id','=',prox_id)]).mapped('id')
#        res = pt_env.search([('proxy_id.id','=',prox_id)]).mapped('id')[0]
        if len(res):
            res = pt_env.browse(res[0])
            _logger.info(" res is: " + unicode(res))
            return res
        else:
            return False
   #     _logger.info("Found connected template, name is: " + unicode(res.name))


    @api.one
    def autoconnect(self):
        if (self.tire_brand and self.tire_model and self.tire_studness and self.tire_wpd and self.tire_wsp):
            et_rset = self.search([('tire_wsp', '=', self.tire_wsp), ('tire_wpd', '=', self.tire_wpd), ('tire_brand', '=', self.tire_brand), ('tire_model','=',self.tire_model),
                                   ('tire_studness','=',self.tire_studness),('if_etalon', '=', True)])
            if len(et_rset):
                self.etalonic_select = et_rset[0].id
                self.etalon_id = et_rset[0].proxy_id.id


    def autoconnect_all_sel_ids(self, cr, uid, ids, context=False):
        for instid in ids:
            inst = self.browse(cr, uid, [instid])[0]
            inst.autoconnect()
            _logger.info(unicode(inst.name)+"         autoconnected!")

    @api.multi
    @api.model
    def conn_to_me(self):
        if self.reverse_etalonic_select == False:
            return False
        n_inst = self.browse([self.reverse_etalonic_select.id])
        _logger.info('self is:  '+unicode(self))
        _logger.info('n_inst is:  '+unicode(n_inst))
        n_inst.write({'etalon_id':self.proxy_id.id})

    @api.one
    def clear_parsed_fields(self):
        self.write({'tire_brand':False,'tire_model':False,'tire_wpd':False,'tire_wsp':False,'tire_studness':False,'country':False})

    @api.one
    def disconnect_etalon(self):
        self.write({'etalon_id':False})
    
    @api.one
    def _get_etalonic_ids(self):
        et_rset = self.search([('tire_wpd', '=', self.tire_wpd), ('tire_wsp', '=', self.tire_wsp), 
                               ('tire_brand', '=', self.tire_brand), ('tire_model','=',self.tire_model),
                               ('tire_studness','=',self.tire_studness),('if_etalon', '=', True)])
        self.etalonic_list = et_rset

    @api.one
    def _get_reverse_etalonic_ids(self):
        et_rset = self.search([('tire_wpd', '=', self.tire_wpd), ('tire_wsp', '=', self.tire_wsp),
                                ('tire_brand', '=', self.tire_brand), ('tire_model','=',self.tire_model),
                                ('tire_studness','=',self.tire_studness),('if_etalon', '=', False)])
        self.reverse_etalonic_list = et_rset
    
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
        self.parse_season()
        self.parse_lg_weightness()
        self.parse_R()
    
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
        return parsed_brand
#        return True
 
    @api.multi 
    @api.model
    def parse_season(self):
        parser = seasonParser(parse_string=self.name, dict_type='tyre_season')
        parsed_brand, name_minus_brand = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_brand :
            self.season = parsed_brand
            self.name_unparsed = name_minus_brand
        else:
            _logger.warning( "########## season not found in name: "+ unicode(self.name))
            #self.tire_studness = 'n/s'
        return True
    
    @api.multi 
    @api.model
    def parse_R(self):
        parser = RParser(self.name)
        parsed_wpd, name_minus_wpd = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_wpd :
            self.R = parsed_wpd.upper()
            self.name_unparsed = name_minus_wpd
        else:
            _logger.warning("########## R not found in name: "+ unicode(self.name))
        return True
    
    @api.multi 
    @api.model
    def parse_lg_weightness(self):
        parser = lg_weightnessParser(parse_string=self.name, dict_type='tyre_lg_weightness')
        parsed_brand, name_minus_brand = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_brand :
            self.lg_weightness = parsed_brand
            self.name_unparsed = name_minus_brand
        else:
            _logger.warning( "########## lg_weightness not found in name: "+ unicode(self.name))
            #self.tire_studness = 'n/s'
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
        if not self.tire_brand:
            _logger.error( "########## NOT set BRAND for model parsing in: "+ unicode(self.name))
            return False
        parser = modelParser(parse_string=self.name, dict_type='tyre_model', parent_key=self.tire_brand, parent_key_dict_type='tyre_brand')
        parsed_model, name_minus_model = parser.parse()
#        parsed_brand, name_minus_brand = parser.parse(self.name)
        if parsed_model :
            self.tire_model = parsed_model
            self.name_unparsed = name_minus_model
        else:
            _logger.warning( "########## model not found in name: "+ unicode(self.name))
        return parsed_model 
    
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
    
          
    @api.multi
    @api.model
    def open_brand_dict(self):
    #Define model name of agreement:
        mod_name = 'parse_dict_keys'
        mod_env = http.request.env[mod_name]
        rec_id = mod_env.search([('type','=','tyre_brand'),('name','=',self.tire_brand)])
        if len(rec_id):
            rec_id = rec_id[0].id
        #print mod_name
            return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': mod_name,
            'res_id': rec_id,
            "views": [[False, "form"]],
            }
        return False
            

