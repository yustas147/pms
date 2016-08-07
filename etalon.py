# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
#from osv import fields, osv
from openerp.tools import logging
from openerp import pooler
#from tools import logging
#from tools.translate import _

class pricelist_partnerinfo(osv.osv):
    _name = 'pricelist.partnerinfo'
    _inherit = 'pricelist.partnerinfo'
    _columns = {
        'sup_quantity': fields.float('Ostatki postavshika', required=False,),
        'min_quantity': fields.float('Min partiya', required=False,),
        }
pricelist_partnerinfo()

class product_supplierinfo(osv.osv):

    def _get_price(self,cr,uid,ids,field_name,arg,context={}):
        res = {}
        for price in self.browse(cr,uid,ids,context=context):
            res[price.id] = {
                'plist_qty': price.pricelist_ids[0].sup_quantity if price.pricelist_ids else 0.0,
                #'plist_qty': price.pricelist_ids[0].min_quantity if price.pricelist_ids else 0.0,
                'plist_price': price.pricelist_ids[0].price if price.pricelist_ids else 0.0,
            }
        return res

    _inherit = 'product.supplierinfo'
    _columns = {
        'plist_qty': fields.function(_get_price, method=True, string='SupQuantity', multi='plists',),
        'plist_price': fields.function(_get_price, method=True, string='Price', multi='plists',),
#	'test_field': fields.float('test field from yustas', required=False,),
        }

product_supplierinfo()



class product_product(osv.osv):


    _inherit = 'product.product'

    _columns = {
        'connected': fields.boolean('Connected', ),
        'etalon_product': fields.many2one('product.product','Etalon product'),
        #'price_ref': fields.integer('Price Ref Record', ),
        'imp_qty': fields.float('Quantity', ),
        'supplier': fields.many2one('res.partner','Supplier', required=True,),
        #yustas: price_ref change
        'price_ref': fields.many2one('pricelist.partnerinfo', 'price_ref', ondelete='set null'),
        'isConnEt': fields.selection([('unconn', 'Unconntd'),('conn','Connected')], 'Etal Connection State'),
       # 'isConnChr': fields.char('IsConn', size=64)

        }
    _defaults = {
        'connected': 0,
        'isConnEt': 'unconn',
       # 'isConnChr': 'no'
#        'price_ref': 0,
        }
    

    def set_list_price(self, cr, uid, etalon_prod_ids, context=False):
      def exclude_null(i): return ( i > 0.01 )
    #def set_list_price(self, cr, uid, ids, context=False):
         
      #pool = self.pool
      plist_pool = self.pool.get('pricelist.partnerinfo')
      psuppl_pool = self.pool.get('product.supplierinfo')
      for etalon_prod_id in etalon_prod_ids:
        #pool_suppinfo = pool.get('product_supplierinfo')
        #for etalon_prod_id in etalon_prod_id :
          inst = self.browse(cr, uid, etalon_prod_id)
        #raise osv.except_osv('Warning', 'inst: '+str(inst)) 
          if inst.etalon_product:
              raise osv.except_osv('Warning', 'To ne etalon product!') 
          etalon_prod_tmpl_id = self.browse(cr, uid, etalon_prod_id).product_tmpl_id.id

          prod_suppl_info_list = psuppl_pool.search(cr, uid, [('product_id', '=', etalon_prod_tmpl_id)])

# not null quantities:
          pricelist_partnerinfo_ids_nonuls = plist_pool.search(cr, uid, [('suppinfo_id', 'in', prod_suppl_info_list), ('sup_quantity', '>', 0.1), ('price', '>', 0.01)])

          price_list = []
          for ppid in pricelist_partnerinfo_ids_nonuls:
               price_list.append(plist_pool.browse(cr, uid, ppid).price)
          price_list.sort()
          if len(price_list) > 0 :
              self.write(cr, uid, inst.id, {'list_price':float(price_list[0]),},) 
              cr.commit()

      return False

    def set_all_lp(self, cr, uid, ids, context={}):
        #lp = []
        etalon_ids = self.search(cr, uid, [('etalon_product', '=', False)])

   #     raise osv.except_osv('Warning','The etalon_ids is: '+ str(etalon_ids))
        self.set_list_price(cr, uid, etalon_ids)
        #etalon_ids = pooler.get_pool(cr.dbname).get('product.product').search(cr, uid, [('etalon_product', '=', False)])
        #for etal_id in etalon_ids :
            
            #inst = self.browse(cr, uid, [etal_id])
        #    inst = self.pool.get('product.product').browse(cr, uid, etal_id)
        #    inst.set_list_price(self, cr, uid, ids)[0]
        #    self.set_list_price(cr, uid, etal_id) 
        #set_list_price(cr, uid, etal_id) 
            #self.set_list_price(self, cr, uid, etal_id, context=False) 
        #    lp.append(inst.list_price)

        #raise osv.except_osv('Warning', 'Etalon products are:' + str(etalon_ids))
        #raise osv.except_osv('Warning', 'Etalon listprices  are:' + str(lp))
       # cr.commit() 
        raise osv.except_osv('Status:', 'Price update was finished successfully !')
        return False
        '''      return {'warning': {
                    'title': _('Status:'),
                    'message':  _('Price update was finished successfully'),
                    }
                }
        '''

    def connect(self, cr, uid, ids):
