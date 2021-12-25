# -*- coding: utf-8 -*-
from pathlib import Path

import yaml
from fastapi import File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

router = InferringRouter(tags=['Mixer Table'])


@cbv(router)
class SpectrumProfilesCRUD:
    mixer_table_0 = Path('MixerTableExcels/MixerTable.xlsx')
    mixer_table_1 = Path('MixerTableExcels/MixerTable_1.xlsx')
    mixer_table_2 = Path('MixerTableExcels/MixerTable_2.xlsx')

    @router.get("/MixerTableExcels/")
    def get_file(self):
        """Retrieves a ONLY the first file"""
        return FileResponse(self.mixer_table_0, filename='MixerTable.xlsx')

    @router.put("/MixerTableExcels/0")
    async def update_file0(self, file: UploadFile = File(...)):
        return await self.update_files(file, self.mixer_table_0)

    @router.put("/MixerTableExcels/1")
    async def update_file1(self, file: UploadFile = File(...)):
        return await self.update_files(file, self.mixer_table_1)

    @router.put("/MixerTableExcels/2")
    async def update_file2(self, file: UploadFile = File(...)):
        return await self.update_files(file, self.mixer_table_2)

    async def update_files(self, file, file_path: Path):
        if file.filename != file_path.name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File name is not matching.")
        try:
            import pandas as pd
            cont = await file.read()
            read_file = pd.read_excel(cont)
            read_file.to_excel(file_path)
            from devices.system import sys
            sys.load_system()
            return read_file.values.tolist()
        except yaml.YAMLError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File is not valid YAML format.")
