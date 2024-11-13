# -*- coding: utf-8 -*-
{
    'name': "Website Image Watermark",

    'summary': """
        Watermarking of base images""",
    'price': '30',
    'currency': 'EUR',
    'description': """
        This module adds a watermark image set on Settings on top of the product's images
    """,

    'author': "Target Integration",
    'website': "http://www.targetintegration.com",
    'category': 'Uncategorized',
    'version': '17.0.1.0',
    'live_test_url': 'https://www.targetintegration.com/openerp',

    'depends': ['base', 'product', 'sales_team'],

    'data': [
        'security/ir.model.access.csv',
        'views/settings.xml',
        # 'views/product_watermarking.xml',
        'views/save_original_image.xml',
    ],
    'assets': {
        'web.assets_backend': [
            "product_watermarking/static/src/css/settings_screen.css"
        ]
    },
    'images': [
        'static/description/watermark_banner.jpeg',
    ],
    # 'css': [
    #     'static/src/css/settings_screen.css',
    # ],
    'application': True,
}
