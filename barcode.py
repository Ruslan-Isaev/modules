version = (1, 0, 0)

# meta developer: @RUIS_VlP
# requires: treepoem pillow
from .. import loader, utils
import treepoem
import uuid
import os
from PIL import Image, ImageOps

async def generate_barcode(data, filename, border_size=20):
    barcode = treepoem.generate_barcode(
            barcode_type="code128",
            data=data
        )
    barcode_with_border = ImageOps.expand(barcode, border=border_size, fill="white")
    barcode_with_border.save(filename)

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
        randuuid = str(uuid.uuid4())
        filename = f"{randuuid}.png"
        await generate_barcode(args, filename)
        await utils.answer_file(message, filename, caption=args)
        os.remove(filename)