#    def connect(self, cr, uid, ids, context=False):

        pool = self.pool
        inst = self.browse(cr, uid, ids)[0]
        if not inst.etalon_product:
            raise osv.except_osv('Warning', 'Etalon product is required !')

        if inst.price_ref:
            partner_info = pool.get('pricelist.partnerinfo').browse(cr, uid, inst.price_ref.id)
            pool.get('product.supplierinfo').unlink(cr, uid, [partner_info.suppinfo_id.id])
            #yustas
            pool.get('pricelist.partnerinfo').unlink(cr, uid, [partner_info.id])

        suppl_info_id = pool.get('product.supplierinfo').create(cr, uid, {
                        'product_id':inst.etalon_product.id,
                        'name':inst.supplier.id,
                        'min_qty':1,
                        'product_code':inst.default_code,
                        'product_name':inst.name,
                        })
        part_info_id = pool.get('pricelist.partnerinfo').create(cr, uid, {
                        'suppinfo_id':suppl_info_id,
                        'sup_quantity':inst.imp_qty,
                        #'min_quantity':inst.imp_qty,
                        #'min_quantity':inst.imp_qty,
                        #'min_quantity':inst.imp_qty,
                        #'min_quantity':inst.imp_qty,
                        #'min_quantity':inst.imp_qty,
                        'price':inst.standard_price,
                        }, context=False)
#                        }, context=context)
        pool.get('product.product').write(cr, uid, inst.id,{'price_ref':part_info_id,})
#        pool.get('product.product').write(cr, uid, inst.id,{'price_ref':part_info_id,}, context=context)

        self.write(cr, uid, inst.id, {'connected':1, 'isConnEt':'conn'})
#        self.write(cr, uid, inst.id, {'connected':1, 'isConnEt':'conn', 'isConnChr':'yes'})
        return True
    
#     def connect(self, cr, uid, ids, context):
# #    def connect(self, cr, uid, ids, context=False):
# 
#         pool = self.pool
#         inst = self.browse(cr, uid, ids)[0]
#         if not inst.etalon_product:
#             raise osv.except_osv('Warning', 'Etalon product is required !')
# 
#         if inst.price_ref:
#             partner_info = pool.get('pricelist.partnerinfo').browse(cr, uid, inst.price_ref.id, context=context)
#             pool.get('product.supplierinfo').unlink(cr, uid, [partner_info.suppinfo_id.id], context=context)
#             #yustas
#             pool.get('pricelist.partnerinfo').unlink(cr, uid, [partner_info.id])
# 
#         suppl_info_id = pool.get('product.supplierinfo').create(cr, uid, {
#                         'product_id':inst.etalon_product.id,
#                         'name':inst.supplier.id,
#                         'min_qty':1,
#                         'product_code':inst.default_code,
#                         'product_name':inst.name,
#                         }, context=context)
#         part_info_id = pool.get('pricelist.partnerinfo').create(cr, uid, {
#                         'suppinfo_id':suppl_info_id,
#                         'sup_quantity':inst.imp_qty,
#                         #'min_quantity':inst.imp_qty,
#                         #'min_quantity':inst.imp_qty,
#                         #'min_quantity':inst.imp_qty,
#                         #'min_quantity':inst.imp_qty,
#                         #'min_quantity':inst.imp_qty,
#                         'price':inst.standard_price,
#                         }, context=context)
#         pool.get('product.product').write(cr, uid, inst.id,{'price_ref':part_info_id,})
# #        pool.get('product.product').write(cr, uid, inst.id,{'price_ref':part_info_id,}, context=context)
# 
#         self.write(cr, uid, inst.id, {'connected':1, 'isConnEt':'conn'})
# #        self.write(cr, uid, inst.id, {'connected':1, 'isConnEt':'conn', 'isConnChr':'yes'})
#         return True    
    

    def disconnect(self, cr, uid, ids, context=False):

        pool = self.pool
        inst = self.browse(cr, uid, ids)[0]
        if not inst.etalon_product:
            raise osv.except_osv('Warning', 'Etalon product is required !')

        if inst.price_ref:
            partner_info = pool.get('pricelist.partnerinfo').browse(cr, uid, inst.price_ref.id, context=context)
            pool.get('product.supplierinfo').unlink(cr, uid, [partner_info.suppinfo_id.id], context=context)
            #yustas
            pool.get('pricelist.partnerinfo').unlink(cr, uid, [partner_info.id])

        pool.get('product.product').write(cr, uid, inst.id,{'price_ref':False,}, context=context)

        self.write(cr, uid, inst.id, {'connected':0, 'etalon_product':False, 'isConnEt':'unconn'})
