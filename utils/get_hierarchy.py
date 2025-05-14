from sqlmodel import select, Session
from fastapi import Depends
from typing import Annotated, List
from models import Account
from db import SECRET_KEY, get_session

from models.Account import Organization


SessionDep = Annotated[Session, Depends(get_session)]


def get_child_organization(session: SessionDep, organization_id: int):
    """
    Fetch all child organizations (descendants) from the database.
    """
    if organization_id is None:
        heirarchy = {'tenants': []}
    else:
        heirarchy = []
        
    children = session.exec(select(Organization).where(Organization.parent_id == organization_id)).all()
    
    for a_child in children:
        if organization_id is None:
            heirarchy['tenants'].append({'id': a_child.id, 'name': a_child.organization_name, 'children': get_child_organization(session, a_child.id)})
        else:        
            heirarchy.append({'id': a_child.id, 'name': a_child.organization_name, 'children': get_child_organization(session, a_child.id)})
        
    if len(children):
        return heirarchy
    else:
        return []  

def get_parent_organizations(session: SessionDep, organization_id: int) -> List[int]:
    """
    Fetch all parent organizations recursively (up to the top-level root).
    """
    parents = []
    current_id = organization_id

    while current_id is not None:
        org = session.get(Organization, current_id)
        if not org or org.parent_id is None:
            break
        parents.append(org.parent_id)
        current_id = org.parent_id

    return parents  # List of parent IDs (ordered bottom-up)


#Let’s say you want to return all related organizations with their hierarchy, you could do:
def get_org_with_parents(session: Session, org_ids: List[int]) -> List[Organization]:
    all_ids = set(org_ids)
    for org_id in org_ids:
        parent_ids = get_parent_organizations(session, org_id)
        all_ids.update(parent_ids)
    return session.exec(select(Organization).where(Organization.id.in_(all_ids))).all()



def get_child_employee(session: SessionDep, employee_id: int):
    """
    Fetch all subordinate employees from the database.
    """
    # TODO check for circular using a dict (dijkstra)
    queue = []
    queue.append(employee_id)

    employee = []
    while queue != []:
        emp = queue.pop(0)
        employee.append(emp)
        db_emp = session.exec(
            select(Account.id).where(Account.manager == employee_id)
        ).all()
        queue.extend(db_emp)

    return employee
