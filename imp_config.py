# -*- coding: utf-8 -*-
import os.path
from openerp.osv import fields, osv
from openerp.tools import logging, file_open #, ustr
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

class imp_config(osv.osv):

    _name = 'imp.config'
    _columns = {
        'name': fields.char('Name', size=64),
        'import_fields_types': fields.text('Fields types'),
        'data_type': fields.selection([('virt.tire','Virtual tire'), ('virt.disk','Virtual disk')],string='Choose the data model type: tyre, disk, etc.')
    }
    _auto = True

    _defaults = {
        'name': 'Import fields config'
    }


    def get_prod_fields(self, cr, uid, ids, context={}):

        inst = self.browse(cr, uid, ids)[0]
        fields = self.pool.get(inst.data_type).fields_get(cr,1)
#        fields = self.pool.get('product.proxy').fields_get(cr,1)

        imp_model_id = self.pool.get('ir.model').search(cr, 1, [('model','=','imp.config')])[0]
        #imp_form_ids = self.pool.get('ir.ui.view').search(cr, 1, [('name','=','imp.config.form')])
        imp_form_id = self.pool.get('ir.ui.view').search(cr, 1, [('name','=','imp.config.form')])[-1]
#        imp_form_id = self.pool.get('ir.ui.view').search(cr, 1, [('name','=','imp.config.form')])[0]
        imp_form = self.pool.get('ir.ui.view').browse(cr, 1, imp_form_id)
        arch = imp_form.arch
        st = ''
        end = '''</group>
</form>'''
        allowed_types = ['float', 'integer', 'char', 'text']
        restricted_fields = []
        keys = fields.keys()
        keys.sort()
        for field in keys:
            if fields[field]['type'] in allowed_types and field not in restricted_fields:
                field_descript = fields[field]['string']
                exist = self.pool.get('ir.model.fields').search(cr, 1, [('name','=','x_'+ field),('model_id','=',imp_model_id)])
                if not exist:
                    new = self.pool.get('ir.model.fields').create(cr, 1, {'name':'x_bool_'+ field,
                                                                        'model_id':imp_model_id,
                                                                        'ttype':'boolean',
                                                                        'state':'manual',
                                                                        'field_description': field_descript
                                                                        })
                if ('x_bool_'+field) in arch:
                    continue
                else:
                    st+='''<field name="x_bool_%s" colspan="3" />\n''' % (field,)
        if st:
            arch = arch.replace(end, st+end)
            self.pool.get('ir.ui.view').write(cr, 1, imp_form_id, {'arch': arch})

        return True

    def set_imp_prod_fields(self, cr, uid, ids, context={}):

        inst = self.browse(cr, uid, ids)[0]
        self_fields = self.fields_get(cr,uid)
#        self_fields = self.pool.get('imp.config').fields_get(cr,uid)
        keys = self_fields.keys()
        allowed_fields = []
        for key in keys:
            if key.startswith('x_bool_'):
                if getattr(inst,key):
                    allowed_fields.append(key[7:])

        fields = self.pool.get(inst.data_type).fields_get(cr,1)
#        fields = self.pool.get('product.proxy').fields_get(cr,1)

        imp_model_id = self.pool.get('ir.model').search(cr, 1, [('model','=','imp.imp')])[0]
        imp_form_id = self.pool.get('ir.ui.view').search(cr, 1, [('name','=','imp.imp.form')])[0]
        imp_form = self.pool.get('ir.ui.view').browse(cr, 1, imp_form_id)
        arch = imp_form.arch
        st = ''
        end = '''</group>
</page>
</notebook>
</form>'''
        allowed_types = ['float', 'integer', 'char', 'text']
        restricted_fields = []

        keys = fields.keys()
        keys.sort()
        fields_types_to_save = {}
        for field in keys:
            if fields[field]['type'] in allowed_types and field not in restricted_fields and field in allowed_fields:
                field_type = fields[field]['type']
                field_descript = fields[field]['string']
                fields_types_to_save[field] = field_type
                exist = self.pool.get('ir.model.fields').search(cr, 1, [('name','=','x_'+ field),('model_id','=',imp_model_id)])
                if not exist:
                    new = self.pool.get('ir.model.fields').create(cr, 1, {'name':'x_'+ field,
                                                                        'model_id':imp_model_id,
                                                                        'ttype':'integer',
                                                                        'state':'manual',
                                                                        'field_description': field_descript
                                                                        })
                    new = self.pool.get('ir.model.fields').create(cr, 1, {'name':'x_bool_'+ field,
                                                                        'model_id':imp_model_id,
                                                                        'ttype':'boolean',
                                                                        'state':'manual',
                                                                        'field_description': field_descript
                                                                        })

                if 'x_'+field in arch:
                    continue
                else:
                    st+=''' <field name="x_bool_%s" nolabel="1" colspan="3" attrs="{'invisible':[('x_bool_%s','=',0),('hide_unused','=',1)]}"/>\n
                            <field name="x_%s" colspan="3" attrs="{'readonly':[('x_bool_%s','=',0)],'invisible':[('x_bool_%s','=',0),('hide_unused','=',1)]}" />\n
                            ''' % (field,field,field,field,field)

        if fields_types_to_save:
            self.write(cr, uid, inst.id, {'import_fields_types': str(fields_types_to_save)})
            # debug for Set imp fields
            # raise osv.except_osv(_('Warning'), fields_types_to_save)
        if st:
            arch = arch.replace(end, st+end)
            self.pool.get('ir.ui.view').write(cr, 1, imp_form_id, {'arch': arch})

        return True

imp_config()

