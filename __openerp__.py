# -*- coding: utf-8 -*-
{
    'name': "product_proxy",
    'summary':'For price merging', 
    'description':'qqqqqqqqqqqqqqqqqqqqqqq', 
    'author': "Yustas",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','crm','sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv', 'product_proxy.xml', 'menu.xml', 'imp_data.xml', 'imp_config_data.xml', 'parser.xml'
#        'security/ir.model.access.csv', 'data/parse_dict_keys.csv','product_proxy.xml', 'menu.xml', 'imp_data.xml', 'imp_config_data.xml', 'parser.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}