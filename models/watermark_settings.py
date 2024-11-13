# -*- encoding: UTF-8 -*-
""" Watermart config settings"""

from odoo import models, fields, api, tools
from odoo.modules.module import get_module_resource
import base64
import logging
_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    """ Inherit config settings model to add watermark config settings"""
    _inherit = 'res.config.settings'

    watermarking = fields.Boolean(
        string='Watermarking',
        config_parameter='product_watermarking.watermarking'
    )
    watermark_picture = fields.Binary(
        string="Watermark Image",
        help="Upload an image to be set as a watermark to your product's images",
    )
    watermarking_option = fields.Selection(
        selection=[('center', 'Center'), ('diagonal', 'Diagonal')],
        string="Watermarking Direction",
        default="center",
        config_parameter='product_watermarking.watermarking_option',
    )
    keep_original_image = fields.Boolean(
        string="Keep Original Image",
        default=True,
        help='Whether to save the original non watermarked image',
        config_parameter='product_watermarking.keep_original_image',
    )  

    def _get_default_image(self):
        """ Get default image"""
        img_path = get_module_resource(
            'product_watermarking', 'static/src/img', 'target_integration.png')
        try:
            with open(img_path, 'rb') as image_file:
                image_content = image_file.read()
                # Encoding the image content to base64 and decoding to string
                image_encoded = base64.b64encode(image_content).decode('utf-8')
                return image_encoded
        except FileNotFoundError:
            _logger.error(f"------------------Image file not found at path: {img_path}")
            return None
        except Exception as e:
            _logger.error(f"------------------Error reading or encoding image: {e}")
            return None

    def get_values(self):
        """ Override get_values method"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            watermark_picture=params.get_param(
                'product_watermarking.watermark_picture',
                default=self._get_default_image()
            ),
        )
        return res

    def set_values(self):
        """ Override set_values method"""
        super(ResConfigSettings, self).set_values()
        value_picture = self.watermark_picture
        self.env['ir.config_parameter'].sudo().set_param(
            'product_watermarking.watermark_picture', value_picture)