#        self.write(cr, uid, inst.id, {'connected':0, 'etalon_product':False, 'isConnEt':'unconn', 'isConnChr':'no'})
        return True

    
    def connect_bkg(self, cr, uid, ids, context = False):
         
        nonet_unconnected = pooler.get_pool(cr.dbname).get('product.product').search(cr, uid, [('connected', '=', False), ('supplier', '!=', 1)])
 
        for non_unc in nonet_unconnected :
            inst = self.browse(cr, uid, non_unc)
            etal_to_con = self.pool.get('product.product').search(cr, uid, [('default_code', '=', inst.default_code), ('supplier', '=', 1)])
            if etal_to_con :
                etal_to_con_inst = self.browse(cr, uid, etal_to_con)
                inst.etalon_product = etal_to_con_inst[0].id
                if inst.price_ref:
                    partner_info = pooler.get_pool(cr.dbname).get('pricelist.partnerinfo').browse(cr, uid, inst.price_ref.id, context=context)
#                    partner_info = osv.pooler.get_pool(cr.dbname).get('pricelist.partnerinfo').browse(cr, uid, inst.price_ref.id, context=context)
                    pooler.get_pool(cr.dbname).get('product.supplierinfo').unlink(cr, uid, [partner_info.suppinfo_id.id], context=context)
#                    osv.pooler.get_pool(cr.dbname).get('product.supplierinfo').unlink(cr, uid, [partner_info.suppinfo_id.id], context=context)
 
                suppl_info_id = pooler.get_pool(cr.dbname).get('product.supplierinfo').create(cr, uid, {
#                suppl_info_id = osv.pooler.get_pool(cr.dbname).get('product.supplierinfo').create(cr, uid, {
                        'product_id':int(inst.etalon_product),
                        'name':int(inst.supplier),
                        'min_qty':1,
                        'product_code':inst.default_code,
                        'product_name':inst.name,
                        }, context=context)
                part_info_id = pooler.get_pool(cr.dbname).get('pricelist.partnerinfo').create(cr, uid, {
#                part_info_id = osv.pooler.get_pool(cr.dbname).get('pricelist.partnerinfo').create(cr, uid, {
                        'suppinfo_id':suppl_info_id,
                        'sup_quantity':inst.imp_qty,
                        #'min_quantity':inst.imp_qty,
                        'price':inst.standard_price,
                        }, context=context)
                pooler.get_pool(cr.dbname).get('product.product').write(cr, uid, inst.id,{'price_ref':part_info_id, 'etalon_product':inst.etalon_product}, context=context)
#                osv.pooler.get_pool(cr.dbname).get('product.product').write(cr, uid, inst.id,{'price_ref':part_info_id, 'etalon_product':inst.etalon_product}, context=context)
                #osv.pooler.get_pool(cr.dbname).get('product.product').write(cr, uid, inst.id,{'price_ref':part_info_id,}, context=context)
 
                self.write(cr, uid, inst.id, {'connected':1})
        return True
                




        sql_qry = ''' SELECT 
  ppet.id AS et_id, 
  ppnonet.id AS nonet_id, 
  ppnonet.connected, 
  ppet.default_code AS et_defcode, 
  ppnonet.default_code AS nonet_defcode
FROM 
  public.product_product ppet, 
  public.product_product ppnonet
WHERE 
  ppnonet.etalon_product IS NULL  AND 
  ppnonet.default_code = ppet.default_code AND 
  ppnonet.id != ppet.id AND 
  ppet.supplier = 1;
'''


    def conn_bkg(self, cr, uid, nonet_et, context=False):
        conn_prod_num = 0
        pool = pooler.get_pool(cr.dbname)
        for nonet in nonet_et.keys():
            et_id = nonet_et[nonet]
            nonet_id = nonet
            inst = self.browse(cr, uid, nonet_id)[0]
            inst.etalon_product = et_id
            if inst.price_ref:
                partner_info = pool.get('pricelist.partnerinfo').browse(cr, uid, inst.price_ref.id, context=context)
                pool.get('product.supplierinfo').unlink(cr, uid, [partner_info.suppinfo_id.id], context=context)
 
            suppl_info_id = pool.get('product.supplierinfo').create(cr, uid, {
                        'product_id':inst.etalon_product.id,
                        'name':inst.supplier.id,
                        'min_qty':1,
                        'product_code':inst.default_code,
                        'product_name':inst.name,
                        }, context=context)
            part_info_id = pool.get('pricelist.partnerinfo').create(cr, uid, {
                        'suppinfo_id':suppl_info_id,
                        'sup_quantity':inst.imp_qty,
                        #'min_quantity':inst.imp_qty,
                        'price':inst.standard_price,
                        }, context=context)
            pool.get('product.product').write(cr, uid, inst.id,{'price_ref':part_info_id,}, context=context)
            self.write(cr, uid, inst.id, {'connected':1})
            conn_prod_num += 1
        return conn_prod_num
         


    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context={}, toolbar=True, submenu=True):

        result = super(product_product, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar=toolbar)
        if view_type == 'form':
            user = self.pool.get('res.users').browse(cr, 1, uid)
            etal_partner_id = user.company_id.partner_id.id
            arch = result['arch']
            arch = arch.replace("'supplier','=',0","'supplier','=',%d" % etal_partner_id)
            arch = arch.replace("'supplier','!=',0","'supplier','!=',%d" % etal_partner_id)
            result['arch']=arch
        return result

product_product()





