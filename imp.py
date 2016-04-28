# -*- coding: utf-8 -*-
import os.path
from openerp.osv import fields, osv
#import logging
from openerp.tools import logging, file_open #, ustr
#from tools import file_open 
import urllib2
from openerp import pooler
import csv
from xlrd import open_workbook
#from tools.translate import _
import StringIO
import time
from hashlib import md5
from copy import copy
from math import modf

class imp(osv.osv):


    def _unconect_count(self, cr, uid, ids, fields, args, context={}):

        res = {}
        for id in ids:
            inst = self.browse(cr, uid, id)
            if inst.etalon_catalog:
                res[id] = 0
            else:
                products = self.pool.get(inst.model_name).search(cr, uid, [('supplier_id','=',inst.name.id),('etalon_id','=',False)])
#                products = self.pool.get('product.product').search(cr, uid, [('supplier','=',inst.name.name),('connected','=',0)])
                res[id] = len(products)
        return res

    def show_unconnected(self, cr, uid, ids, context=None):

        if context is None:
            context = {}
        inst = self.browse(cr, uid, ids[0])
        supplier = inst.name.id
        return {
                'name':"Products of " + inst.name.name,
                #'name':_("Products of ") + inst.name.name,
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': inst.model_name,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'domain': "[('etalon_id','=',False), ('supplier_id','=',%d)]" % supplier,
#                'domain': "[('connected','=',0), ('supplier','=',%d)]" % supplier,
                'context': "{}", # "{'search_default_connected':0,'search_default_categ_id':%d}" % cat_id[0]
            }

    _name = 'imp.imp'
    _columns = {
        'name': fields.many2one('res.partner','SupplierX', required=True,),
        'model_name': fields.selection([('virt.tire','Virtual tire'), ('virt.disk', 'Virtual disk')], 'Type of info', required=True),
        'url': fields.char('Url', size=64,
                                 help="Provide a path to your "
                                      "file"),
        'loc': fields.binary('File',filters='*.xls,*.xlsx,*.csv'),
        'description': fields.text('Information'),
        'etalon_catalog': fields.boolean('Etalon catalog'),
        'md5': fields.char('MD5', size=64),
        'fields_order': fields.char('Fields order', size=12),
        'imp_file': fields.selection([('local','Local'),
             ('remote','Remote')],'Location of file'),
        'imp_type': fields.selection([('csv','CSV'),
             ('xls','XLS')],'Type of file'),
        'force_import': fields.boolean('Force import'),
        'notes': fields.text('Notes'),
        'unconect_count': fields.function(_unconect_count, method=True, string='Unconected products', type='integer'),
        'import_order': fields.char('Order of fields', size=512),
        'import_order_main': fields.char('Order of fields (main)', size=512),
        'sheet_num': fields.integer('Sheet number'),
        'line_start': fields.integer('Number of line the data begins from'),
        'hide_unused': fields.boolean('Hide unused fields'),
        'last_import': fields.char('Last Import Time', size=32),
        'category_id': fields.many2one('product.category','Category', ),

    }
    _auto = True
    _defaults = {
        'etalon_catalog': False,
        'imp_type': 'xls',
        'force_import': False,
        'imp_file': 'local',
        'sheet_num': 1,
        'line_start': 2,
        'hide_unused': False,
        }

    def imp_import(self, cr, uid, ids, context={}):

        logger = logging.getLogger('imp')
        inst = self.browse(cr, uid, ids[0])

        if inst.imp_file == 'remote':
            try:
                sock = urllib2.urlopen(inst.url)
                del sock
            except Exception :
                raise osv.except_osv('Warning', 'URl is incorrect or wrong type or format of the file !')
                #raise osv.except_osv(_('Warning'), _('URl is incorrect or wrong type or format of the file !'))
        else:
            if not inst.loc:
                raise osv.except_osv('Warning', 'Please, provide a file !')
                #raise osv.except_osv(_('Warning'), _('Please, provide a file !'))

        remote = inst.imp_file == 'remote'
        checkmd5 = False
        md = md5()

        if remote:
            try:
                sock = urllib2.urlopen(inst.url)
                if inst.imp_type == 'csv':
                    source = csv.reader(sock, quotechar='"', delimiter=',')
                elif inst.imp_type == 'xls':
                    source = open_workbook(file_contents=sock.read())
            except Exception :
                logger.warning("Except my remote")
                raise osv.except_osv('Warning', 'Cant open Url !')
                #raise osv.except_osv(_('Warning'), _('Cant open Url !'))
        else:
            try:
                if inst.imp_type == 'csv':
                    source = csv.reader(StringIO.StringIO(inst.loc.decode('base64')), quotechar='"', delimiter=',')
                elif inst.imp_type == 'xls':
                    source = open_workbook(file_contents=StringIO.StringIO(inst.loc.decode('base64')).read())
            except Exception :
                raise osv.except_osv('Warning', 'Corrupt Fie format or incorrect file format !')
                #raise osv.except_osv(_('Warning'), _('Corrupt Fie format or incorrect file format !'))

        if remote:
            sock = urllib2.urlopen(inst.url)
            md.update(sock.read())
            _md5 = md.hexdigest()
        else:
            md.update(StringIO.StringIO(inst.loc.decode('base64')).read())
            _md5 = md.hexdigest()

        if not inst.force_import:
            if inst.md5:
                if inst.md5 == _md5:
                    raise osv.except_osv('Warning', 'Old version of the file !')
                    #raise osv.except_osv(_('Warning'), _('Old version of the file !'))

        fields_str = inst.import_order_main
        if not fields_str:
            raise osv.except_osv('Warning', 'Please, set fields order first !')
            #raise osv.except_osv(_('Warning'), _('Please, set fields order first !'))
        fields_dict = eval(fields_str)
        fields=[]
        poss = fields_dict.keys()
        poss.sort()
        for key in poss:
            fields.append(fields_dict[key])

        sheet_line_poss = [inst.sheet_num-1, inst.line_start-1]
        arrgs = (cr, inst, source, fields, poss, sheet_line_poss, inst.model_name)
