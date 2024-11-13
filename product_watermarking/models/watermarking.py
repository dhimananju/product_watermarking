# -*- coding: utf-8 -*-
"""Product file"""

import base64
import io
import codecs
import math
import logging
from PIL import Image, ImageEnhance
from odoo import models, fields, api
_logger = logging.getLogger(__name__)


def get_product_image_fields():
    """ Get product image fields """
    return ['image_1920', 'image_1024', 'image_512', 'image_256', 'image_128']


class ProductTemplate(models.Model):
    """ Inherit Product Template model"""
    _inherit = 'product.template'

    original_image = fields.Binary(
        string='Original Image',
        help='Holds the original non watermarked image',
        readonly=True
    )
    is_watermarked = fields.Boolean(
        string='Whether this product\'s image is watermarked', readonly=True)

    def write(self, vals):
        """ Override write method"""
        _logger.info("="*90)
        _logger.info("\nWrite method for product.template is called.\n")

        vals = self.full_watermark(vals)
        if self.env.context.get("called_from_pp") and 'original_image' in vals.keys():
            if self.env.context.get("original_image"):
                vals.update(
                    {"original_image": self.env.context.get("original_image")})
        if not self.env.context.get("called_from_pp") and 'original_image' in vals.keys():
            for product in self:
                if len(product.product_variant_ids) == 1:
                    variant_images = {}
                    variant_images.update(
                        {'original_image': vals['original_image']})
                    product.product_variant_ids.write(variant_images)
        res = super(ProductTemplate, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        """ Override create method"""
        _logger.info("="*90)
        _logger.info("\nCreate method for product.template.\n")

        return_value = self.full_watermark(vals)
        if self.env.context.get("called_from_pp") and 'original_image' in vals.keys():
            if self.env.context.get("original_image"):
                vals.update(
                    {"original_image": self.env.context.get("original_image")})
        created_product = super(ProductTemplate, self).create(return_value)
        if 'original_image' in vals.keys() and len(created_product.product_variant_ids) == 1:
            variant_images = {}
            variant_images.update({'original_image': vals['original_image']})
            created_product.product_variant_ids.write(variant_images)
        return created_product

    def full_watermark(self, vals):
        """ Watermark method """
        _logger.info("="*90)
        _logger.info("full_watermark method called")
        _logger.info("+"*90)
        _logger.info(vals.keys())
        ir_config = self.env['ir.config_parameter'].sudo()
        _logger.info("+"*90)
        _logger.info(ir_config)
        config_settings = self.env['res.config.settings'].sudo().get_values()
        _logger.info("+"*90)
        _logger.info(config_settings.keys())
        if ir_config.get_param('product_watermarking.watermarking') and config_settings.get("watermark_picture"):
            # can be binary or relational image related field
            keys = get_product_image_fields()
            for field in keys:
                if field in vals:
                    is_binary_field = False
                    list_image_dict = []

                    # New code 2022
                    if isinstance(vals.get(field), list):
                        # means field is one2many or many2many
                        _logger.info(f"\n{field} is either on2many or many2many.\n")
                        pass
                    elif isinstance(vals.get(field), int):
                        # means field is many2one, not supporting many2one field now
                        _logger.info(f"\n{field} is many2one type.\n")
                        pass
                    else:
                        is_binary_field = True
                        list_image_dict = [{"image": vals.get(field)}]
                        _logger.info(f"\n\nList Image Dict: {list_image_dict}\n")

                    # list_image_dict will list of dict. Each dict will hold image data with 'image' key.
                    for image_dict in list_image_dict:
                        original_image = image_dict.get('image', False)
                        if original_image:  # This means we have a new image
                            _logger.info(f"\n=========>We do have original image.<=============\n")
                            # Get the watermark image
                            image_string_1 = io.BytesIO(base64.b64decode(
                                config_settings.get("watermark_picture")))
                            watermark_image = Image.open(image_string_1)

                            # Get the new image
                            if isinstance(image_dict.get('image'), str):
                                image_string_2 = io.BytesIO(base64.b64decode(
                                    codecs.encode(image_dict.get('image'))))
                            else:
                                image_string_2 = io.BytesIO(
                                    base64.b64decode(image_dict.get('image')))
                            new_product_image = Image.open(image_string_2)

                            _logger.info(f"\nNew Product Image: {new_product_image}\n")

                            # Check setting whether to rotate the watermark image
                            if ir_config.get_param('product_watermarking.watermarking_option') == 'diagonal':
                                _logger.info(f"\n\nWatermark should be placed diagonally!\n")
                                width, height = new_product_image.size
                                division = float(height) / width
                                watermark_image = watermark_image.rotate(
                                    math.degrees(math.atan(division)),
                                    expand=True
                                )

                            # Watermark
                            watermarked_final_image = ProductTemplate.watermark(
                                new_product_image,
                                watermark_image,
                                'scale',
                                1.0
                            )

                            # Put the watermarked image to vals again (encoded in base64)
                            _buffer = io.BytesIO()
                            watermarked_final_image.save(
                                _buffer, format="JPEG")
                            watermarked_final_image_string = base64.b64encode(
                                _buffer.getvalue())
                            image_dict['image'] = watermarked_final_image_string
                            vals.update({
                                'is_watermarked': True,
                                'original_image': original_image
                            })
                            if is_binary_field:
                                # needed for binary field as we using dummy variable for this
                                vals.update({
                                    field: watermarked_final_image_string,
                                })
        return vals

    @staticmethod
    def watermark(ti_image, mark, position, opacity=1):
        """Adds a watermark to an image."""

        _logger.info(f"\nWatermark method is called.\n")
        if opacity < 1:
            mark = ProductTemplate.reduce_opacity(mark, opacity)
        if ti_image.mode != 'RGB':
            ti_image = ti_image.convert('RGB')
        # create a transparent layer the size of the image and draw the
        # watermark in that layer.
        layer = Image.new('RGBA', ti_image.size, (0, 0, 0, 0))
        if position == 'tile':
            for index_y in range(0, ti_image.size[1], mark.size[1]):
                for index_x in range(0, ti_image.size[0], mark.size[0]):
                    layer.paste(mark, (index_x, index_y))
        elif position == 'scale':
            # scale, but preserve the aspect ratio
            ratio = min(
                float(ti_image.size[0]) / mark.size[0], float(ti_image.size[1]) / mark.size[1])
            width = int(mark.size[0] * ratio)
            height = int(mark.size[1] * ratio)
            mark = mark.resize((width, height))
            layer.paste(
                mark, (int((ti_image.size[0] - width) / 2), int((ti_image.size[1] - height) / 2)))
        else:
            layer.paste(mark, position)
        # composite the watermark with the layer
        return Image.composite(layer, ti_image, layer)

    @staticmethod
    def reduce_opacity(ti_image, opacity):
        """Returns an image with reduced opacity."""
        assert 0 <= opacity <= 1
        if ti_image.mode != 'RGB':
            ti_image = ti_image.convert('RGB')
        else:
            ti_image = ti_image.copy()
        alpha = ti_image.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        ti_image.putalpha(alpha)
        return ti_image

class ProductProduct(models.Model):
    """ Inherit Product model"""
    _inherit = 'product.product'

    original_image = fields.Binary(
        string='Original Image',
        help='Holds the original non watermarked image',
        readonly=True
    )
    is_watermarked = fields.Boolean(
        string='Whether this product\'s image is watermarked', readonly=True)

    def write(self, vals):
        """ Override write method."""

        _logger.info(f"\nWrite method for product.product is called.\n")
        vals_final = self.full_watermark(vals)
        return super(
            ProductProduct,
            self.with_context(called_from_pp=True, original_image=vals_final.get("original_image"))
        ).write(vals_final)

    @api.model
    def create(self, vals):
        """ Override create method."""

        _logger.info(f"\nCreate method for product.product is called.\n")
        vals = self.full_watermark(vals)
        return super(
            ProductProduct,
            self.with_context(called_from_pp=True, original_image=vals.get("original_image"))
        ).create(vals)

    def full_watermark(self, vals):
        """ Watremark method."""
        return self.env["product.template"].full_watermark(vals)
