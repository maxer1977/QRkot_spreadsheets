from app.crud.base import CRUDBase
from app.models.donation import Donation


class CRUDProject(CRUDBase):
    pass


crud_donations = CRUDProject(Donation)