#        arrgs = (cr, inst, source, fields, poss, sheet_line_poss, self.model_name)

        if inst.imp_type == 'xls':
            msg = check_fields_types(*arrgs)
            if msg:
                context.update({'import_results':msg})
                return {
                        'name':"Test Wizard",
                        #'name':_("Test Wizard"),
                        'view_mode': 'form',
                        'view_type': 'form',
                        'res_model': 'imp.wizard.fields',
                        'target': 'new',
                        'nodestroy': True,
                        'type': 'ir.actions.act_window',
                        'context': "%s" % context
                    }
            else:
                if inst.etalon_catalog:
                    res = tmp_xls_import_etalon(*arrgs)
                else:
                    res = tmp_xls_import(*arrgs)
        else:
            if inst.etalon_catalog:
##                res = tmp_csv_import_etalon(*arrgs)
                pass
            else:
 ##               res = tmp_csv_import(*arrgs)
                pass


        result, rows, warning_msg, dummy = res[0]
        report = res[1]

        if result < 0:
            print res
            #raise Exception('Import error: %s' % (warning_msg,))
            #raise Exception(_('Import error: %s') % (warning_msg,))
        else:
            if inst.description:
                old_reports_list = inst.description.split('\n*')
                if len(old_reports_list) > 50:
                    old_reports_list.pop()
                    report = report + '\n' + '\n*'.join(old_reports_list)
                else:
                    report = report + '\n' + '\n*'.join(old_reports_list)

            return self.write(cr, uid, inst.id,{'md5':_md5,
                                                'description':report,
                                                'last_import':str(time.strftime('%d.%m.%y %H:%M:%S'))
                                                })


    def set_import_order(self, cr, uid, ids, context={}):

        inst = self.browse(cr, uid, ids)[0]
        fields = self.fields_get(cr,uid)
        f_names = fields.keys()
        f_names_bool = [i for i in f_names if i.startswith('x_bool_')]

        f_names_bool_true = []
        for attr in f_names_bool:
            if getattr(inst, attr):
                f_names_bool_true.append(attr.replace('x_bool_','x_'))

        li = [ getattr(inst, fld) for fld in f_names_bool_true]
        for pos in li:
            if li.count(pos)>1:
                raise osv.except_osv('Warning', 'Duplicated field position !')
                #raise osv.except_osv(_('Warning'), _('Duplicated field position !'))

        di = {}
        for fld in f_names_bool_true:
            di[getattr(inst, fld)] = fld

        st=st_main=''
        keys = di.keys()
        keys.sort()
        for key in keys:
            st += ' %s - #%d; ' % (fields[di[key]]['string'], key)
            st_main += "%d:'%s'," % (key-1, di[key].replace('x_',''))
        st_main = '{'+st_main[:-1]+'}'
        done = self.write(cr, uid, inst.id, {'import_order':st})
        done = self.write(cr, uid, inst.id, {'import_order_main':st_main})
        # fucking debug by @podarok // Drupal way! we need comments for code!!!!
        # raise osv.except_osv(_('Warning'), st_main)


        return True

