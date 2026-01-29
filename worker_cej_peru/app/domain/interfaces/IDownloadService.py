from abc import ABC, abstractmethod

class IDownloadService(ABC):
  

    @abstractmethod
    async def upload_data(self,driver, radicado, cod_despacho_rama,conn, case_download_dir, data_process_rama, actors_rama):
        pass