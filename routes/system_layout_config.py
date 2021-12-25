from pathlib import Path

import yaml
from fastapi import HTTPException, status
from fastapi import UploadFile, File
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from starlette.responses import FileResponse

router = InferringRouter(tags=["System Layout"])


@cbv(router)
class SystemSetup:
    ROOT_FOLDER = Path('config/system_layout_config.yaml')

    @router.get("/system_layout_config/")
    def get_file(self):
        """Retrieves a file given a path - if the file is empty is does not return a download link"""
        return FileResponse(self.ROOT_FOLDER, filename='system_layout_config.yaml')

    @router.put("/system_layout_config/")
    async def update_file(self, file: UploadFile = File(...)):
        """Updates an existing file given a path"""
        if file.filename != self.ROOT_FOLDER.name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File name is not matching.")
        try:
            content = await file.read()
            parsed_data = yaml.load(content, Loader=yaml.FullLoader)
            with open(self.ROOT_FOLDER, 'w') as f:
                yaml.safe_dump(parsed_data, f, default_flow_style=False)
            from devices.system import sys
            sys.load_system()
            return parsed_data
        except yaml.YAMLError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File is not valid YAML format.")