imp()


#===============================================================================
#===============================================================================

def check_fields_types(cr, inst, source, fields, poss, sheet_line_poss, model_nm):

    pool = pooler.get_pool(cr.dbname)
    config_ids = pool.get('imp.config').search(cr,1,[])
    if not config_ids:
        raise osv.except_osv('Warning', 'Configure import fields, firs !')
        #raise osv.except_osv(_('Warning'), _('Configure import fields, firs !'))
    config = pool.get('imp.config').browse(cr,1,config_ids)[0]
    if not config.import_fields_types:
        raise osv.except_osv('Warning', 'No field allowed, configure import fields !')
        #raise osv.except_osv(_('Warning'), _('No field allowed, configure import fields !'))
    fields_types = eval(config.import_fields_types)
#yustas
 #   raise osv.except_osv(_('Warning'), str(fields_types))

    sheet = source.sheets()[sheet_line_poss[0]]
    warning_lst = {}

    for row in xrange(sheet_line_poss[1],sheet.nrows):
        itr = 0
        warning_cols = []
        for col in poss:
            cell_value = sheet.cell(row,col).value
            fld = fields[itr]
            if fields_types[fld]=='float':
                try:
                    if cell_value:
                        float(cell_value)
                except:
                    if isinstance (cell_value,str) or isinstance (cell_value,unicode):
                        cell_value = cell_value.replace(',','.')
                        try:
                             float(cell_value)
                        except:
                            warning_cols.append(col+1)
            elif fields_types[fld]=='int':
                try:
                    if cell_value:
                        int(cell_value)
                except:
                    warning_cols.append(col+1)
            itr += 1

        if warning_cols:
            warning_lst[row] = warning_cols

    if warning_lst:
        m_info = 'Warning ! Values of some cells cannot be converted to appropriate types in system. Check values of these cells:'
        #m_info = _('Warning ! Values of some cells cannot be converted to appropriate types in system. Check values of these cells:')
        m_col = 'Column'
        #m_col = _('Column')
        m_row = 'Rows'
        #m_row = _('Rows')
        msg = u''' \t\t%s\n\n%s\t\t\t%s\n''' % (m_info,m_row,m_col)
        for key in warning_lst:
            warn = str(warning_lst[key])
            warn = warn[1:-1]
            msg += u'%d\t\t\t\t\t%s\n' % (key+1,warn)

        return msg

#===============================================================================
#===============================================================================


def tmp_xls_import(cr, inst, source, fields, poss, sheet_line_poss, model_nm):
#def tmp_xls_import(cr, inst, source, fields, poss, sheet_line_poss):

    pool = pooler.get_pool(cr.dbname)
    logger = logging.getLogger('imp')
    product_pool = pool.get(model_nm)
