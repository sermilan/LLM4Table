from pydantic import BaseModel
from typing import List, Optional

class DataTable(BaseModel):
    id: str
    table_name: str
    file_path: str
    file_name: str
    description: Optional[str] = None
    columns: List[str]
    row_count: int
    column_count: int

class DataUploadResponse(BaseModel):
    success: bool
    message: str
    data: DataTable