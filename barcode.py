__version__ = (2, 0, 0)

# meta developer: @RUIS_VlP
# requires: python-barcode[images]
import barcode
from barcode.writer import ImageWriter
from .. import loader, utils
import uuid
import os

async def generate_barcode(data, filename):
    options = {
        'write_text': False,
        'quiet_zone': 2,
        'module_height': 15.0
    }
    code128 = barcode.get('code128', data, writer=ImageWriter())
    code128.save(filename, options)

@loader.tds
class BarcodeGeneratorMod(loader.Module):
    """Генерирует штрих код (code128) """

    strings = {
        "name": "BarcodeGenerator",
    }

    @loader.command()
    async def barcodecmd(self, message):
        """<код> - генерирует штрих-код"""
        args = utils.get_args_raw(message)
        if not args:
        	args = " "
        randuuid = str(uuid.uuid4())
        filename = f"{randuuid}.png"
        await generate_barcode(args, randuuid)
        await utils.answer_file(message, filename, caption=args)
        os.remove(filename)