#    product_pool = pool.get('product.product')
    uid = 1
    datas = []
    supplier = inst.name

    config_ids = pool.get('imp.config').search(cr,1,[])
    config = pool.get('imp.config').browse(cr,1,config_ids)[0]
    fields_types = eval(config.import_fields_types)

    sheet = source.sheets()[sheet_line_poss[0]]
    fields += ['supplier_id.id']
##    fields += ['supplier.id']
    #raise osv.except_osv(_('Warning'), str(fields))
# #     category = inst.category_id
# #     if category:
# #         fields += ['categ_id.id']
# hardcode by Sasha
# required fields for non-etalon catalog
# yustas
    
    qty_pos = fields.index('quantity')
#    qty_pos = fields.index('imp_qty')
    price_pos = fields.index('price')
#    price_pos = fields.index('standard_price')
    defcode_pos = fields.index('name')
#    defcode_pos = fields.index('default_code')
#    name_pos = fields.index('name')

    new_prod_count = 0
    exist_prod_count = 0
    error_rows_list = []

    for row in xrange(sheet_line_poss[1],sheet.nrows):
        vals = []
        itr = 0
        try:
            for col in poss:
                cell_value = sheet.cell(row,col).value
                cell_type = sheet.cell(row,col).ctype
                fld = fields[itr]
                if cell_type == 2:
                    if fields_types[fld]=='char':
                            if isinstance(cell_value,float):
                                if modf(cell_value)[0]:
                                    cell_value = str(cell_value)
                                else:
                                    cell_value = str(int(cell_value))
                else:
                    if fields_types[fld]=='float':
                        try:
                            if cell_value:
                                cell_value = float(cell_value)
                            else:
                                cell_value = 0.0
                        except:
                            if isinstance (cell_value,str) or isinstance (cell_value,unicode):
                                cell_value = cell_value.replace(',','.')
                                cell_value = float(cell_value)
                    if fields_types[fld]=='int':
                        if cell_value:
                            cell_value = int(cell_value)
                        else:
                            cell_value = 0

                vals.append(cell_value)
                itr += 1
        except:
            vals = []
            error_rows_list.append(row+1)
            #logger.error("Cannot import the line #%s", row+1)

        if any(vals):
            exist_id = product_pool.search(cr, uid, [('name','=',vals[defcode_pos]),('supplier_id','=',supplier.id)])
#            exist_id = product_pool.search(cr, uid, [('name','=',vals[defcode_pos]),('supplier','=',supplier.id)])
#            exist_id = product_pool.search(cr, uid, [('default_code','=',vals[defcode_pos]),('supplier','=',supplier.id)])
            if not exist_id:
                vals += [supplier]
##                if category:
##                    vals += [category]
                datas.append(vals)
                new_prod_count += 1
            else:
                exist = product_pool.browse(cr, uid, exist_id[0])
                product_rewrite = product_pool.write(cr, uid, exist.id,
                                         {'quantity':vals[qty_pos],
                                         #'imp_qty':vals[qty_pos],
                                          'price':vals[price_pos]
#                                          'standard_price':vals[price_pos]
                                          })
                if product_rewrite:
                    logger.warning("\nProduct with ID = %s is rewrote with values:\nQTY = %s\nPRICE = %s" \
                                                     % (exist_id,vals[qty_pos],vals[price_pos]))

#                 if exist.price_ref:
#                     part_inf_rewrite = pool.get('pricelist.partnerinfo').write(cr, uid, exist.price_ref.id,
#                               {'sup_quantity':vals[qty_pos],'price':vals[price_pos]})
#                               #{'min_quantity':vals[qty_pos],'price':vals[price_pos]})
# 				#yustas
#                     if part_inf_rewrite:logger.warning("\nPartber info with ID = %s is rewrote with values:\nQTY = %s\nPRICE = %s" \
#                                                      % (exist.price_ref,vals[qty_pos],vals[price_pos]))
                exist_prod_count += 1
    report = u'* %s : %d %s:' % (time.strftime('%d.%m.%y %H:%M:%S'),new_prod_count+exist_prod_count,('records imported'))
#    report = u'* %s : %d %s:' % (time.strftime('%d.%m.%y %H:%M:%S'),new_prod_count+exist_prod_count,_('records imported'))
    report += u'\n\t- %d %s' % (new_prod_count,('records created'))
    #report += u'\n\t- %d %s' % (new_prod_count,_('records created'))
    report += u'\n\t- %d %s' % (exist_prod_count,('records updated'))
    #report += u'\n\t- %d %s' % (exist_prod_count,_('records updated'))
    if error_rows_list:
        report += u'\n\t- %s: %s' % (('could not import records on rows'),str(error_rows_list)[1:-1])
        #report += u'\n\t- %s: %s' % (_('could not import records on rows'),str(error_rows_list)[1:-1])

    return product_pool.import_data(cr, uid, fields, datas), report

#===============================================================================
#===============================================================================

def tmp_xls_import_etalon(cr, inst, source, fields, poss, sheet_line_poss):

    pool = pooler.get_pool(cr.dbname)
    orig_fields = copy(fields)
    etalon_supplier = inst.name.id
    logger = logging.getLogger('imp')
    product_pool = pool.get('product.product')
    uid = 1
    datas = []

    config_ids = pool.get('imp.config').search(cr,1,[])
    config = pool.get('imp.config').browse(cr,1,config_ids)[0]
    fields_types = eval(config.import_fields_types)

    sheet = source.sheets()[sheet_line_poss[0]]
    fields += ['supplier.id']
    category = inst.category_id
    if category:
        fields += ['categ_id.id']
# required fields Name and Reference (SKU)
#yustas
    name_pos = fields.index('name')
    code_pos = fields.index('default_code')

    new_prod_count = 0
    exist_prod_count = 0
    error_rows_list = []

    for row in xrange(sheet_line_poss[1],sheet.nrows):
        vals = []
        itr = 0
        try:
            for col in poss:
                cell_value = sheet.cell(row,col).value
                cell_type = sheet.cell(row,col).ctype
                fld = fields[itr]
                if cell_type == 2:
                    if fields_types[fld]=='char':
                            if isinstance(cell_value,float):
                                if modf(cell_value)[0]:
                                    cell_value = str(cell_value)
                                else:
                                    cell_value = str(int(cell_value))
                else:
                    if fields_types[fld]=='float':
                        try:
                            if cell_value:
                                cell_value = float(cell_value)
                            else:
                                cell_value = 0.0
                        except:
                            if isinstance (cell_value,str) or isinstance (cell_value,unicode):
                                cell_value = cell_value.replace(',','.')
                                cell_value = float(cell_value)
                    if fields_types[fld]=='int':
                        if cell_value:
                            cell_value = int(cell_value)
                        else:
                            cell_value = 0

                vals.append(cell_value)
                itr += 1
        except:
            vals = []
            error_rows_list.append(row+1)
            #logger.error("Cannot import the line #%s", row+1)
        if any(vals):
            exist_ids = product_pool.search(cr, uid, [('default_code','=',vals[code_pos]),('supplier','=',etalon_supplier)])
            if not exist_ids:
                vals += [etalon_supplier]
                if category:
                    vals += [category]
                datas.append(vals)
                new_prod_count += 1
            else:
                exist_data = product_pool.read(cr, uid, exist_ids[0], orig_fields)
                exist_id = exist_data['id']
                di = {}
                for i in range(len(orig_fields)):
                    di[orig_fields[i]] = vals[i]
                wr = {}
                for key in di:
                    if di[key]:
                        if di[key]!=exist_data[key]:
                            wr[key]=vals[orig_fields.index(key)]
                if wr:
                    product_pool.write(cr, uid, exist_id, wr)
                exist_prod_count += 1

    report = u'* %s : %d %s:' % (time.strftime('%d.%m.%y %H:%M:%S'),new_prod_count+exist_prod_count,('records imported'))
    #report = u'* %s : %d %s:' % (time.strftime('%d.%m.%y %H:%M:%S'),new_prod_count+exist_prod_count,_('records imported'))
    report += u'\n\t- %d %s' % (new_prod_count,('records created'))
    #report += u'\n\t- %d %s' % (new_prod_count,_('records created'))
    report += u'\n\t- %d %s' % (exist_prod_count,('records updated'))
    #report += u'\n\t- %d %s' % (exist_prod_count,_('records updated'))
    if error_rows_list:
        report += u'\n\t- %s: %s' % (_('could not import records on rows'),str(error_rows_list)[1:-1])

    return product_pool.import_data(cr, uid, fields, datas),report

#===============================================================================
#===============================================================================
# csv - old, not updated
#===============================================================================
#===============================================================================

old = '''
def tmp_csv_import(cr, inst, source):

    logger = logging.getLogger('imp')
    pool = pooler.get_pool(cr.dbname)
    product_pool = pool.get('product.product')
    uid = 1
    datas = []
    suppl_name = inst.name.name

    ctg = pool.get('product.category').search(cr, uid, [('name','=',suppl_name)])
    if ctg:
        logger.warning("Category %s already exist" % suppl_name)
        categ_id = ctg[0]
    else:
        logger.warning("Creating category %s" % suppl_name)
        categ_id = pool.get('product.category').create(cr, uid, {'name':suppl_name})

    reader = source
    fields = reader.next() + ['categ_id.id', 'default_code_main']

    name_pos = fields.index('name')
    qty_pos = fields.index('imp_qty')
    price_pos = fields.index('standard_price')

    for line in reader:
        if (not line) or not reduce(lambda x,y: x or y, line) :
            continue
        def_code = '[%s]%s' % (suppl_name, line[name_pos])
        line += [categ_id, def_code]
        exist_id = product_pool.search(cr, uid, [('default_code_main','=',def_code)])
        if not exist_id:
            try:
                datas.append(map(lambda x: ustr(x), line))
            except:
                logger.error("Cannot import the line: %s", line)
        else:
            exist = product_pool.browse(cr, uid, exist_id[0])
            product_rewrite = product_pool.write(cr, uid, exist.id,
                                {'imp_qty':line[qty_pos],'standard_price':line[price_pos]})
            if product_rewrite:
                logger.warning("\nProduct with ID = %s is rewrote with values:\nQTY = %s\nPRICE = %s" \
                                    % (exist_id,line[qty_pos],line[price_pos]))

            if exist.price_ref:
                part_inf_rewrite = pool.get('pricelist.partnerinfo').write(cr, uid, exist.price_ref.id,
                                  {'sup_quantity':line[qty_pos],'price':line[price_pos]})
                                  #{'min_quantity':line[qty_pos],'price':line[price_pos]})
				#yustas
                if part_inf_rewrite:logger.warning("\nPartber info with ID = %s is rewrote with values:\nQTY = %s\nPRICE = %s" \
                                    % (exist.price_ref,line[qty_pos],line[price_pos]))

    return product_pool.import_data(cr, uid, fields, datas)


def tmp_csv_import_etalon(cr, inst, source):

    et_cat_name = 'Etalon product'
    logger = logging.getLogger('imp')
    pool = pooler.get_pool(cr.dbname)
    product_pool = pool.get('product.product')
    uid = 1
    datas = []
    etal_categ_id = pool.get('product.category').search(cr, uid, [('name','=',et_cat_name)])[0]

    reader = source
    fields = reader.next() + ['categ_id.id']

    name_pos = fields.index('name')

    for line in reader:
        if (not line) or not reduce(lambda x,y: x or y, line) :
            continue
        line += [str(etal_categ_id)]
        exist_ids = product_pool.search(cr, uid, [('name','=',line[name_pos])])
        if not exist_ids:
            try:
                datas.append(map(lambda x: ustr(x), line))
            except:
                logger.error("Cannot import the line: %s", line)

    return product_pool.import_data(cr, uid, fields, datas)

'''
